"""Schemas JSON das tools no formato function calling da OpenAI.

Cada item segue o contrato `{"type": "function", "function": {...}}` aceito pelo
endpoint `chat.completions`. Os nomes batem com as chaves registradas no
`ToolRegistry`.
"""

from __future__ import annotations

from typing import Any

_PAGAMENTOS = ["PIX", "CREDITO", "DEBITO", "DINHEIRO"]
_TIPOS_GASTO = ["FIXO", "VARIAVEL"]
_TIPOS_TRANSACAO = ["entrada", "saida", "parcelamento"]


def _func(nome: str, descricao: str, parametros: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": nome,
            "description": descricao,
            "parameters": parametros,
        },
    }


def _obj(props: dict[str, Any], obrigatorios: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": props,
        "required": obrigatorios,
        "additionalProperties": False,
    }


TOOL_SCHEMAS: list[dict[str, Any]] = [
    _func(
        "criar_entrada",
        "Registra uma nova entrada financeira (receita) do usuário.",
        _obj(
            {
                "nome": {"type": "string", "description": "Descrição da entrada."},
                "valor": {"type": "number", "description": "Valor monetário (> 0)."},
                "fonte": {"type": "string", "description": "Origem da entrada."},
                "recorrencia": {
                    "type": "boolean",
                    "description": "Se a entrada é recorrente.",
                },
            },
            ["nome", "valor"],
        ),
    ),
    _func(
        "criar_saida",
        "Registra uma nova saída financeira (despesa) do usuário.",
        _obj(
            {
                "nome": {"type": "string", "description": "Descrição da saída."},
                "valor": {"type": "number", "description": "Valor monetário (> 0)."},
                "categoria_id": {
                    "type": "string",
                    "description": "UUID da categoria.",
                },
                "categoria_nome": {
                    "type": "string",
                    "description": "Nome da categoria (alternativa ao id).",
                },
                "pagamento": {"type": "string", "enum": _PAGAMENTOS},
                "tipo_gasto": {
                    "type": "string",
                    "enum": _TIPOS_GASTO,
                    "description": (
                        "Tipo do gasto. Default: VARIAVEL. Só envie FIXO se o "
                        "usuário disser explicitamente que é um gasto fixo."
                    ),
                },
            },
            ["nome", "valor", "pagamento"],
        ),
    ),
    _func(
        "criar_parcelamento",
        "Registra um parcelamento (compra dividida em parcelas mensais).",
        _obj(
            {
                "nome": {"type": "string"},
                "valor": {
                    "type": "number",
                    "description": "Valor total da compra (> 0).",
                },
                "num_parcelas": {"type": "integer", "minimum": 1},
                "categoria_id": {"type": "string"},
                "categoria_nome": {"type": "string"},
                "pagamento": {"type": "string", "enum": _PAGAMENTOS},
            },
            ["nome", "valor", "num_parcelas", "pagamento"],
        ),
    ),
    _func(
        "editar_entrada",
        "Edita uma entrada existente.",
        _obj(
            {
                "id": {"type": "string", "description": "UUID da entrada."},
                "nome": {"type": "string"},
                "valor": {"type": "number"},
                "fonte": {"type": "string"},
                "recorrencia": {"type": "boolean"},
            },
            ["id"],
        ),
    ),
    _func(
        "editar_saida",
        "Edita uma saída existente.",
        _obj(
            {
                "id": {"type": "string"},
                "nome": {"type": "string"},
                "valor": {"type": "number"},
                "pagamento": {"type": "string", "enum": _PAGAMENTOS},
                "tipo_gasto": {"type": "string", "enum": _TIPOS_GASTO},
                "categoria_id": {"type": "string"},
                "categoria_nome": {"type": "string"},
            },
            ["id"],
        ),
    ),
    _func(
        "editar_parcelamento",
        "Edita um parcelamento — só permitido enquanto estiver na 1ª parcela.",
        _obj(
            {
                "id": {"type": "string"},
                "nome": {"type": "string"},
                "valor": {"type": "number"},
                "num_parcelas": {"type": "integer", "minimum": 1},
                "pagamento": {"type": "string", "enum": _PAGAMENTOS},
                "categoria_id": {"type": "string"},
                "categoria_nome": {"type": "string"},
            },
            ["id"],
        ),
    ),
    _func(
        "excluir_entrada",
        "Exclui uma entrada do usuário.",
        _obj({"id": {"type": "string"}}, ["id"]),
    ),
    _func(
        "excluir_saida",
        "Exclui uma saída do usuário.",
        _obj({"id": {"type": "string"}}, ["id"]),
    ),
    _func(
        "excluir_parcelamento",
        "Exclui um parcelamento do usuário.",
        _obj({"id": {"type": "string"}}, ["id"]),
    ),
    _func(
        "simular_gasto",
        "Simula o impacto financeiro de um gasto antes de realizá-lo.",
        _obj(
            {
                "valor": {"type": "number", "description": "Valor do gasto (> 0)."},
                "parcelado": {"type": "boolean", "default": False},
                "num_parcelas": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Obrigatório se parcelado=true.",
                },
            },
            ["valor"],
        ),
    ),
    _func(
        "listar_extrato",
        "Lista o extrato financeiro do usuário com filtros opcionais.",
        _obj(
            {
                "tipo": {"type": "string", "enum": _TIPOS_TRANSACAO},
                "ano": {"type": "integer"},
                "mes": {"type": "integer", "minimum": 1, "maximum": 12},
                "categoria_id": {"type": "string"},
                "pagamento": {"type": "string", "enum": _PAGAMENTOS},
                "tipo_gasto": {"type": "string", "enum": _TIPOS_GASTO},
                "pesquisa_nome": {"type": "string"},
            },
            [],
        ),
    ),
    _func(
        "listar_entradas",
        "Lista as entradas do usuário (opcionalmente filtradas por ano/mês).",
        _obj(
            {
                "ano": {"type": "integer"},
                "mes": {"type": "integer", "minimum": 1, "maximum": 12},
            },
            [],
        ),
    ),
    _func(
        "listar_saidas",
        "Lista as saídas do usuário (opcionalmente filtradas por ano/mês).",
        _obj(
            {
                "ano": {"type": "integer"},
                "mes": {"type": "integer", "minimum": 1, "maximum": 12},
            },
            [],
        ),
    ),
    _func(
        "listar_parcelamentos",
        "Lista os parcelamentos do usuário.",
        _obj({}, []),
    ),
]
