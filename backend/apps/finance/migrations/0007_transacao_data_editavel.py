from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0006_capitaliza_nomes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transacao",
            name="data",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
