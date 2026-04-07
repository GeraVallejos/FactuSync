export function Field({ label, children, hint }) {
  return (
    <label className="flex flex-col gap-3">
      <span className="ml-1 text-[11px] font-black uppercase tracking-[0.25em] text-emerald-900">{label}</span>
      {children}
      {hint ? <span className="ml-1 text-xs text-emerald-900/45">{hint}</span> : null}
    </label>
  );
}
