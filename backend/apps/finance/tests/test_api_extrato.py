"""Testes de integração do endpoint de Extrato Financeiro (Issue #09)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import Categoria, Pagamento, TipoGasto, Transacao
from apps.finance.services import FinancasTransacaoService

User = get_user_model()


def _set_data(transacao: Transacao, ano: int, mes: int, dia: int = 15) -> None:
    Transacao.objects.filter(pk=transacao.pk).update(
        data=datetime(ano, mes, dia, 12, 0, tzinfo=timezone.utc)
    )


class ExtratoEndpointTests(APITestCase):
    url = "/api/v1/finance/extrato/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="Senha!2026")
        self.outro = User.objects.create_user(username="bob", password="Senha!2026")
        self.cat_mercado = Categoria.objects.create(
            nome="Mercado", descricao="Compras", cor="#112233", usuario=self.user
        )
        self.cat_lazer = Categoria.objects.create(
            nome="Lazer", descricao="Hobbies", cor="#445566", usuario=self.user
        )
        self.cat_outro = Categoria.objects.create(
            nome="Bob-cat", descricao="Bob", cor="#000000", usuario=self.outro
        )

        service = FinancasTransacaoService()
        self.entrada = service.criar_transacao(
            tipo="entrada",
            nome="Salário",
            valor=Decimal("5000.00"),
            usuario=self.user,
            fonte="Empresa",
            recorrencia=True,
        )
        self.saida_mercado = service.criar_transacao(
            tipo="saida",
            nome="Feira",
            valor=Decimal("200.00"),
            usuario=self.user,
            categoria=self.cat_mercado,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        self.saida_lazer = service.criar_transacao(
            tipo="saida",
            nome="Cinema",
            valor=Decimal("50.00"),
            usuario=self.user,
            categoria=self.cat_lazer,
            pagamento=Pagamento.CREDITO,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        self.parc = service.criar_transacao(
            tipo="parcelamento",
            nome="Notebook",
            valor=Decimal("3000.00"),
            usuario=self.user,
            categoria=self.cat_lazer,
            pagamento=Pagamento.CREDITO,
            num_parcelas=10,
        )
        self.client.force_authenticate(self.user)

    def test_exige_autenticacao(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sem_filtros_retorna_todas_do_usuario(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["transacoes"]), 4)
        self.assertEqual(Decimal(response.data["saldo_atual"]), Decimal("4450.00"))
        self.assertEqual(response.data["filtros_aplicados"], {})

    def test_resposta_inclui_tipo_e_detalhes_polimorficos(self) -> None:
        response = self.client.get(self.url, {"tipo": "saida"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tipos = {t["tipo"] for t in response.data["transacoes"]}
        self.assertEqual(tipos, {"saida"})
        for tx in response.data["transacoes"]:
            self.assertIn("categoria", tx["detalhes"])
            self.assertIn("pagamento", tx["detalhes"])
            self.assertIn("tipo_gasto", tx["detalhes"])

    def test_filtro_tipo_entrada(self) -> None:
        response = self.client.get(self.url, {"tipo": "entrada"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["transacoes"]), 1)
        self.assertEqual(response.data["transacoes"][0]["tipo"], "entrada")
        self.assertEqual(Decimal(response.data["saldo_atual"]), Decimal("5000.00"))

    def test_filtro_tipo_invalido_retorna_400(self) -> None:
        response = self.client.get(self.url, {"tipo": "boleto"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_ano_mes(self) -> None:
        _set_data(self.entrada, 2026, 4)
        _set_data(self.saida_mercado, 2026, 5)
        _set_data(self.saida_lazer, 2026, 5)
        _set_data(self.parc, 2026, 6)
        response = self.client.get(self.url, {"ano": "2026", "mes": "5"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["transacoes"]), 2)
        self.assertEqual(
            response.data["filtros_aplicados"]["ano_mes"], {"ano": 2026, "mes": 5}
        )

    def test_filtro_ano_sem_mes_retorna_400(self) -> None:
        response = self.client.get(self.url, {"ano": "2026"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_ano_mes_nao_inteiro_retorna_400(self) -> None:
        response = self.client.get(self.url, {"ano": "abc", "mes": "5"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_mes_fora_de_intervalo_retorna_400(self) -> None:
        response = self.client.get(self.url, {"ano": "2026", "mes": "13"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_categoria(self) -> None:
        response = self.client.get(self.url, {"categoria": str(self.cat_lazer.pk)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {t["id"] for t in response.data["transacoes"]}
        self.assertEqual(ids, {str(self.saida_lazer.pk), str(self.parc.pk)})

    def test_filtro_categoria_de_outro_usuario_retorna_400(self) -> None:
        response = self.client.get(self.url, {"categoria": str(self.cat_outro.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_categoria_inexistente_retorna_400(self) -> None:
        response = self.client.get(
            self.url, {"categoria": "00000000-0000-0000-0000-000000000000"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_pagamento(self) -> None:
        response = self.client.get(self.url, {"pagamento": "pix"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["transacoes"]), 1)
        self.assertEqual(
            response.data["transacoes"][0]["id"], str(self.saida_mercado.pk)
        )

    def test_filtro_tipo_gasto_so_inclui_saidas(self) -> None:
        response = self.client.get(self.url, {"tipo_gasto": "variavel"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {t["id"] for t in response.data["transacoes"]}
        self.assertEqual(ids, {str(self.saida_mercado.pk), str(self.saida_lazer.pk)})

    def test_pesquisa_nome_case_insensitive_e_parcial(self) -> None:
        response = self.client.get(self.url, {"nome": "NOTEB"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["transacoes"]), 1)
        self.assertEqual(response.data["transacoes"][0]["id"], str(self.parc.pk))

    def test_combinacao_de_filtros(self) -> None:
        response = self.client.get(
            self.url,
            {
                "tipo": "saida",
                "categoria": str(self.cat_lazer.pk),
                "pagamento": "credito",
                "tipo_gasto": "variavel",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["transacoes"]), 1)
        self.assertEqual(
            response.data["transacoes"][0]["id"], str(self.saida_lazer.pk)
        )
        self.assertEqual(
            set(response.data["filtros_aplicados"].keys()),
            {"tipo", "categoria", "pagamento", "tipo_gasto"},
        )

    def test_escopo_isolado_por_usuario(self) -> None:
        self.client.force_authenticate(self.outro)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["transacoes"], [])
        self.assertEqual(Decimal(response.data["saldo_atual"]), Decimal("0.00"))
