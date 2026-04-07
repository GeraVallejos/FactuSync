import { AlertCircle, CheckCircle2, FileText } from "lucide-react";
import { MetricCard } from "@shared/ui";

export function MetricsOverview({ dashboard, processedCount }) {
  return (
    <section className="mb-8 grid gap-6 md:grid-cols-3">
      <MetricCard
        label="Total documentos"
        value={dashboard?.totalDocuments ?? 0}
        hint="Registrados en la empresa actual."
        icon={FileText}
        tone="blue"
      />
      <MetricCard
        label="PDF generados"
        value={processedCount}
        hint="Disponibles para descarga."
        icon={CheckCircle2}
        tone="emerald"
      />
      <MetricCard
        label="Tasa de error"
        value={`${dashboard?.errorRate ?? 0}%`}
        hint="Incidencias detectadas en validación."
        icon={AlertCircle}
        tone="amber"
      />
    </section>
  );
}
