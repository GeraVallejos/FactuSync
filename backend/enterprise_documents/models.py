from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from enterprise_documents.secret_store import decrypt_secret, encrypt_secret


class Tenant(models.Model):
    class OperationMode(models.TextChoices):
        STANDALONE = "standalone", "Standalone"
        ERP_MANAGED = "erp_managed", "ERP Managed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=64, unique=True)
    erp_tenant_id = models.CharField(max_length=128, blank=True, db_index=True)
    erp_company_id = models.CharField(max_length=128, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    rut = models.CharField(max_length=16, blank=True)
    operation_mode = models.CharField(
        max_length=32,
        choices=OperationMode.choices,
        default=OperationMode.STANDALONE,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class DocumentRecord(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "recibido", "Recibido"
        QUEUED = "en_cola", "En cola"
        PROCESSING = "procesando", "Procesando"
        VALID = "valido", "Valido"
        ERROR = "con_error", "Con error"
        PDF_GENERATED = "pdf_generado", "PDF generado"

    class Source(models.TextChoices):
        MANUAL_XML = "manual_xml", "Manual XML"
        SII = "sii", "SII"
        BULK = "bulk", "Bulk"
        EMAIL = "email", "Email"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="documents")
    source = models.CharField(max_length=32, choices=Source.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.RECEIVED)
    document_type = models.CharField(max_length=8, blank=True)
    folio = models.CharField(max_length=64, blank=True)
    issuer_rut = models.CharField(max_length=16, blank=True)
    receiver_rut = models.CharField(max_length=16, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    xml_sha256 = models.CharField(max_length=64)
    xml_storage_path = models.CharField(max_length=500)
    pdf_storage_path = models.CharField(max_length=500, blank=True)
    normalized_data = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    validation_errors = models.JSONField(default=list)
    version = models.PositiveIntegerField(default=1)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "xml_sha256"], name="uq_document_tenant_xml_sha256"),
        ]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "document_type"]),
            models.Index(fields=["tenant", "issue_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.tenant.code} {self.document_type} {self.folio}"


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="audit_events")
    document = models.ForeignKey(
        DocumentRecord,
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=64)
    actor = models.CharField(max_length=255)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.event_type} - {self.document_id}"


class TaxServiceProfile(models.Model):
    class Environment(models.TextChoices):
        CERTIFICATION = "certificacion", "Certificacion"
        PRODUCTION = "produccion", "Produccion"

    class SyncStatus(models.TextChoices):
        IDLE = "idle", "Idle"
        RUNNING = "running", "Running"
        ERROR = "error", "Error"

    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="tax_profile")
    sii_environment = models.CharField(
        max_length=32,
        choices=Environment.choices,
        default=Environment.CERTIFICATION,
    )
    sii_rut = models.CharField(max_length=16, blank=True)
    sync_enabled = models.BooleanField(default=False)
    poll_interval_minutes = models.PositiveIntegerField(default=15)
    certificate_path = models.CharField(max_length=500, blank=True)
    certificate_password_encrypted = models.TextField(blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(
        max_length=32,
        choices=SyncStatus.choices,
        default=SyncStatus.IDLE,
    )
    last_sync_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.tenant.code} - {self.sii_environment}"

    @property
    def certificate_password(self) -> str:
        return decrypt_secret(self.certificate_password_encrypted)

    @certificate_password.setter
    def certificate_password(self, value: str) -> None:
        self.certificate_password_encrypted = encrypt_secret(value)


class TenantMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"
        VIEWER = "viewer", "Viewer"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_memberships")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.ADMIN)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "tenant"], name="uq_membership_user_tenant"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.tenant.code} ({self.role})"
