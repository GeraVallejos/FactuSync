import { getTenantContext, request } from "./client";

function buildDocumentUrl(path) {
  const { tenantCode } = getTenantContext();
  if (!tenantCode) {
    return path;
  }

  const params = new URLSearchParams({ tenant: tenantCode });
  return `${path}?${params.toString()}`;
}

export const facturaSiiApi = {
  login: (username, password) =>
    request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  refresh: () =>
    request("/api/auth/refresh", {
      method: "POST",
      skipAuthRefresh: true,
    }),
  me: () => request("/api/auth/me"),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  currentTenant: () => request("/api/me/tenant"),
  updateCurrentTenant: (payload) =>
    request("/api/me/tenant", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  currentTaxProfile: () => request("/api/me/tax-profile"),
  updateCurrentTaxProfile: (payload) =>
    request("/api/me/tax-profile", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  testSiiAuth: () => request("/api/sii/test-auth", { method: "POST" }),
  dashboard: () => request("/api/dashboard"),
  documents: () => request("/api/documentos"),
  deleteDocument: (documentId) =>
    request(`/api/documentos/${documentId}`, {
      method: "DELETE",
    }),
  reprocessDocument: (documentId) =>
    request(`/api/documentos/${documentId}/reprocesar`, {
      method: "POST",
    }),
  documentPdfUrl: (documentId) => buildDocumentUrl(`/api/documentos/${documentId}/pdf`),
  documentXmlUrl: (documentId) => buildDocumentUrl(`/api/documentos/${documentId}/xml`),
  importXml: (file) => {
    const formData = new FormData();
    formData.append("file", file);

    return request("/api/documentos/importar", {
      method: "POST",
      body: formData,
    });
  },
  syncSii: () => request("/api/sii/sync", { method: "POST" }),
};
