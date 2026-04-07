import { useMemo, useRef } from "react";
import { useWorkspaceContext } from "@app/providers";
import { DocumentUploadCard, DocumentsSection, FeedbackBanner, MetricsOverview } from "@features/dashboard/components";

export function DocumentsPage() {
  const fileRef = useRef(null);
  const { activeDocumentId, busy, dashboard, documents, feedback, importDocument, reprocessDocument } =
    useWorkspaceContext();

  const processedCount = useMemo(
    () => documents.filter((document) => document.status === "pdf_generado").length,
    [documents],
  );

  return (
    <>
      {feedback?.message ? <FeedbackBanner feedback={feedback} /> : null}
      <MetricsOverview dashboard={dashboard} processedCount={processedCount} />

      <section>
        <DocumentUploadCard busy={busy} fileRef={fileRef} onSelectFile={importDocument} />
      </section>

      <section className="mt-6">
        <DocumentsSection
          activeDocumentId={activeDocumentId}
          busy={busy}
          documents={documents}
          onReprocess={reprocessDocument}
        />
      </section>
    </>
  );
}
