"""Testes da task Celery ``processar_mensagem_task`` (Issue #18).

Verifica o fluxo completo Webhook → Celery → Facade → Sender, o
*retry* exponencial em falhas transitórias e o descarte silencioso de
erros permanentes. A task é executada *eager* (síncrona) via
``CELERY_TASK_ALWAYS_EAGER``, dispensando broker Redis na suíte.
"""

from __future__ import annotations

import json
import logging
import urllib.error
from io import BytesIO
from typing import Any

from celery import current_app
from django.test import SimpleTestCase, override_settings

from apps.provider_mensageria import tasks as tasks_module
from apps.provider_mensageria.services.telegram_sender import (
    TelegramSender,
    TelegramSenderError,
    TelegramTransientError,
)
from apps.provider_mensageria.tasks import processar_mensagem_task


class _StubFacade:
    """Facade falsa controlável — guarda chamadas e responde com texto fixo."""

    def __init__(self, resposta: str = "ok", erro: Exception | None = None) -> None:
        self.resposta = resposta
        self.erro = erro
        self.chamadas: list[tuple[str, str]] = []

    def processar_mensagem(self, telegram_user_id: str, texto: str) -> str:
        self.chamadas.append((telegram_user_id, texto))
        if self.erro is not None:
            raise self.erro
        return self.resposta


class _StubSender:
    def __init__(self, erro: Exception | None = None) -> None:
        self.erro = erro
        self.enviadas: list[tuple[str, str]] = []

    def enviar(self, chat_id: str, texto: str) -> None:
        self.enviadas.append((chat_id, texto))
        if self.erro is not None:
            raise self.erro


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=False)
class ProcessarMensagemTaskTests(SimpleTestCase):
    def setUp(self) -> None:
        # Garante que a configuração eager seja lida pelo Celery em runtime.
        current_app.conf.task_always_eager = True
        current_app.conf.task_eager_propagates = False

        self.facade = _StubFacade(resposta="resposta final")
        self.sender = _StubSender()

        self._original_facade = tasks_module.MensageriaFacade
        self._original_sender = tasks_module.TelegramSender
        tasks_module.MensageriaFacade = lambda: self.facade  # type: ignore[assignment]
        tasks_module.TelegramSender = lambda: self.sender  # type: ignore[assignment]

    def tearDown(self) -> None:
        tasks_module.MensageriaFacade = self._original_facade  # type: ignore[assignment]
        tasks_module.TelegramSender = self._original_sender  # type: ignore[assignment]
        current_app.conf.task_always_eager = False

    def test_fluxo_feliz_chama_facade_e_sender(self) -> None:
        resultado = processar_mensagem_task.apply(
            kwargs={"telegram_user_id": "42", "texto": "oi"}
        ).get()

        self.assertEqual(resultado, "resposta final")
        self.assertEqual(self.facade.chamadas, [("42", "oi")])
        self.assertEqual(self.sender.enviadas, [("42", "resposta final")])

    def test_erro_permanente_e_descartado_sem_crash(self) -> None:
        self.facade.erro = ValueError("payload inválido")

        with self.assertLogs(tasks_module.logger, level=logging.ERROR):
            resultado = processar_mensagem_task.apply(
                kwargs={"telegram_user_id": "42", "texto": "oi"}
            ).get()

        self.assertIsNone(resultado)
        self.assertEqual(self.sender.enviadas, [])

    def test_erro_transitorio_dispara_retry_exponencial(self) -> None:
        self.facade.erro = TimeoutError("openai timeout")

        with self.assertLogs(tasks_module.logger, level=logging.ERROR):
            resultado = processar_mensagem_task.apply(
                kwargs={"telegram_user_id": "42", "texto": "oi"}
            ).get()

        # Esgotados os retries, a task devolve None sem propagar para o worker.
        self.assertIsNone(resultado)
        # Facade foi chamada 1 + MAX_RETRIES vezes (inicial + retries).
        self.assertEqual(len(self.facade.chamadas), 1 + tasks_module.MAX_RETRIES)

    def test_telegram_transient_error_tambem_e_retentado(self) -> None:
        self.facade.erro = None
        self.sender.erro = TelegramTransientError("429 too many")

        with self.assertLogs(tasks_module.logger, level=logging.ERROR):
            resultado = processar_mensagem_task.apply(
                kwargs={"telegram_user_id": "42", "texto": "oi"}
            ).get()

        self.assertIsNone(resultado)
        self.assertEqual(len(self.facade.chamadas), 1 + tasks_module.MAX_RETRIES)


class EhTransitorioTests(SimpleTestCase):
    def test_telegram_transient_e_transitorio(self) -> None:
        self.assertTrue(tasks_module._eh_transitorio(TelegramTransientError("x")))

    def test_telegram_permanente_nao_e_transitorio(self) -> None:
        self.assertFalse(tasks_module._eh_transitorio(TelegramSenderError("x")))

    def test_timeout_e_connection_error_sao_transitorios(self) -> None:
        self.assertTrue(tasks_module._eh_transitorio(TimeoutError()))
        self.assertTrue(tasks_module._eh_transitorio(ConnectionError()))

    def test_value_error_nao_e_transitorio(self) -> None:
        self.assertFalse(tasks_module._eh_transitorio(ValueError("bug")))


class TelegramSenderTests(SimpleTestCase):
    """Testa a tradução de erros HTTP em ``Transient``/``SenderError``."""

    def _patch_urlopen(self, fake: Any) -> None:
        import apps.provider_mensageria.services.telegram_sender as sender_module

        self._original_urlopen = sender_module.urllib.request.urlopen
        sender_module.urllib.request.urlopen = fake  # type: ignore[assignment]

    def tearDown(self) -> None:
        if hasattr(self, "_original_urlopen"):
            import apps.provider_mensageria.services.telegram_sender as sender_module

            sender_module.urllib.request.urlopen = self._original_urlopen  # type: ignore[assignment]

    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_sem_token_apenas_loga_e_retorna(self) -> None:
        # Sem token nem em settings nem no construtor — é no-op (apenas warning).
        TelegramSender().enviar(chat_id="1", texto="oi")

    def test_texto_vazio_e_no_op(self) -> None:
        chamado = []

        def _fail(*a: Any, **k: Any) -> Any:
            chamado.append(True)
            raise AssertionError("não deveria chamar")

        self._patch_urlopen(_fail)
        TelegramSender(bot_token="t").enviar(chat_id="1", texto="")
        self.assertEqual(chamado, [])

    def test_resposta_200_envia_com_payload_correto(self) -> None:
        capturado: dict[str, Any] = {}

        class _Resp:
            status = 200

            def __enter__(self) -> "_Resp":
                return self

            def __exit__(self, *args: Any) -> None:
                return None

        def _fake(req: Any, timeout: int = 0) -> _Resp:
            capturado["url"] = req.full_url
            capturado["body"] = json.loads(req.data.decode("utf-8"))
            return _Resp()

        self._patch_urlopen(_fake)
        TelegramSender(bot_token="abc").enviar(chat_id="42", texto="oi")

        self.assertIn("/botabc/sendMessage", capturado["url"])
        self.assertEqual(capturado["body"], {"chat_id": "42", "text": "oi"})

    def test_http_429_vira_transient(self) -> None:
        def _fake(req: Any, timeout: int = 0) -> Any:
            raise urllib.error.HTTPError(
                req.full_url, 429, "Too Many Requests", {}, BytesIO(b"")
            )

        self._patch_urlopen(_fake)
        with self.assertRaises(TelegramTransientError):
            TelegramSender(bot_token="x").enviar(chat_id="1", texto="oi")

    def test_http_500_vira_transient(self) -> None:
        def _fake(req: Any, timeout: int = 0) -> Any:
            raise urllib.error.HTTPError(
                req.full_url, 503, "Service Unavailable", {}, BytesIO(b"")
            )

        self._patch_urlopen(_fake)
        with self.assertRaises(TelegramTransientError):
            TelegramSender(bot_token="x").enviar(chat_id="1", texto="oi")

    def test_http_400_vira_permanente(self) -> None:
        def _fake(req: Any, timeout: int = 0) -> Any:
            raise urllib.error.HTTPError(
                req.full_url, 400, "Bad Request", {}, BytesIO(b"")
            )

        self._patch_urlopen(_fake)
        with self.assertRaises(TelegramSenderError) as ctx:
            TelegramSender(bot_token="x").enviar(chat_id="1", texto="oi")
        self.assertNotIsInstance(ctx.exception, TelegramTransientError)

    def test_url_error_vira_transient(self) -> None:
        def _fake(req: Any, timeout: int = 0) -> Any:
            raise urllib.error.URLError("connection refused")

        self._patch_urlopen(_fake)
        with self.assertRaises(TelegramTransientError):
            TelegramSender(bot_token="x").enviar(chat_id="1", texto="oi")
