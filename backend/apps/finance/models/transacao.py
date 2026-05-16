from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import ExpressionWrapper, F, IntegerField
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone

from apps.finance.models.categoria import Categoria
from apps.finance.models.choices import Pagamento, TipoGasto


class Transacao(models.Model):
    """Base concreta da hierarquia (Product do Factory Method da Issue #03)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=120)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    data = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transacoes",
    )

    class Meta:
        ordering = ["-data"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(valor__gt=0),
                name="transacao_valor_positivo",
            ),
            models.CheckConstraint(
                check=~models.Q(nome=""),
                name="transacao_nome_not_empty",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.valor})"

    def clean(self) -> None:
        super().clean()
        if not self.nome or not self.nome.strip():
            raise ValidationError({"nome": "Nome não pode ser vazio."})
        if self.valor is None or self.valor <= 0:
            raise ValidationError({"valor": "Valor deve ser maior que zero."})


class Entrada(Transacao):
    fonte = models.CharField(max_length=120, blank=True)
    recorrencia = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"

    @classmethod
    def ativas_no_mes(cls, usuario, ano: int, mes: int):
        """Entradas do usuário consideradas no mês (ano, mes).

        Entradas com `recorrencia=True` repetem todo mês a partir do mês de
        criação; as não recorrentes só aparecem no próprio mês.
        """
        alvo = ano * 12 + mes
        return (
            cls.objects.filter(usuario=usuario)
            .annotate(
                _inicio=ExpressionWrapper(
                    ExtractYear("data") * 12 + ExtractMonth("data"),
                    output_field=IntegerField(),
                )
            )
            .filter(
                models.Q(recorrencia=True, _inicio__lte=alvo)
                | models.Q(recorrencia=False, _inicio=alvo)
            )
        )


class Saida(Transacao):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="saidas",
    )
    pagamento = models.CharField(max_length=10, choices=Pagamento.choices)
    tipo_gasto = models.CharField(max_length=10, choices=TipoGasto.choices)

    class Meta:
        verbose_name = "Saída"
        verbose_name_plural = "Saídas"


class Parcelamento(Transacao):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="parcelamentos",
    )
    pagamento = models.CharField(max_length=10, choices=Pagamento.choices)
    num_parcelas = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    parcela_atual = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    valor_parcela = models.DecimalField(max_digits=12, decimal_places=2)
    antecipadas_no_ciclo = models.PositiveIntegerField(default=0)
    ciclo_referencia = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Parcelamento"
        verbose_name_plural = "Parcelamentos"
        constraints = [
            models.CheckConstraint(
                check=models.Q(num_parcelas__gte=1),
                name="parcelamento_num_parcelas_min1",
            ),
            models.CheckConstraint(
                check=models.Q(parcela_atual__gte=1),
                name="parcelamento_parcela_atual_min1",
            ),
            models.CheckConstraint(
                check=models.Q(valor_parcela__gt=0),
                name="parcelamento_valor_parcela_positivo",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.valor and self.num_parcelas and not self.valor_parcela:
            self.valor_parcela = (Decimal(self.valor) / self.num_parcelas).quantize(
                Decimal("0.01")
            )
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if (
            self.parcela_atual
            and self.num_parcelas
            and self.parcela_atual > self.num_parcelas
        ):
            raise ValidationError(
                {
                    "parcela_atual": (
                        "Parcela atual não pode exceder o número total de parcelas."
                    )
                }
            )

    def pode_editar(self) -> bool:
        return self.parcela_atual == 1

    @staticmethod
    def _inicio_do_ciclo(today=None):
        today = today or timezone.localdate()
        return today.replace(day=1)

    @property
    def antecipadas_no_ciclo_atual(self) -> int:
        inicio = self._inicio_do_ciclo()
        if self.ciclo_referencia == inicio:
            return self.antecipadas_no_ciclo
        return 0

    def antecipar_parcela(self) -> None:
        if self.parcela_atual >= self.num_parcelas:
            raise ValidationError(
                {"parcela_atual": "Parcelamento já está quitado."}
            )
        inicio = self._inicio_do_ciclo()
        if self.ciclo_referencia != inicio:
            self.antecipadas_no_ciclo = 0
            self.ciclo_referencia = inicio
        self.parcela_atual += 1
        self.antecipadas_no_ciclo += 1
        self.save()

    @classmethod
    def ativos_no_mes(cls, usuario, ano: int, mes: int):
        """Parcelamentos do usuário com parcela devida no mês (ano, mes).

        Um parcelamento criado em (Y0, M0) com N parcelas é ativo nos meses
        [Y0*12+M0, Y0*12+M0 + N - 1]. Fora dessa janela, o parcelamento ainda
        não começou ou já foi quitado.
        """
        alvo = ano * 12 + mes
        return (
            cls.objects.filter(usuario=usuario)
            .annotate(
                _inicio=ExpressionWrapper(
                    ExtractYear("data") * 12 + ExtractMonth("data"),
                    output_field=IntegerField(),
                )
            )
            .annotate(
                _fim=ExpressionWrapper(
                    F("_inicio") + F("num_parcelas") - 1,
                    output_field=IntegerField(),
                )
            )
            .filter(_inicio__lte=alvo, _fim__gte=alvo)
        )
