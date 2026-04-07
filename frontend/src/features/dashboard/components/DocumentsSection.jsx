import { useMemo, useState } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowDownUp, Download, Eye, Search } from "lucide-react";
import { facturaSiiApi as api } from "@services/api";
import { statusLabel, statusTone } from "@shared/constants";
import { cn } from "@shared/lib";
import { SectionCard } from "@shared/ui";

const columnHelper = createColumnHelper();

const statusOptions = [
  { label: "Todos", value: "all" },
  { label: "PDF generado", value: "pdf_generado" },
  { label: "Con error", value: "con_error" },
  { label: "En cola", value: "en_cola" },
  { label: "Procesando", value: "procesando" },
  { label: "Recibido", value: "recibido" },
  { label: "Validado", value: "valido" },
];

export function DocumentsSection({ activeDocumentId, busy, documents, onReprocess }) {
  const [globalFilter, setGlobalFilter] = useState("");
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
        header: "Documento",
        cell: ({ row }) => (
          <div>
            <p className="text-sm font-semibold text-emerald-950">{row.original.title}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.18em] text-emerald-900/45">{row.original.sourceLabel}</p>
          </div>
        ),
      }),
      columnHelper.display({
        id: "participants",
        header: "Participantes",
        cell: ({ row }) => (
          <div className="text-sm text-emerald-900/65">
            <p>{row.original.issuerRut}</p>
            <p className="mt-1">{row.original.receiverRut}</p>
          </div>
        ),
      }),
      columnHelper.accessor("amountLabel", {
        header: "Total",
        cell: ({ getValue }) => <span className="text-sm font-semibold text-emerald-950">{getValue()}</span>,
      }),
      columnHelper.accessor("status", {
        header: "Estado",
        cell: ({ row }) => (
          <span
            className={cn(
              "inline-flex items-center rounded-full px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.18em]",
              statusTone[row.original.status] || "bg-stone-100 text-stone-700 border border-stone-200",
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
          <div className="flex flex-wrap justify-end gap-2">
            {row.original.canReprocess ? (
              <button
                className="rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.18em] text-emerald-800 transition hover:bg-emerald-50 disabled:opacity-60"
                onClick={() => onReprocess(row.original)}
                disabled={busy || activeDocumentId === row.original.id}
              >
                {activeDocumentId === row.original.id ? "Procesando" : "Reprocesar"}
              </button>
            ) : null}
            {row.original.hasPdf ? (
              <a
                className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.18em] text-emerald-800 transition hover:bg-emerald-50"
                href={api.documentPdfUrl(row.original.id)}
                target="_blank"
                rel="noreferrer"
              >
                <Eye size={14} />
                PDF
              </a>
            ) : null}
            <a
              className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.18em] text-emerald-800 transition hover:bg-emerald-50"
              href={api.documentXmlUrl(row.original.id)}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={14} />
              XML
            </a>
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

  return (
    <SectionCard
      title="Documentos Procesados"
      subtitle="Tabla operativa con scroll, búsqueda y estados para que el historial no crezca sin control."
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-black uppercase tracking-[0.2em] text-emerald-800">
            {table.getFilteredRowModel().rows.length} visibles
          </span>
          <span className="inline-flex items-center rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-xs font-black uppercase tracking-[0.2em] text-emerald-800">
            {documents.length} total
          </span>
        </div>
      }
    >
      <div className="mb-4 grid gap-3 lg:grid-cols-[1fr_auto]">
        <label className="group relative">
          <Search
            size={16}
            className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-emerald-800/45"
          />
          <input
            type="search"
            value={globalFilter}
            onChange={(event) => setGlobalFilter(event.target.value)}
            placeholder="Buscar por documento, RUT o estado"
            className="w-full rounded-[1.3rem] border border-emerald-100 bg-white/70 py-3 pl-11 pr-4 text-sm text-emerald-950 outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-50"
          />
        </label>

        <div className="flex flex-wrap items-center gap-2">
          {statusOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setStatusFilter(option.value)}
              className={cn(
                "rounded-full border px-3 py-2 text-[11px] font-black uppercase tracking-[0.18em] transition",
                statusFilter === option.value
                  ? "border-emerald-900 bg-emerald-900 text-amber-100"
                  : "border-emerald-200 bg-white text-emerald-800 hover:bg-emerald-50",
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-[1.8rem] border border-emerald-100 bg-white/60">
        <div className="max-h-155 overflow-auto">
          <table className="min-w-full border-separate border-spacing-0">
            <thead className="sticky top-0 z-10 bg-[#f7fbf7]">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const canSort = header.column.getCanSort();

                    return (
                      <th
                        key={header.id}
                        className={cn(
                          "border-b border-emerald-100 px-5 py-4 text-left text-[11px] font-black uppercase tracking-[0.22em] text-emerald-900/55",
                          header.id === "actions" ? "text-right" : "",
                        )}
                      >
                        {header.isPlaceholder ? null : (
                          <button
                            type="button"
                            onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                            className={cn(
                              "inline-flex items-center gap-2",
                              canSort ? "cursor-pointer hover:text-emerald-900" : "cursor-default",
                            )}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {canSort ? <ArrowDownUp size={13} /> : null}
                          </button>
                        )}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>

            <tbody>
              {table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-5 py-12 text-center text-sm text-emerald-900/55">
                    No hay documentos para los filtros actuales.
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <FragmentRow
                    key={row.id}
                    row={row}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </SectionCard>
  );
}

function FragmentRow({ row }) {
  return (
    <>
      <tr className="align-top transition hover:bg-emerald-50/45">
        {row.getVisibleCells().map((cell) => (
          <td
            key={cell.id}
            className={cn(
              "border-b border-emerald-100 px-5 py-4",
              cell.column.id === "actions" ? "text-right" : "",
            )}
          >
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </td>
        ))}
      </tr>

      {row.original.hasErrorDetail ? (
        <tr>
          <td colSpan={row.getVisibleCells().length} className="border-b border-emerald-100 bg-red-50/45 px-5 pb-4 pt-0">
            <div className="rounded-[1.2rem] border border-red-100 bg-red-50/80 px-4 py-3 text-sm text-red-800">
              <p className="font-semibold uppercase tracking-[0.16em] text-red-700">Detalle del error</p>
              <p className="mt-2 leading-6">{row.original.errorDetail}</p>
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}
