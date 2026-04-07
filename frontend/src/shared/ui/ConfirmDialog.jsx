import { AlertTriangle } from "lucide-react";

export function ConfirmDialog({
  cancelLabel = "Cancelar",
  confirmLabel = "Confirmar",
  description,
  loading = false,
  onCancel,
  onConfirm,
  open = false,
  title,
}) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-emerald-950/35 px-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-[2rem] border border-white/60 bg-white p-6 shadow-[0_30px_80px_rgba(2,44,34,0.2)]">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600">
            <AlertTriangle size={22} />
          </div>

          <div className="flex-1">
            <p className="text-xs font-black uppercase tracking-[0.24em] text-red-600/80">Confirmacion</p>
            <h3 className="mt-2 text-xl font-bold text-emerald-950">{title}</h3>
            <p className="mt-3 text-sm leading-6 text-emerald-900/70">{description}</p>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-full border border-emerald-200 bg-white px-5 py-2.5 text-sm font-semibold text-emerald-900 transition hover:bg-emerald-50 disabled:opacity-60"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className="rounded-full bg-red-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-red-500 disabled:opacity-60"
          >
            {loading ? "Eliminando..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
