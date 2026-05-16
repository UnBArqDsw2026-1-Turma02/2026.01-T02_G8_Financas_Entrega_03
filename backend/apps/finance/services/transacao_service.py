"""TransacaoService — Creator abstrato do Factory Method (Issue #03).

Define a interface que os clientes (views, tools de IA, etc.) usam para criar,
listar, editar e excluir transações sem conhecer as classes concretas
(`Entrada`, `Saida`, `Parcelamento`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from django.db.models import QuerySet

from apps.finance.models import Transacao


class TransacaoService(ABC):
    """Creator abstrato — declara o factory method `criar_transacao`.

    Operações CRUD genéricas (listar/editar/excluir) operam sobre `Transacao`,
    a base concreta da hierarquia multi-table. Apenas a criação precisa
    decidir o produto concreto, por isso só `criar_transacao` é abstrato.
    """

    @abstractmethod
    def criar_transacao(self, tipo: str, **dados: Any) -> Transacao:
        """Factory method — decide qual subclasse concreta instanciar."""

    def listar_transacoes(self, usuario) -> QuerySet[Transacao]:
        return Transacao.objects.filter(usuario=usuario)

    def editar_transacao(self, transacao_id: UUID | str, **dados: Any) -> Transacao:
        transacao = Transacao.objects.get(pk=transacao_id)
        for campo, valor in dados.items():
            setattr(transacao, campo, valor)
        transacao.full_clean()
        transacao.save()
        return transacao

    def excluir_transacao(self, transacao_id: UUID | str) -> None:
        Transacao.objects.filter(pk=transacao_id).delete()
