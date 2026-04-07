export function SectionCard({ title, subtitle, actions, children }) {
  return (
    <article className="rounded-[2rem] border border-white/70 bg-white/75 p-6 shadow-[0_20px_60px_rgba(2,44,34,0.08)] backdrop-blur-xl">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-emerald-950">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-emerald-900/55">{subtitle}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {children}
    </article>
  );
}
