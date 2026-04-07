from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.auth import logout
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from enterprise_documents.models import DocumentRecord
from enterprise_documents.serializers import (
    AuditEventSerializer,
    DashboardSerializer,
    DocumentImportResponseSerializer,
    DocumentRecordSerializer,
    LoginSerializer,
    SIIAuthResponseSerializer,
    SessionSerializer,
    TaxServiceProfileSerializer,
    TenantSerializer,
)
from enterprise_documents.auth_tokens import TokenType, build_token, decode_token
from enterprise_documents.services import DocumentService
from enterprise_documents.sii import SIIAuthError, SIIClientError, SIIConfigurationError
import jwt


class TenantScopedAPIView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @property
    def service(self) -> DocumentService:
        return DocumentService()

    def get_tenant(self, request):
        tenant_code = request.headers.get("X-Tenant-Id")
        erp_tenant_id = request.headers.get("X-ERP-Tenant-Id")
        erp_company_id = request.headers.get("X-ERP-Company-Id")
        return self.service.resolve_tenant(
            user=request.user,
            tenant_code=tenant_code,
            erp_tenant_id=erp_tenant_id,
            erp_company_id=erp_company_id,
        )

    def get_actor(self, request) -> str:
        return request.headers.get("X-Actor", "system")


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = DocumentService()
        user = service.authenticate_user(serializer.validated_data["username"], serializer.validated_data["password"])
        if user is None:
            return Response({"detail": "Credenciales invalidas."}, status=status.HTTP_401_UNAUTHORIZED)

        payload = service.session_payload(user)
        response = Response(SessionSerializer(payload).data, status=status.HTTP_200_OK)
        _set_auth_cookies(response, user.id)
        return response


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not raw_refresh:
            return Response({"detail": "Refresh token requerido."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = decode_token(raw_refresh, TokenType.REFRESH)
        except jwt.InvalidTokenError:
            return Response({"detail": "Refresh token invalido."}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({"refreshed": True}, status=status.HTTP_200_OK)
        _set_auth_cookies(response, int(payload["sub"]))
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        response = Response({"logged_out": True}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME)
        response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = DocumentService().session_payload(request.user)
        return Response(SessionSerializer(payload).data)


class CurrentTenantView(TenantScopedAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response({"detail": "Tenant no resuelto."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TenantSerializer(tenant).data)

    def patch(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response({"detail": "Tenant no resuelto."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = TenantSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CurrentTaxProfileView(TenantScopedAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response({"detail": "Tenant no resuelto."}, status=status.HTTP_400_BAD_REQUEST)
        profile = self.service.get_or_create_tax_profile(tenant)
        return Response(TaxServiceProfileSerializer(profile).data)

    def patch(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response({"detail": "Tenant no resuelto."}, status=status.HTTP_400_BAD_REQUEST)
        profile = self.service.get_or_create_tax_profile(tenant)
        serializer = TaxServiceProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DocumentImportView(TenantScopedAPIView):
    def post(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        upload = request.FILES.get("file")
        if upload is None or not upload.name.lower().endswith(".xml"):
            return Response({"detail": "Solo se aceptan archivos XML."}, status=status.HTTP_400_BAD_REQUEST)
        payload = self.service.ingest_xml(tenant, upload.read(), DocumentRecord.Source.MANUAL_XML, self.get_actor(request))
        response_status = status.HTTP_202_ACCEPTED if payload.get("queued") and not payload.get("duplicated") else status.HTTP_200_OK
        return Response(DocumentImportResponseSerializer(payload).data, status=response_status)


class DocumentListView(TenantScopedAPIView):
    def get(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        documents = self.service.list_documents(
            tenant,
            {
                "status": request.query_params.get("status"),
                "document_type": request.query_params.get("document_type"),
                "issuer_rut": request.query_params.get("issuer_rut"),
                "receiver_rut": request.query_params.get("receiver_rut"),
                "issue_date": request.query_params.get("issue_date"),
            },
        )
        return Response(DocumentRecordSerializer(documents, many=True).data)


class DocumentDetailView(TenantScopedAPIView):
    def get(self, request, document_id: str):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            document = self.service.get_document(tenant, document_id)
        except DocumentRecord.DoesNotExist:
            return Response({"detail": "Documento no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(DocumentRecordSerializer(document).data)


class DocumentPDFView(TenantScopedAPIView):
    def get(self, request, document_id: str):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            document = self.service.get_document(tenant, document_id)
        except DocumentRecord.DoesNotExist as exc:
            raise Http404("Documento no encontrado.") from exc
        if not document.pdf_storage_path:
            raise Http404("PDF no disponible.")
        return FileResponse(open(Path(document.pdf_storage_path), "rb"), content_type="application/pdf")


class DocumentXMLView(TenantScopedAPIView):
    def get(self, request, document_id: str):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            document = self.service.get_document(tenant, document_id)
        except DocumentRecord.DoesNotExist as exc:
            raise Http404("Documento no encontrado.") from exc
        return FileResponse(open(Path(document.xml_storage_path), "rb"), content_type="application/xml")


class DocumentAuditView(TenantScopedAPIView):
    def get(self, request, document_id: str):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            document = self.service.get_document(tenant, document_id)
        except DocumentRecord.DoesNotExist:
            return Response({"detail": "Documento no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AuditEventSerializer(document.audit_events.all(), many=True).data)


class DocumentReprocessView(TenantScopedAPIView):
    def post(self, request, document_id: str):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            document = self.service.get_document(tenant, document_id)
        except DocumentRecord.DoesNotExist:
            return Response({"detail": "Documento no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        payload = self.service.reprocess_document(document, self.get_actor(request))
        response_status = status.HTTP_202_ACCEPTED if payload.get("queued") else status.HTTP_200_OK
        return Response(DocumentImportResponseSerializer(payload).data, status=response_status)


class DashboardView(TenantScopedAPIView):
    def get(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(DashboardSerializer(self.service.metrics(tenant)).data)


class SIISyncView(TenantScopedAPIView):
    def post(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "Debe enviar X-Tenant-Id o el contexto ERP (X-ERP-Tenant-Id/X-ERP-Company-Id)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        profile = getattr(tenant, "tax_profile", None)
        if profile is None:
            return Response({"detail": "Tenant sin perfil tributario configurado."}, status=status.HTTP_400_BAD_REQUEST)
        payload = self.service.enqueue_sii_sync(profile.id)
        response_status = status.HTTP_202_ACCEPTED if payload.get("queued") else status.HTTP_200_OK
        return Response(payload, status=response_status)


class SIITestAuthView(TenantScopedAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = self.get_tenant(request)
        if tenant is None:
            return Response({"detail": "Tenant no resuelto."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = self.service.test_sii_auth(tenant, self.get_actor(request))
        except SIIConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (SIIAuthError, SIIClientError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(SIIAuthResponseSerializer(payload).data, status=status.HTTP_200_OK)


def _set_auth_cookies(response, user_id: int) -> None:
    access_token = build_token(user_id, TokenType.ACCESS)
    refresh_token = build_token(user_id, TokenType.REFRESH)
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.JWT_COOKIE_SECURE,
        "samesite": settings.JWT_COOKIE_SAMESITE,
        "path": "/",
    }
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        access_token,
        max_age=settings.JWT_ACCESS_LIFETIME_SECONDS,
        **cookie_kwargs,
    )
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=settings.JWT_REFRESH_LIFETIME_SECONDS,
        **cookie_kwargs,
    )
