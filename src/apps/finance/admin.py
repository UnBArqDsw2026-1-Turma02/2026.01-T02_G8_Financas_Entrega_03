from django.contrib import admin

from apps.finance.models import (
    Categoria,
    Entrada,
    Extra,
    LimiteDiario,
    Parcelamento,
    ProgressoDiario,
    Reserva,
    Saida,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor", "usuario")
    search_fields = ("nome", "usuario__username")


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ("nome", "valor", "fonte", "recorrencia", "data", "usuario")
    list_filter = ("recorrencia",)
    search_fields = ("nome", "fonte")


@admin.register(Saida)
class SaidaAdmin(admin.ModelAdmin):
    list_display = ("nome", "valor", "categoria", "pagamento", "tipo_gasto", "data", "usuario")
    list_filter = ("pagamento", "tipo_gasto")
    search_fields = ("nome",)


@admin.register(Parcelamento)
class ParcelamentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "valor",
        "categoria",
        "pagamento",
        "num_parcelas",
        "parcela_atual",
        "valor_parcela",
        "data",
        "usuario",
    )
    list_filter = ("pagamento",)
    search_fields = ("nome",)


@admin.register(LimiteDiario)
class LimiteDiarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "data", "limite_calculado", "limite_ajustado", "gasto_dia")
    list_filter = ("data",)
    search_fields = ("usuario__username",)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "saldo")
    search_fields = ("usuario__username",)


@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    list_display = ("usuario", "data", "valor")
    list_filter = ("data",)
    search_fields = ("usuario__username",)


@admin.register(ProgressoDiario)
class ProgressoDiarioAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "data",
        "dentro_limite",
        "usou_reserva",
        "usou_extra",
    )
    list_filter = ("data", "dentro_limite", "usou_reserva", "usou_extra")
    search_fields = ("usuario__username",)
