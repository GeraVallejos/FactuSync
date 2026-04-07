from __future__ import annotations

import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("enterprise_documents", "0002_rename_enterprise__tenant__0f6037_idx_enterprise__tenant__01b018_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="erp_company_id",
            field=models.CharField(blank=True, db_index=True, max_length=128),
        ),
        migrations.AddField(
            model_name="tenant",
            name="erp_tenant_id",
            field=models.CharField(blank=True, db_index=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="documentrecord",
            name="status",
            field=models.CharField(
                choices=[
                    ("recibido", "Recibido"),
                    ("en_cola", "En cola"),
                    ("procesando", "Procesando"),
                    ("valido", "Valido"),
                    ("con_error", "Con error"),
                    ("pdf_generado", "PDF generado"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="auditevent",
            name="document",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="audit_events",
                to="enterprise_documents.documentrecord",
            ),
        ),
        migrations.CreateModel(
            name="TaxServiceProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "sii_environment",
                    models.CharField(
                        choices=[("certificacion", "Certificacion"), ("produccion", "Produccion")],
                        default="certificacion",
                        max_length=32,
                    ),
                ),
                ("sii_rut", models.CharField(blank=True, max_length=16)),
                ("sync_enabled", models.BooleanField(default=False)),
                ("poll_interval_minutes", models.PositiveIntegerField(default=15)),
                ("certificate_path", models.CharField(blank=True, max_length=500)),
                ("last_sync_at", models.DateTimeField(blank=True, null=True)),
                (
                    "last_sync_status",
                    models.CharField(
                        choices=[("idle", "Idle"), ("running", "Running"), ("error", "Error")],
                        default="idle",
                        max_length=32,
                    ),
                ),
                ("last_sync_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tax_profile",
                        to="enterprise_documents.tenant",
                    ),
                ),
            ],
        ),
    ]
