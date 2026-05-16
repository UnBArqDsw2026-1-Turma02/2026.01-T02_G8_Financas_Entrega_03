"""Director do Builder (Issue #04) — receitas pré-definidas de extrato."""

from __future__ import annotations

from apps.finance.models import Categoria
from apps.finance.services.extrato import Extrato
from apps.finance.services.extrato_builder import ExtratoBuilder


class ExtratoDirector:
    """Encapsula sequências de chamadas ao Builder usadas com frequência.

    O Director é opcional no padrão Builder, mas centraliza as receitas
    comuns (extrato do mês, extrato por categoria, extrato completo) que
    são reusadas tanto pelas views da API quanto pelas Tools de IA.
    """

    def __init__(self, builder: ExtratoBuilder) -> None:
        self._builder = builder

    def construir_extrato_mensal(self, ano: int, mes: int) -> Extrato:
        return self._builder.filtro_ano_mes(ano, mes).build()

    def construir_extrato_por_categoria(self, categoria: Categoria) -> Extrato:
        return self._builder.filtro_categoria(categoria).build()

    def construir_extrato_completo(self) -> Extrato:
        return self._builder.build()
