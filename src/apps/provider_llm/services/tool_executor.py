"""ToolExecutor — Subsistema executor das tools chamadas pelo LLM (Issue #16).

Encapsula o `ToolRegistry` por trás de um callable compatível com a interface
`ToolExecutor = Callable[[ToolCall], Any]` esperada pelo `ProviderLLM`.
Permite que a Facade de mensageria injete um executor já amarrado ao usuário
autenticado sem expor o registry inteiro.
"""

from __future__ import annotations

from typing import Any

from apps.provider_llm.domain import ToolCall
from apps.provider_llm.tools.registry import ToolRegistry


class ToolExecutor:
    """Despacha `ToolCall`s para o `ToolRegistry` associado a um usuário."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def __call__(self, tool_call: ToolCall) -> Any:
        return self.executar(tool_call)

    def executar(self, tool_call: ToolCall) -> Any:
        return self._registry.executar(tool_call)
