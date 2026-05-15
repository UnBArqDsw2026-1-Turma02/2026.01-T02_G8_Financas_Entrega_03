"""Adapter concreto para a API da OpenAI (Issue #15).

Traduz nos dois sentidos:

* Domínio → OpenAI: monta a lista de `messages` e converte tools do formato
  do domínio (`{"nome", "descricao", "parametros"}`) para o formato JSON
  esperado pela OpenAI (`{"type": "function", "function": {...}}`).
* OpenAI → Domínio: lê o `ChatCompletion` retornado e produz `LLMResposta`
  com `ToolCall`s já com argumentos parseados.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from apps.provider_llm.clients.openai_client import OpenAiClient
from apps.provider_llm.domain import LLMResposta, ToolCall
from apps.provider_llm.ports.llm_port import LLMPort


class OpenAIAdapter(LLMPort):
    """Adapter — implementa `LLMPort` usando `OpenAiClient` como Adaptee."""

    def __init__(self, client: OpenAiClient) -> None:
        self._client = client

    def enviar(
        self,
        mensagem: str,
        tools: list[dict[str, Any]] | None = None,
        historico: list[dict[str, Any]] | None = None,
    ) -> LLMResposta:
        messages = self._montar_messages(mensagem, historico)
        tools_openai = self._traduzir_tools(tools) if tools else None
        completion = self._client.chat_completions(messages=messages, tools=tools_openai)
        return self._parsear_resposta(completion)

    @staticmethod
    def _montar_messages(
        mensagem: str, historico: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = list(historico or [])
        messages.append({"role": "user", "content": mensagem})
        return messages

    @staticmethod
    def _traduzir_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Converte tools do domínio para o schema de function calling da OpenAI."""
        traduzidas: list[dict[str, Any]] = []
        for tool in tools:
            if tool.get("type") == "function" and "function" in tool:
                traduzidas.append(tool)
                continue
            traduzidas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["nome"],
                        "description": tool.get("descricao", ""),
                        "parameters": tool.get(
                            "parametros",
                            {"type": "object", "properties": {}},
                        ),
                    },
                }
            )
        return traduzidas

    @staticmethod
    def _parsear_resposta(completion: Any) -> LLMResposta:
        choice = completion.choices[0]
        message = choice.message
        tool_calls = [
            ToolCall(
                id=tc.id,
                nome=tc.function.name,
                argumentos=OpenAIAdapter._parse_args(tc.function.arguments),
            )
            for tc in (getattr(message, "tool_calls", None) or [])
        ]
        return LLMResposta(
            conteudo=getattr(message, "content", None),
            tool_calls=tool_calls,
            finish_reason=getattr(choice, "finish_reason", None),
        )

    @staticmethod
    def _parse_args(raw: str | dict[str, Any] | None) -> dict[str, Any]:
        if raw is None or raw == "":
            return {}
        if isinstance(raw, dict):
            return raw
        return json.loads(raw, parse_float=Decimal)
