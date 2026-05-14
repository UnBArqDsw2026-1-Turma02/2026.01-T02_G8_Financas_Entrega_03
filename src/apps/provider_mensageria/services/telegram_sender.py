"""Provider de saída do Telegram — envia a resposta gerada pela Facade (Issue #18).

A Facade orquestra LLM/tools e devolve uma string; cabe a este componente
publicar essa string de volta no chat do usuário via Bot API. É um colaborador
da task Celery — fica isolado aqui para que erros de I/O (timeout, 5xx, rate
limit) sejam tipados e a task possa decidir entre *retry* e descarte.

Usa apenas a stdlib (``urllib``) porque o projeto não inclui ``requests``
nas dependências.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramSenderError(Exception):
    """Falha permanente na chamada ao Bot API — não deve ser retentada."""


class TelegramTransientError(TelegramSenderError):
    """Falha transitória (timeout, 5xx, 429) — alvo de *retry* exponencial."""


class TelegramSender:
    BASE_URL = "https://api.telegram.org"
    TIMEOUT_SEGUNDOS = 5
    STATUS_TRANSITORIOS = {408, 425, 429}

    def __init__(self, bot_token: str | None = None) -> None:
        self._bot_token = bot_token or getattr(settings, "TELEGRAM_BOT_TOKEN", "")

    def enviar(self, chat_id: str, texto: str) -> None:
        if not texto:
            return
        if not self._bot_token:
            logger.warning(
                "TELEGRAM_BOT_TOKEN ausente — resposta não foi entregue ao chat %s",
                chat_id,
            )
            return

        url = f"{self.BASE_URL}/bot{self._bot_token}/sendMessage"
        body = json.dumps({"chat_id": chat_id, "text": texto}).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SEGUNDOS) as resp:
                if resp.status >= 500:
                    raise TelegramTransientError(f"status {resp.status}")
        except urllib.error.HTTPError as exc:
            if exc.code in self.STATUS_TRANSITORIOS or 500 <= exc.code < 600:
                raise TelegramTransientError(str(exc)) from exc
            raise TelegramSenderError(str(exc)) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TelegramTransientError(str(exc)) from exc
