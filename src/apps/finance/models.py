"""Models do domínio financeiro (G8).

Hierarquia (multi-table inheritance):
    Transacao
    ├── Entrada
    ├── Saida
    └── Parcelamento

Categoria é uma entidade independente referenciada por Saida e Parcelamento.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Pagamento(models.TextChoices):
    PIX = "PIX", "PIX"
    CREDITO = "CREDITO", "Crédito"
    DEBITO = "DEBITO", "Débito"
    DINHEIRO = "DINHEIRO", "Dinheiro"


class TipoGasto(models.TextChoices):
    FIXO = "FIXO", "Fixo"
    VARIAVEL = "VARIAVEL", "Variável"


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


class Transacao(models.Model):
    """Base concreta da hierarquia (Product do Factory Method da Issue #03)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=120)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    data = models.DateTimeField(auto_now_add=True)
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
