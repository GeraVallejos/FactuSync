import { MetricCard } from "@shared/ui";

export function MetricsOverview({ dashboard, processedCount }) {
  return (
    <section className="mb-6 grid gap-4 md:grid-cols-3">
      <MetricCard
        label="Total documentos"
        value={dashboard?.totalDocuments ?? 0}
        hint="Documentos registrados en la empresa actual."
      />
      <MetricCard
        label="PDF generados"
        value={processedCount}
        hint="Representaciones tributarias disponibles para descarga."
      />
      <MetricCard
        label="Tasa de error"
        value={`${dashboard?.errorRate ?? 0}%`}
        hint="Incidencias detectadas en parsing o validacion."
      />
    </section>
  );
}
