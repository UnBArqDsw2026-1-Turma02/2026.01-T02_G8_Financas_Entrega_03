"""Cliente do padrão Adapter (Issue #15).

`ProviderLLM` é o serviço que orquestra o loop de *function calling*: envia
uma mensagem, executa as tools que o LLM solicitar, devolve os resultados ao
LLM e repete até que ele responda em linguagem natural. Depende apenas da
interface `LLMPort` — não conhece a OpenAI nem qualquer SDK.

A execução das tools é injetada via `tool_executor`, mantendo a separação
entre comunicação com o LLM (este serviço) e a lógica de negócio das tools
(implementada na Issue #17).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from apps.provider_llm.domain import LLMResposta, ToolCall
from apps.provider_llm.ports.llm_port import LLMPort

ToolExecutor = Callable[[ToolCall], Any]


class ProviderLLM:
    """Orquestra a conversa com o LLM via interface `LLMPort`."""

    LIMITE_PADRAO_ITERACOES = 5

    def __init__(self, llm: LLMPort, max_iteracoes: int | None = None) -> None:
        self._llm = llm
        self._max_iteracoes = max_iteracoes or self.LIMITE_PADRAO_ITERACOES

    def conversar(
        self,
        mensagem: str,
        tools: list[dict[str, Any]] | None = None,
        tool_executor: ToolExecutor | None = None,
        historico: list[dict[str, Any]] | None = None,
    ) -> LLMResposta:
        """Loop de function calling até obter resposta final em linguagem natural."""
        contexto: list[dict[str, Any]] = list(historico or [])
        proxima_mensagem = mensagem

        for _ in range(self._max_iteracoes):
            resposta = self._llm.enviar(
                mensagem=proxima_mensagem, tools=tools, historico=contexto
            )
            contexto.append({"role": "user", "content": proxima_mensagem})

            if not resposta.tem_tool_calls:
                return resposta

            if tool_executor is None:
                # LLM pediu tools mas o cliente não as ofereceu — devolve mesmo assim.
                return resposta

            contexto.append(self._mensagem_assistant(resposta))
            for tool_call in resposta.tool_calls:
                resultado = tool_executor(tool_call)
                contexto.append(self._mensagem_tool(tool_call, resultado))

            proxima_mensagem = ""

        return resposta

    @staticmethod
    def _mensagem_assistant(resposta: LLMResposta) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": resposta.conteudo or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.nome,
                        "arguments": json.dumps(tc.argumentos),
                    },
                }
                for tc in resposta.tool_calls
            ],
        }

    @staticmethod
    def _mensagem_tool(tool_call: ToolCall, resultado: Any) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.nome,
            "content": resultado if isinstance(resultado, str) else repr(resultado),
        }
