"""Testes do ProgressoService e AlertaService (Issue #13)."""

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
    ProgressoDiario,
    Saida,
    TipoGasto,
    Transacao,
)
from apps.finance.services import AlertaService, ProgressoService

User = get_user_model()

HOJE = timezone.localdate()
ANO, MES = HOJE.year, HOJE.month
DIAS_MES = calendar.monthrange(ANO, MES)[1]


def _aware(dia: int, hora: int = 12) -> datetime:
    return timezone.make_aware(datetime(ANO, MES, dia, hora, 0))


def _redatar(transacao: Transacao, dia: int) -> None:
    Transacao.objects.filter(pk=transacao.pk).update(data=_aware(dia))


class _ProgressoBaseTestCase(TestCase):
    """Base com renda mensal = DIAS_MES * 100 → limite_base = 100/dia."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="prog", password="x")
        self.categoria = Categoria.objects.create(
            nome="Variaveis",
            descricao="Gastos do dia a dia",
            cor="#aabbcc",
            usuario=self.user,
        )
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal(DIAS_MES) * Decimal("100.00"),
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)

    def _saida(self, dia: int, valor: Decimal) -> Saida:
        s = Saida.objects.create(
            nome=f"Compra dia {dia}",
            valor=valor,
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(s, dia)
        return s


class ProgressoServiceTests(_ProgressoBaseTestCase):
    def test_streak_conta_dias_dentro_do_limite(self) -> None:
        # Dias 1-3 sem gasto (sobra completa) → dentro_limite; data_ref=4.
        progresso = ProgressoService().obter_progresso(
            self.user, date(ANO, MES, 4)
        )
        self.assertEqual(progresso.streak, 4)
        for dia in progresso.calendario[:4]:
            self.assertTrue(dia.dentro_limite)
            self.assertFalse(dia.usou_reserva)
            self.assertFalse(dia.usou_extra)

    def test_uso_de_reserva_nao_quebra_streak(self) -> None:
        # Dia 1: sobra 100 → reserva=100.
        # Dia 2: gasto 150 (excesso 50, coberto pela reserva) → usou_reserva.
        # Streak deve continuar (apenas extra quebra).
        self._saida(2, Decimal("150.00"))
        progresso = ProgressoService().obter_progresso(
            self.user, date(ANO, MES, 3)
        )
        self.assertEqual(progresso.streak, 3)
        dia_2 = progresso.calendario[1]
        self.assertTrue(dia_2.usou_reserva)
        self.assertFalse(dia_2.usou_extra)
        self.assertFalse(dia_2.dentro_limite)

    def test_uso_de_extra_quebra_streak(self) -> None:
        # Dia 1: gasto 250 → excesso 150, reserva=0, extra=150 → usou_extra.
        # Dia 2: data_ref. Streak (a partir de data_ref) = 1 (dia 2 ainda 'dentro').
        self._saida(1, Decimal("250.00"))
        progresso = ProgressoService().obter_progresso(
            self.user, date(ANO, MES, 2)
        )
        self.assertEqual(progresso.streak, 1)
        dia_1 = progresso.calendario[0]
        self.assertTrue(dia_1.usou_extra)
        self.assertFalse(dia_1.dentro_limite)

    def test_calendario_tem_todos_os_dias_do_mes(self) -> None:
        progresso = ProgressoService().obter_progresso(
            self.user, date(ANO, MES, 5)
        )
        self.assertEqual(len(progresso.calendario), DIAS_MES)
        self.assertEqual(progresso.calendario[0].data, date(ANO, MES, 1))
        self.assertEqual(
            progresso.calendario[-1].data, date(ANO, MES, DIAS_MES)
        )

    def test_dias_futuros_sem_status(self) -> None:
        # Dias após data_ref ficam sem registro → dentro_limite=False, etc.
        progresso = ProgressoService().obter_progresso(
            self.user, date(ANO, MES, 2)
        )
        if DIAS_MES > 2:
            futuro = progresso.calendario[-1]
            self.assertFalse(futuro.dentro_limite)
            self.assertFalse(futuro.usou_reserva)
            self.assertFalse(futuro.usou_extra)

    def test_progresso_persiste_em_progresso_diario(self) -> None:
        ProgressoService().obter_progresso(self.user, date(ANO, MES, 3))
        self.assertEqual(
            ProgressoDiario.objects.filter(usuario=self.user).count(), 3
        )

    def test_progresso_idempotente(self) -> None:
        service = ProgressoService()
        service.obter_progresso(self.user, date(ANO, MES, 3))
        service.obter_progresso(self.user, date(ANO, MES, 3))
        self.assertEqual(
            ProgressoDiario.objects.filter(usuario=self.user).count(), 3
        )


class AlertaServiceTests(_ProgressoBaseTestCase):
    def test_sem_alertas_quando_dentro_do_limite(self) -> None:
        alertas = AlertaService().obter_alertas(self.user, date(ANO, MES, 1))
        self.assertEqual(alertas, ())

    def test_alerta_limite_70_dispara(self) -> None:
        self._saida(1, Decimal("75.00"))
        alertas = AlertaService().obter_alertas(self.user, date(ANO, MES, 1))
        gatilhos = {a.gatilho for a in alertas}
        self.assertIn(AlertaService.LIMITE_70, gatilhos)
        self.assertNotIn(AlertaService.LIMITE_100, gatilhos)

    def test_alerta_limite_100_substitui_70(self) -> None:
        self._saida(1, Decimal("100.00"))
        alertas = AlertaService().obter_alertas(self.user, date(ANO, MES, 1))
        gatilhos = {a.gatilho for a in alertas}
        self.assertIn(AlertaService.LIMITE_100, gatilhos)
        self.assertNotIn(AlertaService.LIMITE_70, gatilhos)

    def test_alerta_reserva_esgotada_quando_extra_existe(self) -> None:
        # Dia 1 fechado com gasto 250 → extra=150. Dia 2 = data_ref.
        self._saida(1, Decimal("250.00"))
        alertas = AlertaService().obter_alertas(self.user, date(ANO, MES, 2))
        gatilhos = {a.gatilho for a in alertas}
        self.assertIn(AlertaService.RESERVA_ESGOTADA, gatilhos)

    def test_alerta_reserva_50(self) -> None:
        # Dia 1: sobra 100 → potencial=100, reserva=100 (consumido=0).
        # Dia 2 fechado: gasto 160 → excesso 60, consumido=60, reserva=40.
        # Dia 3 = data_ref. pct_consumido = 60/100 = 0.6 → 50% trigger.
        self._saida(2, Decimal("160.00"))
        alertas = AlertaService().obter_alertas(self.user, date(ANO, MES, 3))
        gatilhos = {a.gatilho for a in alertas}
        self.assertIn(AlertaService.RESERVA_50, gatilhos)
        self.assertNotIn(AlertaService.RESERVA_80, gatilhos)

    def test_alerta_reserva_80(self) -> None:
        # Dia 1: sobra 100 → potencial=100.
        # Dia 2: gasto 185 → consumido=85, reserva=15. pct=0.85 → 80% trigger.
        self._saida(2, Decimal("185.00"))
        alertas = AlertaService().obter_alertas(self.user, date(ANO, MES, 3))
        gatilhos = {a.gatilho for a in alertas}
        self.assertIn(AlertaService.RESERVA_80, gatilhos)
        self.assertNotIn(AlertaService.RESERVA_50, gatilhos)

    def test_mensagem_corresponde_ao_gatilho(self) -> None:
        self._saida(1, Decimal("100.00"))
        alertas = AlertaService().obter_alertas(self.user, date(ANO, MES, 1))
        alerta = next(a for a in alertas if a.gatilho == AlertaService.LIMITE_100)
        self.assertEqual(alerta.mensagem, "Você atingiu o limite diário")


class ProgressoAlertasApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="api", password="Senha!2026")
        self.categoria = Categoria.objects.create(
            nome="Casa",
            descricao="Despesas",
            cor="#123456",
            usuario=self.user,
        )
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal(DIAS_MES) * Decimal("100.00"),
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)
        self.client.force_authenticate(self.user)

    def test_get_progresso_exige_auth(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/v1/progresso/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_progresso_retorna_streak_e_calendario(self) -> None:
        resp = self.client.get("/api/v1/progresso/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["ano"], ANO)
        self.assertEqual(resp.data["mes"], MES)
        self.assertEqual(len(resp.data["calendario"]), DIAS_MES)
        self.assertGreaterEqual(resp.data["streak"], 0)

    def test_get_alertas_exige_auth(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/v1/alertas/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_alertas_sem_gastos_retorna_lista_vazia(self) -> None:
        resp = self.client.get("/api/v1/alertas/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["alertas"], [])

    def test_get_alertas_dispara_limite_quando_gasto_alto(self) -> None:
        Saida.objects.create(
            nome="Mercado",
            valor=Decimal("80.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        resp = self.client.get("/api/v1/alertas/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        gatilhos = {a["gatilho"] for a in resp.data["alertas"]}
        self.assertIn(AlertaService.LIMITE_70, gatilhos)


class ProgressoIsolamentoTests(TestCase):
    def test_progresso_isolado_por_usuario(self) -> None:
        u1 = User.objects.create_user(username="i1", password="x")
        u2 = User.objects.create_user(username="i2", password="x")
        Entrada.objects.create(
            nome="A",
            valor=Decimal(DIAS_MES) * Decimal("100.00"),
            usuario=u1,
            recorrencia=True,
        )
        # u2 sem renda → limite=0, mas não interfere em u1.
        service = ProgressoService()
        p1 = service.obter_progresso(u1, date(ANO, MES, 3))
        p2 = service.obter_progresso(u2, date(ANO, MES, 3))
        self.assertEqual(p1.streak, 3)
        # u2 sem renda: dias com gasto 0 e limite 0 → dentro_limite=True.
        self.assertEqual(p2.streak, 3)
        self.assertEqual(
            ProgressoDiario.objects.filter(usuario=u1).count(), 3
        )
        self.assertEqual(
            ProgressoDiario.objects.filter(usuario=u2).count(), 3
        )
