"""Product do Builder (Issue #04) — objeto Extrato construído pelo Builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from apps.finance.models import Transacao


@dataclass
class Extrato:
    """Resultado da construção pelo Builder.

    `transacoes` é a lista materializada (não um QuerySet) para que o objeto
    seja imutável após `build()` e possa ser serializado pela API.
    `filtros_aplicados` mantém um registro dos filtros que foram efetivamente
    aplicados — útil para devolver ao cliente o "estado" da consulta.
    """

    transacoes: list[Transacao] = field(default_factory=list)
    saldo_atual: Decimal = Decimal("0.00")
    filtros_aplicados: dict[str, Any] = field(default_factory=dict)
