"""Views de autenticação (Issue #19)."""

from __future__ import annotations

import re

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
    UsuarioSerializer,
)
from apps.accounts.services import AuthService


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UpdateProfileSerializer
        return UsuarioSerializer

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UsuarioSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TelegramVinculoView(APIView):
    """Endpoints para vincular/desvincular o ``telegram_id`` do usuário logado.

    Consumido pela tela ``Integrações`` do frontend. O fluxo evita expor
    operações arbitrárias sobre o usuário inteiro — apenas o campo
    ``telegram_id`` é tocado, com unicidade garantida pelo ``AuthService``.
    """

    permission_classes = [permissions.IsAuthenticated]
    TELEGRAM_ID_REGEX = re.compile(r"^\d{5,20}$")

    def get(self, request: Request) -> Response:
        return Response({"telegram_id": request.user.telegram_id})

    def post(self, request: Request) -> Response:
        telegram_id = str(request.data.get("telegram_id", "")).strip()
        if not self.TELEGRAM_ID_REGEX.match(telegram_id):
            return Response(
                {"telegram_id": ["Informe um ID numérico do Telegram (5 a 20 dígitos)."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            AuthService.link_telegram(request.user, telegram_id)
        except ValueError as exc:
            return Response(
                {"telegram_id": [str(exc)]},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({"telegram_id": request.user.telegram_id})

    def delete(self, request: Request) -> Response:
        AuthService.unlink_telegram(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
