from __future__ import annotations

from django.urls import path

from enterprise_documents.views import (
    DashboardView,
    CurrentTaxProfileView,
    CurrentTenantView,
    DocumentAuditView,
    DocumentDetailView,
    DocumentImportView,
    DocumentListView,
    DocumentPDFView,
    DocumentReprocessView,
    DocumentXMLView,
    HealthView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    SIISyncView,
    SIITestAuthView,
)


urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/refresh", RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/me", MeView.as_view(), name="auth-me"),
    path("me/tenant", CurrentTenantView.as_view(), name="current-tenant"),
    path("me/tax-profile", CurrentTaxProfileView.as_view(), name="current-tax-profile"),
    path("documentos/importar", DocumentImportView.as_view(), name="document-import"),
    path("documentos", DocumentListView.as_view(), name="document-list"),
    path("documentos/<uuid:document_id>", DocumentDetailView.as_view(), name="document-detail"),
    path("documentos/<uuid:document_id>/pdf", DocumentPDFView.as_view(), name="document-pdf"),
    path("documentos/<uuid:document_id>/xml", DocumentXMLView.as_view(), name="document-xml"),
    path("documentos/<uuid:document_id>/audit", DocumentAuditView.as_view(), name="document-audit"),
    path("documentos/<uuid:document_id>/reprocesar", DocumentReprocessView.as_view(), name="document-reprocess"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("sii/test-auth", SIITestAuthView.as_view(), name="sii-test-auth"),
    path("sii/sync", SIISyncView.as_view(), name="sii-sync"),
]
