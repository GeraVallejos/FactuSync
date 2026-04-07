import { documentTypeLabel, initialProfileForm, initialTenantForm, sourceLabel, statusLabel } from "@shared/constants";
import { formatCurrency, formatFallback, joinMessages } from "@shared/lib";

/**
 * @typedef {Object} DashboardModel
 * @property {number} totalDocuments
 * @property {number} errorRate
 * @property {unknown} raw
 */

/**
 * @typedef {Object} DocumentModel
 * @property {string|number} id
 * @property {string} referenceLabel
 * @property {string} title
 * @property {string} sourceLabel
 * @property {string} issuerRut
 * @property {string} receiverRut
 * @property {string} amountLabel
 * @property {string} status
 * @property {string} statusLabel
 * @property {boolean} canReprocess
 * @property {boolean} hasPdf
 * @property {boolean} hasErrorDetail
 * @property {string} errorDetail
 * @property {unknown} raw
 */

/**
 * @param {any} payload
 * @returns {DashboardModel}
 */
export function mapDashboard(payload) {
  return {
    totalDocuments: Number(payload?.total_documents ?? 0),
    errorRate: Number(payload?.error_rate ?? 0),
    raw: payload,
  };
}

export function mapDocument(payload) {
  const id = formatFallback(payload?.id, "");
  const status = formatFallback(payload?.status, "recibido");
  const documentType = formatFallback(payload?.document_type, "DTE");
  const errorDetail = formatFallback(payload?.last_error, joinMessages(payload?.validation_errors, ""));
  const friendlyDocumentType = documentTypeLabel[documentType] || "Documento tributario";
  const friendlySource = sourceLabel[payload?.source] || "Origen desconocido";

  return {
    id,
    referenceLabel: formatFallback(payload?.folio, id),
    title: `${friendlyDocumentType} ${formatFallback(payload?.folio, "Sin folio")}`,
    sourceLabel: `${friendlySource} - v${formatFallback(payload?.version, "1")}`,
    issuerRut: formatFallback(payload?.issuer_rut, "Sin emisor"),
    receiverRut: formatFallback(payload?.receiver_rut, "Sin receptor"),
    amountLabel: formatCurrency(payload?.total_amount),
    status,
    statusLabel: statusLabel[status] || status,
    canReprocess: status === "en_cola" || status === "con_error",
    hasPdf: Boolean(payload?.pdf_storage_path) || status === "pdf_generado",
    hasErrorDetail: status === "con_error" && Boolean(errorDetail),
    errorDetail,
    raw: payload,
  };
}

/**
 * @param {any[]} payload
 * @returns {DocumentModel[]}
 */
export function mapDocuments(payload) {
  if (!Array.isArray(payload)) {
    return [];
  }

  return payload.map(mapDocument);
}

export function mapTenantForm(payload) {
  return {
    name: formatFallback(payload?.name, initialTenantForm.name),
    rut: formatFallback(payload?.rut, initialTenantForm.rut),
  };
}

export function mapTaxProfileForm(payload) {
  return {
    sii_environment: formatFallback(payload?.sii_environment, initialProfileForm.sii_environment),
    sii_rut: formatFallback(payload?.sii_rut, initialProfileForm.sii_rut),
    sync_enabled: Boolean(payload?.sync_enabled),
    poll_interval_minutes: Number(payload?.poll_interval_minutes || initialProfileForm.poll_interval_minutes),
    certificate_path: formatFallback(payload?.certificate_path, initialProfileForm.certificate_path),
    certificate_password: "",
  };
}
