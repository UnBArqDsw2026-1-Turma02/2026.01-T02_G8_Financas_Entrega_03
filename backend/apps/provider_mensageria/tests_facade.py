"""Testes da Facade de mensageria (Issue #16).

Cada subsistema é mockado em isolamento para garantir que a Facade orquestra
o fluxo descrito nos diagramas de Sequência/Atividades:

1. consulta o ``AuthService``;
2. quando não autenticado → devolve a mensagem padrão e nada mais é chamado;
3. quando autenticado → cria o registry/executor com o usuário e delega ao
   ``ProviderLLM`` o loop de function calling;
4. devolve o ``conteudo`` da ``LLMResposta`` para o cliente.

O ``WebhookTelegram`` também é exercitado para confirmar que só conhece a
Facade (Critério de Aceite #1).
"""

from __future__ import annotations

import json
from typing import Any

from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase

from apps.provider_llm.domain import LLMResposta, ToolCall
from apps.provider_mensageria.api.views import WebhookTelegram
from apps.provider_mensageria.services.auth_service import AuthService
from apps.provider_mensageria.services.mensageria_facade import MensageriaFacade

User = get_user_model()


class _FakeCoreAuth:
    """Stub do ``apps.accounts.services.AuthService`` usado pelos testes."""

    def __init__(self, by_telegram: dict[str, Any] | None = None) -> None:
        self._by_telegram = by_telegram or {}

    def get_by_telegram_id(self, telegram_id: str) -> Any:
        return self._by_telegram.get(str(telegram_id))


class _FakeAuth:
    def __init__(self, usuario: Any) -> None:
        self.usuario = usuario
        self.chamadas: list[str] = []

    def validar_user(self, telegram_user_id: str) -> Any:
        self.chamadas.append(telegram_user_id)
        return self.usuario


class _FakeRegistry:
    def __init__(self, usuario: Any) -> None:
        self.usuario = usuario

    def schemas(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": "criar_entrada"}}]

    def executar(self, tool_call: ToolCall) -> dict[str, Any]:
        return {"ok": True, "nome": tool_call.nome}


class _FakeProvider:
    """Stub do ``ProviderLLM`` que captura os argumentos de ``conversar``."""

    def __init__(self, resposta: LLMResposta) -> None:
        self.resposta = resposta
        self.chamadas: list[dict[str, Any]] = []

    def conversar(self, **kwargs: Any) -> LLMResposta:
        self.chamadas.append(kwargs)
        return self.resposta


class AuthServiceTests(SimpleTestCase):
    def test_validar_user_delega_para_core_auth(self) -> None:
        marker = object()
        core = _FakeCoreAuth(by_telegram={"42": marker})

        service = AuthService(core=core)

        self.assertIs(service.validar_user("42"), marker)
        self.assertIs(service.validar_user(42), marker)  # converte para str
        self.assertIsNone(service.validar_user("nao-existe"))

    def test_validar_user_com_none_devolve_none(self) -> None:
        service = AuthService(core=_FakeCoreAuth())
        self.assertIsNone(service.validar_user(None))


class MensageriaFacadeTests(SimpleTestCase):
    def _facade(
        self,
        usuario: Any,
        resposta: LLMResposta,
    ) -> tuple[MensageriaFacade, _FakeAuth, _FakeProvider, list[_FakeRegistry]]:
        auth = _FakeAuth(usuario=usuario)
        provider = _FakeProvider(resposta=resposta)
        criados: list[_FakeRegistry] = []

        def registry_factory(usuario: Any) -> _FakeRegistry:
            reg = _FakeRegistry(usuario=usuario)
            criados.append(reg)
            return reg

        facade = MensageriaFacade(
            provider_llm=provider,
            auth_service=auth,
            registry_factory=registry_factory,
        )
        return facade, auth, provider, criados

    def test_usuario_nao_autenticado_devolve_msg_padrao(self) -> None:
        facade, auth, provider, criados = self._facade(
            usuario=None,
            resposta=LLMResposta(conteudo="nao deveria ser usado"),
        )

        resposta = facade.processar_mensagem("123", "oi")

        self.assertEqual(resposta, MensageriaFacade.MSG_NAO_AUTENTICADO)
        self.assertEqual(auth.chamadas, ["123"])
        self.assertEqual(provider.chamadas, [])  # LLM não foi acionado
        self.assertEqual(criados, [])  # registry nem foi criado

    def test_usuario_autenticado_aciona_llm_com_tools_do_registry(self) -> None:
        usuario_fake = object()
        facade, auth, provider, criados = self._facade(
            usuario=usuario_fake,
            resposta=LLMResposta(conteudo="resposta final"),
        )

        resposta = facade.processar_mensagem("123", "gastei 10 no almoço")

        self.assertEqual(resposta, "resposta final")
        self.assertEqual(len(criados), 1)
        self.assertIs(criados[0].usuario, usuario_fake)

        chamada = provider.chamadas[0]
        self.assertEqual(chamada["mensagem"], "gastei 10 no almoço")
        self.assertEqual(
            chamada["tools"],
            [{"type": "function", "function": {"name": "criar_entrada"}}],
        )
        # o executor injetado precisa delegar ao registry recém-criado
        tool_call = ToolCall(id="call_1", nome="criar_entrada", argumentos={})
        self.assertEqual(
            chamada["tool_executor"](tool_call),
            {"ok": True, "nome": "criar_entrada"},
        )

    def test_resposta_sem_conteudo_devolve_string_vazia(self) -> None:
        facade, *_ = self._facade(
            usuario=object(),
            resposta=LLMResposta(conteudo=None),
        )
        self.assertEqual(facade.processar_mensagem("9", "msg"), "")


class WebhookTelegramTests(SimpleTestCase):
    """O webhook agora apenas enfileira via Celery (Issue #18).

    Os testes substituem ``WebhookTelegram.task`` por um *stub* que registra
    as chamadas, evitando depender de um broker Redis no ambiente de teste.
    """

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.enfileiradas: list[dict[str, Any]] = []

        outer = self

        class _StubTask:
            def delay(self, **kwargs: Any) -> None:
                outer.enfileiradas.append(kwargs)

        self._original_task = WebhookTelegram.task
        WebhookTelegram.task = _StubTask()  # type: ignore[assignment]

    def tearDown(self) -> None:
        WebhookTelegram.task = self._original_task  # type: ignore[assignment]

    def _post(self, payload: dict[str, Any] | str) -> Any:
        body = payload if isinstance(payload, str) else json.dumps(payload)
        request = self.factory.post(
            "/api/v1/mensageria/webhook/telegram/",
            data=body,
            content_type="application/json",
        )
        return WebhookTelegram.as_view()(request)

    def test_payload_valido_enfileira_task(self) -> None:
        response = self._post(
            {"message": {"chat": {"id": 42}, "text": "oi"}}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {"ok": True, "enfileirado": True})
        self.assertEqual(
            self.enfileiradas,
            [{"telegram_user_id": "42", "texto": "oi"}],
        )

    def test_payload_sem_texto_e_ignorado(self) -> None:
        response = self._post({"message": {"chat": {"id": 42}}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"ok": True, "ignorado": True})
        self.assertEqual(self.enfileiradas, [])

    def test_payload_json_invalido_retorna_400(self) -> None:
        response = self._post("{nao-json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)["ok"])
        self.assertEqual(self.enfileiradas, [])

    def test_broker_offline_nao_propaga(self) -> None:
        class _BrokerOffline:
            def delay(self, **kwargs: Any) -> None:
                raise RuntimeError("broker offline")

        WebhookTelegram.task = _BrokerOffline()  # type: ignore[assignment]

        response = self._post({"message": {"chat": {"id": 1}, "text": "oi"}})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content), {"ok": True, "erro": "interno"}
        )


class FacadeIntegracaoComProviderLLMTests(TestCase):
    """Garante que a Facade casa de verdade com o ``ProviderLLM`` real.

    Usa um ``LLMPort`` falso para fechar o ciclo function calling sem precisar
    do SDK da OpenAI: a 1ª resposta pede uma tool e a 2ª devolve texto.
    """

    def test_loop_completo_executa_tool_e_retorna_texto(self) -> None:
        from apps.provider_llm.ports.llm_port import LLMPort
        from apps.provider_llm.services.provider_llm import ProviderLLM

        usuario = User.objects.create_user(
            username="ana", password="x", telegram_id="55"
        )

        class _FakeLLM(LLMPort):
            def __init__(self) -> None:
                self.respostas = [
                    LLMResposta(
                        conteudo=None,
                        tool_calls=[
                            ToolCall(
                                id="call_1",
                                nome="listar_entradas",
                                argumentos={},
                            )
                        ],
                    ),
                    LLMResposta(conteudo="você não tem entradas"),
                ]

            def enviar(self, mensagem: str, tools=None, historico=None):
                return self.respostas.pop(0)

        facade = MensageriaFacade(provider_llm=ProviderLLM(llm=_FakeLLM()))

        resposta = facade.processar_mensagem("55", "quais minhas entradas?")

        self.assertEqual(resposta, "você não tem entradas")
        usuario.delete()
