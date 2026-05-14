"""ProgressoService — streak de economia e calendário mensal (Issue #13).

Para cada dia do mês corrente, classifica o estado do orçamento em uma das três
situações: `dentro_limite`, `usou_reserva` (excesso coberto pelas sobras) ou
`usou_extra` (excesso além da reserva). O streak conta dias consecutivos a
partir do dia atual, retrocedendo, em que o usuário NÃO atingiu o extra —
segundo a regra do backlog "Quebra de sequência apenas quando atinge o extra".
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.finance.models import ProgressoDiario
from apps.finance.services.orcamento_service import (
    CENTAVO,
    ZERO,
    OrcamentoService,
)


@dataclass(frozen=True)
class DiaProgresso:
    data: date
    dentro_limite: bool
    usou_reserva: bool
    usou_extra: bool
    gasto: Decimal
    limite: Decimal


@dataclass(frozen=True)
class ProgressoMensal:
    ano: int
    mes: int
    streak: int
    calendario: tuple[DiaProgresso, ...]


class ProgressoService:
    """Service responsável pelo cálculo de streak e calendário de progresso."""

    def __init__(self, orcamento_service: OrcamentoService | None = None) -> None:
        self._orcamento = orcamento_service or OrcamentoService()

    def obter_progresso(
        self, usuario, data_ref: date | None = None
    ) -> ProgressoMensal:
        if data_ref is None:
            data_ref = timezone.localdate()

        with transaction.atomic():
            metricas = self._atualizar_progresso(usuario, data_ref)
            calendario = self._montar_calendario(usuario, data_ref, metricas)
            streak = self._calcular_streak(usuario, data_ref)

        return ProgressoMensal(
            ano=data_ref.year,
            mes=data_ref.month,
            streak=streak,
            calendario=calendario,
        )

    def _atualizar_progresso(
        self, usuario, data_ref: date
    ) -> dict[date, tuple[Decimal, Decimal]]:
        """Recalcula o `ProgressoDiario` de cada dia <= `data_ref` do mês.

        Reaplica a mesma simulação do `OrcamentoService` (renda - fixos -
        extra_acumulado) para classificar o dia. Apenas dias fechados podem ser
        marcados como `usou_reserva`/`usou_extra`; o dia corrente fica como
        `dentro_limite` enquanto o gasto não ultrapassar o limite efetivo.
        """
        ano, mes = data_ref.year, data_ref.month
        dias_mes = calendar.monthrange(ano, mes)[1]

        renda = OrcamentoService._renda_mensal(usuario, ano, mes)
        fixos = OrcamentoService._gastos_fixos(usuario, ano, mes)

        reserva_saldo = ZERO
        extra_acumulado = ZERO
        metricas: dict[date, tuple[Decimal, Decimal]] = {}

        for dia in range(1, data_ref.day + 1):
            data_dia = date(ano, mes, dia)
            gasto = OrcamentoService._gasto_variavel_do_dia(usuario, data_dia)
            limite = OrcamentoService._dividir(
                renda - fixos - extra_acumulado, dias_mes
            )
            if limite < ZERO:
                limite = ZERO
            metricas[data_dia] = (gasto.quantize(CENTAVO), limite.quantize(CENTAVO))

            if dia < data_ref.day:
                dentro, usou_res, usou_ext, reserva_saldo, extra_acumulado = (
                    self._classificar_dia_fechado(
                        gasto, limite, reserva_saldo, extra_acumulado
                    )
                )
            else:
                dentro = gasto <= limite
                usou_res = False
                usou_ext = False

            ProgressoDiario.objects.update_or_create(
                usuario=usuario,
                data=data_dia,
                defaults={
                    "dentro_limite": dentro,
                    "usou_reserva": usou_res,
                    "usou_extra": usou_ext,
                },
            )

        return metricas

    @staticmethod
    def _classificar_dia_fechado(
        gasto: Decimal,
        limite: Decimal,
        reserva_saldo: Decimal,
        extra_acumulado: Decimal,
    ) -> tuple[bool, bool, bool, Decimal, Decimal]:
        diff = limite - gasto
        if diff >= ZERO:
            reserva_saldo = (reserva_saldo + diff).quantize(CENTAVO)
            return True, False, False, reserva_saldo, extra_acumulado

        excesso = -diff
        if reserva_saldo >= excesso:
            reserva_saldo = (reserva_saldo - excesso).quantize(CENTAVO)
            return False, True, False, reserva_saldo, extra_acumulado

        extra_dia = (excesso - reserva_saldo).quantize(CENTAVO)
        usou_reserva = reserva_saldo > ZERO
        reserva_saldo = ZERO
        extra_acumulado = (extra_acumulado + extra_dia).quantize(CENTAVO)
        return False, usou_reserva, True, reserva_saldo, extra_acumulado

    @staticmethod
    def _montar_calendario(
        usuario,
        data_ref: date,
        metricas: dict[date, tuple[Decimal, Decimal]],
    ) -> tuple[DiaProgresso, ...]:
        dias_mes = calendar.monthrange(data_ref.year, data_ref.month)[1]
        registros = {
            p.data: p
            for p in ProgressoDiario.objects.filter(
                usuario=usuario,
                data__year=data_ref.year,
                data__month=data_ref.month,
            )
        }
        calendario: list[DiaProgresso] = []
        for dia in range(1, dias_mes + 1):
            data_dia = date(data_ref.year, data_ref.month, dia)
            registro = registros.get(data_dia)
            gasto, limite = metricas.get(data_dia, (ZERO, ZERO))
            if registro is None:
                calendario.append(
                    DiaProgresso(
                        data=data_dia,
                        dentro_limite=False,
                        usou_reserva=False,
                        usou_extra=False,
                        gasto=gasto,
                        limite=limite,
                    )
                )
            else:
                calendario.append(
                    DiaProgresso(
                        data=data_dia,
                        dentro_limite=registro.dentro_limite,
                        usou_reserva=registro.usou_reserva,
                        usou_extra=registro.usou_extra,
                        gasto=gasto,
                        limite=limite,
                    )
                )
        return tuple(calendario)

    @staticmethod
    def _calcular_streak(usuario, data_ref: date) -> int:
        """Conta dias consecutivos terminando em `data_ref` sem `usou_extra`.

        A sequência só quebra quando o usuário atinge o extra; dias em que
        apenas a reserva foi usada ainda contam.
        """
        streak = 0
        cur = data_ref
        while True:
            registro = ProgressoDiario.objects.filter(
                usuario=usuario, data=cur
            ).first()
            if registro is None or registro.usou_extra:
                break
            streak += 1
            cur = cur - timedelta(days=1)
        return streak
