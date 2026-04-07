import { describe, expect, it } from "vitest";
import {
  mapDashboard,
  mapDocument,
  mapDocuments,
  mapTaxProfileForm,
  mapTenantForm,
} from "./workspaceMappers";

describe("workspace mappers", () => {
  it("maps dashboard metrics in the happy path", () => {
    expect(
      mapDashboard({
        total_documents: "12",
        error_rate: "25",
      }),
    ).toMatchObject({
      totalDocuments: 12,
      errorRate: 25,
    });
  });

  it("maps a processed document to friendly labels", () => {
    const document = mapDocument({
      id: "doc-1",
      folio: "564",
      document_type: "33",
      source: "manual_xml",
      issuer_rut: "76111111-1",
      receiver_rut: "76999999-9",
      total_amount: 195160,
      status: "pdf_generado",
      version: 3,
      pdf_storage_path: "/tmp/doc.pdf",
    });

    expect(document).toMatchObject({
      id: "doc-1",
      referenceLabel: "564",
      title: "Factura afecta (33) 564",
      sourceLabel: "Carga manual - v3",
      issuerRut: "76111111-1",
      receiverRut: "76999999-9",
      status: "pdf_generado",
      statusLabel: "PDF generado",
      canReprocess: false,
      hasPdf: true,
      hasErrorDetail: false,
    });
    expect(document.amountLabel).toContain("$");
  });

  it("handles border cases for error documents and invalid collections", () => {
    const errored = mapDocument({
      id: "doc-2",
      status: "con_error",
      validation_errors: ["XML invalido", "Falta folio"],
    });

    expect(errored.hasErrorDetail).toBe(true);
    expect(errored.errorDetail).toBe("XML invalido; Falta folio");
    expect(mapDocuments(null)).toEqual([]);
  });

  it("maps forms with safe defaults", () => {
    expect(mapTenantForm({})).toEqual({
      name: "",
      rut: "",
    });

    expect(
      mapTaxProfileForm({
        sii_environment: "produccion",
        sii_rut: "76111111-1",
        sync_enabled: true,
        poll_interval_minutes: "10",
        certificate_path: "/certs/demo.pfx",
      }),
    ).toEqual({
      sii_environment: "produccion",
      sii_rut: "76111111-1",
      sync_enabled: true,
      poll_interval_minutes: 10,
      certificate_path: "/certs/demo.pfx",
      certificate_password: "",
    });
  });
});
