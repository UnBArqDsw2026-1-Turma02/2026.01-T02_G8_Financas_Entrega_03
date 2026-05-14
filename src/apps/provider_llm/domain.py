"""Objetos de domínio do subsistema de LLM (Issue #15).

Dataclasses produzidas pelo Adapter a partir da resposta da API externa.
São o vocabulário usado pelo `ProviderLLM` e por quem consome o LLM —
nunca contêm campos específicos do provedor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """Chamada de tool solicitada pelo LLM (function calling)."""

    id: str
    nome: str
    argumentos: dict[str, Any]


@dataclass(frozen=True)
class LLMResposta:
    """Resposta normalizada do LLM no formato do domínio."""

    conteudo: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str | None = None

    @property
    def tem_tool_calls(self) -> bool:
        return bool(self.tool_calls)
