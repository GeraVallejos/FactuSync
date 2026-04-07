import { Loader2, Upload } from "lucide-react";
import { SectionCard } from "@shared/ui";

export function DocumentUploadCard({ busy, fileRef, onSelectFile }) {
  return (
    <SectionCard
      title="Centro de Ingreso"
      subtitle="Carga un XML desde SII o proveedores."
      actions={
        <button
          className="inline-flex items-center gap-2 rounded-full bg-emerald-900 px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-amber-100 transition hover:bg-emerald-800 disabled:opacity-60"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
        >
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
          Subir XML
        </button>
      }
    >
      <input
        ref={fileRef}
        type="file"
        accept=".xml"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0];

          if (file) {
            onSelectFile(file);
          }

          event.target.value = "";
        }}
      />
    </SectionCard>
  );
}
