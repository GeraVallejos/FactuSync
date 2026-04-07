from __future__ import annotations

from enterprise_documents.dte.models import DTEModel


class PDFRenderer:
    def render(self, document: DTEModel, brand_name: str, brand_color: str) -> bytes:
        lines = [
            brand_name,
            f"DTE {document.document_type} Folio {document.folio}",
            f"Emision: {document.issue_date or 'N/D'}",
            f"Emisor: {document.issuer.name or 'N/D'} ({document.issuer.rut or 'N/D'})",
            f"Receptor: {document.receiver.name or 'N/D'} ({document.receiver.rut or 'N/D'})",
            "",
            "Detalle:",
        ]
        for item in document.line_items:
            lines.append(
                f"{item.line_number}. {item.description} | Cant {item.quantity} | PU {item.unit_price} | Total {item.line_amount}"
            )
        lines.extend(
            [
                "",
                f"Neto: {document.totals.net_amount}",
                f"Exento: {document.totals.exempt_amount}",
                f"IVA: {document.totals.vat_amount}",
                f"Total: {document.totals.total_amount}",
            ]
        )
        return self._build_simple_pdf(lines, brand_color)

    def _build_simple_pdf(self, lines: list[str], brand_color: str) -> bytes:
        safe_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
        text_commands = ["BT", "/F1 12 Tf", "50 780 Td"]
        rgb = self._hex_to_rgb(brand_color)
        text_commands.append(f"{rgb[0]} {rgb[1]} {rgb[2]} rg")
        for index, line in enumerate(safe_lines):
            if index == 0:
                text_commands.append(f"({line}) Tj")
            else:
                text_commands.append("0 -18 Td")
                text_commands.append(f"({line}) Tj")
        text_commands.append("ET")
        stream = "\n".join(text_commands).encode("latin-1", errors="replace")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
        ]
        return self._assemble_pdf(objects)

    def _assemble_pdf(self, objects: list[bytes]) -> bytes:
        buffer = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(buffer))
            buffer.extend(f"{index} 0 obj\n".encode())
            buffer.extend(obj)
            buffer.extend(b"\nendobj\n")
        xref_start = len(buffer)
        buffer.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        buffer.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            buffer.extend(f"{offset:010d} 00000 n \n".encode())
        buffer.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode()
        )
        return bytes(buffer)

    def _hex_to_rgb(self, value: str) -> tuple[str, str, str]:
        raw = value.lstrip("#")
        if len(raw) != 6:
            return ("0", "0", "0")
        rgb = tuple(int(raw[i : i + 2], 16) / 255 for i in range(0, 6, 2))
        return tuple(f"{component:.3f}" for component in rgb)
