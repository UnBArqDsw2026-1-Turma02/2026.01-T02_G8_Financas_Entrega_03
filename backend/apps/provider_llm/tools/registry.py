"""Registry que mapeia nome de tool → função executora.

O `ProviderLLM` chama `ToolRegistry.executar` para cada `ToolCall` produzido
pelo LLM. O registry isola o orquestrador do conjunto concreto de tools e
fornece os schemas no formato esperado pela OpenAI.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from apps.provider_llm.domain import ToolCall
from apps.provider_llm.tools import functions as fn
from apps.provider_llm.tools.schemas import TOOL_SCHEMAS

ToolFunction = Callable[..., Any]

_TOOLS: dict[str, ToolFunction] = {
    "criar_entrada": fn.criar_entrada,
    "criar_saida": fn.criar_saida,
    "criar_parcelamento": fn.criar_parcelamento,
    "editar_entrada": fn.editar_entrada,
    "editar_saida": fn.editar_saida,
    "editar_parcelamento": fn.editar_parcelamento,
    "excluir_entrada": fn.excluir_entrada,
    "excluir_saida": fn.excluir_saida,
    "excluir_parcelamento": fn.excluir_parcelamento,
    "simular_gasto": fn.simular_gasto,
    "listar_extrato": fn.listar_extrato,
    "listar_entradas": fn.listar_entradas,
    "listar_saidas": fn.listar_saidas,
    "listar_parcelamentos": fn.listar_parcelamentos,
}


class ToolRegistry:
    """Catálogo de tools amarrado a um usuário autenticado."""

    def __init__(self, usuario, tools: dict[str, ToolFunction] | None = None) -> None:
        self._usuario = usuario
        self._tools = dict(tools or _TOOLS)

    @property
    def nomes(self) -> list[str]:
        return list(self._tools)

    def schemas(self) -> list[dict[str, Any]]:
        """Schemas JSON para passar como `tools=` no chat.completions."""
        return [
            s
            for s in TOOL_SCHEMAS
            if s["function"]["name"] in self._tools
        ]

    def executar(self, tool_call: ToolCall) -> dict[str, Any]:
        """Despacha uma `ToolCall` para a função correspondente."""
        funcao = self._tools.get(tool_call.nome)
        if funcao is None:
            return {"ok": False, "erro": f"Tool desconhecida: {tool_call.nome}"}
        try:
            return funcao(self._usuario, **dict(tool_call.argumentos))
        except Exception as exc:  # noqa: BLE001 — devolvido ao LLM como texto
            return {"ok": False, "erro": str(exc)}
