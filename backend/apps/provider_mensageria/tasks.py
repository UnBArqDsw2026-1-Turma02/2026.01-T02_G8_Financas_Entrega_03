"""Tarefas Celery do app de mensageria (Issue #18).

O webhook do Telegram precisa responder em poucos ms — qualquer chamada ao
LLM/tools rodando no request-thread arrisca timeout no Bot API. Esta task
move o trabalho pesado para um worker:

    Telegram → webhook → ``processar_mensagem_task.delay`` → Facade → Sender

Retry exponencial é aplicado apenas em falhas reconhecidas como transitórias
(rate limit/timeout do LLM, 5xx/429 do Telegram, perda de conexão). Erros
permanentes (payload inválido, bug de tool) são logados e descartados para
não derrubar o worker — o usuário não recebe resposta, mas o consumer
continua processando o resto da fila.
"""

from __future__ import annotations

import logging

from celery import shared_task

from apps.provider_mensageria.services.mensageria_facade import MensageriaFacade
from apps.provider_mensageria.services.telegram_sender import (
    TelegramSender,
    TelegramTransientError,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE_SEGUNDOS = 2


def _eh_transitorio(exc: BaseException) -> bool:
    if isinstance(exc, (TelegramTransientError, TimeoutError, ConnectionError)):
        return True
    try:
        from openai import APIConnectionError, APITimeoutError, RateLimitError
    except ImportError:
        return False
    return isinstance(exc, (APIConnectionError, APITimeoutError, RateLimitError))


@shared_task(
    bind=True,
    name="provider_mensageria.processar_mensagem",
    max_retries=MAX_RETRIES,
    acks_late=True,
)
def processar_mensagem_task(
    self, telegram_user_id: str, texto: str
) -> str | None:
    """Processa uma mensagem do Telegram em background.

    Retorna o texto enviado ao usuário (útil para testes) ou ``None`` quando
    a mensagem foi descartada por erro permanente.
    """
    try:
        resposta = MensageriaFacade().processar_mensagem(
            telegram_user_id=telegram_user_id, texto=texto
        )
        TelegramSender().enviar(chat_id=telegram_user_id, texto=resposta)
        return resposta
    except Exception as exc:  # noqa: BLE001 — classificamos antes de propagar
        if _eh_transitorio(exc) and self.request.retries < MAX_RETRIES:
            countdown = RETRY_BACKOFF_BASE_SEGUNDOS ** (self.request.retries + 1)
            raise self.retry(exc=exc, countdown=countdown)
        logger.exception(
            "Falha ao processar mensagem do Telegram (chat=%s)",
            telegram_user_id,
        )
        return None
