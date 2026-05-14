"""Testes de integração do CRUD de Categorias (Issue #08)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import Categoria

User = get_user_model()


class CategoriaCRUDApiTests(APITestCase):
    url = "/api/v1/categorias/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="Senha!2026")
        self.other = User.objects.create_user(username="bob", password="Senha!2026")
        self.client.force_authenticate(self.user)

    def _payload(self, **overrides):
        data = {
            "nome": "Mercado",
            "descricao": "Compras do mês",
            "cor": "#112233",
        }
        data.update(overrides)
        return data

    def test_exige_autenticacao(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cria_categoria_com_dados_validos(self) -> None:
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome"], "Mercado")
        categoria = Categoria.objects.get(pk=response.data["id"])
        self.assertEqual(categoria.usuario, self.user)
        self.assertEqual(categoria.descricao, "Compras do mês")
        self.assertEqual(categoria.cor, "#112233")

    def test_cria_categoria_nome_vazio_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(nome=""), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nome", response.data)

    def test_cria_categoria_descricao_vazia_rejeitada(self) -> None:
        response = self.client.post(
            self.url, self._payload(descricao=""), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("descricao", response.data)

    def test_cria_categoria_cor_vazia_rejeitada(self) -> None:
        response = self.client.post(
            self.url, self._payload(cor=""), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cor", response.data)

    def test_cria_categoria_sem_nome_rejeitado(self) -> None:
        payload = self._payload()
        payload.pop("nome")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nome", response.data)

    def test_lista_categorias_ordenadas_por_nome(self) -> None:
        Categoria.objects.create(
            nome="Zoológico", descricao="x", cor="#000000", usuario=self.user
        )
        Categoria.objects.create(
            nome="Alimentação", descricao="y", cor="#111111", usuario=self.user
        )
        Categoria.objects.create(
            nome="Mercado", descricao="z", cor="#222222", usuario=self.user
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nomes = [item["nome"] for item in response.data]
        self.assertEqual(nomes, ["Alimentação", "Mercado", "Zoológico"])

    def test_lista_filtra_por_usuario_autenticado(self) -> None:
        Categoria.objects.create(
            nome="Minha", descricao="x", cor="#000000", usuario=self.user
        )
        Categoria.objects.create(
            nome="Outra", descricao="y", cor="#111111", usuario=self.other
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nome"], "Minha")

    def test_detalha_categoria(self) -> None:
        categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras",
            cor="#112233",
            usuario=self.user,
        )
        response = self.client.get(f"{self.url}{categoria.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], "Mercado")

    def test_detalha_categoria_de_outro_usuario_retorna_404(self) -> None:
        categoria = Categoria.objects.create(
            nome="Outra",
            descricao="x",
            cor="#000000",
            usuario=self.other,
        )
        response = self.client.get(f"{self.url}{categoria.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edita_categoria(self) -> None:
        categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras",
            cor="#112233",
            usuario=self.user,
        )
        response = self.client.put(
            f"{self.url}{categoria.pk}/",
            self._payload(nome="Supermercado", cor="#445566"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        categoria.refresh_from_db()
        self.assertEqual(categoria.nome, "Supermercado")
        self.assertEqual(categoria.cor, "#445566")

    def test_edita_categoria_nome_vazio_rejeitado(self) -> None:
        categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras",
            cor="#112233",
            usuario=self.user,
        )
        response = self.client.put(
            f"{self.url}{categoria.pk}/",
            self._payload(nome=""),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nome", response.data)

    def test_exclui_categoria(self) -> None:
        categoria = Categoria.objects.create(
            nome="Mercado",
            descricao="Compras",
            cor="#112233",
            usuario=self.user,
        )
        response = self.client.delete(f"{self.url}{categoria.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_exclui_categoria_de_outro_usuario_retorna_404(self) -> None:
        categoria = Categoria.objects.create(
            nome="Outra",
            descricao="x",
            cor="#000000",
            usuario=self.other,
        )
        response = self.client.delete(f"{self.url}{categoria.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_usuario_e_atribuido_automaticamente(self) -> None:
        payload = self._payload()
        payload["usuario"] = str(self.other.pk)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        categoria = Categoria.objects.get(pk=response.data["id"])
        self.assertEqual(categoria.usuario, self.user)
