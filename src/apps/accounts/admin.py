from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "telegram_id", "is_staff", "is_active")
    search_fields = ("username", "email", "telegram_id")
    fieldsets = UserAdmin.fieldsets + (
        ("Integração Telegram", {"fields": ("telegram_id",)}),
    )
