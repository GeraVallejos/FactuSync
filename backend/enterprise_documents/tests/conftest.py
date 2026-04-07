from __future__ import annotations

from pathlib import Path
import shutil

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from enterprise_documents.models import Tenant, TenantMembership


TEST_STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "testsuite"
SAMPLE_XML_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_dte.xml"


@pytest.fixture(autouse=True)
def isolated_storage(settings):
    settings.STORAGE_ROOT = TEST_STORAGE_ROOT
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    shutil.rmtree(TEST_STORAGE_ROOT, ignore_errors=True)
    TEST_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    yield TEST_STORAGE_ROOT
    shutil.rmtree(TEST_STORAGE_ROOT, ignore_errors=True)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant_headers():
    return {
        "HTTP_X_TENANT_ID": "demo-test",
        "HTTP_X_ACTOR": "tester@example.com",
    }


@pytest.fixture
def second_tenant_headers():
    return {
        "HTTP_X_TENANT_ID": "other-tenant",
        "HTTP_X_ACTOR": "other@example.com",
    }


@pytest.fixture
def sample_xml_path():
    return SAMPLE_XML_PATH


@pytest.fixture
def invalid_xml_bytes():
    return b"<DTE><Documento><Encabezado></Documento>"


@pytest.fixture
def standalone_user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="standalone",
        email="standalone@example.com",
        password="secret123",
    )


@pytest.fixture
def standalone_tenant(db):
    return Tenant.objects.create(
        code="standalone-main",
        name="Mi Empresa SPA",
        rut="76111111-1",
        operation_mode=Tenant.OperationMode.STANDALONE,
    )


@pytest.fixture
def standalone_membership(db, standalone_user, standalone_tenant):
    return TenantMembership.objects.create(
        user=standalone_user,
        tenant=standalone_tenant,
        role=TenantMembership.Role.OWNER,
        is_default=True,
    )


@pytest.fixture
def superuser(db):
    user_model = get_user_model()
    return user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="secret123",
    )
