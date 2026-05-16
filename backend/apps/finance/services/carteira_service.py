"""CarteiraService — visão consolidada do estado financeiro diário (Issue #12).

Agrega LimiteDiario, Reserva e Extra do mês corrente em um único DTO usado
pelo endpoint `GET /api/v1/carteira/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import Extra, Reserva
from apps.finance.services.orcamento_service import (
    CENTAVO,
    ZERO,
    OrcamentoService,
)


@dataclass(frozen=True)
class CarteiraEstado:
    gasto_dia: Decimal
    falta_limite: Decimal
    limite_diario: Decimal
    saldo_reserva: Decimal
    saldo_extra: Decimal


class CarteiraService:
    def __init__(self, orcamento_service: OrcamentoService | None = None) -> None:
        self._orcamento = orcamento_service or OrcamentoService()

    def obter_estado(self, usuario, data_ref: date | None = None) -> CarteiraEstado:
        if data_ref is None:
            data_ref = timezone.localdate()

        # `obter_limite_diario` ja dispara o recalculo do orcamento em `data_ref`,
        # entao basta ler Reserva/Extra diretamente para evitar um recalculo extra
        # (que usaria sempre `timezone.localdate()` e desalinharia o estado).
        limite = self._orcamento.obter_limite_diario(usuario, data_ref)
        reserva = Reserva.objects.filter(usuario=usuario).first()
        saldo_reserva = reserva.saldo if reserva is not None else ZERO
        saldo_extra = (
            Extra.objects.filter(
                usuario=usuario,
                data__year=data_ref.year,
                data__month=data_ref.month,
            ).aggregate(s=Sum("valor"))["s"]
            or ZERO
        )

        limite_efetivo = limite.limite_efetivo
        falta = limite_efetivo - limite.gasto_dia
        if falta < ZERO:
            falta = ZERO

        return CarteiraEstado(
            gasto_dia=limite.gasto_dia.quantize(CENTAVO),
            falta_limite=falta.quantize(CENTAVO),
            limite_diario=limite_efetivo.quantize(CENTAVO),
            saldo_reserva=saldo_reserva.quantize(CENTAVO),
            saldo_extra=saldo_extra.quantize(CENTAVO),
        )
