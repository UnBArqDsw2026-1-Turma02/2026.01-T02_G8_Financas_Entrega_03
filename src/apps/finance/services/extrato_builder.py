"""Builder abstrato do Extrato (Issue #04).

Declara os 6 passos opcionais de construção identificados na Story 1.1.5.1
do Backlog. Todos os métodos de filtro retornam `self` para suportar a
fluent interface (encadeamento de chamadas).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from apps.finance.models import Categoria, Pagamento, TipoGasto
from apps.finance.services.extrato import Extrato


class ExtratoBuilder(ABC):
    """Builder abstrato — interface dos passos de construção do Extrato."""

    @abstractmethod
    def filtro_tipo(self, tipo: str) -> "ExtratoBuilder":
        """Filtra por tipo de transação ('entrada', 'saida' ou 'parcelamento')."""

    @abstractmethod
    def filtro_ano_mes(self, ano: int, mes: int) -> "ExtratoBuilder":
        """Filtra por ano e mês da data da transação."""

    @abstractmethod
    def filtro_categoria(self, categoria: Categoria) -> "ExtratoBuilder":
        """Filtra por categoria (aplica-se a Saídas e Parcelamentos)."""

    @abstractmethod
    def filtro_pagamento(self, pagamento: Pagamento | str) -> "ExtratoBuilder":
        """Filtra por forma de pagamento (PIX, CREDITO, DEBITO, DINHEIRO)."""

    @abstractmethod
    def filtro_tipo_gasto(self, tipo_gasto: TipoGasto | str) -> "ExtratoBuilder":
        """Filtra por tipo de gasto (FIXO ou VARIAVEL) — só afeta Saídas."""

    @abstractmethod
    def pesquisa_nome(self, termo: str) -> "ExtratoBuilder":
        """Pesquisa por nome (case-insensitive, casamento parcial)."""

    @abstractmethod
    def build(self) -> Extrato:
        """Executa a consulta acumulada e devolve o `Extrato` final."""
