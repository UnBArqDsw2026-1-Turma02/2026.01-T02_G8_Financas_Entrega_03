"""Testes unitários e de integração da Simulação de Gasto (Issue #10)."""

from __future__ import annotations

import calendar
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
    Pagamento,
    Parcelamento,
    Saida,
    TipoGasto,
)
from apps.finance.services import SimulacaoGastoService

User = get_user_model()


def _dias_mes_atual() -> int:
    hoje = timezone.now()
    return calendar.monthrange(hoje.year, hoje.month)[1]


class SimulacaoGastoServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="hugo", password="x")
        self.categoria = Categoria.objects.create(
            nome="Lazer",
            descricao="Saidas",
            cor="#abcdef",
            usuario=self.user,
        )
        self.service = SimulacaoGastoService()

        Entrada.objects.create(
            nome="Salário",
            valor=Decimal("3000.00"),
            usuario=self.user,
            recorrencia=True,
        )
        Saida.objects.create(
            nome="Aluguel",
            valor=Decimal("1000.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.FIXO,
        )

    def test_simulacao_a_vista_calcula_novo_orcamento(self) -> None:
        resultado = self.service.simular(
            usuario=self.user, valor=Decimal("500.00")
        )
        self.assertEqual(resultado["orcamento_mensal_atual"], Decimal("2000.00"))
        self.assertEqual(resultado["novo_orcamento"], Decimal("1500.00"))
        esperado_limite = (Decimal("1500.00") / Decimal(_dias_mes_atual())).quantize(
            Decimal("0.01")
        )
        self.assertEqual(resultado["novo_limite_diario"], esperado_limite)
        self.assertTrue(resultado["dentro_orcamento"])
        self.assertNotIn("simulacao_parcelamento", resultado)

    def test_simulacao_impacta_mais_de_30_porcento(self) -> None:
        resultado = self.service.simular(
            usuario=self.user, valor=Decimal("800.00")
        )
        # 800 / 2000 = 40% > 30%
        self.assertTrue(resultado["impacta_30_porcento"])

    def test_simulacao_nao_impacta_mais_de_30_porcento(self) -> None:
        resultado = self.service.simular(
            usuario=self.user, valor=Decimal("300.00")
        )
        # 300 / 2000 = 15% <= 30%
        self.assertFalse(resultado["impacta_30_porcento"])

    def test_simulacao_extrapola_orcamento(self) -> None:
        resultado = self.service.simular(
            usuario=self.user, valor=Decimal("2500.00")
        )
        self.assertFalse(resultado["dentro_orcamento"])
        self.assertEqual(resultado["novo_orcamento"], Decimal("-500.00"))

    def test_simulacao_parcelada_usa_valor_parcela(self) -> None:
        resultado = self.service.simular(
            usuario=self.user,
            valor=Decimal("1200.00"),
            parcelado=True,
            num_parcelas=4,
        )
        self.assertIn("simulacao_parcelamento", resultado)
        self.assertEqual(
            resultado["simulacao_parcelamento"]["valor_parcela"],
            Decimal("300.00"),
        )
        self.assertEqual(
            resultado["simulacao_parcelamento"]["impacto_mensal"],
            Decimal("300.00"),
        )
        # impacto mensal = 300; novo orcamento = 2000 - 300 = 1700
        self.assertEqual(resultado["novo_orcamento"], Decimal("1700.00"))
        # 300 / 2000 = 15% — não estoura 30%
        self.assertFalse(resultado["impacta_30_porcento"])

    def test_simulacao_inclui_parcelamentos_existentes_em_gastos_fixos(self) -> None:
        Parcelamento.objects.create(
            nome="TV",
            valor=Decimal("1200.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.CREDITO,
            num_parcelas=4,
            valor_parcela=Decimal("300.00"),
        )
        resultado = self.service.simular(
            usuario=self.user, valor=Decimal("100.00")
        )
        # renda 3000 - aluguel 1000 - parcela 300 = 1700
        self.assertEqual(resultado["orcamento_mensal_atual"], Decimal("1700.00"))
        self.assertEqual(resultado["novo_orcamento"], Decimal("1600.00"))
        esperado_limite_atual = (
            Decimal("1700.00") / Decimal(_dias_mes_atual())
        ).quantize(Decimal("0.01"))
        self.assertEqual(
            resultado["limite_diario_atual"], esperado_limite_atual
        )

    def test_simulacao_ignora_saida_variavel_em_gastos_fixos(self) -> None:
        Saida.objects.create(
            nome="Cinema",
            valor=Decimal("100.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        resultado = self.service.simular(
            usuario=self.user, valor=Decimal("100.00")
        )
        self.assertEqual(resultado["orcamento_mensal_atual"], Decimal("2000.00"))

    def test_simulacao_isolada_por_usuario(self) -> None:
        outro = User.objects.create_user(username="other", password="x")
        Entrada.objects.create(
            nome="Outro salário",
            valor=Decimal("9999.00"),
            usuario=outro,
            recorrencia=False,
        )
        resultado = self.service.simular(
            usuario=self.user, valor=Decimal("100.00")
        )
        self.assertEqual(resultado["orcamento_mensal_atual"], Decimal("2000.00"))

    def test_simulacao_valor_zero_falha(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.simular(usuario=self.user, valor=Decimal("0"))

    def test_simulacao_valor_negativo_falha(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.simular(usuario=self.user, valor=Decimal("-10"))


class SimulacaoGastoApiTests(APITestCase):
    url = "/api/v1/finance/simular-gasto/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="ivy", password="Senha!2026")
        self.categoria = Categoria.objects.create(
            nome="Casa",
            descricao="Despesas",
            cor="#123456",
            usuario=self.user,
        )
        Entrada.objects.create(
            nome="Salário",
            valor=Decimal("4000.00"),
            usuario=self.user,
            recorrencia=True,
        )
        Saida.objects.create(
            nome="Aluguel",
            valor=Decimal("1000.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.FIXO,
        )
        self.client.force_authenticate(self.user)

    def test_exige_autenticacao(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.url, {"valor": "100.00"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_a_vista_retorna_simulacao(self) -> None:
        response = self.client.post(
            self.url, {"valor": "500.00"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Decimal(response.data["orcamento_mensal_atual"]),
            Decimal("3000.00"),
        )
        self.assertEqual(
            Decimal(response.data["novo_orcamento"]), Decimal("2500.00")
        )
        self.assertFalse(response.data["impacta_30_porcento"])
        self.assertTrue(response.data["dentro_orcamento"])
        self.assertNotIn("simulacao_parcelamento", response.data)

    def test_post_parcelado_inclui_simulacao_parcelamento(self) -> None:
        response = self.client.post(
            self.url,
            {"valor": "1200.00", "parcelado": True, "num_parcelas": 4},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("simulacao_parcelamento", response.data)
        self.assertEqual(
            Decimal(response.data["simulacao_parcelamento"]["valor_parcela"]),
            Decimal("300.00"),
        )
        self.assertEqual(
            Decimal(response.data["simulacao_parcelamento"]["impacto_mensal"]),
            Decimal("300.00"),
        )

    def test_post_valor_invalido_retorna_400(self) -> None:
        response = self.client.post(
            self.url, {"valor": "0"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor", response.data)

    def test_post_valor_ausente_retorna_400(self) -> None:
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor", response.data)
