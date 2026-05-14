"""AlertaService — gera alertas de comportamento de gastos (Issue #13).

Cinco gatilhos do backlog (Feature 3.1.3):

- 70% do limite diário
- 100% do limite diário
- 50% da reserva consumida
- 80% da reserva consumida
- Reserva esgotada

Para os gatilhos da reserva, o consumo é medido em relação à *reserva
potencial* do mês — o quanto poderia ter acumulado se nenhum dia tivesse
estourado. Assim, `consumido = potencial - saldo_atual` reflete o que já foi
debitado pela cobertura de excessos, independente do dia do mês.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.finance.models import Reserva
from apps.finance.services.orcamento_service import (
    CENTAVO,
    ZERO,
    OrcamentoService,
)


@dataclass(frozen=True)
class Alerta:
    gatilho: str
    mensagem: str


class AlertaService:
    """Service que avalia os gatilhos do dia e devolve os alertas pendentes."""

    LIMITE_70 = "limite_70"
    LIMITE_100 = "limite_100"
    RESERVA_50 = "reserva_50"
    RESERVA_80 = "reserva_80"
    RESERVA_ESGOTADA = "reserva_esgotada"

    _MENSAGENS = {
        LIMITE_70: "Atenção: você já usou 70% do seu limite diário",
        LIMITE_100: "Você atingiu o limite diário",
        RESERVA_50: "Você já usou metade da sua reserva",
        RESERVA_80: "Atenção: 80% da reserva foi consumida",
        RESERVA_ESGOTADA: "Reserva esgotada — gastos extras serão registrados",
    }

    def __init__(self, orcamento_service: OrcamentoService | None = None) -> None:
        self._orcamento = orcamento_service or OrcamentoService()

    def obter_alertas(
        self, usuario, data_ref: date | None = None
    ) -> tuple[Alerta, ...]:
        if data_ref is None:
            data_ref = timezone.localdate()

        limite = self._orcamento.obter_limite_diario(usuario, data_ref)
        reserva = Reserva.objects.filter(usuario=usuario).first()
        saldo_reserva = reserva.saldo if reserva is not None else ZERO
        extra_mes = self._orcamento.obter_extra_mes(
            usuario, ano=data_ref.year, mes=data_ref.month
        )

        alertas: list[Alerta] = []
        alertas.extend(self._alertas_limite(limite.limite_efetivo, limite.gasto_dia))
        alertas.extend(
            self._alertas_reserva(usuario, data_ref, saldo_reserva, extra_mes)
        )
        return tuple(alertas)

    def _alertas_limite(
        self, limite_efetivo: Decimal, gasto_dia: Decimal
    ) -> list[Alerta]:
        if limite_efetivo <= ZERO:
            return []
        pct = (gasto_dia / limite_efetivo).quantize(Decimal("0.0001"))
        if pct >= Decimal("1"):
            return [self._alerta(self.LIMITE_100)]
        if pct >= Decimal("0.7"):
            return [self._alerta(self.LIMITE_70)]
        return []

    def _alertas_reserva(
        self,
        usuario,
        data_ref: date,
        saldo_reserva: Decimal,
        extra_mes: Decimal,
    ) -> list[Alerta]:
        alertas: list[Alerta] = []
        potencial = self._reserva_potencial_mes(usuario, data_ref)
        if potencial > ZERO:
            consumido = potencial - saldo_reserva
            if consumido < ZERO:
                consumido = ZERO
            pct = (consumido / potencial).quantize(Decimal("0.0001"))
            if pct >= Decimal("0.8"):
                alertas.append(self._alerta(self.RESERVA_80))
            elif pct >= Decimal("0.5"):
                alertas.append(self._alerta(self.RESERVA_50))

        if extra_mes > ZERO:
            alertas.append(self._alerta(self.RESERVA_ESGOTADA))
        return alertas

    @staticmethod
    def _reserva_potencial_mes(usuario, data_ref: date) -> Decimal:
        """Soma das sobras teóricas dos dias fechados (limite - gasto, se >0).

        Usa a mesma fórmula do `OrcamentoService` para o limite aplicável de
        cada dia (renda - fixos), sem descontar extra acumulado — já que o
        objetivo é estimar o potencial de reserva, não o saldo efetivo.
        """
        ano, mes = data_ref.year, data_ref.month
        dias_mes = calendar.monthrange(ano, mes)[1]
        renda = OrcamentoService._renda_mensal(usuario, ano, mes)
        fixos = OrcamentoService._gastos_fixos(usuario, ano, mes)
        limite_base = OrcamentoService._dividir(renda - fixos, dias_mes)
        if limite_base < ZERO:
            limite_base = ZERO

        potencial = ZERO
        for dia in range(1, data_ref.day):
            gasto = OrcamentoService._gasto_variavel_do_dia(
                usuario, date(ano, mes, dia)
            )
            diff = limite_base - gasto
            if diff > ZERO:
                potencial = (potencial + diff).quantize(CENTAVO)
        return potencial

    def _alerta(self, gatilho: str) -> Alerta:
        return Alerta(gatilho=gatilho, mensagem=self._MENSAGENS[gatilho])
