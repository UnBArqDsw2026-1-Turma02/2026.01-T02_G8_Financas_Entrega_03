"""Implementações das tools — uma função por operação exposta ao LLM.

Cada função recebe o usuário autenticado e os argumentos vindos do LLM,
delega para o service do domínio e devolve um dicionário serializável.
Nada de lógica de negócio nova: as tools são adaptadores fininhos sobre
`FinancasTransacaoService`, `SimulacaoGastoService` e o Builder do extrato.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError

from apps.finance.models import (
    Categoria,
    Entrada,
    Parcelamento,
    Saida,
    Transacao,
)
from apps.finance.services.extrato_financeiro_builder import (
    ExtratoFinanceiroBuilder,
)
from apps.finance.services.financas_transacao_service import (
    FinancasTransacaoService,
)
from apps.finance.services.simulacao_gasto_service import SimulacaoGastoService


def _resolver_categoria(usuario, args: dict[str, Any]) -> Categoria | None:
    cat_id = args.pop("categoria_id", None)
    cat_nome = args.pop("categoria_nome", None)
    if cat_id:
        return Categoria.objects.get(pk=cat_id, usuario=usuario)
    if cat_nome:
        return Categoria.objects.get(nome__iexact=cat_nome, usuario=usuario)
    return None


def _para_subclasse(t: Transacao) -> Transacao:
    """Resolve um `Transacao` base para sua subclasse concreta via reverse OneToOne."""
    if isinstance(t, (Entrada, Saida, Parcelamento)):
        return t
    for atributo, modelo in (
        ("entrada", Entrada),
        ("saida", Saida),
        ("parcelamento", Parcelamento),
    ):
        try:
            return getattr(t, atributo)
        except modelo.DoesNotExist:
            continue
    return t


def _serializar_transacao(t: Transacao) -> dict[str, Any]:
    t = _para_subclasse(t)
    base = {
        "id": str(t.pk),
        "nome": t.nome,
        "valor": str(t.valor),
        "data": t.data.isoformat() if t.data else None,
    }
    if isinstance(t, Entrada):
        base.update(
            {"tipo": "entrada", "fonte": t.fonte, "recorrencia": t.recorrencia}
        )
    elif isinstance(t, Saida):
        base.update(
            {
                "tipo": "saida",
                "categoria": t.categoria.nome,
                "pagamento": t.pagamento,
                "tipo_gasto": t.tipo_gasto,
            }
        )
    elif isinstance(t, Parcelamento):
        base.update(
            {
                "tipo": "parcelamento",
                "categoria": t.categoria.nome,
                "pagamento": t.pagamento,
                "num_parcelas": t.num_parcelas,
                "parcela_atual": t.parcela_atual,
                "valor_parcela": str(t.valor_parcela),
            }
        )
    return base


def criar_entrada(usuario, **args: Any) -> dict[str, Any]:
    entrada = FinancasTransacaoService().criar_transacao(
        tipo="entrada", usuario=usuario, **args
    )
    return {"ok": True, "entrada": _serializar_transacao(entrada)}


def criar_saida(usuario, **args: Any) -> dict[str, Any]:
    args["categoria"] = _resolver_categoria(usuario, args)
    if args["categoria"] is None:
        raise ValidationError(
            {"categoria": "Informe categoria_id ou categoria_nome."}
        )
    args.setdefault("tipo_gasto", "VARIAVEL")
    saida = FinancasTransacaoService().criar_transacao(
        tipo="saida", usuario=usuario, **args
    )
    return {"ok": True, "saida": _serializar_transacao(saida)}


def criar_parcelamento(usuario, **args: Any) -> dict[str, Any]:
    args["categoria"] = _resolver_categoria(usuario, args)
    if args["categoria"] is None:
        raise ValidationError(
            {"categoria": "Informe categoria_id ou categoria_nome."}
        )
    parcelamento = FinancasTransacaoService().criar_transacao(
        tipo="parcelamento", usuario=usuario, **args
    )
    return {"ok": True, "parcelamento": _serializar_transacao(parcelamento)}


def _editar(usuario, modelo, args: dict[str, Any]) -> Transacao:
    pk = args.pop("id")
    obj = modelo.objects.get(pk=pk, usuario=usuario)
    if "categoria_id" in args or "categoria_nome" in args:
        cat = _resolver_categoria(usuario, args)
        if cat is not None:
            args["categoria"] = cat
    for campo, valor in args.items():
        setattr(obj, campo, valor)
    obj.full_clean()
    obj.save()
    return obj


def editar_entrada(usuario, **args: Any) -> dict[str, Any]:
    entrada = _editar(usuario, Entrada, args)
    return {"ok": True, "entrada": _serializar_transacao(entrada)}


def editar_saida(usuario, **args: Any) -> dict[str, Any]:
    saida = _editar(usuario, Saida, args)
    return {"ok": True, "saida": _serializar_transacao(saida)}


def editar_parcelamento(usuario, **args: Any) -> dict[str, Any]:
    parcelamento = Parcelamento.objects.get(pk=args["id"], usuario=usuario)
    if not parcelamento.pode_editar():
        raise ValidationError(
            {
                "parcela_atual": (
                    "Edição permitida apenas enquanto estiver na 1ª parcela."
                )
            }
        )
    parcelamento = _editar(usuario, Parcelamento, args)
    return {"ok": True, "parcelamento": _serializar_transacao(parcelamento)}


def _excluir(usuario, modelo, args: dict[str, Any]) -> str:
    pk = args["id"]
    apagados, _ = modelo.objects.filter(pk=pk, usuario=usuario).delete()
    if apagados == 0:
        raise modelo.DoesNotExist(f"{modelo.__name__} {pk} não encontrado.")
    return str(pk)


def excluir_entrada(usuario, **args: Any) -> dict[str, Any]:
    pk = _excluir(usuario, Entrada, args)
    return {"ok": True, "id": pk}


def excluir_saida(usuario, **args: Any) -> dict[str, Any]:
    pk = _excluir(usuario, Saida, args)
    return {"ok": True, "id": pk}


def excluir_parcelamento(usuario, **args: Any) -> dict[str, Any]:
    pk = _excluir(usuario, Parcelamento, args)
    return {"ok": True, "id": pk}


def simular_gasto(usuario, **args: Any) -> dict[str, Any]:
    valor = Decimal(str(args["valor"]))
    parcelado = bool(args.get("parcelado", False))
    num_parcelas = int(args.get("num_parcelas", 1))
    resultado = SimulacaoGastoService().simular(
        usuario=usuario,
        valor=valor,
        parcelado=parcelado,
        num_parcelas=num_parcelas,
    )
    return {k: str(v) if isinstance(v, Decimal) else v for k, v in resultado.items()}


def listar_extrato(usuario, **args: Any) -> dict[str, Any]:
    builder = ExtratoFinanceiroBuilder(usuario)
    if "tipo" in args:
        builder.filtro_tipo(args["tipo"])
    if "ano" in args and "mes" in args:
        builder.filtro_ano_mes(args["ano"], args["mes"])
    if "categoria_id" in args:
        categoria = Categoria.objects.get(
            pk=UUID(str(args["categoria_id"])), usuario=usuario
        )
        builder.filtro_categoria(categoria)
    if "pagamento" in args:
        builder.filtro_pagamento(args["pagamento"])
    if "tipo_gasto" in args:
        builder.filtro_tipo_gasto(args["tipo_gasto"])
    if "pesquisa_nome" in args:
        builder.pesquisa_nome(args["pesquisa_nome"])
    extrato = builder.build()
    return {
        "saldo_atual": str(extrato.saldo_atual),
        "filtros_aplicados": extrato.filtros_aplicados,
        "transacoes": [_serializar_transacao(t) for t in extrato.transacoes],
    }


def _listar_por_periodo(qs, args: dict[str, Any]):
    if "ano" in args:
        qs = qs.filter(data__year=int(args["ano"]))
    if "mes" in args:
        qs = qs.filter(data__month=int(args["mes"]))
    return qs.order_by("-data")


def listar_entradas(usuario, **args: Any) -> dict[str, Any]:
    qs = _listar_por_periodo(Entrada.objects.filter(usuario=usuario), args)
    return {"entradas": [_serializar_transacao(t) for t in qs]}


def listar_saidas(usuario, **args: Any) -> dict[str, Any]:
    qs = _listar_por_periodo(Saida.objects.filter(usuario=usuario), args)
    return {"saidas": [_serializar_transacao(t) for t in qs]}


def listar_parcelamentos(usuario, **args: Any) -> dict[str, Any]:
    qs = Parcelamento.objects.filter(usuario=usuario).order_by("-data")
    return {"parcelamentos": [_serializar_transacao(t) for t in qs]}
