import { Outlet } from "react-router-dom";
import { useAuthContext, useWorkspaceContext } from "@app/providers";
import { DashboardHeader, DashboardTabs } from "@features/dashboard/components";

export function DashboardPage() {
  const { logout, session } = useAuthContext();
  const { busy, syncSii } = useWorkspaceContext();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="sticky top-0 z-20 border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <DashboardHeader session={session} busy={busy} onSync={syncSii} onLogout={logout} />
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <DashboardTabs />
        </div>

        <Outlet />
      </main>
    </div>
  );
}
