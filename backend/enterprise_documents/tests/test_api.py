from __future__ import annotations

from pathlib import Path
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from enterprise_documents.models import AuditEvent, DocumentRecord, TaxServiceProfile, Tenant
from enterprise_documents.dte.models import DTEModel, LineItem, Party, Totals
from enterprise_documents.dte.validators import DTEValidator
from enterprise_documents.pdf_renderer import PDFRenderer
from enterprise_documents.services import DocumentService
from enterprise_documents.sii import SIIAuthResult, SIIConfigurationError


def import_sample(api_client, tenant_headers, sample_xml_path):
    with sample_xml_path.open("rb") as xml_file:
        return api_client.post(
            "/api/documentos/importar",
            {"file": xml_file},
            format="multipart",
            **tenant_headers,
        )


@pytest.mark.django_db(transaction=True)
def test_health_endpoint_returns_ok(api_client):
    response = api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db(transaction=True)
def test_import_xml_creates_tenant_document_audit_and_pdf(api_client, tenant_headers, sample_xml_path):
    response = import_sample(api_client, tenant_headers, sample_xml_path)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pdf_generado"
    assert payload["duplicated"] is False
    assert payload["queued"] is False
    assert payload["validation_errors"] == []

    tenant = Tenant.objects.get(code="demo-test")
    document = DocumentRecord.objects.get(pk=payload["id"])
    assert document.tenant == tenant
    assert document.document_type == "33"
    assert document.folio == "1001"
    assert str(document.total_amount) == "11900.00"
    assert Path(document.xml_storage_path).exists()
    assert Path(document.pdf_storage_path).exists()
    assert AuditEvent.objects.filter(document=document).count() >= 3


@pytest.mark.django_db(transaction=True)
def test_import_same_xml_is_idempotent(api_client, tenant_headers, sample_xml_path):
    first = import_sample(api_client, tenant_headers, sample_xml_path).json()
    second = import_sample(api_client, tenant_headers, sample_xml_path).json()

    assert first["duplicated"] is False
    assert second["duplicated"] is True
    assert DocumentRecord.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_document_endpoints_return_detail_audit_and_binary_files(api_client, tenant_headers, sample_xml_path):
    payload = import_sample(api_client, tenant_headers, sample_xml_path).json()
    document_id = payload["id"]

    detail_response = api_client.get(f"/api/documentos/{document_id}", **tenant_headers)
    audit_response = api_client.get(f"/api/documentos/{document_id}/audit", **tenant_headers)
    xml_response = api_client.get(f"/api/documentos/{document_id}/xml", **tenant_headers)
    pdf_response = api_client.get(f"/api/documentos/{document_id}/pdf", **tenant_headers)

    assert detail_response.status_code == 200
    assert detail_response.json()["folio"] == "1001"
    assert audit_response.status_code == 200
    assert len(audit_response.json()) >= 3
    assert xml_response.status_code == 200
    assert xml_response["Content-Type"] == "application/xml"
    assert pdf_response.status_code == 200
    assert pdf_response["Content-Type"] == "application/pdf"
    xml_response.close()
    pdf_response.close()


@pytest.mark.django_db(transaction=True)
def test_dashboard_and_reprocess_flow(api_client, tenant_headers, sample_xml_path):
    payload = import_sample(api_client, tenant_headers, sample_xml_path).json()
    document_id = payload["id"]

    reprocess_response = api_client.post(f"/api/documentos/{document_id}/reprocesar", **tenant_headers)
    dashboard_response = api_client.get("/api/dashboard", **tenant_headers)

    assert reprocess_response.status_code == 200
    assert reprocess_response.json()["status"] == "pdf_generado"
    document = DocumentRecord.objects.get(pk=document_id)
    assert document.version == 2
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["total_documents"] == 1


@pytest.mark.django_db(transaction=True)
def test_document_can_be_deleted_and_assets_are_removed(api_client, tenant_headers, sample_xml_path):
    payload = import_sample(api_client, tenant_headers, sample_xml_path).json()
    document = DocumentRecord.objects.get(pk=payload["id"])
    xml_path = Path(document.xml_storage_path)
    pdf_path = Path(document.pdf_storage_path)

    delete_response = api_client.delete(f"/api/documentos/{document.id}", **tenant_headers)
    list_response = api_client.get("/api/documentos", **tenant_headers)
    dashboard_response = api_client.get("/api/dashboard", **tenant_headers)

    assert delete_response.status_code == 204
    assert DocumentRecord.objects.filter(pk=document.id).exists() is False
    assert xml_path.exists() is False
    assert pdf_path.exists() is False
    assert list_response.status_code == 200
    assert list_response.json() == []
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["total_documents"] == 0


@pytest.mark.django_db(transaction=True)
def test_invalid_xml_returns_error_status(api_client, tenant_headers, invalid_xml_bytes):
    invalid_file = SimpleUploadedFile("broken.xml", invalid_xml_bytes, content_type="application/xml")
    response = api_client.post(
        "/api/documentos/importar",
        {"file": invalid_file},
        format="multipart",
        **tenant_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "con_error"
    assert payload["duplicated"] is False
    assert payload["validation_errors"]
    document = DocumentRecord.objects.get(pk=payload["id"])
    assert document.status == "con_error"
    assert document.last_error


@pytest.mark.django_db(transaction=True)
def test_document_isolated_by_tenant(api_client, tenant_headers, second_tenant_headers, sample_xml_path):
    payload = import_sample(api_client, tenant_headers, sample_xml_path).json()
    document_id = payload["id"]

    foreign_response = api_client.get(f"/api/documentos/{document_id}", **second_tenant_headers)
    own_response = api_client.get(f"/api/documentos/{document_id}", **tenant_headers)

    assert own_response.status_code == 200
    assert foreign_response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_import_accepts_erp_context_headers(api_client, sample_xml_path):
    headers = {
        "HTTP_X_ERP_TENANT_ID": "erp-tenant-1",
        "HTTP_X_ERP_COMPANY_ID": "company-001",
        "HTTP_X_ACTOR": "erp-service",
    }
    payload = import_sample(api_client, headers, sample_xml_path).json()

    tenant = Tenant.objects.get(erp_company_id="company-001")
    assert payload["status"] == "pdf_generado"
    assert tenant.erp_tenant_id == "erp-tenant-1"


@pytest.mark.django_db(transaction=True)
def test_jwt_http_only_login_and_me(api_client, standalone_user, standalone_membership):
    response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )

    assert response.status_code == 200
    assert "facturasii_access" in response.cookies
    assert response.cookies["facturasii_access"]["httponly"]
    me_response = api_client.get("/api/auth/me")
    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["username"] == "standalone"
    assert len(payload["memberships"]) == 1
    assert payload["memberships"][0]["tenant_code"] == "standalone-main"


@pytest.mark.django_db(transaction=True)
def test_standalone_user_can_use_document_api_without_headers(
    api_client,
    standalone_user,
    standalone_membership,
    sample_xml_path,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    with sample_xml_path.open("rb") as xml_file:
        import_response = api_client.post(
            "/api/documentos/importar",
            {"file": xml_file},
            format="multipart",
        )

    assert import_response.status_code == 200
    payload = import_response.json()
    document = DocumentRecord.objects.get(pk=payload["id"])
    assert document.tenant.code == "standalone-main"


@pytest.mark.django_db(transaction=True)
def test_standalone_user_can_download_pdf_with_tenant_query_param(
    api_client,
    standalone_user,
    standalone_membership,
    sample_xml_path,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    with sample_xml_path.open("rb") as xml_file:
        import_response = api_client.post(
            "/api/documentos/importar",
            {"file": xml_file},
            format="multipart",
        )

    document_id = import_response.json()["id"]
    pdf_response = api_client.get(f"/api/documentos/{document_id}/pdf?tenant=standalone-main")

    assert pdf_response.status_code == 200
    assert pdf_response["Content-Type"] == "application/pdf"
    pdf_response.close()


@pytest.mark.django_db(transaction=True)
def test_logout_clears_session_cookies(api_client, standalone_user, standalone_membership):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    logout_response = api_client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    me_response = api_client.get("/api/auth/me")
    assert me_response.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_logout_still_clears_cookies_when_access_cookie_is_invalid(
    api_client,
    standalone_user,
    standalone_membership,
    settings,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    api_client.cookies[settings.JWT_ACCESS_COOKIE_NAME] = "expired-or-invalid-token"

    logout_response = api_client.post("/api/auth/logout")

    assert logout_response.status_code == 200
    assert logout_response.json()["logged_out"] is True
    assert logout_response.cookies[settings.JWT_ACCESS_COOKIE_NAME].value == ""
    assert logout_response.cookies[settings.JWT_REFRESH_COOKIE_NAME].value == ""


@pytest.mark.django_db(transaction=True)
def test_standalone_can_read_and_update_current_tenant_and_tax_profile(
    api_client,
    standalone_user,
    standalone_membership,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    tenant_response = api_client.get("/api/me/tenant")
    profile_response = api_client.get("/api/me/tax-profile")
    assert tenant_response.status_code == 200
    assert profile_response.status_code == 200

    update_tenant = api_client.patch(
        "/api/me/tenant",
        {"name": "Mi Empresa Editada", "rut": "76999999-9"},
        format="json",
    )
    update_profile = api_client.patch(
        "/api/me/tax-profile",
        {
            "sii_environment": "certificacion",
            "sii_rut": "76999999-9",
            "sync_enabled": True,
            "poll_interval_minutes": 10,
        },
        format="json",
    )

    assert update_tenant.status_code == 200
    assert update_tenant.json()["name"] == "Mi Empresa Editada"
    assert update_profile.status_code == 200
    assert update_profile.json()["sync_enabled"] is True


@pytest.mark.django_db(transaction=True)
def test_tax_profile_hides_certificate_password_and_stores_it_encrypted(
    api_client,
    standalone_user,
    standalone_membership,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    update_profile = api_client.patch(
        "/api/me/tax-profile",
        {
            "certificate_path": "C:\\certificados\\empresa.pfx",
            "certificate_password": "clave-super-secreta",
        },
        format="json",
    )

    assert update_profile.status_code == 200
    assert "certificate_password" not in update_profile.json()
    profile = TaxServiceProfile.objects.get(tenant=standalone_membership.tenant)
    assert profile.certificate_path == "C:\\certificados\\empresa.pfx"
    assert profile.certificate_password_encrypted
    assert profile.certificate_password_encrypted != "clave-super-secreta"
    assert profile.certificate_password == "clave-super-secreta"


@pytest.mark.django_db(transaction=True)
def test_sii_test_auth_endpoint_returns_auth_metadata(
    api_client,
    standalone_user,
    standalone_membership,
    monkeypatch,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    def fake_authenticate(self, profile):
        return SIIAuthResult(
            environment="certificacion",
            host="maullin.sii.cl",
            seed="123456",
            token="ABCD1234TOKEN9876",
            seed_endpoint="https://maullin.sii.cl/DTEWS/CrSeed.jws",
            token_endpoint="https://maullin.sii.cl/DTEWS/GetTokenFromSeed.jws",
        )

    monkeypatch.setattr(DocumentService, "_authenticate_sii", fake_authenticate)

    response = api_client.post("/api/sii/test-auth")

    assert response.status_code == 200
    payload = response.json()
    assert payload["authenticated"] is True
    assert payload["host"] == "maullin.sii.cl"
    assert payload["token_preview"] == "ABCD...9876"
    assert AuditEvent.objects.filter(
        tenant=standalone_membership.tenant,
        event_type="sii_auth_ok",
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_sii_test_auth_returns_400_on_configuration_error(
    api_client,
    standalone_user,
    standalone_membership,
    monkeypatch,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    def fake_authenticate(self, profile):
        raise SIIConfigurationError("Falta certificado.")

    monkeypatch.setattr(DocumentService, "_authenticate_sii", fake_authenticate)

    response = api_client.post("/api/sii/test-auth")

    assert response.status_code == 400
    assert response.json()["detail"] == "Falta certificado."


@pytest.mark.django_db(transaction=True)
def test_sii_sync_endpoint_runs_auth_flow_when_celery_is_eager(
    api_client,
    standalone_user,
    standalone_membership,
    monkeypatch,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    profile = TaxServiceProfile.objects.create(
        tenant=standalone_membership.tenant,
        sii_rut="76999999-9",
        sync_enabled=True,
    )

    def fake_authenticate(self, current_profile):
        assert current_profile.id == profile.id
        return SIIAuthResult(
            environment="certificacion",
            host="maullin.sii.cl",
            seed="654321",
            token="SYNC1234TOKEN8888",
            seed_endpoint="https://maullin.sii.cl/DTEWS/CrSeed.jws",
            token_endpoint="https://maullin.sii.cl/DTEWS/GetTokenFromSeed.jws",
        )

    monkeypatch.setattr(DocumentService, "_authenticate_sii", fake_authenticate)

    response = api_client.post("/api/sii/sync")

    assert response.status_code == 200
    profile.refresh_from_db()
    assert profile.last_sync_status == TaxServiceProfile.SyncStatus.IDLE
    assert profile.last_sync_error == ""
    assert AuditEvent.objects.filter(
        tenant=standalone_membership.tenant,
        event_type="sii_sync_autenticado",
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_import_falls_back_to_inline_processing_when_celery_dispatch_fails(
    api_client,
    tenant_headers,
    sample_xml_path,
    monkeypatch,
    settings,
):
    settings.CELERY_TASK_ALWAYS_EAGER = False
    settings.CELERY_FALLBACK_TO_SYNC_ON_ERROR = True

    def fail_delay(*args, **kwargs):
        raise RuntimeError("Retry limit exceeded while trying to reconnect")

    monkeypatch.setattr("enterprise_documents.tasks.process_document_task.delay", fail_delay)

    response = import_sample(api_client, tenant_headers, sample_xml_path)

    assert response.status_code == 200
    payload = response.json()
    assert payload["queued"] is False
    assert payload["status"] == "pdf_generado"
    document = DocumentRecord.objects.get(pk=payload["id"])
    assert document.status == "pdf_generado"


@pytest.mark.django_db(transaction=True)
def test_sii_sync_falls_back_to_inline_processing_when_celery_dispatch_fails(
    api_client,
    standalone_user,
    standalone_membership,
    monkeypatch,
    settings,
):
    settings.CELERY_TASK_ALWAYS_EAGER = False
    settings.CELERY_FALLBACK_TO_SYNC_ON_ERROR = True

    login_response = api_client.post(
        "/api/auth/login",
        {"username": standalone_user.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    TaxServiceProfile.objects.create(
        tenant=standalone_membership.tenant,
        sii_rut="76999999-9",
        sync_enabled=True,
    )

    def fail_delay(*args, **kwargs):
        raise RuntimeError("Retry limit exceeded while trying to reconnect")

    def fake_authenticate(self, current_profile):
        return SIIAuthResult(
            environment="certificacion",
            host="maullin.sii.cl",
            seed="654321",
            token="SYNC1234TOKEN8888",
            seed_endpoint="https://maullin.sii.cl/DTEWS/CrSeed.jws",
            token_endpoint="https://maullin.sii.cl/DTEWS/GetTokenFromSeed.jws",
        )

    monkeypatch.setattr("enterprise_documents.tasks.sync_sii_profile_task.delay", fail_delay)
    monkeypatch.setattr(DocumentService, "_authenticate_sii", fake_authenticate)

    response = api_client.post("/api/sii/sync")

    assert response.status_code == 200
    payload = response.json()
    assert payload["queued"] is False
    assert payload["fallback_sync"] is True
    assert AuditEvent.objects.filter(
        tenant=standalone_membership.tenant,
        event_type="sii_sync_autenticado",
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_superuser_can_resolve_current_tenant_without_membership(
    api_client,
    superuser,
    standalone_tenant,
):
    login_response = api_client.post(
        "/api/auth/login",
        {"username": superuser.username, "password": "secret123"},
        format="json",
    )
    assert login_response.status_code == 200

    tenant_response = api_client.get("/api/me/tenant")
    profile_response = api_client.get("/api/me/tax-profile")

    assert tenant_response.status_code == 200
    assert tenant_response.json()["code"] == standalone_tenant.code
    assert profile_response.status_code == 200
    assert profile_response.json()["sii_rut"] == standalone_tenant.rut


def test_validator_allows_real_world_totals_with_extra_components():
    document = DTEModel(
        document_type="33",
        folio="2044306",
        issue_date="2026-04-06",
        issuer=Party(rut="89005900-7"),
        receiver=Party(rut="76909655-8"),
        totals=Totals(
            net_amount=Decimal("52266"),
            exempt_amount=Decimal("0"),
            vat_amount=Decimal("9930"),
            total_amount=Decimal("82014"),
        ),
        line_items=[
            LineItem(
                line_number=1,
                description="Servicio",
                quantity=Decimal("1"),
                unit_price=Decimal("52266"),
                line_amount=Decimal("52266"),
            )
        ],
    )

    errors = DTEValidator().validate(document)

    assert errors == []


def test_pdf_renderer_builds_structured_invoice_and_adds_pages_for_long_documents():
    document = DTEModel(
        document_type="33",
        folio="564",
        issue_date="2026-04-07",
        issuer=Party(
            rut="76111111-1",
            name="Comercial Demo SPA",
            giro="Servicios tecnológicos",
            address="Av. Principal 1234",
            commune="Providencia",
            city="Santiago",
        ),
        receiver=Party(
            rut="76999999-9",
            name="Cliente de Ejemplo Limitada",
            giro="Administración",
            address="Los Alerces 778",
            commune="Las Condes",
            city="Santiago",
        ),
        totals=Totals(
            net_amount=Decimal("125000"),
            exempt_amount=Decimal("0"),
            vat_amount=Decimal("23750"),
            total_amount=Decimal("148750"),
        ),
        line_items=[
            LineItem(
                line_number=index + 1,
                description=f"Servicio mensual de soporte y operación tributaria para sucursal {index + 1}",
                quantity=Decimal("1"),
                unit_price=Decimal("5000"),
                line_amount=Decimal("5000"),
            )
            for index in range(32)
        ],
    )

    pdf_bytes = PDFRenderer().render(document, brand_name="ValCri ERP", brand_color="#0F5B3F")
    pdf_text = pdf_bytes.decode("latin-1", errors="ignore")

    assert "FACTURA ELECTRONICA" in pdf_text
    assert "DETALLE DEL DOCUMENTO" in pdf_text
    assert "RESUMEN DE TOTALES" in pdf_text
    assert "Cliente de Ejemplo Limitada" in pdf_text
    assert pdf_text.count("/Type /Page ") >= 2
