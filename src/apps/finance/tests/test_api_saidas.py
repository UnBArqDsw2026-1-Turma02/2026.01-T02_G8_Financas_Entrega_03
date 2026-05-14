"""Testes de integração do CRUD de Saídas (Issue #06)."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import Categoria, Pagamento, Saida, TipoGasto

User = get_user_model()


class SaidaCRUDApiTests(APITestCase):
    url = "/api/v1/finance/saidas/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="Senha!2026")
        self.other = User.objects.create_user(username="bob", password="Senha!2026")
        self.categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras do mês",
            cor="#112233",
            usuario=self.user,
        )
        self.categoria_outro = Categoria.objects.create(
            nome="Lazer",
            descricao="Entretenimento",
            cor="#445566",
            usuario=self.other,
        )
        self.client.force_authenticate(self.user)

    def _payload(self, **overrides):
        data = {
            "nome": "Feira",
            "valor": "120.50",
            "categoria": str(self.categoria.pk),
            "pagamento": Pagamento.PIX,
            "tipo_gasto": TipoGasto.VARIAVEL,
        }
        data.update(overrides)
        return data

    def test_exige_autenticacao(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cria_saida_com_dados_validos(self) -> None:
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome"], "Feira")
        self.assertIn("data", response.data)
        saida = Saida.objects.get(pk=response.data["id"])
        self.assertEqual(saida.usuario, self.user)
        self.assertEqual(saida.valor, Decimal("120.50"))
        self.assertEqual(saida.categoria, self.categoria)

    def test_cria_saida_valor_zero_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(valor="0"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor", response.data)

    def test_cria_saida_valor_negativo_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(valor="-10.00"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor", response.data)

    def test_cria_saida_nome_vazio_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(nome=""), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nome", response.data)

    def test_cria_saida_sem_categoria_rejeitado(self) -> None:
        payload = self._payload()
        payload.pop("categoria")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("categoria", response.data)

    def test_cria_saida_sem_pagamento_rejeitado(self) -> None:
        payload = self._payload()
        payload.pop("pagamento")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pagamento", response.data)

    def test_cria_saida_sem_tipo_gasto_rejeitado(self) -> None:
        payload = self._payload()
        payload.pop("tipo_gasto")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tipo_gasto", response.data)

    def test_categoria_de_outro_usuario_rejeitada(self) -> None:
        response = self.client.post(
            self.url,
            self._payload(categoria=str(self.categoria_outro.pk)),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("categoria", response.data)

    def test_lista_saidas_ordenadas_por_data_desc(self) -> None:
        antiga = Saida.objects.create(
            nome="Antiga",
            valor=Decimal("100"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        nova = Saida.objects.create(
            nome="Nova",
            valor=Decimal("200"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data]
        self.assertEqual(ids, [str(nova.pk), str(antiga.pk)])

    def test_lista_filtra_por_usuario_autenticado(self) -> None:
        Saida.objects.create(
            nome="Minha",
            valor=Decimal("100"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        Saida.objects.create(
            nome="Outra",
            valor=Decimal("100"),
            usuario=self.other,
            categoria=self.categoria_outro,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nome"], "Minha")

    def test_detalha_saida(self) -> None:
        saida = Saida.objects.create(
            nome="Feira",
            valor=Decimal("80"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.DEBITO,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.get(f"{self.url}{saida.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], "Feira")

    def test_detalha_saida_de_outro_usuario_retorna_404(self) -> None:
        saida = Saida.objects.create(
            nome="Outra",
            valor=Decimal("80"),
            usuario=self.other,
            categoria=self.categoria_outro,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.get(f"{self.url}{saida.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edita_saida(self) -> None:
        saida = Saida.objects.create(
            nome="Feira",
            valor=Decimal("80"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.put(
            f"{self.url}{saida.pk}/",
            self._payload(nome="Mercado", valor="150.00", pagamento=Pagamento.DEBITO),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        saida.refresh_from_db()
        self.assertEqual(saida.nome, "Mercado")
        self.assertEqual(saida.valor, Decimal("150.00"))
        self.assertEqual(saida.pagamento, Pagamento.DEBITO)

    def test_edita_saida_valor_invalido_rejeitado(self) -> None:
        saida = Saida.objects.create(
            nome="Feira",
            valor=Decimal("80"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.put(
            f"{self.url}{saida.pk}/",
            self._payload(valor="0"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exclui_saida(self) -> None:
        saida = Saida.objects.create(
            nome="Feira",
            valor=Decimal("80"),
            usuario=self.user,
            categoria=self.categoria,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.delete(f"{self.url}{saida.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Saida.objects.filter(pk=saida.pk).exists())

    def test_exclui_saida_de_outro_usuario_retorna_404(self) -> None:
        saida = Saida.objects.create(
            nome="Outra",
            valor=Decimal("80"),
            usuario=self.other,
            categoria=self.categoria_outro,
            pagamento=Pagamento.PIX,
            tipo_gasto=TipoGasto.VARIAVEL,
        )
        response = self.client.delete(f"{self.url}{saida.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
