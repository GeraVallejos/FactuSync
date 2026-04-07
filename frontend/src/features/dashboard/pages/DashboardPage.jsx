import { Outlet } from "react-router-dom";
import { useAuthContext, useWorkspaceContext } from "@app/providers";
import { DashboardHeader, DashboardTabs } from "@features/dashboard/components";

export function DashboardPage() {
  const { logout, session } = useAuthContext();
  const { busy, syncSii } = useWorkspaceContext();

  return (
    <div className="min-h-screen bg-[#f4f7f4] text-emerald-950">
      <div className="absolute left-0 top-0 h-2 w-full bg-linear-to-r from-emerald-800 via-emerald-600 to-amber-200" />

      <div className="mx-auto max-w-[1320px] px-4 py-8 sm:px-6 lg:px-8">
        <DashboardHeader session={session} busy={busy} onSync={syncSii} onLogout={logout} />
        <DashboardTabs />
        <div className="mt-6">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
