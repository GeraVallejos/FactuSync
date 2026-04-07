import { Loader2, Upload } from "lucide-react";

export function DocumentUploadCard({ busy, fileRef, onSelectFile }) {
  return (
    <section className="mb-8 overflow-hidden rounded-[1.5rem] border border-emerald-800 bg-emerald-900 p-6 shadow-xl shadow-emerald-950/10">
      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Centro de ingreso</h2>
          <p className="mt-1 text-sm text-emerald-200">
            Carga un archivo XML directamente desde SII o desde tus proveedores locales.
          </p>
        </div>

        <button
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500 px-8 py-3 text-sm font-bold text-white transition hover:bg-emerald-400 disabled:opacity-60 md:w-auto"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
        >
          {busy ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
          Subir XML
        </button>
      </div>

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
    </section>
  );
}
