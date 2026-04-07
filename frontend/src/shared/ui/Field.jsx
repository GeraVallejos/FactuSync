export function Field({ label, children, hint }) {
  return (
    <label className="flex flex-col gap-2.5">
      <span className="ml-1 text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">{label}</span>
      {children}
      {hint ? <span className="ml-1 text-xs text-slate-400">{hint}</span> : null}
    </label>
  );
}
