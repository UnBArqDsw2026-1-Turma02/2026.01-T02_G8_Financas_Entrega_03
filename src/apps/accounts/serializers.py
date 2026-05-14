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
