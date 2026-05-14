"""Serviços de autenticação.

``AuthService`` faz o vínculo entre a identidade do Telegram (``telegram_id``)
e o ``Usuario`` da aplicação. É consumido pelo Facade de mensageria
(Issue #16) ao receber mensagens do bot.
"""

from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class AuthService:
    @staticmethod
    def get_by_telegram_id(telegram_id: str) -> Optional["User"]:
        if not telegram_id:
            return None
        return User.objects.filter(telegram_id=str(telegram_id)).first()

    @staticmethod
    @transaction.atomic
    def link_telegram(user: "User", telegram_id: str) -> "User":
        """Vincula um ``telegram_id`` a um usuário existente.

        Lança ``ValueError`` se o ``telegram_id`` já estiver em uso por
        outro usuário — garantia de unicidade do vínculo.
        """
        telegram_id = str(telegram_id)
        conflict = User.objects.filter(telegram_id=telegram_id).exclude(pk=user.pk).first()
        if conflict is not None:
            raise ValueError("telegram_id já vinculado a outro usuário")
        user.telegram_id = telegram_id
        user.save(update_fields=["telegram_id"])
        return user

    @staticmethod
    @transaction.atomic
    def unlink_telegram(user: "User") -> "User":
        """Desfaz o vínculo do ``telegram_id`` do usuário (no-op se já vazio)."""
        if user.telegram_id:
            user.telegram_id = None
            user.save(update_fields=["telegram_id"])
        return user

    @staticmethod
    def is_authorized(telegram_id: str) -> bool:
        return AuthService.get_by_telegram_id(telegram_id) is not None
