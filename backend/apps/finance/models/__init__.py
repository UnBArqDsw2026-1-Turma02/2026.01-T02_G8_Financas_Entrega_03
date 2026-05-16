"""Models do domínio financeiro (G8).

Hierarquia (multi-table inheritance):
    Transacao
    ├── Entrada
    ├── Saida
    └── Parcelamento

Categoria é uma entidade independente referenciada por Saida e Parcelamento.
"""

from apps.finance.models.carteira import Extra, LimiteDiario, Reserva
from apps.finance.models.categoria import Categoria
from apps.finance.models.choices import Pagamento, TipoGasto
from apps.finance.models.progresso import ProgressoDiario
from apps.finance.models.transacao import Entrada, Parcelamento, Saida, Transacao

__all__ = [
    "Categoria",
    "Entrada",
    "Extra",
    "LimiteDiario",
    "Pagamento",
    "Parcelamento",
    "ProgressoDiario",
    "Reserva",
    "Saida",
    "TipoGasto",
    "Transacao",
]
