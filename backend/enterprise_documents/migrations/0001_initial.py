from __future__ import annotations

import django.db.models.deletion
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.SlugField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("rut", models.CharField(blank=True, max_length=16)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="DocumentRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source", models.CharField(choices=[("manual_xml", "Manual XML"), ("sii", "SII"), ("bulk", "Bulk"), ("email", "Email")], max_length=32)),
                ("status", models.CharField(choices=[("recibido", "Recibido"), ("procesando", "Procesando"), ("valido", "Valido"), ("con_error", "Con error"), ("pdf_generado", "PDF generado")], default="recibido", max_length=32)),
                ("document_type", models.CharField(blank=True, max_length=8)),
                ("folio", models.CharField(blank=True, max_length=64)),
                ("issuer_rut", models.CharField(blank=True, max_length=16)),
                ("receiver_rut", models.CharField(blank=True, max_length=16)),
                ("issue_date", models.DateField(blank=True, null=True)),
                ("total_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True)),
                ("xml_sha256", models.CharField(max_length=64)),
                ("xml_storage_path", models.CharField(max_length=500)),
                ("pdf_storage_path", models.CharField(blank=True, max_length=500)),
                ("normalized_data", models.JSONField(blank=True, null=True)),
                ("metadata", models.JSONField(default=dict)),
                ("validation_errors", models.JSONField(default=list)),
                ("version", models.PositiveIntegerField(default=1)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents", to="enterprise_documents.tenant")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=64)),
                ("actor", models.CharField(max_length=255)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="enterprise_documents.documentrecord")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="enterprise_documents.tenant")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="documentrecord",
            index=models.Index(fields=["tenant", "status"], name="enterprise__tenant__0f6037_idx"),
        ),
        migrations.AddIndex(
            model_name="documentrecord",
            index=models.Index(fields=["tenant", "document_type"], name="enterprise__tenant__ff4c79_idx"),
        ),
        migrations.AddIndex(
            model_name="documentrecord",
            index=models.Index(fields=["tenant", "issue_date"], name="enterprise__tenant__004d4a_idx"),
        ),
        migrations.AddConstraint(
            model_name="documentrecord",
            constraint=models.UniqueConstraint(fields=("tenant", "xml_sha256"), name="uq_document_tenant_xml_sha256"),
        ),
    ]
