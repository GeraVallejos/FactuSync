import { LogOut, RefreshCw } from "lucide-react";

export function DashboardHeader({ session, busy, onSync, onLogout }) {
  const primaryMembership = session?.primaryMembership;
  const tenantName = primaryMembership?.tenantName || "Sin empresa";
  const operationMode = primaryMembership?.operationMode || "standalone";

  return (
    <header className="flex h-16 items-center justify-between gap-6">
      <div className="flex items-center gap-8">
        <div className="flex items-center gap-3">
          <img src="/factysync.svg" alt="FactuSync" className="h-9 w-9 object-contain" />
          <span className="text-xl font-bold tracking-tight text-slate-800">
            Factu<span className="text-emerald-600">Sync</span>
          </span>
        </div>

        <span className="hidden rounded border border-emerald-100 bg-emerald-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-700 sm:inline-flex">
          {operationMode} mode
        </span>
      </div>

      <div className="flex items-center gap-3">
        <button
          className="rounded-lg p-2 text-slate-400 transition hover:text-emerald-600 disabled:opacity-60"
          onClick={onSync}
          disabled={busy}
          title="Sincronizar SII"
        >
          <RefreshCw size={18} className={busy ? "animate-spin" : ""} />
        </button>

        <button className="hidden rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-bold text-slate-700 transition hover:bg-slate-50 md:inline-flex">
          {tenantName}
        </button>

        <button
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
          onClick={onLogout}
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">Salir</span>
        </button>
      </div>
    </header>
  );
}
