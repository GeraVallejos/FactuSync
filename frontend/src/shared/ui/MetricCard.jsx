export function MetricCard({ label, value, hint }) {
  return (
    <article className="rounded-[1.8rem] border border-white/70 bg-white/70 p-5 shadow-[0_20px_50px_rgba(2,44,34,0.06)] backdrop-blur-xl">
      <p className="text-xs font-black uppercase tracking-[0.25em] text-emerald-900/45">{label}</p>
      <strong className="mt-3 block text-4xl font-semibold tracking-tight text-emerald-950">{value}</strong>
      <p className="mt-2 text-sm text-emerald-900/55">{hint}</p>
    </article>
  );
}
