"""ConcreteBuilder do Extrato (Issue #04).

Implementa cada passo de filtro como composição incremental sobre o
QuerySet de `Transacao`, e materializa o `Extrato` em `build()`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Q, Sum

from apps.finance.models import (
    Categoria,
    Entrada,
    Pagamento,
    Parcelamento,
    Saida,
    TipoGasto,
    Transacao,
)
from apps.finance.services.extrato import Extrato
from apps.finance.services.extrato_builder import ExtratoBuilder

TIPOS_VALIDOS = {"entrada", "saida", "parcelamento"}


class ExtratoFinanceiroBuilder(ExtratoBuilder):
    """ConcreteBuilder — escopo do extrato é sempre do usuário fornecido."""

    def __init__(self, usuario) -> None:
        self._usuario = usuario
        self._queryset = Transacao.objects.filter(usuario=usuario)
        self._filtros: dict[str, Any] = {}

    def filtro_tipo(self, tipo: str) -> "ExtratoFinanceiroBuilder":
        tipo_norm = (tipo or "").strip().lower()
        if tipo_norm not in TIPOS_VALIDOS:
            raise ValidationError({"tipo": f"Tipo inválido: '{tipo}'."})
        # multi-table inheritance: cada subclasse cria reverse accessor com o
        # nome em minúsculas no parent (entrada, saida, parcelamento).
        self._queryset = self._queryset.filter(**{f"{tipo_norm}__isnull": False})
        self._filtros["tipo"] = tipo_norm
        return self

    def filtro_ano_mes(self, ano: int, mes: int) -> "ExtratoFinanceiroBuilder":
        if not (1 <= int(mes) <= 12):
            raise ValidationError({"mes": "Mês deve estar entre 1 e 12."})
        self._queryset = self._queryset.filter(data__year=ano, data__month=mes)
        self._filtros["ano_mes"] = {"ano": int(ano), "mes": int(mes)}
        return self

    def filtro_categoria(
        self, categoria: Categoria
    ) -> "ExtratoFinanceiroBuilder":
        # Só Saída e Parcelamento têm categoria — Entradas são excluídas
        # automaticamente porque não satisfazem nenhum dos dois ramos.
        self._queryset = self._queryset.filter(
            Q(saida__categoria=categoria) | Q(parcelamento__categoria=categoria)
        )
        self._filtros["categoria"] = {
            "id": str(categoria.id),
            "nome": categoria.nome,
        }
        return self

    def filtro_pagamento(
        self, pagamento: Pagamento | str
    ) -> "ExtratoFinanceiroBuilder":
        valor = getattr(pagamento, "value", pagamento)
        self._queryset = self._queryset.filter(
            Q(saida__pagamento=valor) | Q(parcelamento__pagamento=valor)
        )
        self._filtros["pagamento"] = valor
        return self

    def filtro_tipo_gasto(
        self, tipo_gasto: TipoGasto | str
    ) -> "ExtratoFinanceiroBuilder":
        valor = getattr(tipo_gasto, "value", tipo_gasto)
        # Apenas Saída tem tipo_gasto — Parcelamentos e Entradas saem do extrato.
        self._queryset = self._queryset.filter(saida__tipo_gasto=valor)
        self._filtros["tipo_gasto"] = valor
        return self

    def pesquisa_nome(self, termo: str) -> "ExtratoFinanceiroBuilder":
        self._queryset = self._queryset.filter(nome__icontains=termo)
        self._filtros["pesquisa_nome"] = termo
        return self

    def build(self) -> Extrato:
        transacoes = list(self._queryset.order_by("-data"))
        saldo = self._calcular_saldo([t.pk for t in transacoes])
        return Extrato(
            transacoes=transacoes,
            saldo_atual=saldo,
            filtros_aplicados=dict(self._filtros),
        )

    @staticmethod
    def _calcular_saldo(pks: list) -> Decimal:
        if not pks:
            return Decimal("0.00")
        entradas = Entrada.objects.filter(pk__in=pks).aggregate(s=Sum("valor"))["s"]
        saidas = Saida.objects.filter(pk__in=pks).aggregate(s=Sum("valor"))["s"]
        parcelas = Parcelamento.objects.filter(pk__in=pks).aggregate(
            s=Sum("valor_parcela")
        )["s"]
        total = (entradas or Decimal("0")) - (saidas or Decimal("0")) - (
            parcelas or Decimal("0")
        )
        return total.quantize(Decimal("0.01"))
