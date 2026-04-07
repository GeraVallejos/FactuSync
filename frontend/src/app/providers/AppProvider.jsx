import { createContext, useContext, useEffect, useState } from "react";
import { useSessionState } from "@features/auth/hooks";
import { useWorkspaceState } from "@features/dashboard/hooks";

const AuthContext = createContext(null);
const WorkspaceContext = createContext(null);

export function AppProvider({ children }) {
  const [busy, setBusy] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const workspace = useWorkspaceState({ setBusy, setFeedback });
  const auth = useSessionState({
    loadWorkspace: workspace.loadWorkspace,
    resetWorkspace: workspace.resetWorkspace,
    setBusy,
    setFeedback,
    setInitialized,
  });

  useEffect(() => {
    auth.loadApp();
  }, []);

  useEffect(() => {
    if (!feedback) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setFeedback(null);
    }, 4000);

    return () => window.clearTimeout(timeoutId);
  }, [feedback]);

  const authValue = {
    busy,
    feedback,
    initialized,
    isAuthenticated: auth.isAuthenticated,
    login: auth.login,
    logout: auth.logout,
    session: auth.session,
  };

  const workspaceValue = {
    activeDocumentId: workspace.activeDocumentId,
    busy,
    dashboard: workspace.dashboard,
    documents: workspace.documents,
    feedback,
    importDocument: (file) => workspace.importDocument(file, { reloadApp: auth.loadApp }),
    profileForm: workspace.profileForm,
    reprocessDocument: (document) => workspace.reprocessDocument(document, { reloadApp: auth.loadApp }),
    saveSettings: (payload) => workspace.saveSettings(payload, { reloadApp: auth.loadApp }),
    syncSii: () => workspace.syncSii({ reloadApp: auth.loadApp }),
    tenantForm: workspace.tenantForm,
    testAuth: (payload) => workspace.testAuth(payload, { reloadApp: auth.loadApp }),
  };

  return (
    <AuthContext.Provider value={authValue}>
      <WorkspaceContext.Provider value={workspaceValue}>{children}</WorkspaceContext.Provider>
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuthContext must be used within AppProvider");
  }

  return context;
}

export function useWorkspaceContext() {
  const context = useContext(WorkspaceContext);

  if (!context) {
    throw new Error("useWorkspaceContext must be used within AppProvider");
  }

  return context;
}
