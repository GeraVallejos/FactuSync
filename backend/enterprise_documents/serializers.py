from __future__ import annotations

from rest_framework import serializers

from enterprise_documents.models import AuditEvent, DocumentRecord, TaxServiceProfile, Tenant, TenantMembership


class DocumentImportResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    duplicated = serializers.BooleanField()
    queued = serializers.BooleanField(default=False)
    task_id = serializers.CharField(allow_blank=True, required=False)
    validation_errors = serializers.ListField(child=serializers.CharField())


class DocumentRecordSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(read_only=True)
    tenant_code = serializers.CharField(source="tenant.code", read_only=True)
    erp_tenant_id = serializers.CharField(source="tenant.erp_tenant_id", read_only=True)
    erp_company_id = serializers.CharField(source="tenant.erp_company_id", read_only=True)

    class Meta:
        model = DocumentRecord
        fields = [
            "id",
            "tenant_id",
            "tenant_code",
            "erp_tenant_id",
            "erp_company_id",
            "source",
            "status",
            "document_type",
            "folio",
            "issuer_rut",
            "receiver_rut",
            "issue_date",
            "total_amount",
            "version",
            "last_error",
            "metadata",
            "normalized_data",
            "validation_errors",
            "created_at",
            "updated_at",
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ["id", "event_type", "actor", "payload", "created_at"]


class DashboardSerializer(serializers.Serializer):
    total_documents = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())
    error_rate = serializers.FloatField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class TenantMembershipSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    tenant_code = serializers.CharField()
    tenant_name = serializers.CharField()
    operation_mode = serializers.CharField()
    role = serializers.CharField()
    is_default = serializers.BooleanField()


class SessionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    memberships = TenantMembershipSerializer(many=True)


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "code",
            "erp_tenant_id",
            "erp_company_id",
            "name",
            "rut",
            "operation_mode",
            "is_active",
        ]
        read_only_fields = ["id", "erp_tenant_id", "erp_company_id", "operation_mode", "is_active"]


class TaxServiceProfileSerializer(serializers.ModelSerializer):
    certificate_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = TaxServiceProfile
        fields = [
            "sii_environment",
            "sii_rut",
            "sync_enabled",
            "poll_interval_minutes",
            "certificate_path",
            "certificate_password",
            "last_sync_at",
            "last_sync_status",
            "last_sync_error",
        ]
        read_only_fields = ["last_sync_at", "last_sync_status", "last_sync_error"]

    def update(self, instance, validated_data):
        certificate_password = validated_data.pop("certificate_password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if certificate_password:
            instance.certificate_password = certificate_password
        instance.save()
        return instance


class SIIAuthResponseSerializer(serializers.Serializer):
    authenticated = serializers.BooleanField()
    environment = serializers.CharField()
    host = serializers.CharField()
    seed = serializers.CharField()
    token_preview = serializers.CharField()
    seed_endpoint = serializers.CharField()
    token_endpoint = serializers.CharField()
