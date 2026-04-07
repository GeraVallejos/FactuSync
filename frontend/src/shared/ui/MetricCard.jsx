export function MetricCard({ label, value, hint, icon: Icon, tone = "emerald" }) {
  const toneStyles = {
    amber: {
      badge: "bg-amber-50 text-amber-600",
      pill: "text-amber-600",
    },
    blue: {
      badge: "bg-blue-50 text-blue-600",
      pill: "text-blue-600",
    },
    emerald: {
      badge: "bg-emerald-50 text-emerald-600",
      pill: "text-emerald-600",
    },
  };

  const styles = toneStyles[tone] || toneStyles.emerald;

  return (
    <article className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className={`rounded-xl p-3 ${styles.badge}`}>{Icon ? <Icon size={22} /> : null}</div>
        <span className={`text-xs font-bold uppercase tracking-[0.22em] ${styles.pill}`}>Activo</span>
      </div>
      <strong className="mt-5 block text-3xl font-bold tracking-tight text-slate-900">{value}</strong>
      <p className="mt-2 text-sm font-semibold text-slate-700">{label}</p>
      <p className="mt-2 text-xs text-slate-400">{hint}</p>
    </article>
  );
}
