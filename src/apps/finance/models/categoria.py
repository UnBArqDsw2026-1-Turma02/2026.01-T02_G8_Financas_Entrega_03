from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Categoria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=80)
    descricao = models.TextField()
    cor = models.CharField(max_length=7)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorias",
    )

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(nome=""),
                name="categoria_nome_not_empty",
            ),
            models.CheckConstraint(
                check=~models.Q(descricao=""),
                name="categoria_descricao_not_empty",
            ),
            models.CheckConstraint(
                check=~models.Q(cor=""),
                name="categoria_cor_not_empty",
            ),
        ]

    def __str__(self) -> str:
        return self.nome

    def clean(self) -> None:
        super().clean()
        if not self.nome or not self.nome.strip():
            raise ValidationError({"nome": "Nome não pode ser vazio."})
        if not self.descricao or not self.descricao.strip():
            raise ValidationError({"descricao": "Descrição não pode ser vazia."})
        if not self.cor or not self.cor.strip():
            raise ValidationError({"cor": "Cor não pode ser vazia."})
