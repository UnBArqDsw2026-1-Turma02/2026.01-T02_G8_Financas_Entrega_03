"""Testes de integração do CRUD de Parcelamentos (Issue #07)."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finance.models import Categoria, Pagamento, Parcelamento

User = get_user_model()


class ParcelamentoCRUDApiTests(APITestCase):
    url = "/api/v1/finance/parcelamentos/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="alice", password="Senha!2026")
        self.other = User.objects.create_user(username="bob", password="Senha!2026")
        self.categoria = Categoria.objects.create(
            nome="Eletrônicos",
            descricao="Gadgets",
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
            "nome": "Notebook",
            "valor": "3000.00",
            "categoria": str(self.categoria.pk),
            "pagamento": Pagamento.CREDITO,
            "num_parcelas": 10,
        }
        data.update(overrides)
        return data

    def _criar_parcelamento(self, **overrides) -> Parcelamento:
        defaults = {
            "nome": "TV",
            "valor": Decimal("1200.00"),
            "usuario": self.user,
            "categoria": self.categoria,
            "pagamento": Pagamento.CREDITO,
            "num_parcelas": 3,
            "valor_parcela": Decimal("400.00"),
        }
        defaults.update(overrides)
        return Parcelamento.objects.create(**defaults)

    def test_exige_autenticacao(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cria_parcelamento_calcula_valor_parcela(self) -> None:
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["valor_parcela"], "300.00")
        self.assertEqual(response.data["parcela_atual"], 1)
        parc = Parcelamento.objects.get(pk=response.data["id"])
        self.assertEqual(parc.usuario, self.user)
        self.assertEqual(parc.valor_parcela, Decimal("300.00"))

    def test_cria_parcelamento_valor_zero_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(valor="0"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("valor", response.data)

    def test_cria_parcelamento_num_parcelas_zero_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(num_parcelas=0), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("num_parcelas", response.data)

    def test_cria_parcelamento_nome_vazio_rejeitado(self) -> None:
        response = self.client.post(
            self.url, self._payload(nome=""), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nome", response.data)

    def test_categoria_de_outro_usuario_rejeitada(self) -> None:
        response = self.client.post(
            self.url,
            self._payload(categoria=str(self.categoria_outro.pk)),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("categoria", response.data)

    def test_valor_parcela_enviado_pelo_cliente_e_ignorado(self) -> None:
        payload = self._payload()
        payload["valor_parcela"] = "999.99"
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["valor_parcela"], "300.00")

    def test_lista_filtra_por_usuario_autenticado(self) -> None:
        self._criar_parcelamento(nome="Meu")
        self._criar_parcelamento(
            nome="Outro",
            usuario=self.other,
            categoria=self.categoria_outro,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["nome"], "Meu")

    def test_detalha_parcelamento(self) -> None:
        parc = self._criar_parcelamento()
        response = self.client.get(f"{self.url}{parc.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome"], "TV")

    def test_detalha_de_outro_usuario_retorna_404(self) -> None:
        parc = self._criar_parcelamento(
            usuario=self.other, categoria=self.categoria_outro
        )
        response = self.client.get(f"{self.url}{parc.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edita_na_primeira_parcela(self) -> None:
        parc = self._criar_parcelamento()
        response = self.client.put(
            f"{self.url}{parc.pk}/",
            self._payload(nome="TV Nova", valor="1500.00", num_parcelas=5),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        parc.refresh_from_db()
        self.assertEqual(parc.nome, "TV Nova")
        self.assertEqual(parc.valor, Decimal("1500.00"))

    def test_edita_apos_primeira_parcela_bloqueada(self) -> None:
        parc = self._criar_parcelamento(parcela_atual=2)
        response = self.client.put(
            f"{self.url}{parc.pk}/",
            self._payload(nome="Tentativa"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("parcela_atual", response.data)

    def test_exclui_parcelamento(self) -> None:
        parc = self._criar_parcelamento()
        response = self.client.delete(f"{self.url}{parc.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Parcelamento.objects.filter(pk=parc.pk).exists())

    def test_exclui_de_outro_usuario_retorna_404(self) -> None:
        parc = self._criar_parcelamento(
            usuario=self.other, categoria=self.categoria_outro
        )
        response = self.client.delete(f"{self.url}{parc.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_antecipar_incrementa_parcela_atual(self) -> None:
        parc = self._criar_parcelamento()
        response = self.client.post(f"{self.url}{parc.pk}/antecipar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["parcela_atual"], 2)
        parc.refresh_from_db()
        self.assertEqual(parc.parcela_atual, 2)

    def test_antecipar_alem_do_total_rejeitado(self) -> None:
        parc = self._criar_parcelamento(num_parcelas=2, parcela_atual=2)
        response = self.client.post(f"{self.url}{parc.pk}/antecipar/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_antecipar_de_outro_usuario_retorna_404(self) -> None:
        parc = self._criar_parcelamento(
            usuario=self.other, categoria=self.categoria_outro
        )
        response = self.client.post(f"{self.url}{parc.pk}/antecipar/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
