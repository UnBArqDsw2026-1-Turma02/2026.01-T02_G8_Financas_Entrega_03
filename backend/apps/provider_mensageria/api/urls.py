"""Rotas do app de mensageria (Issue #16)."""

from __future__ import annotations

from django.urls import path

from apps.provider_mensageria.api.views import WebhookTelegram

urlpatterns = [
    path("webhook/telegram/", WebhookTelegram.as_view(), name="telegram-webhook"),
]
