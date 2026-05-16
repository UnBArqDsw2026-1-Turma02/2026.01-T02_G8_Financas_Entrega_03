"""Testes da Issue #19 — autenticação, registro, JWT e AuthService."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.services import AuthService
from apps.finance.categorias_padrao import CATEGORIAS_PADRAO
from apps.finance.models import Categoria

User = get_user_model()


class RegisterEndpointTests(APITestCase):
    url = "/api/v1/auth/register/"

    def test_registra_usuario_e_retorna_201(self) -> None:
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "Senha!2026",
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "alice")
        self.assertNotIn("password", response.data)
        user = User.objects.get(username="alice")
        self.assertTrue(user.check_password("Senha!2026"))

    def test_registro_cria_categorias_padrao(self) -> None:
        payload = {
            "username": "seed",
            "email": "seed@example.com",
            "password": "Senha!2026",
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="seed")
        nomes = set(Categoria.objects.filter(usuario=user).values_list("nome", flat=True))
        self.assertEqual(nomes, {c["nome"] for c in CATEGORIAS_PADRAO})

    def test_senha_fraca_rejeitada(self) -> None:
        payload = {"username": "bob", "email": "bob@example.com", "password": "123"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_username_duplicado_rejeitado(self) -> None:
        User.objects.create_user(username="dup", password="Senha!2026")
        payload = {
            "username": "dup",
            "email": "x@example.com",
            "password": "OutraSenha!9",
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginRefreshTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="carol", email="c@example.com", password="Senha!2026"
        )

    def test_login_retorna_access_e_refresh(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "carol", "password": "Senha!2026"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_credenciais_invalidas(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "carol", "password": "errada"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_gera_novo_access(self) -> None:
        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": "carol", "password": "Senha!2026"},
            format="json",
        )
        refresh = login.data["refresh"]
        response = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class MeEndpointTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="dani", email="d@example.com", password="Senha!2026"
        )

    def test_me_exige_token(self) -> None:
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_retorna_usuario_autenticado(self) -> None:
        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": "dani", "password": "Senha!2026"},
            format="json",
        )
        token = login.data["access"]
        response = self.client.get(
            "/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "dani")
        self.assertEqual(response.data["email"], "d@example.com")


class AuthServiceTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="erin", password="Senha!2026")
        self.other = User.objects.create_user(username="frank", password="Senha!2026")

    def test_link_telegram_vincula_id(self) -> None:
        AuthService.link_telegram(self.user, "111222333")
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_id, "111222333")

    def test_get_by_telegram_id_localiza_usuario(self) -> None:
        AuthService.link_telegram(self.user, "999")
        found = AuthService.get_by_telegram_id("999")
        self.assertEqual(found, self.user)

    def test_get_by_telegram_id_inexistente_retorna_none(self) -> None:
        self.assertIsNone(AuthService.get_by_telegram_id("nao-existe"))

    def test_link_telegram_conflito_levanta_valueerror(self) -> None:
        AuthService.link_telegram(self.user, "555")
        with self.assertRaises(ValueError):
            AuthService.link_telegram(self.other, "555")

    def test_is_authorized(self) -> None:
        self.assertFalse(AuthService.is_authorized("nada"))
        AuthService.link_telegram(self.user, "777")
        self.assertTrue(AuthService.is_authorized("777"))

    def test_unlink_telegram_zera_vinculo(self) -> None:
        AuthService.link_telegram(self.user, "888")
        AuthService.unlink_telegram(self.user)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.telegram_id)


class TelegramVinculoEndpointTests(APITestCase):
    """Endpoint usado pela página Integrações do frontend."""

    url = "/api/v1/auth/me/telegram/"

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="gio", email="g@example.com", password="Senha!2026"
        )
        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": "gio", "password": "Senha!2026"},
            format="json",
        )
        self.token = login.data["access"]
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_get_sem_token_retorna_401(self) -> None:
        self.assertEqual(
            self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_get_retorna_telegram_id_atual(self) -> None:
        response = self.client.get(self.url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["telegram_id"])

    def test_post_vincula_telegram_id(self) -> None:
        response = self.client.post(
            self.url, {"telegram_id": "1380108006"}, format="json", **self.auth
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["telegram_id"], "1380108006")
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_id, "1380108006")

    def test_post_formato_invalido_retorna_400(self) -> None:
        response = self.client.post(
            self.url, {"telegram_id": "abc123"}, format="json", **self.auth
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("telegram_id", response.data)

    def test_post_conflito_retorna_409(self) -> None:
        outro = User.objects.create_user(username="hugo", password="Senha!2026")
        AuthService.link_telegram(outro, "1380108006")

        response = self.client.post(
            self.url, {"telegram_id": "1380108006"}, format="json", **self.auth
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("telegram_id", response.data)

    def test_delete_desvincula(self) -> None:
        AuthService.link_telegram(self.user, "1380108006")

        response = self.client.delete(self.url, **self.auth)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.telegram_id)
