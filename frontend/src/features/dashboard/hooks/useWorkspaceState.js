import { useState } from "react";
import { mapDashboard, mapDocuments, mapTaxProfileForm, mapTenantForm } from "@features/dashboard/mappers";
import { facturaSiiApi as api } from "@services/api";
import { initialProfileForm, initialTenantForm } from "@shared/constants";
import { buildFeedback } from "@shared/lib";

export function useWorkspaceState({ setBusy, setFeedback }) {
  const [dashboard, setDashboard] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [tenantForm, setTenantForm] = useState(initialTenantForm);
  const [profileForm, setProfileForm] = useState(initialProfileForm);
  const [activeDocumentId, setActiveDocumentId] = useState("");

  function resetWorkspace() {
    setDashboard(null);
    setDocuments([]);
    setTenantForm(initialTenantForm);
    setProfileForm(initialProfileForm);
    setActiveDocumentId("");
  }

  async function loadWorkspace() {
    const [dashboardPayload, documentPayload, tenantPayload, taxProfilePayload] = await Promise.all([
      api.dashboard(),
      api.documents(),
      api.currentTenant(),
      api.currentTaxProfile(),
    ]);

    setDashboard(mapDashboard(dashboardPayload));
    setDocuments(mapDocuments(documentPayload));
    setTenantForm(mapTenantForm(tenantPayload));
    setProfileForm(mapTaxProfileForm(taxProfilePayload));
  }

  async function importDocument(file, { reloadApp }) {
    setBusy(true);
    setFeedback(null);

    try {
      const payload = await api.importXml(file);
      const importedDocument = mapDocuments([payload])[0];
      setFeedback(buildFeedback(`Documento ${importedDocument.statusLabel} correctamente.`, "success"));
      await reloadApp({ clearFeedback: false });
    } catch (error) {
      setFeedback(buildFeedback(error.message, "error"));
      setBusy(false);
    }
  }

  async function reprocessDocument(document, { reloadApp }) {
    setBusy(true);
    setActiveDocumentId(document.id);
    setFeedback(null);

    try {
      const payload = await api.reprocessDocument(document.id);
      const nextStatusLabel = mapDocuments([payload])[0]?.statusLabel || payload.status;
      setFeedback(
        buildFeedback(
          payload.queued
            ? `Documento ${document.referenceLabel || document.id} reenviado a la cola correctamente.`
            : `Documento ${document.referenceLabel || document.id} reprocesado con estado ${nextStatusLabel}.`,
          "success",
        ),
      );
      await reloadApp({ clearFeedback: false });
    } catch (error) {
      setFeedback(buildFeedback(error.message, "error"));
      setBusy(false);
    } finally {
      setActiveDocumentId("");
    }
  }

  async function deleteDocument(document, { reloadApp }) {
    setBusy(true);
    setActiveDocumentId(document.id);
    setFeedback(null);

    try {
      await api.deleteDocument(document.id);
      setFeedback(
        buildFeedback(`Documento ${document.referenceLabel || document.id} eliminado correctamente.`, "success"),
      );
      await reloadApp({ clearFeedback: false });
    } catch (error) {
      setFeedback(buildFeedback(error.message, "error"));
      setBusy(false);
    } finally {
      setActiveDocumentId("");
    }
  }

  async function syncSii({ reloadApp }) {
    setBusy(true);
    setFeedback(null);

    try {
      await api.syncSii();
      setFeedback(buildFeedback("La sincronización con SII quedó encolada correctamente.", "success"));
      await reloadApp({ clearFeedback: false });
    } catch (error) {
      setFeedback(buildFeedback(error.message, "error"));
      setBusy(false);
    }
  }

  async function saveSettings(payload, { reloadApp }) {
    setBusy(true);
    setFeedback(null);

    try {
      await Promise.all([api.updateCurrentTenant(payload.tenantForm), api.updateCurrentTaxProfile(payload.profileForm)]);
      setFeedback(buildFeedback("La configuración se actualizó correctamente.", "success"));
      await reloadApp({ clearFeedback: false });
    } catch (error) {
      setFeedback(buildFeedback(error.message, "error"));
      setBusy(false);
    }
  }

  async function testAuth(payload, { reloadApp }) {
    setBusy(true);
    setFeedback(null);

    try {
      await api.updateCurrentTaxProfile(payload.profileForm);
      const authResult = await api.testSiiAuth();
      setFeedback(
        buildFeedback(
          `SII autenticado en ${authResult.environment} (${authResult.host}) con token ${authResult.token_preview}.`,
          "success",
        ),
      );
      await reloadApp({ clearFeedback: false });
    } catch (error) {
      setFeedback(buildFeedback(error.message, "error"));
      setBusy(false);
    }
  }

  return {
    activeDocumentId,
    dashboard,
    deleteDocument,
    documents,
    importDocument,
    loadWorkspace,
    profileForm,
    reprocessDocument,
    resetWorkspace,
    saveSettings,
    syncSii,
    tenantForm,
    testAuth,
  };
}
