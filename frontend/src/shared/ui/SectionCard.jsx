export function SectionCard({ title, subtitle, actions, children }) {
  const hasHeading = Boolean(title || subtitle);

  return (
    <article className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
      {hasHeading || actions ? (
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {hasHeading ? (
            <div>
              {title ? <h2 className="text-lg font-bold text-slate-900">{title}</h2> : null}
              {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
            </div>
          ) : null}
          {actions ? <div className="flex min-w-0 flex-wrap items-center gap-2">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </article>
  );
}
