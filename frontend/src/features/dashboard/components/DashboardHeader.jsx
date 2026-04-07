export function DashboardHeader({ session, busy, onSync, onLogout }) {
  const primaryMembership = session?.primaryMembership;

  return (
    <header className="mb-6 rounded-[2.4rem] border border-white/70 bg-white/70 px-6 py-6 shadow-[0_25px_60px_rgba(2,44,34,0.08)] backdrop-blur-xl lg:px-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.28em] text-emerald-700/70">
            {primaryMembership?.operationMode || "standalone"} mode
          </p>
          <h1 className="mt-3 font-serif text-4xl font-bold tracking-tight text-emerald-950 sm:text-5xl">
            Panel Tributario
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-emerald-900/60">
            Monitorea recepción documental, autenticación con SII, PDFs generados y trazabilidad tributaria de tu
            empresa.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-black uppercase tracking-[0.2em] text-emerald-800">
            {primaryMembership?.tenantName || "Sin empresa"}
          </span>
          <button
            className="rounded-full border border-emerald-200 bg-white px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-emerald-800 transition hover:bg-emerald-50 disabled:opacity-60"
            onClick={onSync}
            disabled={busy}
          >
            Sincronizar SII
          </button>
          <button
            className="rounded-full bg-emerald-900 px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-amber-100 transition hover:bg-emerald-800"
            onClick={onLogout}
          >
            Salir
          </button>
        </div>
      </div>
    </header>
  );
}
