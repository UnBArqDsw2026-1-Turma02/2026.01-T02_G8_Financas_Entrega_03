"""Backfill das categorias padrão para usuários existentes."""

from __future__ import annotations

from django.conf import settings
from django.db import migrations

from apps.finance.categorias_padrao import seed_categorias_padrao


def seed_para_existentes(apps, schema_editor):
    Categoria = apps.get_model("finance", "Categoria")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    for user in User.objects.all():
        seed_categorias_padrao(user, model=Categoria)


def remover_seed(apps, schema_editor):
    # Não removemos categorias na reversão: o usuário pode tê-las personalizado
    # (renomeado transações para apontar para elas) e a remoção seria destrutiva.
    return


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0004_parcelamento_antecipadas_no_ciclo"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(seed_para_existentes, remover_seed),
    ]
