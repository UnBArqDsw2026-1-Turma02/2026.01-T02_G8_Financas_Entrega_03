"""Webhook do Telegram — entrega updates à task Celery (Issue #18).

O Bot API do Telegram considera o webhook ``offline`` se o servidor demorar
mais que poucos segundos para responder. Por isso a view só faz três coisas:

1. parseia o JSON;
2. extrai ``telegram_user_id`` e ``texto`` (ignora updates sem texto);
3. enfileira ``processar_mensagem_task`` e devolve ``200 OK`` imediatamente.

O processamento (Auth → LLM → tools → Sender) acontece no worker. Erros lá
nunca chegam ao Telegram — eles são logados e descartados pela própria task.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.provider_mensageria.tasks import processar_mensagem_task

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class WebhookTelegram(View):
    """Endpoint público que entrega updates do Telegram para a fila Celery."""

    task = processar_mensagem_task

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            payload: dict[str, Any] = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"ok": False, "erro": "payload JSON inválido"}, status=400
            )

        telegram_user_id, texto = self._extrair_mensagem(payload)
        if telegram_user_id is None or not texto:
            return JsonResponse({"ok": True, "ignorado": True})

        try:
            self.task.delay(
                telegram_user_id=str(telegram_user_id), texto=texto
            )
        except Exception:  # noqa: BLE001 — broker offline não pode derrubar webhook
            logger.exception("Falha ao enfileirar task de mensagem do Telegram")
            return JsonResponse({"ok": True, "erro": "interno"})

        return JsonResponse({"ok": True, "enfileirado": True})

    @staticmethod
    def _extrair_mensagem(
        payload: dict[str, Any],
    ) -> tuple[str | int | None, str]:
        message = payload.get("message") or payload.get("edited_message") or {}
        chat = message.get("chat") or {}
        autor = message.get("from") or {}
        telegram_user_id = chat.get("id") or autor.get("id")
        texto = message.get("text") or ""
        return telegram_user_id, texto
