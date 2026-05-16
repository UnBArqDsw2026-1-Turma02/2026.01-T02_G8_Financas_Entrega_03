"""Rotas da API de Finance."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.finance.api.views import (
    AjustarLimiteDiarioView,
    AlertasView,
    CarteiraView,
    CategoriaViewSet,
    DashboardCategoriasView,
    DashboardTendenciaView,
    DashboardVisaoGeralView,
    EntradaViewSet,
    ExtraView,
    ExtratoView,
    LimiteDiarioView,
    ParcelamentoViewSet,
    ProgressoView,
    ReservaView,
    SaidaViewSet,
    SimulacaoGastoView,
)

app_name = "finance"

router = DefaultRouter()
router.register(r"categorias", CategoriaViewSet, basename="categoria")
router.register(r"entradas", EntradaViewSet, basename="entrada")
router.register(r"saidas", SaidaViewSet, basename="saida")
router.register(r"parcelamentos", ParcelamentoViewSet, basename="parcelamento")

urlpatterns = [
    path(
        "simular-gasto/",
        SimulacaoGastoView.as_view(),
        name="simular-gasto",
    ),
    path("extrato/", ExtratoView.as_view(), name="extrato"),
    path(
        "limite-diario/",
        LimiteDiarioView.as_view(),
        name="limite-diario",
    ),
    path(
        "limite-diario/ajustar/",
        AjustarLimiteDiarioView.as_view(),
        name="limite-diario-ajustar",
    ),
    path("reserva/", ReservaView.as_view(), name="reserva"),
    path("extra/", ExtraView.as_view(), name="extra"),
    path("carteira/", CarteiraView.as_view(), name="carteira"),
    path("progresso/", ProgressoView.as_view(), name="progresso"),
    path("alertas/", AlertasView.as_view(), name="alertas"),
    path(
        "dashboard/",
        DashboardVisaoGeralView.as_view(),
        name="dashboard-visao-geral",
    ),
    path(
        "dashboard/categorias/",
        DashboardCategoriasView.as_view(),
        name="dashboard-categorias",
    ),
    path(
        "dashboard/tendencia/",
        DashboardTendenciaView.as_view(),
        name="dashboard-tendencia",
    ),
    *router.urls,
]
