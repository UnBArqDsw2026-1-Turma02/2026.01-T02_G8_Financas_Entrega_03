"""Testes de integração do CRUD de Entradas (Issue #05)."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import Entrada

User = get_user_model()


class EntradaCRUDApiTests(APITestCase):
    url = "/api/v1/finance/entradas/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="Senha!2026")
        self.other = User.objects.create_user(username="bob", password="Senha!2026")
        self.client.force_authenticate(self.user)

    def _payload(self, **overrides):
        data = {
            "nome": "Salário",
            "valor": "5000.00",
            "fonte": "Empresa X",
            "recorrencia": True,
        }
        data.update(overrides)
        return data

    def test_exige_autenticacao(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cria_entrada_com_dados_validos(self) -> None:
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome"], "Salário")
        self.assertIn("data", response.data)
        entrada = Entrada.objects.get(pk=response.data["id"])
        self.assertEqual(entrada.usuario, self.user)
        self.assertEqual(entrada.valor, Decimal("5000.00"))

    def test_cria_entrada_valor_zero_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(valor="0"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor", response.data)

    def test_cria_entrada_valor_negativo_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(valor="-10.00"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor", response.data)

    def test_cria_entrada_nome_vazio_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(nome=""), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nome", response.data)

    def test_cria_entrada_sem_recorrencia_rejeitado(self) -> None:
        payload = self._payload()
        payload.pop("recorrencia")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("recorrencia", response.data)

    def test_lista_entradas_ordenadas_por_data_desc(self) -> None:
        antiga = Entrada.objects.create(
            nome="Antiga",
            valor=Decimal("100"),
            usuario=self.user,
            recorrencia=False,
        )
        nova = Entrada.objects.create(
            nome="Nova",
            valor=Decimal("200"),
            usuario=self.user,
            recorrencia=False,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data]
        self.assertEqual(ids, [str(nova.pk), str(antiga.pk)])

    def test_lista_filtra_por_usuario_autenticado(self) -> None:
        Entrada.objects.create(
            nome="Minha",
            valor=Decimal("100"),
            usuario=self.user,
            recorrencia=False,
        )
        Entrada.objects.create(
            nome="Outra",
            valor=Decimal("100"),
            usuario=self.other,
            recorrencia=False,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nome"], "Minha")

    def test_detalha_entrada(self) -> None:
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal("500"),
            usuario=self.user,
            recorrencia=True,
        )
        response = self.client.get(f"{self.url}{entrada.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], "Salário")

    def test_detalha_entrada_de_outro_usuario_retorna_404(self) -> None:
        entrada = Entrada.objects.create(
            nome="Outra",
            valor=Decimal("500"),
            usuario=self.other,
            recorrencia=True,
        )
        response = self.client.get(f"{self.url}{entrada.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edita_entrada(self) -> None:
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal("500"),
            usuario=self.user,
            recorrencia=True,
        )
        response = self.client.put(
            f"{self.url}{entrada.pk}/",
            self._payload(nome="Bônus", valor="750.00"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entrada.refresh_from_db()
        self.assertEqual(entrada.nome, "Bônus")
        self.assertEqual(entrada.valor, Decimal("750.00"))

    def test_exclui_entrada(self) -> None:
        entrada = Entrada.objects.create(
            nome="Salário",
            valor=Decimal("500"),
            usuario=self.user,
            recorrencia=True,
        )
        response = self.client.delete(f"{self.url}{entrada.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Entrada.objects.filter(pk=entrada.pk).exists())
