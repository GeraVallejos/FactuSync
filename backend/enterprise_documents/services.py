from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date

from enterprise_documents.dte.parser import DTEParseError, DTEParser
from enterprise_documents.dte.validators import DTEValidator
from enterprise_documents.models import AuditEvent, DocumentRecord, TaxServiceProfile, Tenant, TenantMembership
from enterprise_documents.pdf_renderer import PDFRenderer
from enterprise_documents.sii import SIIAuthError, SIIClient, SIIClientError, SIIConfigurationError
from enterprise_documents.storage import DocumentStorage

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self) -> None:
        self.parser = DTEParser()
        self.validator = DTEValidator()
        self.renderer = PDFRenderer()
        self.storage = DocumentStorage(settings.STORAGE_ROOT)
        self.storage.initialize()

    def resolve_tenant(
        self,
        *,
        user=None,
        tenant_code: str | None = None,
        erp_tenant_id: str | None = None,
        erp_company_id: str | None = None,
    ) -> Tenant | None:
        if user is not None and getattr(user, "is_authenticated", False):
            memberships = TenantMembership.objects.select_related("tenant").filter(user=user, is_active=True, tenant__is_active=True)
            if tenant_code:
                membership = memberships.filter(tenant__code=tenant_code).first()
                if membership:
                    return membership.tenant
            default_membership = memberships.filter(is_default=True).first() or memberships.first()
            if default_membership:
                return default_membership.tenant
            if getattr(user, "is_superuser", False):
                return self._resolve_superuser_tenant(tenant_code=tenant_code)

        if erp_company_id:
            tenant, _ = Tenant.objects.get_or_create(
                erp_company_id=erp_company_id,
                defaults={
                    "code": tenant_code or self._build_code(erp_company_id),
                    "erp_tenant_id": erp_tenant_id or "",
                    "operation_mode": Tenant.OperationMode.ERP_MANAGED,
                    "name": tenant_code or erp_company_id,
                },
            )
            changed = False
            if erp_tenant_id and tenant.erp_tenant_id != erp_tenant_id:
                tenant.erp_tenant_id = erp_tenant_id
                changed = True
            if tenant_code and tenant.code != tenant_code:
                tenant.code = tenant_code
                changed = True
            if changed:
                tenant.save(update_fields=["erp_tenant_id", "code"])
            return tenant if tenant.is_active else None

        if tenant_code:
            tenant, _ = Tenant.objects.get_or_create(
                code=tenant_code,
                defaults={
                    "erp_tenant_id": erp_tenant_id or "",
                    "erp_company_id": "",
                    "operation_mode": Tenant.OperationMode.STANDALONE if not erp_tenant_id else Tenant.OperationMode.ERP_MANAGED,
                    "name": tenant_code.upper(),
                },
            )
            if erp_tenant_id and tenant.erp_tenant_id != erp_tenant_id:
                tenant.erp_tenant_id = erp_tenant_id
                tenant.save(update_fields=["erp_tenant_id"])
            return tenant if tenant.is_active else None
        return None

    def ingest_xml(self, tenant: Tenant, xml_content: bytes, source: str, actor: str) -> dict:
        document_id = uuid.uuid4()
        xml_hash = self.storage.compute_hash(xml_content)
        duplicate = DocumentRecord.objects.filter(tenant=tenant, xml_sha256=xml_hash).first()
        if duplicate:
            return {
                "id": duplicate.id,
                "status": duplicate.status,
                "duplicated": True,
                "queued": False,
                "task_id": "",
                "validation_errors": duplicate.validation_errors,
            }

        try:
            with transaction.atomic():
                _, xml_path = self.storage.write_xml(tenant.code, str(document_id), xml_content, digest=xml_hash)
                document = DocumentRecord.objects.create(
                    id=document_id,
                    tenant=tenant,
                    source=source,
                    status=DocumentRecord.Status.QUEUED,
                    xml_sha256=xml_hash,
                    xml_storage_path=xml_path,
                    metadata={
                        "received_at": timestamp(),
                        "origin": source,
                        "size_bytes": len(xml_content),
                    },
                )
                self.log(tenant, document, "documento_recibido", actor, {"source": source})
                task_info = {"task_id": "", "queued": False, "fallback_sync": False}

                def enqueue() -> None:
                    task_info.update(self.enqueue_document_processing(document.id, actor))

                transaction.on_commit(enqueue)
        except IntegrityError:
            duplicate = DocumentRecord.objects.get(tenant=tenant, xml_sha256=xml_hash)
            return {
                "id": duplicate.id,
                "status": duplicate.status,
                "duplicated": True,
                "queued": False,
                "task_id": "",
                "validation_errors": duplicate.validation_errors,
            }

        if settings.CELERY_TASK_ALWAYS_EAGER or task_info.get("fallback_sync"):
            document.refresh_from_db()
            return {
                "id": document.id,
                "status": document.status,
                "duplicated": False,
                "queued": task_info.get("queued", document.status == DocumentRecord.Status.QUEUED),
                "task_id": task_info.get("task_id", ""),
                "validation_errors": document.validation_errors,
            }

        return {
            "id": document.id,
            "status": document.status,
            "duplicated": False,
            "queued": task_info.get("queued", True),
            "task_id": task_info.get("task_id", ""),
            "validation_errors": [],
        }

    def enqueue_document_processing(self, document_id: uuid.UUID, actor: str) -> dict[str, str]:
        from enterprise_documents.tasks import process_document_task

        if settings.CELERY_TASK_ALWAYS_EAGER:
            self.process_document_by_id(str(document_id), actor)
            return {"task_id": "", "queued": False, "fallback_sync": True}
        try:
            task = process_document_task.delay(str(document_id), actor)
            return {"task_id": task.id, "queued": True, "fallback_sync": False}
        except Exception as exc:
            return self._fallback_or_raise(
                "process_document",
                exc,
                lambda: self.process_document_by_id(str(document_id), actor),
            )

    def process_document_by_id(self, document_id: str, actor: str) -> dict:
        document = DocumentRecord.objects.get(id=document_id)
        return self.process_document(document, actor)

    def process_document(self, document: DocumentRecord, actor: str) -> dict:
        document.status = DocumentRecord.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])
        self.log(document.tenant, document, "documento_procesando", actor, {})

        xml_content = Path(document.xml_storage_path).read_bytes()
        try:
            parsed = self.parser.parse(xml_content)
            validation_errors = self.validator.validate(parsed)
            pdf_bytes = self.renderer.render(
                parsed,
                brand_name=settings.DEFAULT_BRAND_NAME,
                brand_color=settings.DEFAULT_BRAND_PRIMARY,
            )
            pdf_path = self.storage.write_pdf(document.tenant.code, str(document.id), pdf_bytes, document.version)
            document.document_type = parsed.document_type
            document.folio = parsed.folio
            document.issuer_rut = parsed.issuer.rut or ""
            document.receiver_rut = parsed.receiver.rut or ""
            document.issue_date = parse_date(parsed.issue_date) if parsed.issue_date else None
            document.total_amount = Decimal(parsed.totals.total_amount)
            document.normalized_data = json.loads(json.dumps(asdict(parsed), default=str))
            document.validation_errors = validation_errors
            document.pdf_storage_path = pdf_path
            document.last_error = "; ".join(validation_errors) if validation_errors else ""
            document.status = (
                DocumentRecord.Status.PDF_GENERATED if not validation_errors else DocumentRecord.Status.ERROR
            )
            document.save()
            self.log(
                document.tenant,
                document,
                "documento_validado" if not validation_errors else "documento_con_error",
                actor,
                {"validation_errors": validation_errors},
            )
            self.log(document.tenant, document, "pdf_generado", actor, {"pdf_path": pdf_path})
            return {
                "id": document.id,
                "status": document.status,
                "duplicated": False,
                "queued": False,
                "task_id": "",
                "validation_errors": validation_errors,
            }
        except DTEParseError as exc:
            document.status = DocumentRecord.Status.ERROR
            document.last_error = str(exc)
            document.validation_errors = [str(exc)]
            document.save(update_fields=["status", "last_error", "validation_errors", "updated_at"])
            self.log(document.tenant, document, "xml_invalido", actor, {"error": str(exc)})
            return {
                "id": document.id,
                "status": document.status,
                "duplicated": False,
                "queued": False,
                "task_id": "",
                "validation_errors": [str(exc)],
            }

    def reprocess_document(self, document: DocumentRecord, actor: str) -> dict:
        previous_version = document.version
        document.version += 1
        document.status = DocumentRecord.Status.QUEUED
        document.save(update_fields=["version", "status", "updated_at"])
        self.log(document.tenant, document, "documento_reprocesado", actor, {"previous_version": previous_version})
        task_info = self.enqueue_document_processing(document.id, actor)
        if settings.CELERY_TASK_ALWAYS_EAGER or task_info.get("fallback_sync"):
            document.refresh_from_db()
        return {
            "id": document.id,
            "status": document.status,
            "duplicated": False,
            "queued": task_info.get("queued", document.status == DocumentRecord.Status.QUEUED),
            "task_id": task_info.get("task_id", ""),
            "validation_errors": document.validation_errors,
        }

    def list_documents(self, tenant: Tenant, filters: dict[str, str | None]):
        queryset = DocumentRecord.objects.filter(tenant=tenant)
        if filters.get("status"):
            queryset = queryset.filter(status=filters["status"])
        if filters.get("document_type"):
            queryset = queryset.filter(document_type=filters["document_type"])
        if filters.get("issuer_rut"):
            queryset = queryset.filter(issuer_rut=filters["issuer_rut"])
        if filters.get("receiver_rut"):
            queryset = queryset.filter(receiver_rut=filters["receiver_rut"])
        if filters.get("issue_date"):
            parsed = parse_date(filters["issue_date"])
            if parsed:
                queryset = queryset.filter(issue_date=parsed)
        return queryset

    def get_document(self, tenant: Tenant, document_id: str) -> DocumentRecord:
        return DocumentRecord.objects.get(tenant=tenant, id=document_id)

    def metrics(self, tenant: Tenant) -> dict:
        grouped = DocumentRecord.objects.filter(tenant=tenant).values("status").annotate(total=Count("id"))
        by_status = {row["status"]: row["total"] for row in grouped}
        total = sum(by_status.values())
        errors = by_status.get(DocumentRecord.Status.ERROR, 0)
        return {
            "total_documents": total,
            "by_status": by_status,
            "error_rate": round((errors / total) * 100, 2) if total else 0.0,
        }

    def sync_enabled_profiles(self) -> int:
        profiles = TaxServiceProfile.objects.select_related("tenant").filter(sync_enabled=True)
        total = 0
        for profile in profiles:
            self.enqueue_sii_sync(profile.id)
            total += 1
        return total

    def enqueue_sii_sync(self, profile_id: int) -> dict[str, str]:
        from enterprise_documents.tasks import sync_sii_profile_task

        if settings.CELERY_TASK_ALWAYS_EAGER:
            self.sync_sii_profile(profile_id)
            return {"task_id": "", "queued": False, "fallback_sync": True}
        try:
            task = sync_sii_profile_task.delay(profile_id)
            return {"task_id": task.id, "queued": True, "fallback_sync": False}
        except Exception as exc:
            return self._fallback_or_raise(
                "sync_sii_profile",
                exc,
                lambda: self.sync_sii_profile(profile_id),
            )

    def sync_sii_profile(self, profile_id: int) -> dict:
        profile = TaxServiceProfile.objects.select_related("tenant").get(id=profile_id)
        profile.last_sync_status = TaxServiceProfile.SyncStatus.RUNNING
        profile.last_sync_error = ""
        profile.last_sync_at = timezone.now()
        profile.save(update_fields=["last_sync_status", "last_sync_error", "last_sync_at", "updated_at"])
        self.log(profile.tenant, None, "sii_sync_iniciado", "celery", {})
        try:
            auth_result = self._authenticate_sii(profile)
        except (SIIConfigurationError, SIIAuthError, SIIClientError) as exc:
            profile.last_sync_status = TaxServiceProfile.SyncStatus.ERROR
            profile.last_sync_error = str(exc)
            profile.save(update_fields=["last_sync_status", "last_sync_error", "updated_at"])
            self.log(profile.tenant, None, "sii_sync_error", "celery", {"error": str(exc)})
            return {"profile_id": profile.id, "status": profile.last_sync_status, "error": str(exc)}

        profile.last_sync_status = TaxServiceProfile.SyncStatus.IDLE
        profile.last_sync_error = ""
        profile.save(update_fields=["last_sync_status", "last_sync_error", "updated_at"])
        self.log(
            profile.tenant,
            None,
            "sii_sync_autenticado",
            "celery",
            {
                "environment": auth_result.environment,
                "host": auth_result.host,
                "token_preview": auth_result.token_preview,
            },
        )
        return {
            "profile_id": profile.id,
            "status": profile.last_sync_status,
            "environment": auth_result.environment,
            "host": auth_result.host,
            "token_preview": auth_result.token_preview,
        }

    def test_sii_auth(self, tenant: Tenant, actor: str) -> dict:
        profile = self.get_or_create_tax_profile(tenant)
        try:
            auth_result = self._authenticate_sii(profile)
        except (SIIConfigurationError, SIIAuthError, SIIClientError) as exc:
            profile.last_sync_at = timezone.now()
            profile.last_sync_status = TaxServiceProfile.SyncStatus.ERROR
            profile.last_sync_error = str(exc)
            profile.save(update_fields=["last_sync_at", "last_sync_status", "last_sync_error", "updated_at"])
            self.log(tenant, None, "sii_auth_error", actor, {"error": str(exc)})
            raise
        profile.last_sync_at = timezone.now()
        profile.last_sync_status = TaxServiceProfile.SyncStatus.IDLE
        profile.last_sync_error = ""
        profile.save(update_fields=["last_sync_at", "last_sync_status", "last_sync_error", "updated_at"])
        self.log(
            tenant,
            None,
            "sii_auth_ok",
            actor,
            {
                "environment": auth_result.environment,
                "host": auth_result.host,
                "token_preview": auth_result.token_preview,
            },
        )
        return {
            "authenticated": True,
            "environment": auth_result.environment,
            "host": auth_result.host,
            "seed": auth_result.seed,
            "token_preview": auth_result.token_preview,
            "seed_endpoint": auth_result.seed_endpoint,
            "token_endpoint": auth_result.token_endpoint,
        }

    def log(self, tenant: Tenant, document: DocumentRecord | None, event_type: str, actor: str, payload: dict) -> None:
        AuditEvent.objects.create(
            tenant=tenant,
            document=document,
            event_type=event_type,
            actor=actor,
            payload=payload,
        )

    def _build_code(self, value: str) -> str:
        normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
        return normalized[:64] or f"tenant-{uuid.uuid4().hex[:8]}"

    def _resolve_superuser_tenant(self, tenant_code: str | None = None) -> Tenant | None:
        queryset = Tenant.objects.filter(is_active=True).order_by("name")
        if tenant_code:
            return queryset.filter(code=tenant_code).first()
        return queryset.first()

    def authenticate_user(self, username: str, password: str):
        return authenticate(username=username, password=password)

    def session_payload(self, user) -> dict:
        memberships = TenantMembership.objects.select_related("tenant").filter(user=user, is_active=True, tenant__is_active=True)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email or "",
            "memberships": [
                {
                    "tenant_id": membership.tenant.id,
                    "tenant_code": membership.tenant.code,
                    "tenant_name": membership.tenant.name,
                    "operation_mode": membership.tenant.operation_mode,
                    "role": membership.role,
                    "is_default": membership.is_default,
                }
                for membership in memberships
            ],
        }

    def get_or_create_tax_profile(self, tenant: Tenant) -> TaxServiceProfile:
        profile, _ = TaxServiceProfile.objects.get_or_create(
            tenant=tenant,
            defaults={"sii_rut": tenant.rut},
        )
        return profile

    def _authenticate_sii(self, profile: TaxServiceProfile):
        client = SIIClient(profile)
        return client.authenticate()

    def _fallback_or_raise(self, task_name: str, exc: Exception, fallback):
        logger.warning("Celery dispatch failed for %s: %s", task_name, exc)
        if not settings.CELERY_FALLBACK_TO_SYNC_ON_ERROR:
            raise
        fallback()
        return {"task_id": "", "queued": False, "fallback_sync": True}


def timestamp() -> str:
    return timezone.now().isoformat()
