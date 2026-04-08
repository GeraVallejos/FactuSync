from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("enterprise_documents", "0006_alter_documentrecord_status"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RevokedToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jti", models.CharField(max_length=64, unique=True)),
                (
                    "token_type",
                    models.CharField(
                        choices=[("refresh", "Refresh")],
                        default="refresh",
                        max_length=16,
                    ),
                ),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="revoked_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="revokedtoken",
            index=models.Index(fields=["token_type", "expires_at"], name="enterprise_d_token_t_9e2554_idx"),
        ),
    ]
