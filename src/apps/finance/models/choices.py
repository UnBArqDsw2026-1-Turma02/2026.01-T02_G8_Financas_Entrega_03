from __future__ import annotations

from django.db import models


class Pagamento(models.TextChoices):
    PIX = "PIX", "PIX"
    CREDITO = "CREDITO", "Crédito"
    DEBITO = "DEBITO", "Débito"
    DINHEIRO = "DINHEIRO", "Dinheiro"


class TipoGasto(models.TextChoices):
    FIXO = "FIXO", "Fixo"
    VARIAVEL = "VARIAVEL", "Variável"
