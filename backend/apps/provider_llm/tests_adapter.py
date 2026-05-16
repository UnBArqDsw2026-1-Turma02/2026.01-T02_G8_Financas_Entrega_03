"""Testes do padrão Adapter para a OpenAI (Issue #15)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from django.test import SimpleTestCase

from apps.provider_llm.adapters.openai_adapter import OpenAIAdapter
from apps.provider_llm.clients.openai_client import OpenAiClient
from apps.provider_llm.domain import LLMResposta, ToolCall
from apps.provider_llm.ports.llm_port import LLMPort
from apps.provider_llm.services.provider_llm import ProviderLLM


def _fake_completion(
    content: str | None = None,
    tool_calls: list[tuple[str, str, str]] | None = None,
    finish_reason: str = "stop",
) -> SimpleNamespace:
    """Constrói um objeto no mesmo formato do `ChatCompletion` da OpenAI."""
    tcs = [
        SimpleNamespace(
            id=tc_id,
            function=SimpleNamespace(name=name, arguments=args),
        )
        for (tc_id, name, args) in (tool_calls or [])
    ]
    message = SimpleNamespace(content=content, tool_calls=tcs or None)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)]
    )


class FakeSDKChat:
    """Stub do `client.chat.completions` do SDK da OpenAI."""

    def __init__(self, completions: list[SimpleNamespace]) -> None:
        self._completions = list(completions)
        self.chamadas: list[dict[str, Any]] = []
        self.completions = self

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.chamadas.append(kwargs)
        return self._completions.pop(0)


class FakeSDKClient:
    def __init__(self, completions: list[SimpleNamespace]) -> None:
        self.chat = FakeSDKChat(completions)


class OpenAIAdapterTests(SimpleTestCase):
    def test_traduz_tools_do_dominio_para_formato_openai(self) -> None:
        completion = _fake_completion(content="ok")
        sdk = FakeSDKClient([completion])
        client = OpenAiClient(client=sdk, model="gpt-test")
        adapter = OpenAIAdapter(client)

        adapter.enviar(
            mensagem="oi",
            tools=[
                {
                    "nome": "criar_entrada",
                    "descricao": "Cria uma entrada",
                    "parametros": {
                        "type": "object",
                        "properties": {"valor": {"type": "number"}},
                    },
                }
            ],
        )

        enviado = sdk.chat.chamadas[0]
        self.assertEqual(enviado["model"], "gpt-test")
        self.assertEqual(enviado["messages"][-1], {"role": "user", "content": "oi"})
        self.assertEqual(
            enviado["tools"],
            [
                {
                    "type": "function",
                    "function": {
                        "name": "criar_entrada",
                        "description": "Cria uma entrada",
                        "parameters": {
                            "type": "object",
                            "properties": {"valor": {"type": "number"}},
                        },
                    },
                }
            ],
        )

    def test_tools_ja_no_formato_openai_passam_inalteradas(self) -> None:
        sdk = FakeSDKClient([_fake_completion(content="ok")])
        adapter = OpenAIAdapter(OpenAiClient(client=sdk))
        tool_openai = {
            "type": "function",
            "function": {"name": "x", "description": "", "parameters": {}},
        }

        adapter.enviar(mensagem="oi", tools=[tool_openai])

        self.assertEqual(sdk.chat.chamadas[0]["tools"], [tool_openai])

    def test_omite_tools_quando_nao_informadas(self) -> None:
        sdk = FakeSDKClient([_fake_completion(content="ok")])
        adapter = OpenAIAdapter(OpenAiClient(client=sdk))

        adapter.enviar(mensagem="oi")

        self.assertNotIn("tools", sdk.chat.chamadas[0])

    def test_parseia_resposta_simples_em_LLMResposta(self) -> None:
        sdk = FakeSDKClient([_fake_completion(content="olá", finish_reason="stop")])
        adapter = OpenAIAdapter(OpenAiClient(client=sdk))

        resposta = adapter.enviar(mensagem="oi")

        self.assertIsInstance(resposta, LLMResposta)
        self.assertEqual(resposta.conteudo, "olá")
        self.assertEqual(resposta.finish_reason, "stop")
        self.assertFalse(resposta.tem_tool_calls)

    def test_parseia_tool_calls_com_argumentos_json(self) -> None:
        completion = _fake_completion(
            tool_calls=[("call_1", "criar_entrada", json.dumps({"valor": 10}))],
            finish_reason="tool_calls",
        )
        sdk = FakeSDKClient([completion])
        adapter = OpenAIAdapter(OpenAiClient(client=sdk))

        resposta = adapter.enviar(mensagem="adicione 10", tools=[])

        self.assertTrue(resposta.tem_tool_calls)
        self.assertEqual(
            resposta.tool_calls[0],
            ToolCall(id="call_1", nome="criar_entrada", argumentos={"valor": 10}),
        )

    def test_inclui_historico_antes_da_nova_mensagem(self) -> None:
        sdk = FakeSDKClient([_fake_completion(content="ok")])
        adapter = OpenAIAdapter(OpenAiClient(client=sdk))
        historico = [{"role": "user", "content": "anterior"}]

        adapter.enviar(mensagem="nova", historico=historico)

        self.assertEqual(
            sdk.chat.chamadas[0]["messages"],
            [
                {"role": "user", "content": "anterior"},
                {"role": "user", "content": "nova"},
            ],
        )


class FakeLLM(LLMPort):
    """Implementação alternativa de `LLMPort` — prova de que trocar de LLM
    se resume a um novo Adapter (Critério de Aceite da Issue #15)."""

    def __init__(self, respostas: list[LLMResposta]) -> None:
        self._respostas = list(respostas)
        self.chamadas: list[dict[str, Any]] = []

    def enviar(
        self,
        mensagem: str,
        tools: list[dict[str, Any]] | None = None,
        historico: list[dict[str, Any]] | None = None,
    ) -> LLMResposta:
        self.chamadas.append(
            {"mensagem": mensagem, "tools": tools, "historico": historico}
        )
        return self._respostas.pop(0)


class ProviderLLMTests(SimpleTestCase):
    def test_retorna_resposta_quando_nao_ha_tool_calls(self) -> None:
        fake = FakeLLM([LLMResposta(conteudo="oi de volta")])
        provider = ProviderLLM(fake)

        resposta = provider.conversar("oi")

        self.assertEqual(resposta.conteudo, "oi de volta")
        self.assertEqual(len(fake.chamadas), 1)

    def test_executa_tool_e_continua_loop_ate_resposta_final(self) -> None:
        fake = FakeLLM(
            [
                LLMResposta(
                    conteudo=None,
                    tool_calls=[ToolCall("call_1", "soma", {"a": 1, "b": 2})],
                    finish_reason="tool_calls",
                ),
                LLMResposta(conteudo="resultado: 3", finish_reason="stop"),
            ]
        )
        executadas: list[ToolCall] = []

        def executor(tc: ToolCall) -> str:
            executadas.append(tc)
            return "3"

        provider = ProviderLLM(fake)
        resposta = provider.conversar(
            "quanto é 1+2?",
            tools=[{"nome": "soma", "descricao": "", "parametros": {}}],
            tool_executor=executor,
        )

        self.assertEqual(resposta.conteudo, "resultado: 3")
        self.assertEqual(len(executadas), 1)
        self.assertEqual(executadas[0].nome, "soma")
        self.assertEqual(len(fake.chamadas), 2)
        segundo_historico = fake.chamadas[1]["historico"]
        self.assertTrue(any(m["role"] == "tool" for m in segundo_historico))

    def test_respeita_limite_de_iteracoes(self) -> None:
        loop_infinito = [
            LLMResposta(
                conteudo=None,
                tool_calls=[ToolCall(f"c{i}", "x", {})],
                finish_reason="tool_calls",
            )
            for i in range(10)
        ]
        fake = FakeLLM(loop_infinito)
        provider = ProviderLLM(fake, max_iteracoes=3)

        resposta = provider.conversar(
            "loop",
            tools=[{"nome": "x", "descricao": "", "parametros": {}}],
            tool_executor=lambda tc: "ok",
        )

        self.assertEqual(len(fake.chamadas), 3)
        self.assertTrue(resposta.tem_tool_calls)
