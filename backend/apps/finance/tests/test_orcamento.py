"""Testes unitários e de API para Limite Diário, Reserva e Extra (Issue #11)."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import (
    Categoria,
    Entrada,
    Extra,
    LimiteDiario,
    Pagamento,
    Reserva,
    Saida,
    TipoGasto,
    Transacao,
)
from apps.finance.services import OrcamentoService

User = get_user_model()

HOJE = timezone.localdate()
ANO, MES = HOJE.year, HOJE.month
DIAS_MES = calendar.monthrange(ANO, MES)[1]


def _aware(dia: int, hora: int = 12) -> datetime:
    return timezone.make_aware(datetime(ANO, MES, dia, hora, 0))


def _redatar(transacao: Transacao, dia: int) -> None:
    """Força a data da transação (auto_now_add) para um dia específico do mês corrente."""
    Transacao.objects.filter(pk=transacao.pk).update(data=_aware(dia))


class OrcamentoServiceLimiteDiarioTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="orc1", password="x")
        self.categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Supermercado",
            cor="#abcdef",
            usuario=self.user,
        )
        # Renda mensal = 3100 → limite_base = 3100 / DIAS_MES por dia.
        # Para o mês de teste, fixamos um valor exato ao usar 3100 com 31 dias = 100.
        # Para outros meses, ajustamos o esperado dinamicamente.
        self.renda = Decimal("3100.00")
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=self.renda,
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)
        self.service = OrcamentoService()

    @property
    def limite_base(self) -> Decimal:
        return (self.renda / Decimal(DIAS_MES)).quantize(Decimal("0.01"))

    def test_limite_calculado_a_partir_da_renda(self) -> None:
        limite = self.service.obter_limite_diario(self.user, date(ANO, MES, 1))
        self.assertEqual(limite.limite_calculado, self.limite_base)
        self.assertEqual(limite.gasto_dia, Decimal("0.00"))

    def test_limite_zero_quando_sem_renda(self) -> None:
        outro = User.objects.create_user(username="zero", password="x")
        limite = self.service.obter_limite_diario(outro, date(ANO, MES, 1))
        self.assertEqual(limite.limite_calculado, Decimal("0.00"))

    def test_gastos_fixos_reduzem_limite(self) -> None:
        saida = Saida.objects.create(
            nome="Aluguel",
            valor=Decimal("1000.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.FIXO,
        )
        _redatar(saida, 1)
        limite = self.service.obter_limite_diario(self.user, date(ANO, MES, 1))
        esperado = ((self.renda - Decimal("1000")) / Decimal(DIAS_MES)).quantize(
            Decimal("0.01")
        )
        self.assertEqual(limite.limite_calculado, esperado)


class OrcamentoServiceReservaTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="orc2", password="x")
        self.categoria = Categoria.objects.create(
            nome="Lazer",
            descricao="Saidas",
            cor="#112233",
            usuario=self.user,
        )
        # Usamos renda = DIAS_MES * 100 para que limite_base seja exatamente 100.
        self.renda = Decimal(DIAS_MES) * Decimal("100.00")
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=self.renda,
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)
        self.service = OrcamentoService()

    def _criar_saida_variavel(self, dia: int, valor: Decimal) -> Saida:
        saida = Saida.objects.create(
            nome=f"Compra dia {dia}",
            valor=valor,
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(saida, dia)
        return saida

    def test_sobra_diaria_acumula_na_reserva(self) -> None:
        # Dia 1: gasto 60 → sobra 40 (fechado);
        # Dia 2: gasto 30 → sobra 70 (fechado); reserva = 110.
        # Dia 3 = data_ref (corrente): nada é creditado em reserva.
        self._criar_saida_variavel(1, Decimal("60.00"))
        self._criar_saida_variavel(2, Decimal("30.00"))

        self.service.obter_limite_diario(self.user, date(ANO, MES, 3))
        reserva = Reserva.objects.get(usuario=self.user)
        self.assertEqual(reserva.saldo, Decimal("110.00"))

    def test_excesso_no_dia_debita_reserva(self) -> None:
        # Dia 1: gasto 30 → sobra 70 (fechado);
        # Dia 2: gasto 150 → excesso 50 (fechado). Reserva = 70 - 50 = 20.
        self._criar_saida_variavel(1, Decimal("30.00"))
        self._criar_saida_variavel(2, Decimal("150.00"))

        self.service.obter_limite_diario(self.user, date(ANO, MES, 3))
        reserva = Reserva.objects.get(usuario=self.user)
        self.assertEqual(reserva.saldo, Decimal("20.00"))
        self.assertFalse(Extra.objects.filter(usuario=self.user).exists())

    def test_gasto_dia_aparece_no_limite(self) -> None:
        self._criar_saida_variavel(1, Decimal("42.00"))
        limite = self.service.obter_limite_diario(self.user, date(ANO, MES, 1))
        self.assertEqual(limite.gasto_dia, Decimal("42.00"))

    def test_sobra_do_dia_corrente_nao_credita_reserva(self) -> None:
        # Apenas dias fechados contribuem para a reserva.
        self._criar_saida_variavel(1, Decimal("0.01"))  # noop no setup
        self.service.obter_limite_diario(self.user, date(ANO, MES, 1))
        reserva = Reserva.objects.get(usuario=self.user)
        self.assertEqual(reserva.saldo, Decimal("0.00"))


class OrcamentoServiceExtraTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="orc3", password="x")
        self.categoria = Categoria.objects.create(
            nome="Lazer",
            descricao="Saidas",
            cor="#112233",
            usuario=self.user,
        )
        self.renda = Decimal(DIAS_MES) * Decimal("100.00")
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=self.renda,
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)
        self.service = OrcamentoService()

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

    def test_extra_ativa_quando_reserva_zera(self) -> None:
        # Dia 1 (fechado): gasto 250 → excesso 150, reserva=0, extra=150.
        # Dia 2 = data_ref.
        self._saida(1, Decimal("250.00"))
        self.service.obter_limite_diario(self.user, date(ANO, MES, 2))

        reserva = Reserva.objects.get(usuario=self.user)
        self.assertEqual(reserva.saldo, Decimal("0.00"))

        extra_total = self.service.obter_extra_mes(self.user, ANO, MES)
        self.assertEqual(extra_total, Decimal("150.00"))

    def test_limite_recalculado_descontando_extra_nos_dias_seguintes(self) -> None:
        # Dia 1 (fechado): gasto 300 → excesso 200, extra=200.
        # Dia 2 = data_ref → limite_aplicavel = (renda - 200) / dias_mes.
        self._saida(1, Decimal("300.00"))
        limite_dia_2 = self.service.obter_limite_diario(self.user, date(ANO, MES, 2))
        esperado = ((self.renda - Decimal("200.00")) / Decimal(DIAS_MES)).quantize(
            Decimal("0.01")
        )
        self.assertEqual(limite_dia_2.limite_calculado, esperado)

    def test_extra_so_ativa_quando_reserva_insuficiente(self) -> None:
        # Dia 1,2 (fechados sem gasto): sobra 100 cada → reserva = 200.
        # Dia 3 (fechado): gasto 350 → excesso 250. Reserva 200 cobre, extra=50.
        # Dia 4 = data_ref.
        self._saida(3, Decimal("350.00"))
        self.service.obter_limite_diario(self.user, date(ANO, MES, 4))
        reserva = Reserva.objects.get(usuario=self.user)
        self.assertEqual(reserva.saldo, Decimal("0.00"))
        self.assertEqual(
            self.service.obter_extra_mes(self.user, ANO, MES), Decimal("50.00")
        )

    def test_recalculo_idempotente(self) -> None:
        self._saida(1, Decimal("250.00"))
        self.service.obter_limite_diario(self.user, date(ANO, MES, 2))
        self.service.obter_limite_diario(self.user, date(ANO, MES, 2))
        # Sem duplicar Extra do dia.
        self.assertEqual(Extra.objects.filter(usuario=self.user).count(), 1)
        self.assertEqual(
            self.service.obter_extra_mes(self.user, ANO, MES), Decimal("150.00")
        )


class OrcamentoServiceAjusteTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="orc4", password="x")
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal(DIAS_MES) * Decimal("100.00"),
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)
        self.service = OrcamentoService()

    def test_ajustar_limite_para_menor_aceito(self) -> None:
        limite = self.service.ajustar_limite(
            self.user, Decimal("80.00"), date(ANO, MES, 1)
        )
        self.assertEqual(limite.limite_ajustado, Decimal("80.00"))
        self.assertEqual(limite.limite_efetivo, Decimal("80.00"))

    def test_ajustar_limite_maior_que_calculado_rejeitado(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.ajustar_limite(
                self.user, Decimal("999.00"), date(ANO, MES, 1)
            )

    def test_ajustar_limite_negativo_rejeitado(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.ajustar_limite(
                self.user, Decimal("-1.00"), date(ANO, MES, 1)
            )


class OrcamentoServiceIsolamentoTests(TestCase):
    def test_orcamento_isolado_por_usuario(self) -> None:
        u1 = User.objects.create_user(username="iso1", password="x")
        u2 = User.objects.create_user(username="iso2", password="x")
        Entrada.objects.create(
            nome="A", valor=Decimal("3100"), usuario=u1, recorrencia=True
        )
        Entrada.objects.create(
            nome="B", valor=Decimal("100"), usuario=u2, recorrencia=True
        )
        service = OrcamentoService()
        limite_u1 = service.obter_limite_diario(u1, date(ANO, MES, 1))
        limite_u2 = service.obter_limite_diario(u2, date(ANO, MES, 1))
        self.assertGreater(limite_u1.limite_calculado, limite_u2.limite_calculado)


class OrcamentoApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="api1", password="Senha!2026")
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

    def test_get_limite_diario_exige_auth(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/v1/finance/limite-diario/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_limite_diario_ok(self) -> None:
        resp = self.client.get("/api/v1/finance/limite-diario/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data["limite_calculado"]), Decimal("100.00"))
        self.assertIsNone(resp.data["limite_ajustado"])
        self.assertEqual(Decimal(resp.data["gasto_dia"]), Decimal("0.00"))
        self.assertEqual(Decimal(resp.data["sobra_dia"]), Decimal("100.00"))

    def test_put_ajustar_limite_ok(self) -> None:
        resp = self.client.put(
            "/api/v1/finance/limite-diario/ajustar/",
            {"limite_ajustado": "70.00"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data["limite_ajustado"]), Decimal("70.00"))
        self.assertEqual(Decimal(resp.data["limite_efetivo"]), Decimal("70.00"))

    def test_put_ajustar_limite_maior_que_calculado_400(self) -> None:
        resp = self.client.put(
            "/api/v1/finance/limite-diario/ajustar/",
            {"limite_ajustado": "9999.00"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_reserva_retorna_saldo_nao_negativo(self) -> None:
        # Sem saídas no mês, a reserva acumula sobras dos dias fechados.
        # Aceitamos qualquer saldo não-negativo (depende do dia do mês).
        resp = self.client.get("/api/v1/finance/reserva/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(Decimal(resp.data["saldo"]), Decimal("0.00"))

    def test_get_extra_inicial_zerado(self) -> None:
        resp = self.client.get("/api/v1/finance/extra/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data["valor"]), Decimal("0.00"))

    def test_fluxo_completo_via_api(self) -> None:
        # Criar saída variável hoje com valor que excede o limite (100).
        # Dia "hoje" — não controlamos o dia real, mas a saída cai em HOJE.
        Saida.objects.create(
            nome="Excesso",
            valor=Decimal("250.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        resp = self.client.get("/api/v1/finance/limite-diario/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data["gasto_dia"]), Decimal("250.00"))

        # Reserva pode estar zerada ou positiva dependendo do dia do mês;
        # mas o saldo nunca pode ser negativo.
        resp_reserva = self.client.get("/api/v1/finance/reserva/")
        self.assertEqual(resp_reserva.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(Decimal(resp_reserva.data["saldo"]), Decimal("0.00"))


class LimiteDiarioModelTests(TestCase):
    def test_limite_efetivo_usa_ajustado_quando_definido(self) -> None:
        user = User.objects.create_user(username="mod1", password="x")
        limite = LimiteDiario.objects.create(
            usuario=user,
            data=HOJE,
            limite_calculado=Decimal("100.00"),
            limite_ajustado=Decimal("50.00"),
        )
        self.assertEqual(limite.limite_efetivo, Decimal("50.00"))

    def test_limite_efetivo_cai_para_calculado_sem_ajuste(self) -> None:
        user = User.objects.create_user(username="mod2", password="x")
        limite = LimiteDiario.objects.create(
            usuario=user,
            data=HOJE,
            limite_calculado=Decimal("100.00"),
        )
        self.assertEqual(limite.limite_efetivo, Decimal("100.00"))
