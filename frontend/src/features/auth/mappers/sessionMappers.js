import { formatFallback } from "@shared/lib";

/**
 * @typedef {Object} SessionModel
 * @property {Array<unknown>} memberships
 * @property {{ tenantCode: string, operationMode: string, tenantName: string }} primaryMembership
 * @property {unknown} raw
 */

/**
 * @param {any} payload
 * @returns {SessionModel}
 */
export function mapSession(payload) {
  const memberships = Array.isArray(payload?.memberships) ? payload.memberships : [];
  const primaryMembership = memberships[0] || null;

  return {
    memberships,
    primaryMembership: primaryMembership
      ? {
          tenantCode: formatFallback(primaryMembership.tenant_code, ""),
          operationMode: formatFallback(primaryMembership.operation_mode, "standalone"),
          tenantName: formatFallback(primaryMembership.tenant_name, "Sin empresa"),
        }
      : {
          tenantCode: "",
          operationMode: "standalone",
          tenantName: "Sin empresa",
        },
    raw: payload,
  };
}
