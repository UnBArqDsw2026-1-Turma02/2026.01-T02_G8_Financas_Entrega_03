"""Adaptee do padrão Adapter (Issue #15).

Wrapper fino sobre o SDK oficial da OpenAI. Mantém-se ignorante quanto ao
domínio do sistema: recebe e devolve estruturas no formato nativo da API.
A tradução para `LLMPort`/`LLMResposta` é responsabilidade do
`OpenAIAdapter`.

O SDK é importado de forma lazy para permitir que partes do código que não
acionam o LLM (tests, jobs sem IA, migrations) rodem sem o pacote instalado.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings


class OpenAiClient:
    """Wrapper do SDK `openai` — Adaptee do padrão Adapter."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        client: Any = None,
    ) -> None:
        self._model = model
        if client is not None:
            self._client = client
            return

        from openai import OpenAI

        key = api_key or getattr(settings, "OPENAI_API_KEY", None)
        self._client = OpenAI(api_key=key)

    @property
    def model(self) -> str:
        return self._model

    def chat_completions(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Chama `chat.completions.create` no formato nativo da OpenAI."""
        kwargs: dict[str, Any] = {"model": self._model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        return self._client.chat.completions.create(**kwargs)
