from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class LimiteDiario(models.Model):
    """Snapshot do limite diário de um usuário em uma data (Issue #11).

    `limite_calculado` é derivado de `(renda_mensal - gastos_fixos) / dias_mes`.
    `limite_ajustado` é opcional e só pode ser menor que `limite_calculado`.
    `gasto_dia` agrega as saídas variáveis do dia.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="limites_diarios",
    )
    data = models.DateField()
    limite_calculado = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    limite_ajustado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    gasto_dia = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ["-data"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "data"], name="limite_diario_unico_por_dia"
            ),
            models.CheckConstraint(
                check=models.Q(limite_calculado__gte=0),
                name="limite_calculado_nao_negativo",
            ),
            models.CheckConstraint(
                check=models.Q(gasto_dia__gte=0),
                name="gasto_dia_nao_negativo",
            ),
        ]

    def __str__(self) -> str:
        return f"LimiteDiario({self.usuario}, {self.data})"

    @property
    def limite_efetivo(self) -> Decimal:
        if self.limite_ajustado is not None:
            return self.limite_ajustado
        return self.limite_calculado


class Reserva(models.Model):
    """Saldo acumulado de sobras do limite diário (Issue #11)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reserva",
    )
    saldo = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(saldo__gte=0),
                name="reserva_saldo_nao_negativo",
            ),
        ]

    def __str__(self) -> str:
        return f"Reserva({self.usuario}, {self.saldo})"


class Extra(models.Model):
    """Saldo negativo ativado quando a reserva zera (Issue #11)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="extras",
    )
    data = models.DateField()
    valor = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ["-data"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "data"], name="extra_unico_por_dia"
            ),
            models.CheckConstraint(
                check=models.Q(valor__gte=0),
                name="extra_valor_nao_negativo",
            ),
        ]

    def __str__(self) -> str:
        return f"Extra({self.usuario}, {self.data}, {self.valor})"
