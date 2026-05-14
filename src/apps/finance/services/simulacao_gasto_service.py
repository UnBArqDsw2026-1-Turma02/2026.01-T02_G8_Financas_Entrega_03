"""SimulacaoGastoService — Issue #10.

Avalia o impacto financeiro de um gasto (à vista ou parcelado) antes de
realizá-lo, retornando orçamento atual, novo orçamento, novo limite diário
e a sinalização de impacto superior a 30% do orçamento mensal.
"""

from __future__ import annotations

import calendar
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import Entrada, Parcelamento, Saida, TipoGasto

CENTAVO = Decimal("0.01")
LIMITE_IMPACTO = Decimal("0.30")


class SimulacaoGastoService:
    def simular(
        self,
        usuario,
        valor: Decimal,
        parcelado: bool = False,
        num_parcelas: int = 1,
    ) -> dict[str, Any]:
        valor = self._normalizar_valor(valor)
        num_parcelas = self._normalizar_parcelas(parcelado, num_parcelas)

        hoje = timezone.now()
        dias_mes = calendar.monthrange(hoje.year, hoje.month)[1]

        renda = self._renda_mensal(usuario, hoje.year, hoje.month)
        gastos_fixos = self._gastos_fixos(usuario, hoje.year, hoje.month)
        orcamento_atual = (renda - gastos_fixos).quantize(CENTAVO)

        impacto_mensal = (
            (valor / Decimal(num_parcelas)) if parcelado else valor
        ).quantize(CENTAVO)

        novo_orcamento = (orcamento_atual - impacto_mensal).quantize(CENTAVO)
        limite_diario_atual = (
            orcamento_atual / Decimal(dias_mes)
        ).quantize(CENTAVO)
        novo_limite_diario = (
            novo_orcamento / Decimal(dias_mes)
        ).quantize(CENTAVO)

        impacta_30 = (
            orcamento_atual > 0
            and impacto_mensal > orcamento_atual * LIMITE_IMPACTO
        )
        dentro_orcamento = (
            orcamento_atual > 0 and impacto_mensal <= orcamento_atual
        )

        resultado: dict[str, Any] = {
            "impacta_30_porcento": impacta_30,
            "dentro_orcamento": dentro_orcamento,
            "orcamento_mensal_atual": orcamento_atual,
            "novo_orcamento": novo_orcamento,
            "limite_diario_atual": limite_diario_atual,
            "novo_limite_diario": novo_limite_diario,
        }

        if parcelado:
            valor_parcela = (valor / Decimal(num_parcelas)).quantize(CENTAVO)
            resultado["simulacao_parcelamento"] = {
                "valor_parcela": valor_parcela,
                "impacto_mensal": valor_parcela,
            }

        return resultado

    @staticmethod
    def _normalizar_valor(valor: Decimal) -> Decimal:
        if valor is None:
            raise ValidationError({"valor": "Valor é obrigatório."})
        if not isinstance(valor, Decimal):
            valor = Decimal(valor)
        if valor <= 0:
            raise ValidationError({"valor": "Valor deve ser maior que zero."})
        return valor

    @staticmethod
    def _normalizar_parcelas(parcelado: bool, num_parcelas: int) -> int:
        if not parcelado:
            return 1
        if num_parcelas is None or int(num_parcelas) < 1:
            raise ValidationError(
                {"num_parcelas": "Número de parcelas deve ser >= 1."}
            )
        return int(num_parcelas)

    @staticmethod
    def _renda_mensal(usuario, ano: int, mes: int) -> Decimal:
        total = Entrada.objects.filter(
            usuario=usuario, data__year=ano, data__month=mes
        ).aggregate(s=Sum("valor"))["s"]
        return total or Decimal("0")

    @staticmethod
    def _gastos_fixos(usuario, ano: int, mes: int) -> Decimal:
        saidas_fixas = Saida.objects.filter(
            usuario=usuario,
            tipo_gasto=TipoGasto.FIXO,
            data__year=ano,
            data__month=mes,
        ).aggregate(s=Sum("valor"))["s"] or Decimal("0")
        parcelas = Parcelamento.objects.filter(usuario=usuario).aggregate(
            s=Sum("valor_parcela")
        )["s"] or Decimal("0")
        return saidas_fixas + parcelas
