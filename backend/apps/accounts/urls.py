from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    ChangePasswordView,
    MeView,
    RegisterView,
    TelegramVinculoView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("me/telegram/", TelegramVinculoView.as_view(), name="me-telegram"),
    path("me/password/", ChangePasswordView.as_view(), name="me-password"),
]
