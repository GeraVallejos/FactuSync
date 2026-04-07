import { useState } from "react";
import { mapSession } from "@features/auth/mappers";
import { facturaSiiApi as api, setTenantContext } from "@services/api";
import { buildFeedback } from "@shared/lib";

export function useSessionState({ setBusy, setFeedback, loadWorkspace, resetWorkspace, setInitialized }) {
  const [session, setSession] = useState(null);

  async function loadApp(options = {}) {
    const { clearFeedback = true } = options;

    setBusy(true);
    if (clearFeedback) {
      setFeedback(null);
    }

    try {
      const currentSession = await api.me();
      const mappedSession = mapSession(currentSession);
      setSession(mappedSession);
      setTenantContext({ tenantCode: mappedSession.primaryMembership?.tenantCode });
      await loadWorkspace();
    } catch {
      setSession(null);
      setTenantContext();
      resetWorkspace();
    } finally {
      setInitialized(true);
      setBusy(false);
    }
  }

  async function login(form) {
    setBusy(true);
    setFeedback(null);

    try {
      await api.login(form.username, form.password);
      await loadApp({ clearFeedback: false });
    } catch (error) {
      setFeedback(buildFeedback(error.message, "error"));
      setBusy(false);
    }
  }

  async function logout() {
    await api.logout();
    setSession(null);
    setTenantContext();
    resetWorkspace();
    setFeedback(null);
  }

  return {
    isAuthenticated: Boolean(session),
    loadApp,
    login,
    logout,
    session,
  };
}
