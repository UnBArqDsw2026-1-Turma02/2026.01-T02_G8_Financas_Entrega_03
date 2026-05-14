"""Testes unitarios e de API para a Carteira (Issue #12)."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import (
    Categoria,
    Entrada,
    Pagamento,
    Saida,
    TipoGasto,
    Transacao,
)
from apps.finance.services import CarteiraService

User = get_user_model()

HOJE = timezone.localdate()
ANO, MES = HOJE.year, HOJE.month
DIAS_MES = calendar.monthrange(ANO, MES)[1]


def _aware(dia: int, hora: int = 12) -> datetime:
    return timezone.make_aware(datetime(ANO, MES, dia, hora, 0))


def _redatar(transacao: Transacao, dia: int) -> None:
    Transacao.objects.filter(pk=transacao.pk).update(data=_aware(dia))


class CarteiraServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="cart1", password="x")
        self.categoria = Categoria.objects.create(
            nome="Lazer",
            descricao="Saidas",
            cor="#aabbcc",
            usuario=self.user,
        )
        # Renda mensal fixa para limite_base = 100/dia.
        self.renda = Decimal(DIAS_MES) * Decimal("100.00")
        entrada = Entrada.objects.create(
            nome="Salario",
            valor=self.renda,
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)
        self.service = CarteiraService()

    def _saida(self, dia: int, valor: Decimal) -> Saida:
        s = Saida.objects.create(
            nome=f"Compra {dia}",
            valor=valor,
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(s, dia)
        return s

    def test_estado_inicial_zerado(self) -> None:
        estado = self.service.obter_estado(self.user, date(ANO, MES, 1))
        self.assertEqual(estado.gasto_dia, Decimal("0.00"))
        self.assertEqual(estado.limite_diario, Decimal("100.00"))
        self.assertEqual(estado.falta_limite, Decimal("100.00"))
        self.assertEqual(estado.saldo_reserva, Decimal("0.00"))
        self.assertEqual(estado.saldo_extra, Decimal("0.00"))

    def test_falta_limite_descontando_gasto(self) -> None:
        self._saida(1, Decimal("85.00"))
        estado = self.service.obter_estado(self.user, date(ANO, MES, 1))
        self.assertEqual(estado.gasto_dia, Decimal("85.00"))
        self.assertEqual(estado.falta_limite, Decimal("15.00"))

    def test_falta_limite_nunca_negativa(self) -> None:
        # Gasto > limite: falta_limite deve ser zerada.
        self._saida(1, Decimal("250.00"))
        estado = self.service.obter_estado(self.user, date(ANO, MES, 1))
        self.assertEqual(estado.falta_limite, Decimal("0.00"))

    def test_estado_inclui_extra_acumulado(self) -> None:
        # Dia 1 fechado: gasto 250 → excesso 150 vira extra (sem reserva).
        # data_ref = dia 2.
        self._saida(1, Decimal("250.00"))
        estado = self.service.obter_estado(self.user, date(ANO, MES, 2))
        self.assertEqual(estado.saldo_reserva, Decimal("0.00"))
        self.assertEqual(estado.saldo_extra, Decimal("150.00"))

    def test_estado_isolado_por_usuario(self) -> None:
        outro = User.objects.create_user(username="cart2", password="x")
        estado_outro = self.service.obter_estado(outro, date(ANO, MES, 1))
        self.assertEqual(estado_outro.limite_diario, Decimal("0.00"))


class CarteiraApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="cartapi", password="Senha!2026")
        entrada = Entrada.objects.create(
            nome="Salario",
            valor=Decimal(DIAS_MES) * Decimal("100.00"),
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)
        self.client.force_authenticate(self.user)

    def test_get_carteira_exige_auth(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/v1/carteira/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_carteira_ok(self) -> None:
        resp = self.client.get("/api/v1/carteira/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(resp.data.keys()),
            {
                "gasto_dia",
                "falta_limite",
                "limite_diario",
                "saldo_reserva",
                "saldo_extra",
            },
        )
        self.assertEqual(Decimal(resp.data["limite_diario"]), Decimal("100.00"))
        self.assertEqual(Decimal(resp.data["gasto_dia"]), Decimal("0.00"))
        self.assertEqual(Decimal(resp.data["falta_limite"]), Decimal("100.00"))
