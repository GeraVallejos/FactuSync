import { useMemo, useState } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowUpDown, Download, FileText, RefreshCw, Search, Trash2 } from "lucide-react";
import { facturaSiiApi as api } from "@services/api";
import { statusLabel, statusTone } from "@shared/constants";
import { cn } from "@shared/lib";
import { ConfirmDialog, SectionCard } from "@shared/ui";

const columnHelper = createColumnHelper();

const statusOptions = [
  { label: "Todos", value: "all" },
  { label: "Errores", value: "con_error" },
  { label: "En cola", value: "en_cola" },
  { label: "Procesando", value: "procesando" },
  { label: "PDF", value: "pdf_generado" },
];

export function DocumentsSection({ activeDocumentId, busy, documents, onDeleteDocument, onReprocess }) {
  const [globalFilter, setGlobalFilter] = useState("");
  const [pendingDeleteDocument, setPendingDeleteDocument] = useState(null);
  const [sorting, setSorting] = useState([{ id: "title", desc: false }]);
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredDocuments = useMemo(() => {
    if (statusFilter === "all") {
      return documents;
    }

    return documents.filter((document) => document.status === statusFilter);
  }, [documents, statusFilter]);

  const columns = useMemo(
    () => [
      columnHelper.accessor("title", {
        header: () => (
          <span className="inline-flex items-center gap-2">
            Documento
            <ArrowUpDown size={12} />
          </span>
        ),
        cell: ({ row }) => (
          <div className="space-y-1">
            <p className="text-sm font-bold tracking-tight text-slate-800">{row.original.title}</p>
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">{row.original.sourceLabel}</p>
          </div>
        ),
      }),
      columnHelper.display({
        id: "participants",
        header: "Participantes",
        cell: ({ row }) => (
          <div className="space-y-1.5 text-xs font-medium text-slate-600">
            <p className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-slate-300" />
              {row.original.issuerRut}
            </p>
            <p className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              {row.original.receiverRut}
            </p>
          </div>
        ),
      }),
      columnHelper.accessor("issueDateLabel", {
        header: () => (
          <span className="inline-flex items-center gap-2">
            Emitida
            <ArrowUpDown size={12} />
          </span>
        ),
        cell: ({ getValue }) => <span className="text-sm tracking-tight text-slate-700">{getValue()}</span>,
      }),
      columnHelper.accessor("amountLabel", {
        header: () => (
          <span className="inline-flex items-center justify-end gap-2">
            Total
            <ArrowUpDown size={12} />
          </span>
        ),
        cell: ({ getValue }) => <span className="text-sm font-bold tracking-tight text-slate-900">{getValue()}</span>,
      }),
      columnHelper.accessor("status", {
        header: "Estado",
        cell: ({ row }) => (
          <span
            className={cn(
              "inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.08em]",
              statusTone[row.original.status] || "border-slate-200 bg-slate-100 text-slate-700",
            )}
          >
            {row.original.statusLabel || statusLabel[row.original.status] || row.original.status}
          </span>
        ),
      }),
      columnHelper.display({
        id: "actions",
        header: "Acciones",
        cell: ({ row }) => (
          <div className="flex items-center justify-end gap-2 text-slate-400">
            {row.original.canReprocess ? (
              <button
                type="button"
                title="Reprocesar"
                className="rounded-lg p-2 transition hover:bg-blue-50 hover:text-blue-600 disabled:opacity-60"
                onClick={() => onReprocess(row.original)}
                disabled={busy || activeDocumentId === row.original.id}
              >
                <RefreshCw size={16} className={activeDocumentId === row.original.id ? "animate-spin" : ""} />
              </button>
            ) : null}

            {row.original.hasPdf ? (
              <a
                title="Ver PDF"
                className="rounded-lg p-2 transition hover:bg-emerald-50 hover:text-emerald-600"
                href={api.documentPdfUrl(row.original.id)}
                target="_blank"
                rel="noreferrer"
              >
                <FileText size={16} />
              </a>
            ) : null}

            <a
              title="Descargar XML"
              className="rounded-lg p-2 transition hover:bg-blue-50 hover:text-blue-600"
              href={api.documentXmlUrl(row.original.id)}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={16} />
            </a>

            <span className="mx-1 h-4 w-px bg-slate-200" />

            <button
              type="button"
              title="Eliminar"
              className="rounded-lg p-2 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-60"
              onClick={() => setPendingDeleteDocument(row.original)}
              disabled={busy || activeDocumentId === row.original.id}
            >
              <Trash2 size={16} />
            </button>
          </div>
        ),
      }),
    ],
    [activeDocumentId, busy, onReprocess],
  );

  const table = useReactTable({
    columns,
    data: filteredDocuments,
    state: {
      globalFilter,
      sorting,
    },
    onGlobalFilterChange: setGlobalFilter,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    globalFilterFn: (row, _, filterValue) => {
      const searchable = [
        row.original.title,
        row.original.sourceLabel,
        row.original.issuerRut,
        row.original.receiverRut,
        row.original.status,
      ]
        .join(" ")
        .toLowerCase();

      return searchable.includes(String(filterValue).toLowerCase());
    },
  });

  const visibleCount = table.getFilteredRowModel().rows.length;

  return (
    <>
      <SectionCard
        title=""
        subtitle=""
        actions={null}
      >
        <div className="mb-5 flex w-full min-w-0 flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <label className="relative block lg:w-[17rem] lg:shrink-0">
            <Search
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="search"
              value={globalFilter}
              onChange={(event) => setGlobalFilter(event.target.value)}
              placeholder="Buscar por documento..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-4 text-sm text-slate-800 outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-500/10"
            />
          </label>

          <div className="overflow-x-auto lg:ml-auto lg:max-w-[32rem]">
            <div className="flex min-w-max items-center rounded-xl bg-slate-100 p-1">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setStatusFilter(option.value)}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.04em] transition",
                    statusFilter === option.value
                      ? "bg-white text-emerald-700 shadow-sm"
                      : "text-slate-500 hover:text-slate-700",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white/80 shadow-[0_10px_40px_rgba(15,23,42,0.04)]">
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse text-left">
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id} className="bg-slate-50/80">
                    {headerGroup.headers.map((header) => {
                      const canSort = header.column.getCanSort();

                      return (
                        <th
                          key={header.id}
                          className={cn(
                            "px-6 py-4 text-[11px] font-bold uppercase tracking-[0.22em] text-slate-400",
                            header.id === "amountLabel" || header.id === "actions" ? "text-right" : "",
                          )}
                        >
                          {header.isPlaceholder ? null : (
                            <button
                              type="button"
                              onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                              className={cn(
                                "inline-flex items-center gap-2",
                                header.id === "amountLabel" || header.id === "actions" ? "justify-end" : "",
                                canSort ? "cursor-pointer hover:text-slate-600" : "cursor-default",
                              )}
                            >
                              {flexRender(header.column.columnDef.header, header.getContext())}
                            </button>
                          )}
                        </th>
                      );
                    })}
                  </tr>
                ))}
              </thead>

              <tbody className="divide-y divide-slate-100">
                {table.getRowModel().rows.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length} className="px-6 py-14 text-center text-sm text-slate-500">
                      No hay documentos para los filtros actuales.
                    </td>
                  </tr>
                ) : (
                  table.getRowModel().rows.map((row) => <FragmentRow key={row.id} row={row} />)
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-3 border-t border-slate-100 bg-slate-50/50 px-6 py-4 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <span className="font-medium">Mostrando {visibleCount} de {documents.length} documentos</span>
            <div className="flex gap-2">
              <button className="cursor-not-allowed rounded border border-slate-200 px-3 py-1 font-bold text-slate-400">
                Anterior
              </button>
              <button className="rounded border border-slate-200 bg-white px-3 py-1 font-bold text-slate-700 transition hover:border-emerald-400 hover:text-emerald-700">
                Siguiente
              </button>
            </div>
          </div>
        </div>
      </SectionCard>

      <ConfirmDialog
        open={Boolean(pendingDeleteDocument)}
        title="Eliminar documento"
        description={
          pendingDeleteDocument
            ? `Se eliminara ${pendingDeleteDocument.referenceLabel || pendingDeleteDocument.id} junto con su XML y los PDFs generados.`
            : ""
        }
        confirmLabel="Si, eliminar"
        cancelLabel="Mantener documento"
        loading={busy && activeDocumentId === pendingDeleteDocument?.id}
        onCancel={() => setPendingDeleteDocument(null)}
        onConfirm={async () => {
          if (!pendingDeleteDocument) {
            return;
          }

          await onDeleteDocument(pendingDeleteDocument);
          setPendingDeleteDocument(null);
        }}
      />
    </>
  );
}

function FragmentRow({ row }) {
  return (
    <>
      <tr className="group transition-colors hover:bg-slate-50/70">
        {row.getVisibleCells().map((cell) => (
          <td
            key={cell.id}
            className={cn(
              "px-6 py-5 align-top",
              cell.column.id === "amountLabel" || cell.column.id === "actions" ? "text-right" : "",
            )}
          >
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </td>
        ))}
      </tr>

      {row.original.hasErrorDetail ? (
        <tr>
          <td colSpan={row.getVisibleCells().length} className="bg-red-50/60 px-6 pb-5 pt-0">
            <div className="rounded-xl border border-red-100 bg-white px-4 py-3 text-left text-sm text-red-800 shadow-sm">
              <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-red-600">Detalle del error</p>
              <p className="mt-2 leading-6">{row.original.errorDetail}</p>
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}
