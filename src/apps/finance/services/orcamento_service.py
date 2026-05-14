"""OrcamentoService — motor financeiro de Limite Diário, Reserva e Extra (Issue #11).

Implementa as regras do Theme 2 do backlog:

- **Limite Diário**: `(renda_mensal - gastos_fixos_mensais) / dias_do_mes`. Pode ser
  ajustado pelo usuário para um valor menor que o calculado.
- **Reserva**: acumula a sobra dos dias em que o gasto fica abaixo do limite e é
  debitada quando o gasto excede o limite.
- **Extra**: quando a reserva chega a zero e ainda há excesso, o saldo negativo
  vira "extra". Enquanto houver extra, o limite diário é recalculado
  descontando o extra da renda disponível.
"""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import (
    Entrada,
    Extra,
    LimiteDiario,
    Parcelamento,
    Reserva,
    Saida,
    TipoGasto,
)

CENTAVO = Decimal("0.01")
ZERO = Decimal("0.00")


class OrcamentoService:
    """Service que centraliza o cálculo de limite/reserva/extra para um usuário."""

    def obter_limite_diario(self, usuario, data_ref: date | None = None) -> LimiteDiario:
        """Retorna (criando, se preciso) o `LimiteDiario` do usuário em `data_ref`.

        Antes de devolver, recalcula `limite_calculado` e `gasto_dia` para refletir
        o estado atual das transações do mês.
        """
        if data_ref is None:
            data_ref = timezone.localdate()

        with transaction.atomic():
            self._recalcular_orcamento(usuario, data_ref)
            limite, _ = LimiteDiario.objects.get_or_create(
                usuario=usuario, data=data_ref
            )
            limite.refresh_from_db()
            return limite

    def ajustar_limite(self, usuario, novo_limite: Decimal, data_ref: date | None = None) -> LimiteDiario:
        """Permite ao usuário ajustar o limite do dia para um valor menor que o calculado."""
        if novo_limite is None:
            raise ValidationError({"limite_ajustado": "Limite é obrigatório."})
        if not isinstance(novo_limite, Decimal):
            novo_limite = Decimal(novo_limite)
        if novo_limite < 0:
            raise ValidationError(
                {"limite_ajustado": "Limite não pode ser negativo."}
            )

        limite = self.obter_limite_diario(usuario, data_ref)
        if novo_limite > limite.limite_calculado:
            raise ValidationError(
                {
                    "limite_ajustado": (
                        "Limite ajustado deve ser menor ou igual ao calculado."
                    )
                }
            )
        limite.limite_ajustado = novo_limite.quantize(CENTAVO)
        limite.save(update_fields=["limite_ajustado"])
        return limite

    def obter_reserva(self, usuario) -> Reserva:
        self._recalcular_orcamento(usuario, timezone.localdate())
        reserva, _ = Reserva.objects.get_or_create(usuario=usuario)
        reserva.refresh_from_db()
        return reserva

    def obter_extra_mes(self, usuario, ano: int | None = None, mes: int | None = None) -> Decimal:
        """Soma o `Extra` acumulado no mês informado (default: mês atual)."""
        hoje = timezone.localdate()
        if ano is None:
            ano = hoje.year
        if mes is None:
            mes = hoje.month
        self._recalcular_orcamento(usuario, hoje)
        total = Extra.objects.filter(
            usuario=usuario, data__year=ano, data__month=mes
        ).aggregate(s=Sum("valor"))["s"]
        return (total or ZERO).quantize(CENTAVO)

    def recalcular_apos_transacao(self, usuario, data_ref: date | None = None) -> None:
        """Hook chamado após criação/edição/remoção de uma transação."""
        if data_ref is None:
            data_ref = timezone.localdate()
        self._recalcular_orcamento(usuario, data_ref)

    def _recalcular_orcamento(self, usuario, data_ref: date) -> None:
        """Recalcula o estado do orçamento do mês corrente.

        - Reseta `Reserva` e `Extra` do mês.
        - Para cada dia do mês até `data_ref`, processa o saldo (sobra/excesso).
        - Atualiza o `LimiteDiario` de `data_ref` com `gasto_dia` e
          `limite_calculado` (descontando o extra acumulado, se houver).
        """
        ano, mes = data_ref.year, data_ref.month
        dias_mes = calendar.monthrange(ano, mes)[1]

        renda = self._renda_mensal(usuario, ano, mes)
        fixos = self._gastos_fixos(usuario, ano, mes)
        limite_base = self._dividir(renda - fixos, dias_mes)
        if limite_base < 0:
            limite_base = ZERO

        with transaction.atomic():
            Extra.objects.filter(
                usuario=usuario, data__year=ano, data__month=mes
            ).delete()
            reserva, _ = Reserva.objects.select_for_update().get_or_create(
                usuario=usuario
            )
            reserva.saldo = ZERO
            extra_acumulado = ZERO

            # Processa apenas dias FECHADOS (anteriores a data_ref) para
            # reserva/extra. O dia corrente só atualiza gasto_dia/limite.
            for dia in range(1, data_ref.day):
                data_dia = date(ano, mes, dia)
                gasto = self._gasto_variavel_do_dia(usuario, data_dia)
                limite_aplicavel = self._dividir(
                    renda - fixos - extra_acumulado, dias_mes
                )
                if limite_aplicavel < 0:
                    limite_aplicavel = ZERO

                diff = limite_aplicavel - gasto  # >0 sobra; <0 excesso
                if diff >= 0:
                    reserva.saldo = (reserva.saldo + diff).quantize(CENTAVO)
                else:
                    excesso = -diff
                    if reserva.saldo >= excesso:
                        reserva.saldo = (reserva.saldo - excesso).quantize(CENTAVO)
                    else:
                        novo_extra = (excesso - reserva.saldo).quantize(CENTAVO)
                        reserva.saldo = ZERO
                        Extra.objects.update_or_create(
                            usuario=usuario,
                            data=data_dia,
                            defaults={"valor": novo_extra},
                        )
                        extra_acumulado = (extra_acumulado + novo_extra).quantize(
                            CENTAVO
                        )

            # Dia corrente: limite_calculado descontando extra acumulado e gasto_dia.
            data_atual = date(ano, mes, data_ref.day)
            gasto_hoje = self._gasto_variavel_do_dia(usuario, data_atual)
            limite_hoje = self._dividir(
                renda - fixos - extra_acumulado, dias_mes
            )
            if limite_hoje < 0:
                limite_hoje = ZERO

            limite_atual, _ = LimiteDiario.objects.get_or_create(
                usuario=usuario, data=data_atual
            )
            limite_atual.limite_calculado = limite_hoje.quantize(CENTAVO)
            limite_atual.gasto_dia = gasto_hoje.quantize(CENTAVO)
            if (
                limite_atual.limite_ajustado is not None
                and limite_atual.limite_ajustado > limite_atual.limite_calculado
            ):
                limite_atual.limite_ajustado = None
            limite_atual.save()

            reserva.save(update_fields=["saldo"])

    @staticmethod
    def _renda_mensal(usuario, ano: int, mes: int) -> Decimal:
        total = Entrada.ativas_no_mes(usuario, ano, mes).aggregate(
            s=Sum("valor")
        )["s"]
        return total or ZERO

    @staticmethod
    def _gastos_fixos(usuario, ano: int, mes: int) -> Decimal:
        saidas_fixas = Saida.objects.filter(
            usuario=usuario,
            tipo_gasto=TipoGasto.FIXO,
            data__year=ano,
            data__month=mes,
        ).aggregate(s=Sum("valor"))["s"] or ZERO
        parcelas = Parcelamento.ativos_no_mes(usuario, ano, mes).aggregate(
            s=Sum("valor_parcela")
        )["s"] or ZERO
        return saidas_fixas + parcelas

    @staticmethod
    def _gasto_variavel_do_dia(usuario, dia: date) -> Decimal:
        total = Saida.objects.filter(
            usuario=usuario,
            tipo_gasto=TipoGasto.VARIAVEL,
            data__year=dia.year,
            data__month=dia.month,
            data__day=dia.day,
        ).aggregate(s=Sum("valor"))["s"]
        return total or ZERO

    @staticmethod
    def _dividir(numerador: Decimal, divisor: int) -> Decimal:
        if divisor <= 0:
            return ZERO
        return (numerador / Decimal(divisor)).quantize(CENTAVO)
