"""Testes do Dashboard (Issue #14) — service e endpoints REST."""

from __future__ import annotations

import calendar
from datetime import datetime
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
    Parcelamento,
    Saida,
    TipoGasto,
    Transacao,
)
from apps.finance.services import DashboardService

User = get_user_model()

HOJE = timezone.localdate()
ANO, MES = HOJE.year, HOJE.month
DIAS_MES = calendar.monthrange(ANO, MES)[1]


def _aware(dia: int, hora: int = 12) -> datetime:
    return timezone.make_aware(datetime(ANO, MES, dia, hora, 0))


def _redatar(transacao: Transacao, dia: int) -> None:
    Transacao.objects.filter(pk=transacao.pk).update(data=_aware(dia))


class DashboardServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="dash", password="x")
        self.outro = User.objects.create_user(username="outro", password="x")

        self.cat_alimentacao = Categoria.objects.create(
            nome="Alimentação",
            descricao="Compras de mercado",
            cor="#FF6B6B",
            usuario=self.user,
        )
        self.cat_transporte = Categoria.objects.create(
            nome="Transporte",
            descricao="Combustível e apps",
            cor="#4ECDC4",
            usuario=self.user,
        )

        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal("5000.00"),
            usuario=self.user,
            recorrencia=True,
        )
        _redatar(entrada, 1)

        aluguel = Saida.objects.create(
            nome="Aluguel",
            valor=Decimal("2000.00"),
            usuario=self.user,
            categoria=self.cat_alimentacao,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.FIXO,
        )
        _redatar(aluguel, 1)

        mercado = Saida.objects.create(
            nome="Mercado",
            valor=Decimal("450.00"),
            usuario=self.user,
            categoria=self.cat_alimentacao,
            pagamento=Pagamento.DEBITO,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(mercado, 5)

        uber = Saida.objects.create(
            nome="Uber",
            valor=Decimal("200.00"),
            usuario=self.user,
            categoria=self.cat_transporte,
            pagamento=Pagamento.CREDITO,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(uber, 5)

        gasolina = Saida.objects.create(
            nome="Gasolina",
            valor=Decimal("150.00"),
            usuario=self.user,
            categoria=self.cat_transporte,
            pagamento=Pagamento.CREDITO,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(gasolina, 10)

        # Transação de outro usuário não deve aparecer nos resultados.
        cat_outro = Categoria.objects.create(
            nome="Outros",
            descricao="Outros gastos",
            cor="#000000",
            usuario=self.outro,
        )
        saida_outro = Saida.objects.create(
            nome="Não deve contar",
            valor=Decimal("999.00"),
            usuario=self.outro,
            categoria=cat_outro,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(saida_outro, 5)

        self.service = DashboardService()

    def test_visao_geral_totaliza_entradas_e_saidas(self) -> None:
        visao = self.service.obter_visao_geral(self.user, ANO, MES)
        self.assertEqual(visao.total_entradas, Decimal("5000.00"))
        self.assertEqual(visao.total_saidas_fixas, Decimal("2000.00"))
        self.assertEqual(visao.total_saidas_variaveis, Decimal("800.00"))
        self.assertEqual(visao.saldo_disponivel, Decimal("2200.00"))

    def test_visao_geral_isolada_por_usuario(self) -> None:
        visao = self.service.obter_visao_geral(self.outro, ANO, MES)
        self.assertEqual(visao.total_entradas, Decimal("0.00"))
        self.assertEqual(visao.total_saidas_fixas, Decimal("0.00"))
        self.assertEqual(visao.total_saidas_variaveis, Decimal("999.00"))

    def test_categorias_com_percentual(self) -> None:
        categorias = self.service.obter_gastos_por_categoria(self.user, ANO, MES)
        por_nome = {c.nome: c for c in categorias}

        # Alimentação: 2000 (fixa) + 450 (variável) = 2450
        # Transporte: 200 + 150 = 350
        # Total: 2800 → Alimentação 87.5%, Transporte 12.5%
        self.assertEqual(por_nome["Alimentação"].total, Decimal("2450.00"))
        self.assertEqual(por_nome["Alimentação"].percentual, Decimal("87.50"))
        self.assertEqual(por_nome["Transporte"].total, Decimal("350.00"))
        self.assertEqual(por_nome["Transporte"].percentual, Decimal("12.50"))
        # Ordenado decrescente por total.
        self.assertEqual(categorias[0].nome, "Alimentação")

    def test_categorias_incluem_parcelamentos_pelo_valor_da_parcela(self) -> None:
        Parcelamento.objects.create(
            nome="Notebook",
            valor=Decimal("1200.00"),
            usuario=self.user,
            categoria=self.cat_transporte,
            pagamento=Pagamento.CREDITO,
            num_parcelas=12,
            valor_parcela=Decimal("100.00"),
        )
        categorias = self.service.obter_gastos_por_categoria(self.user, ANO, MES)
        por_nome = {c.nome: c for c in categorias}

        # Transporte: 200 + 150 (saídas) + 100 (parcela do mês) = 450
        # Alimentação: 2450; total = 2900 → Transporte 15.52%, Alimentação 84.48%
        self.assertEqual(por_nome["Transporte"].total, Decimal("450.00"))
        self.assertEqual(por_nome["Alimentação"].total, Decimal("2450.00"))
        self.assertEqual(por_nome["Transporte"].percentual, Decimal("15.52"))
        self.assertEqual(por_nome["Alimentação"].percentual, Decimal("84.48"))

    def test_categorias_vazias_quando_sem_saidas(self) -> None:
        novo = User.objects.create_user(username="vazio", password="x")
        categorias = self.service.obter_gastos_por_categoria(novo, ANO, MES)
        self.assertEqual(categorias, [])

    def test_tendencia_tem_um_ponto_por_dia(self) -> None:
        serie = self.service.obter_tendencia_diaria(self.user, ANO, MES)
        self.assertEqual(len(serie), DIAS_MES)
        por_dia = {dia.data.day: dia.total_gasto for dia in serie}
        # Dia 1: aluguel 2000 (fixa) — soma de todas as saídas do dia.
        self.assertEqual(por_dia[1], Decimal("2000.00"))
        # Dia 5: mercado 450 + uber 200 = 650
        self.assertEqual(por_dia[5], Decimal("650.00"))
        # Dia 10: gasolina 150
        self.assertEqual(por_dia[10], Decimal("150.00"))
        # Dia 2: sem saídas — total zero.
        self.assertEqual(por_dia[2], Decimal("0.00"))

    def test_default_usa_mes_atual(self) -> None:
        visao = self.service.obter_visao_geral(self.user)
        self.assertEqual(visao.total_entradas, Decimal("5000.00"))


class DashboardApiTests(APITestCase):
    base_url = "/api/v1/dashboard/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="api", password="Senha!2026")
        self.categoria = Categoria.objects.create(
            nome="Lazer",
            descricao="Diversão",
            cor="#123456",
            usuario=self.user,
        )
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal("3000.00"),
            usuario=self.user,
        )
        _redatar(entrada, 1)
        saida = Saida.objects.create(
            nome="Cinema",
            valor=Decimal("60.00"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        _redatar(saida, 3)
        self.client.force_authenticate(self.user)

    def test_visao_geral_exige_autenticacao(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_visao_geral_retorna_totais(self) -> None:
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_entradas"], "3000.00")
        self.assertEqual(response.data["total_saidas_variaveis"], "60.00")
        self.assertEqual(response.data["saldo_disponivel"], "2940.00")

    def test_categorias_retorna_lista(self) -> None:
        response = self.client.get(self.base_url + "categorias/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        categorias = response.data["categorias"]
        self.assertEqual(len(categorias), 1)
        self.assertEqual(categorias[0]["nome"], "Lazer")
        self.assertEqual(categorias[0]["cor"], "#123456")
        self.assertEqual(categorias[0]["total"], "60.00")
        self.assertEqual(categorias[0]["percentual"], "100.00")

    def test_tendencia_retorna_serie_mensal(self) -> None:
        response = self.client.get(self.base_url + "tendencia/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dias = response.data["dias"]
        self.assertEqual(len(dias), DIAS_MES)
        por_dia = {item["data"]: item["total_gasto"] for item in dias}
        self.assertEqual(por_dia[f"{ANO:04d}-{MES:02d}-03"], "60.00")

    def test_filtro_ano_mes_exige_ambos(self) -> None:
        response = self.client.get(self.base_url + f"?ano={ANO}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_mes_invalido(self) -> None:
        response = self.client.get(self.base_url + f"?ano={ANO}&mes=13")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_ano_mes_aplica(self) -> None:
        # Mês anterior não tem dados.
        mes_anterior = MES - 1 if MES > 1 else 12
        ano_ref = ANO if MES > 1 else ANO - 1
        response = self.client.get(
            self.base_url + f"?ano={ano_ref}&mes={mes_anterior}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_entradas"], "0.00")
        self.assertEqual(response.data["total_saidas_variaveis"], "0.00")
