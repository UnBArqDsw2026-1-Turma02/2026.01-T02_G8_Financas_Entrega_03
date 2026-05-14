"""Modelo de usuário (G8).

Estende ``AbstractUser`` para preservar o fluxo padrão de autenticação Django
e adicionar o vínculo com o Telegram, usado pelo bot conversacional.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    telegram_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.username
