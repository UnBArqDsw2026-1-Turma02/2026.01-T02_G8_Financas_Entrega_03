"""Serializers de autenticação."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "telegram_id")
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "telegram_id": {"required": False, "allow_null": True},
        }

    def create(self, validated_data: dict) -> "User":
        from apps.finance.categorias_padrao import seed_categorias_padrao

        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        seed_categorias_padrao(user)
        return user


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "telegram_id", "date_joined")
        read_only_fields = fields


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email")
        extra_kwargs = {
            "username": {"required": False},
            "email": {"required": False, "allow_blank": False},
        }

    def validate_username(self, value: str) -> str:
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Nome de usuário já está em uso.")
        return value

    def validate_email(self, value: str) -> str:
        user = self.instance
        if value and User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("E-mail já está em uso.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value

    def save(self, **kwargs) -> "User":
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
