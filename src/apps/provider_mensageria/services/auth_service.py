"""AuthService — Subsistema 1 da Facade de mensageria (Issue #16).

Wrapper fino sobre ``apps.accounts.services.AuthService`` que expõe a
operação ``validar_user`` no vocabulário do diagrama de sequência:
recebe um ``telegram_user_id`` e devolve o ``Usuario`` correspondente —
ou ``None`` se o vínculo ainda não foi feito.
"""

from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model

from apps.accounts.services import AuthService as _CoreAuthService

User = get_user_model()


class AuthService:
    """Valida se um ``telegram_user_id`` corresponde a um usuário autenticado."""

    def __init__(self, core: type[_CoreAuthService] | None = None) -> None:
        self._core = core or _CoreAuthService

    def validar_user(self, telegram_user_id: str) -> Optional["User"]:
        if telegram_user_id is None:
            return None
        return self._core.get_by_telegram_id(str(telegram_user_id))
