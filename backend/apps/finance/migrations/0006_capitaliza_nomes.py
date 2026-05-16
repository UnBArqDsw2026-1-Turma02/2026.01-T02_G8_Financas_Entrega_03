"""Padroniza a primeira letra dos nomes existentes em Categoria e Transacao."""

from __future__ import annotations

from django.db import migrations


def _capitaliza(valor: str) -> str:
    valor = (valor or "").strip()
    if not valor:
        return valor
    return valor[0].upper() + valor[1:]


def capitaliza_nomes(apps, schema_editor):
    for label in ("Categoria", "Transacao"):
        Model = apps.get_model("finance", label)
        for obj in Model.objects.all().only("id", "nome"):
            novo = _capitaliza(obj.nome)
            if novo != obj.nome:
                obj.nome = novo
                obj.save(update_fields=["nome"])


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0005_seed_categorias_padrao"),
    ]

    operations = [
        migrations.RunPython(capitaliza_nomes, migrations.RunPython.noop),
    ]
