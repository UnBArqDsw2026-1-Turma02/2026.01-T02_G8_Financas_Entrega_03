"""Histórico de conversa por usuário do Telegram.

Mantém uma janela curta das últimas mensagens (user/assistant) em Redis para
que o LLM tenha contexto entre turnos. Sem persistência longa: o objetivo é
permitir que o usuário continue uma operação sem repetir tudo (ex.: enviar
o valor depois de ter dito "quero registrar uma despesa").
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class ConversationStore:
    """Armazena o histórico de cada conversa em Redis com TTL e janela fixa."""

    KEY_PREFIX = "mensageria:conv:"
    DEFAULT_TTL_SEGUNDOS = 3600
    DEFAULT_MAX_MENSAGENS = 10
    DEFAULT_DB = 2

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
        ttl_segundos: int | None = None,
        max_mensagens: int | None = None,
    ) -> None:
        self._redis = redis_client or self._default_client()
        self._ttl = ttl_segundos or self.DEFAULT_TTL_SEGUNDOS
        self._max = max_mensagens or self.DEFAULT_MAX_MENSAGENS

    @classmethod
    def _default_client(cls) -> redis.Redis:
        broker_url = getattr(
            settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"
        )
        base = broker_url.rsplit("/", 1)[0]
        return redis.Redis.from_url(f"{base}/{cls.DEFAULT_DB}")

    def _key(self, telegram_user_id: str) -> str:
        return f"{self.KEY_PREFIX}{telegram_user_id}"

    def carregar(self, telegram_user_id: str) -> list[dict[str, Any]]:
        try:
            raw = self._redis.get(self._key(telegram_user_id))
        except redis.RedisError:
            logger.exception("Falha ao ler histórico do Redis (chat=%s)", telegram_user_id)
            return []
        if not raw:
            return []
        try:
            historico = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return historico if isinstance(historico, list) else []

    def adicionar_turno(
        self,
        telegram_user_id: str,
        mensagem_user: str,
        resposta_assistant: str,
    ) -> None:
        historico = self.carregar(telegram_user_id)
        historico.append({"role": "user", "content": mensagem_user})
        historico.append({"role": "assistant", "content": resposta_assistant})
        historico = historico[-self._max :]
        try:
            self._redis.setex(
                self._key(telegram_user_id),
                self._ttl,
                json.dumps(historico),
            )
        except redis.RedisError:
            logger.exception(
                "Falha ao gravar histórico no Redis (chat=%s)", telegram_user_id
            )
