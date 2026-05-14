from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class ProgressoDiario(models.Model):
    """Snapshot diário do progresso de orçamento do usuário (Issue #13).

    Cada registro classifica o dia em uma das três situações mutuamente
    exclusivas, na ordem de severidade: `usou_extra` > `usou_reserva` >
    `dentro_limite`. O `ProgressoService` é responsável por preencher esses
    campos a partir do estado do orçamento.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progressos_diarios",
    )
    data = models.DateField()
    dentro_limite = models.BooleanField(default=False)
    usou_reserva = models.BooleanField(default=False)
    usou_extra = models.BooleanField(default=False)

    class Meta:
        ordering = ["-data"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "data"], name="progresso_diario_unico_por_dia"
            ),
        ]

    def __str__(self) -> str:
        return f"ProgressoDiario({self.usuario}, {self.data})"
