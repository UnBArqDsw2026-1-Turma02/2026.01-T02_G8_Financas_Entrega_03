"""Serializers da API de Finance."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.finance.models import (
    Categoria,
    Entrada,
    LimiteDiario,
    Pagamento,
    Parcelamento,
    Reserva,
    Saida,
    TipoGasto,
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nome", "descricao", "cor")
        read_only_fields = ("id",)

    def validate_nome(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Nome não pode ser vazio.")
        return value

    def validate_descricao(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Descrição não pode ser vazia.")
        return value

    def validate_cor(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Cor não pode ser vazia.")
        return value


class EntradaSerializer(serializers.ModelSerializer):
    recorrencia = serializers.BooleanField()

    class Meta:
        model = Entrada
        fields = ("id", "nome", "valor", "fonte", "recorrencia", "data")
        read_only_fields = ("id", "data")

    def validate_nome(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Nome não pode ser vazio.")
        return value

    def validate_valor(self, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero.")
        return value


class ParcelamentoSerializer(serializers.ModelSerializer):
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())
    pagamento = serializers.ChoiceField(choices=Pagamento.choices)
    valor_parcela = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    antecipadas_no_ciclo = serializers.SerializerMethodField()

    class Meta:
        model = Parcelamento
        fields = (
            "id",
            "nome",
            "valor",
            "categoria",
            "pagamento",
            "num_parcelas",
            "parcela_atual",
            "valor_parcela",
            "antecipadas_no_ciclo",
            "data",
        )
        read_only_fields = (
            "id",
            "data",
            "parcela_atual",
            "valor_parcela",
            "antecipadas_no_ciclo",
        )

    def get_antecipadas_no_ciclo(self, obj: Parcelamento) -> int:
        return obj.antecipadas_no_ciclo_atual

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request") if hasattr(self, "context") else None
        if request is not None and request.user.is_authenticated:
            self.fields["categoria"].queryset = Categoria.objects.filter(
                usuario=request.user
            )

    def validate_nome(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Nome não pode ser vazio.")
        return value

    def validate_valor(self, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero.")
        return value

    def validate_num_parcelas(self, value: int) -> int:
        if value is None or value < 1:
            raise serializers.ValidationError("Número de parcelas deve ser >= 1.")
        return value


class SimulacaoGastoRequestSerializer(serializers.Serializer):
    valor = serializers.DecimalField(max_digits=12, decimal_places=2)
    parcelado = serializers.BooleanField(default=False)
    num_parcelas = serializers.IntegerField(default=1, min_value=1)

    def validate_valor(self, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs.get("parcelado") and attrs.get("num_parcelas", 1) < 1:
            raise serializers.ValidationError(
                {"num_parcelas": "Número de parcelas deve ser >= 1."}
            )
        return attrs


class SimulacaoParcelamentoSerializer(serializers.Serializer):
    valor_parcela = serializers.DecimalField(max_digits=12, decimal_places=2)
    impacto_mensal = serializers.DecimalField(max_digits=12, decimal_places=2)


class SimulacaoGastoResponseSerializer(serializers.Serializer):
    impacta_30_porcento = serializers.BooleanField()
    dentro_orcamento = serializers.BooleanField()
    orcamento_mensal_atual = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    novo_orcamento = serializers.DecimalField(max_digits=12, decimal_places=2)
    limite_diario_atual = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    novo_limite_diario = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    simulacao_parcelamento = SimulacaoParcelamentoSerializer(required=False)


class TransacaoExtratoSerializer(serializers.Serializer):
    """Serializer polimórfico para o extrato — devolve o tipo concreto da Transacao."""

    id = serializers.UUIDField()
    nome = serializers.CharField()
    valor = serializers.DecimalField(max_digits=12, decimal_places=2)
    data = serializers.DateTimeField()
    tipo = serializers.SerializerMethodField()
    detalhes = serializers.SerializerMethodField()

    _TIPOS = ("entrada", "saida", "parcelamento")

    def _subtipo(self, obj):
        for nome in self._TIPOS:
            sub = getattr(obj, nome, None)
            if sub is not None:
                return nome, sub
        return None, obj

    def get_tipo(self, obj) -> str:
        tipo, _ = self._subtipo(obj)
        return tipo or "transacao"

    def get_detalhes(self, obj) -> dict:
        tipo, sub = self._subtipo(obj)
        if tipo == "entrada":
            return {"fonte": sub.fonte, "recorrencia": sub.recorrencia}
        if tipo == "saida":
            return {
                "categoria": {"id": str(sub.categoria_id), "nome": sub.categoria.nome},
                "pagamento": sub.pagamento,
                "tipo_gasto": sub.tipo_gasto,
            }
        if tipo == "parcelamento":
            return {
                "categoria": {"id": str(sub.categoria_id), "nome": sub.categoria.nome},
                "pagamento": sub.pagamento,
                "num_parcelas": sub.num_parcelas,
                "parcela_atual": sub.parcela_atual,
                "valor_parcela": str(sub.valor_parcela),
            }
        return {}


class ExtratoResponseSerializer(serializers.Serializer):
    transacoes = TransacaoExtratoSerializer(many=True)
    saldo_atual = serializers.DecimalField(max_digits=14, decimal_places=2)
    filtros_aplicados = serializers.DictField()


class SaidaSerializer(serializers.ModelSerializer):
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())
    pagamento = serializers.ChoiceField(choices=Pagamento.choices)
    tipo_gasto = serializers.ChoiceField(choices=TipoGasto.choices)

    class Meta:
        model = Saida
        fields = ("id", "nome", "valor", "categoria", "pagamento", "tipo_gasto", "data")
        read_only_fields = ("id", "data")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request") if hasattr(self, "context") else None
        if request is not None and request.user.is_authenticated:
            self.fields["categoria"].queryset = Categoria.objects.filter(
                usuario=request.user
            )

    def validate_nome(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Nome não pode ser vazio.")
        return value

    def validate_valor(self, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero.")
        return value


class LimiteDiarioSerializer(serializers.ModelSerializer):
    limite_efetivo = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    sobra_dia = serializers.SerializerMethodField()

    class Meta:
        model = LimiteDiario
        fields = (
            "id",
            "data",
            "limite_calculado",
            "limite_ajustado",
            "limite_efetivo",
            "gasto_dia",
            "sobra_dia",
        )
        read_only_fields = fields

    def get_sobra_dia(self, obj: LimiteDiario) -> Decimal:
        return (obj.limite_efetivo - obj.gasto_dia).quantize(Decimal("0.01"))


class AjustarLimiteDiarioSerializer(serializers.Serializer):
    limite_ajustado = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_limite_ajustado(self, value: Decimal) -> Decimal:
        if value is None or value < 0:
            raise serializers.ValidationError(
                "Limite ajustado nao pode ser negativo."
            )
        return value


class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = ("id", "saldo")
        read_only_fields = fields


class ExtraSerializer(serializers.Serializer):
    valor = serializers.DecimalField(max_digits=12, decimal_places=2)
    ano = serializers.IntegerField()
    mes = serializers.IntegerField()


class CarteiraSerializer(serializers.Serializer):
    gasto_dia = serializers.DecimalField(max_digits=12, decimal_places=2)
    falta_limite = serializers.DecimalField(max_digits=12, decimal_places=2)
    limite_diario = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo_reserva = serializers.DecimalField(max_digits=12, decimal_places=2)
    saldo_extra = serializers.DecimalField(max_digits=12, decimal_places=2)


class DashboardVisaoGeralSerializer(serializers.Serializer):
    total_entradas = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_saidas_fixas = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_saidas_variaveis = serializers.DecimalField(
        max_digits=14, decimal_places=2
    )
    saldo_disponivel = serializers.DecimalField(max_digits=14, decimal_places=2)


class DashboardCategoriaSerializer(serializers.Serializer):
    id = serializers.CharField()
    nome = serializers.CharField()
    cor = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    percentual = serializers.DecimalField(max_digits=6, decimal_places=2)


class DashboardCategoriasResponseSerializer(serializers.Serializer):
    categorias = DashboardCategoriaSerializer(many=True)


class DashboardDiaSerializer(serializers.Serializer):
    data = serializers.DateField()
    total_gasto = serializers.DecimalField(max_digits=14, decimal_places=2)


class DashboardTendenciaResponseSerializer(serializers.Serializer):
    dias = DashboardDiaSerializer(many=True)


class DiaProgressoSerializer(serializers.Serializer):
    data = serializers.DateField()
    dentro_limite = serializers.BooleanField()
    usou_reserva = serializers.BooleanField()
    usou_extra = serializers.BooleanField()
    gasto = serializers.DecimalField(max_digits=14, decimal_places=2)
    limite = serializers.DecimalField(max_digits=14, decimal_places=2)


class ProgressoSerializer(serializers.Serializer):
    ano = serializers.IntegerField()
    mes = serializers.IntegerField()
    streak = serializers.IntegerField()
    calendario = DiaProgressoSerializer(many=True)


class AlertaSerializer(serializers.Serializer):
    gatilho = serializers.CharField()
    mensagem = serializers.CharField()


class AlertasResponseSerializer(serializers.Serializer):
    alertas = AlertaSerializer(many=True)
