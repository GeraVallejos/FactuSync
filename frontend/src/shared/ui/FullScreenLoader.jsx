import { Loader2 } from "lucide-react";

export function FullScreenLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f4f7f4] text-emerald-950">
      <div className="flex items-center gap-3 rounded-full border border-emerald-100 bg-white px-5 py-3 shadow-sm">
        <Loader2 size={18} className="animate-spin text-emerald-700" />
        <span className="text-sm font-semibold">Cargando aplicación...</span>
      </div>
    </div>
  );
}
