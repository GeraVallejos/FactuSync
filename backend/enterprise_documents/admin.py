from __future__ import annotations

from django.contrib import admin

from enterprise_documents.models import AuditEvent, DocumentRecord, TaxServiceProfile, Tenant, TenantMembership


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("code", "operation_mode", "erp_tenant_id", "erp_company_id", "name", "rut", "is_active", "created_at")
    search_fields = ("code", "erp_tenant_id", "erp_company_id", "name", "rut")
    list_filter = ("is_active", "operation_mode")


@admin.register(DocumentRecord)
class DocumentRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "document_type", "folio", "status", "source", "created_at")
    search_fields = ("folio", "issuer_rut", "receiver_rut", "xml_sha256")
    list_filter = ("status", "source", "document_type", "tenant")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "document", "tenant", "actor", "created_at")
    search_fields = ("event_type", "actor", "document__folio")
    list_filter = ("event_type", "tenant")


@admin.register(TaxServiceProfile)
class TaxServiceProfileAdmin(admin.ModelAdmin):
    list_display = ("tenant", "sii_environment", "sync_enabled", "last_sync_status", "last_sync_at")
    search_fields = ("tenant__code", "tenant__erp_company_id", "sii_rut")
    list_filter = ("sii_environment", "sync_enabled", "last_sync_status")
    exclude = ("certificate_password_encrypted",)


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role", "is_default", "is_active", "created_at")
    search_fields = ("user__username", "user__email", "tenant__code")
    list_filter = ("role", "is_default", "is_active")
