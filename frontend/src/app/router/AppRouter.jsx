import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useAuthContext } from "@app/providers";
import { FullScreenLoader } from "@shared/ui";

const LoginPage = lazy(() => import("@features/auth/pages/LoginPage").then((module) => ({ default: module.LoginPage })));
const DashboardPage = lazy(() =>
  import("@features/dashboard/pages/DashboardPage").then((module) => ({ default: module.DashboardPage })),
);
const DocumentsPage = lazy(() =>
  import("@features/dashboard/pages/DocumentsPage").then((module) => ({ default: module.DocumentsPage })),
);
const SettingsPage = lazy(() =>
  import("@features/dashboard/pages/SettingsPage").then((module) => ({ default: module.SettingsPage })),
);

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthContext();

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function PublicRoute({ children }) {
  const { isAuthenticated } = useAuthContext();

  return isAuthenticated ? <Navigate to="/" replace /> : children;
}

export function AppRouter() {
  const { initialized, busy } = useAuthContext();

  if (!initialized && busy) {
    return <FullScreenLoader />;
  }

  return (
    <BrowserRouter>
      <Suspense fallback={<FullScreenLoader />}>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/documentos" replace />} />
            <Route path="documentos" element={<DocumentsPage />} />
            <Route path="configuracion" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/documentos" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
