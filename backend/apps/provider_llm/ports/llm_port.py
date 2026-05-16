"""Interface Target do padrão Adapter (Issue #15).

`LLMPort` é a interface que o domínio espera ao falar com um LLM. O
`ProviderLLM` depende apenas deste contrato; a tradução para o formato
específico do provedor fica a cargo do Adapter concreto (ex.: `OpenAIAdapter`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from apps.provider_llm.domain import LLMResposta


class LLMPort(ABC):
    """Target do padrão Adapter — vocabulário do domínio para o LLM."""

    @abstractmethod
    def enviar(
        self,
        mensagem: str,
        tools: list[dict[str, Any]] | None = None,
        historico: list[dict[str, Any]] | None = None,
    ) -> LLMResposta:
        """Envia uma mensagem ao LLM e devolve a resposta normalizada."""
