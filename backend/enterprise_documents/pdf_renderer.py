from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from math import ceil

from enterprise_documents.dte.models import DTEModel, Reference


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN_X = 32
MARGIN_TOP = 34
MARGIN_BOTTOM = 32
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN_X * 2)

TEXT_PRIMARY = "#111111"
TEXT_MUTED = "#4F4F4F"
TEXT_SOFT = "#767676"
BORDER_COLOR = "#AFAFAF"
FILL_SUBTLE = "#F6F6F6"
FILL_LIGHT = "#FBFBFB"
WHITE = "#FFFFFF"
ACCENT_RED = "#D7261E"
ACCENT_BLUE = "#3B76D8"
DISPLAY_BRAND_NAME = "FactuSync"


DOCUMENT_TYPE_LABELS = {
    "33": "FACTURA ELECTRONICA",
    "34": "FACTURA EXENTA ELECTRONICA",
    "35": "BOLETA AFECTA ELECTRONICA",
    "39": "BOLETA ELECTRONICA",
    "41": "BOLETA EXENTA ELECTRONICA",
    "52": "GUIA DE DESPACHO ELECTRONICA",
    "56": "NOTA DE DEBITO ELECTRONICA",
    "61": "NOTA DE CREDITO ELECTRONICA",
}


@dataclass(slots=True)
class PDFPage:
    commands: list[str] = field(default_factory=list)


class PDFRenderer:
    def render(self, document: DTEModel, brand_name: str, brand_color: str) -> bytes:
        canvas = PDFCanvas(brand_color=brand_color)
        invoice = InvoiceLayout(canvas=canvas, document=document, brand_name=brand_name)
        invoice.draw()
        return canvas.build()


class InvoiceLayout:
    def __init__(self, canvas: "PDFCanvas", document: DTEModel, brand_name: str) -> None:
        self.canvas = canvas
        self.document = document
        self.brand_name = DISPLAY_BRAND_NAME
        self.y = PAGE_HEIGHT - MARGIN_TOP
        self.table_started = False

    def draw(self) -> None:
        self._draw_top_header()
        self._draw_client_summary()
        self._draw_reference_block()
        self._draw_line_items()
        self._draw_totals()
        self._draw_footer()

    def _draw_top_header(self) -> None:
        left_width = 360
        right_width = CONTENT_WIDTH - left_width - 14
        right_x = MARGIN_X + left_width + 14
        top_y = self.y
        is_exempt = self.document.document_type in ("34", "41")

        brand_x = MARGIN_X
        self.canvas.text(brand_x, top_y - 8, self.document.issuer.name or self.brand_name, font="F2", size=16, color=TEXT_PRIMARY)
        self.canvas.text(brand_x, top_y - 25, self.brand_name, font="F2", size=9, color=TEXT_PRIMARY)

        detail_lines = [
            f"DIRECCION: {self._join_parts([self.document.issuer.address, self.document.issuer.commune, self.document.issuer.city]) or 'NO INFORMADA'}",
            f"TELEFONO: NO INFORMADO",
            f"E-MAIL: NO INFORMADO",
            f"WEB: NO INFORMADA",
        ]
        current_y = top_y - 44
        for line in detail_lines:
            consumed = self.canvas.wrapped_text(
                brand_x,
                current_y,
                line,
                width=left_width - 8,
                size=8.3,
                color=TEXT_MUTED,
                line_height=10,
            )
            current_y -= consumed * 10 + 1

        rect_height = 85 if is_exempt else 70
        self.canvas.rounded_rect(
            right_x,
            top_y - rect_height,
            right_width,
            rect_height,
            radius=6,
            fill_color=WHITE,
            stroke_color=ACCENT_RED,
            line_width=1.0,
        )
        rut_text = f"R.U.T.: {self.document.issuer.rut or 'N/D'}"
        center_x = right_x + (right_width / 2)
        self._draw_text_centered(center_x, top_y - 14, rut_text, font="F2", size=8.3, color=ACCENT_RED)
        self._draw_wrapped_text_centered(
            center_x,
            top_y - 28,
            DOCUMENT_TYPE_LABELS.get(self.document.document_type, f"DTE {self.document.document_type}"),
            width=right_width - 28,
            font="F2",
            size=8.6,
            color=ACCENT_RED,
            line_height=9,
        )
        folio_y = top_y - 50 if is_exempt else top_y - 42
        self._draw_text_centered(center_x, folio_y, f"Nro: {self.document.folio}", font="F2", size=8.6, color=ACCENT_RED)
        sii_label = f"S.I.I. - {self.document.issuer.city or 'SANTIAGO'}"
        sii_y = top_y - 64 if is_exempt else top_y - 56
        self._draw_wrapped_text_centered(
            center_x,
            sii_y,
            sii_label,
            width=right_width - 28,
            font="F2",
            size=8.0,
            color=ACCENT_RED,
            line_height=9,
        )

        y_offset = 105 if is_exempt else 92
        self.y -= y_offset

    def _draw_client_summary(self) -> None:
        self._ensure_space(112, allow_table_header=False)
        box_height = 96
        divider_x = MARGIN_X + 360
        top_y = self.y

        self.canvas.rounded_rect(
            MARGIN_X,
            top_y - box_height,
            CONTENT_WIDTH,
            box_height,
            radius=5,
            fill_color=WHITE,
            stroke_color=BORDER_COLOR,
            line_width=0.9,
        )
        self.canvas.line(divider_x, top_y - box_height, divider_x, top_y, color=BORDER_COLOR, line_width=0.8)

        left_lines = [
            f"SENOR(ES): {self.document.receiver.name or 'NO INFORMADO'}",
            f"RUT: {self.document.receiver.rut or 'NO INFORMADO'}",
            f"DIRECCION: {self._join_parts([self.document.receiver.address]) or 'NO INFORMADA'}",
            f"COMUNA: {self.document.receiver.commune or 'NO INFORMADA'}",
            f"CIUDAD: {self.document.receiver.city or 'NO INFORMADA'}",
            f"GIRO: {self.document.receiver.giro or 'NO INFORMADO'}",
        ]
        current_y = top_y - 14
        for line in left_lines:
            consumed = self.canvas.wrapped_text(
                MARGIN_X + 10,
                current_y,
                line,
                width=divider_x - MARGIN_X - 20,
                font="F2" if ":" in line.split(" ", 1)[0] or line.startswith("SENOR") else "F1",
                size=8.1,
                color=TEXT_PRIMARY,
                line_height=10,
            )
            current_y -= consumed * 10 + 1

        right_lines = [
            f"F. EMISION: {self._format_date(self.document.issue_date)}",
            f"F. VENCIMIENTO: {self._format_date(self.document.issue_date)}",
            "",
            "FORMA DE PAGO: CONTADO",
            (self.document.issuer.giro or "SIN GIRO").upper(),
        ]
        current_y = top_y - 14
        for line in right_lines:
            if not line:
                current_y -= 8
                continue
            consumed = self.canvas.wrapped_text(
                divider_x + 12,
                current_y,
                line,
                width=PAGE_WIDTH - MARGIN_X - divider_x - 20,
                font="F2" if ":" in line or line.isupper() else "F1",
                size=8.1,
                color=TEXT_PRIMARY,
                line_height=10,
            )
            current_y -= consumed * 10 + 2

        self.y -= box_height + 10

    def _draw_reference_block(self) -> None:
        self._ensure_space(56, allow_table_header=False)
        self.canvas.rounded_rect(MARGIN_X, self.y - 28, CONTENT_WIDTH, 28, radius=5, fill_color=WHITE, stroke_color=BORDER_COLOR, line_width=0.9)
        self.canvas.text(MARGIN_X + 149, self.y - 17, "DOCUMENTO(S) DE REFERENCIA", font="F2", size=8.3, color=TEXT_PRIMARY)
        self.y -= 34

        if self.document.references:
            for reference in self.document.references:
                lines = self.canvas.wrap_text(self._reference_label(reference), width=CONTENT_WIDTH - 22, size=8.5)
                height = max(24, len(lines) * 10 + 10)
                self._ensure_space(height + 6, allow_table_header=False)
                self.canvas.rounded_rect(MARGIN_X, self.y - height, CONTENT_WIDTH, height, radius=5, fill_color=FILL_LIGHT, stroke_color=BORDER_COLOR, line_width=0.8)
                current_y = self.y - 14
                for line in lines:
                    self.canvas.text(MARGIN_X + 10, current_y, line, size=8.5, color=TEXT_MUTED)
                    current_y -= 10
                self.y -= height + 6
        else:
            self.canvas.rounded_rect(MARGIN_X, self.y - 24, CONTENT_WIDTH, 24, radius=4, fill_color=WHITE, stroke_color=BORDER_COLOR, line_width=0.8)
            self.canvas.text(MARGIN_X + 10, self.y - 15, "Sin referencias asociadas.", size=8.2, color=TEXT_MUTED)
            self.y -= 32

    def _draw_line_items(self) -> None:
        self._ensure_space(52, allow_table_header=False)
        self.canvas.text(MARGIN_X, self.y - 10, "DETALLE DEL DOCUMENTO", font="F2", size=9.5, color=TEXT_PRIMARY)
        self.y -= 20
        self._draw_table_header()

        if not self.document.line_items:
            self._ensure_space(30)
            self.canvas.rect(MARGIN_X, self.y - 24, CONTENT_WIDTH, 24, stroke_color=BORDER_COLOR, line_width=0.8)
            self.canvas.text(MARGIN_X + 10, self.y - 15, "Sin lineas de detalle informadas.", size=8.5, color=TEXT_MUTED)
            self.y -= 28
            return

        for item in self.document.line_items:
            self._draw_line_row(item)

    def _draw_table_header(self) -> None:
        self.canvas.rounded_rect(MARGIN_X, self.y - 24, CONTENT_WIDTH, 24, radius=4, stroke_color=BORDER_COLOR, fill_color=FILL_SUBTLE, line_width=0.9)
        self.canvas.text(MARGIN_X + 16, self.y - 15, "DESCRIPCION", font="F2", size=7.0, color=TEXT_PRIMARY)
        self.canvas.text(MARGIN_X + 344, self.y - 15, "UND.", font="F2", size=7.0, color=TEXT_PRIMARY)
        self._draw_text_right(MARGIN_X + 404, self.y - 15, "CANT.", font="F2", size=7.0)
        self._draw_text_right(MARGIN_X + 472, self.y - 15, "P. UNIT.", font="F2", size=7.0)
        self._draw_text_right(MARGIN_X + CONTENT_WIDTH - 14, self.y - 15, "TOTAL", font="F2", size=7.0)
        self.y -= 28
        self.table_started = True

    def _draw_line_row(self, item) -> None:
        description = item.description or "Sin descripcion"
        description_lines = self.canvas.wrap_text(description, width=304, size=8.0)
        row_height = max(30, len(description_lines) * 10 + 10)
        self._ensure_space(row_height + 4)

        self.canvas.rect(MARGIN_X, self.y - row_height, CONTENT_WIDTH, row_height, stroke_color=BORDER_COLOR, line_width=0.8)
        self.canvas.text(MARGIN_X + 16, self.y - 16, description_lines[0], size=8.0, color=TEXT_PRIMARY)

        current_y = self.y - 26
        for line in description_lines[1:]:
            self.canvas.text(MARGIN_X + 16, current_y, line, size=8.0, color=TEXT_PRIMARY)
            current_y -= 10

        self.canvas.text(MARGIN_X + 348, self.y - 16, item.unit_name or "(un)", size=7.4, color=TEXT_PRIMARY)
        self._draw_text_right(MARGIN_X + 404, self.y - 16, self._format_quantity(item.quantity), size=7.4)
        self._draw_text_right(MARGIN_X + 472, self.y - 16, self._format_amount(item.unit_price), size=6.8)
        self._draw_text_right(MARGIN_X + CONTENT_WIDTH - 10, self.y - 16, self._format_amount(item.line_amount), font="F2", size=7.1)
        self.y -= row_height

    def _draw_totals(self) -> None:
        self._ensure_space(132, allow_table_header=False)
        self.y -= 14
        box_width = 246
        x = PAGE_WIDTH - MARGIN_X - box_width
        box_height = 122
        self.canvas.rounded_rect(x, self.y - box_height, box_width, box_height, radius=6, fill_color=WHITE, stroke_color=BORDER_COLOR, line_width=0.9)
        self.canvas.rounded_rect(x + 1, self.y - 28, box_width - 2, 27, radius=5, fill_color=FILL_SUBTLE, stroke_color=FILL_SUBTLE)
        self.canvas.text(x + 14, self.y - 17, "RESUMEN DE TOTALES", font="F2", size=8.8, color=TEXT_PRIMARY)

        rows = [
            ("Monto neto", self._format_amount(self.document.totals.net_amount)),
            ("Monto exento", self._format_amount(self.document.totals.exempt_amount)),
            (f"IVA ({self._format_quantity(self.document.totals.vat_rate)}%)", self._format_amount(self.document.totals.vat_amount)),
            ("Total documento", self._format_amount(self.document.totals.total_amount)),
        ]

        current_y = self.y - 48
        for index, (label, value) in enumerate(rows):
            is_total = index == len(rows) - 1
            if is_total:
                self.canvas.line(x + 10, current_y + 12, x + box_width - 10, current_y + 12, color=BORDER_COLOR, line_width=0.8)
            font = "F2" if is_total else "F1"
            self.canvas.text(x + 14, current_y, label, font=font, size=8.5, color=TEXT_PRIMARY)
            self.canvas.text(
                x + box_width - 14 - self.canvas.text_width(value, size=8.5, font=font),
                current_y,
                value,
                font=font,
                size=8.5,
                color=TEXT_PRIMARY,
            )
            current_y -= 22

        self.y -= box_height + 8

    def _draw_footer(self) -> None:
        self._ensure_space(42, allow_table_header=False)
        footer_y = self.y - 8
        self.canvas.line(MARGIN_X, footer_y, PAGE_WIDTH - MARGIN_X, footer_y, color=BORDER_COLOR, line_width=0.8)
        self.canvas.text(MARGIN_X, footer_y - 14, f"Documento ID: {self.document.raw_id or 'N/D'}", size=8, color=TEXT_SOFT)
        self.canvas.text(
            MARGIN_X,
            footer_y - 28,
            "Representacion referencial generada desde el XML tributario. Verifique siempre el DTE original ante usos formales.",
            size=8,
            color=TEXT_SOFT,
        )

    def _ensure_space(self, required_height: float, allow_table_header: bool = True) -> None:
        if self.y - required_height >= MARGIN_BOTTOM:
            return
        self.canvas.new_page()
        self.y = PAGE_HEIGHT - MARGIN_TOP
        if allow_table_header and self.table_started:
            self._draw_table_header()

    def _reference_label(self, reference: Reference) -> str:
        parts = [
            f"Referencia {reference.line_number}",
            f"Tipo {reference.referenced_document_type or 'N/D'}",
            f"Folio {reference.referenced_folio or 'N/D'}",
            f"Fecha {self._format_date(reference.referenced_date)}",
        ]
        if reference.reason:
            parts.append(f"Motivo {reference.reason}")
        return " | ".join(parts)

    def _format_date(self, value: str | None) -> str:
        if not value:
            return "No informada"
        parts = value.split("-")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return value

    def _format_amount(self, value: Decimal | int | str | None) -> str:
        if value in (None, ""):
            return "$0"
        decimal_value = Decimal(str(value))
        rounded = decimal_value.quantize(Decimal("1")) if decimal_value == decimal_value.to_integral() else decimal_value.quantize(Decimal("0.01"))
        raw = f"{rounded:,.2f}" if rounded != rounded.to_integral() else f"{int(rounded):,}"
        formatted = raw.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${formatted}"

    def _format_quantity(self, value: Decimal | int | str | None) -> str:
        if value in (None, ""):
            return "0"
        decimal_value = Decimal(str(value))
        if decimal_value == decimal_value.to_integral():
            return str(int(decimal_value))
        return format(decimal_value.normalize(), "f").rstrip("0").rstrip(".")

    def _join_parts(self, values: list[str | None]) -> str:
        return ", ".join(part.strip() for part in values if part and part.strip())

    def _draw_text_right(self, right_x: float, y: float, value: str, *, font: str = "F1", size: float = 8.5, color: str = TEXT_PRIMARY) -> None:
        x = right_x - self.canvas.text_width(value, size=size, font=font)
        self.canvas.text(x, y, value, font=font, size=size, color=color)

    def _draw_text_centered(self, center_x: float, y: float, value: str, *, font: str = "F1", size: float = 8.5, color: str = TEXT_PRIMARY) -> None:
        x = center_x - (self.canvas.text_width(value, size=size, font=font) / 2)
        self.canvas.text(x, y, value, font=font, size=size, color=color)

    def _draw_wrapped_text_centered(
        self,
        center_x: float,
        y: float,
        value: str,
        *,
        width: float,
        font: str = "F1",
        size: float = 10,
        color: str = TEXT_PRIMARY,
        line_height: float = 10,
    ) -> int:
        lines = self.canvas.wrap_text(value, width=width, size=size, font=font)
        current_y = y
        for line in lines:
            self._draw_text_centered(center_x, current_y, line, font=font, size=size, color=color)
            current_y -= line_height
        return len(lines)


class PDFCanvas:
    def __init__(self, brand_color: str) -> None:
        self.brand_color = brand_color if self._is_hex_color(brand_color) else ACCENT_BLUE
        self.pages: list[PDFPage] = [PDFPage()]

    def build(self) -> bytes:
        page_count = len(self.pages)
        font_object_ids = {"F1": 3, "F2": 4}
        first_page_id = 5
        content_start_id = first_page_id + page_count
        page_ids = [first_page_id + index for index in range(page_count)]
        content_ids = [content_start_id + index for index in range(page_count)]

        page_kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects: list[bytes] = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            f"<< /Type /Pages /Kids [{page_kids}] /Count {page_count} >>".encode(),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        ]

        resources = (
            "<< /Font << "
            + " ".join(f"/{font_name} {object_id} 0 R" for font_name, object_id in font_object_ids.items())
            + " >> >>"
        ).encode()
        for page_id, content_id in zip(page_ids, content_ids, strict=True):
            objects.append(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] /Resources ".encode()
                + resources
                + f" /Contents {content_id} 0 R >>".encode()
            )

        for page in self.pages:
            stream = "\n".join(page.commands).encode("latin-1", errors="replace")
            objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        return self._assemble_pdf(objects)

    def new_page(self) -> None:
        self.pages.append(PDFPage())

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        fill_color: str | None = None,
        stroke_color: str | None = "#000000",
        line_width: float = 1,
    ) -> None:
        commands = [f"{line_width:.2f} w"]
        if fill_color:
            commands.append(f"{self._rgb(fill_color)} rg")
        if stroke_color:
            commands.append(f"{self._rgb(stroke_color)} RG")
        operator = "B" if fill_color and stroke_color else "f" if fill_color else "S"
        commands.append(f"{x:.2f} {y:.2f} {width:.2f} {height:.2f} re {operator}")
        self._append(*commands)

    def rounded_rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        radius: float = 10,
        fill_color: str | None = None,
        stroke_color: str | None = "#000000",
        line_width: float = 1,
    ) -> None:
        r = min(radius, width / 2, height / 2)
        k = 0.5522847498
        commands = [f"{line_width:.2f} w"]
        if fill_color:
            commands.append(f"{self._rgb(fill_color)} rg")
        if stroke_color:
            commands.append(f"{self._rgb(stroke_color)} RG")
        commands.extend(
            [
                f"{x + r:.2f} {y:.2f} m",
                f"{x + width - r:.2f} {y:.2f} l",
                f"{x + width - r + (r * k):.2f} {y:.2f} {x + width:.2f} {y + r - (r * k):.2f} {x + width:.2f} {y + r:.2f} c",
                f"{x + width:.2f} {y + height - r:.2f} l",
                f"{x + width:.2f} {y + height - r + (r * k):.2f} {x + width - r + (r * k):.2f} {y + height:.2f} {x + width - r:.2f} {y + height:.2f} c",
                f"{x + r:.2f} {y + height:.2f} l",
                f"{x + r - (r * k):.2f} {y + height:.2f} {x:.2f} {y + height - r + (r * k):.2f} {x:.2f} {y + height - r:.2f} c",
                f"{x:.2f} {y + r:.2f} l",
                f"{x:.2f} {y + r - (r * k):.2f} {x + r - (r * k):.2f} {y:.2f} {x + r:.2f} {y:.2f} c",
            ]
        )
        operator = "b" if fill_color and stroke_color else "f" if fill_color else "s"
        commands.append(operator)
        self._append(*commands)

    def line(self, x1: float, y1: float, x2: float, y2: float, *, color: str = "#000000", line_width: float = 1) -> None:
        self._append(
            f"{line_width:.2f} w",
            f"{self._rgb(color)} RG",
            f"{x1:.2f} {y1:.2f} m",
            f"{x2:.2f} {y2:.2f} l S",
        )

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        font: str = "F1",
        size: float = 10,
        color: str = "#000000",
    ) -> None:
        safe = self._escape_text(value)
        self._append(
            "BT",
            f"/{font} {size:.2f} Tf",
            f"{self._rgb(color)} rg",
            f"1 0 0 1 {x:.2f} {y:.2f} Tm",
            f"({safe}) Tj",
            "ET",
        )

    def wrapped_text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        width: float,
        font: str = "F1",
        size: float = 10,
        color: str = "#000000",
        line_height: float | None = None,
    ) -> int:
        lines = self.wrap_text(value, width=width, size=size, font=font)
        step = line_height or ceil(size * 1.4)
        current_y = y
        for line in lines:
            self.text(x, current_y, line, font=font, size=size, color=color)
            current_y -= step
        return len(lines)

    def wrap_text(self, value: str, *, width: float, size: float = 10, font: str = "F1") -> list[str]:
        words = str(value or "").split()
        if not words:
            return [""]

        lines: list[str] = []
        current = self._fit_word(words[0], width=width, size=size, font=font, lines=lines)
        for raw_word in words[1:]:
            word = self._fit_word(raw_word, width=width, size=size, font=font, lines=lines)
            candidate = f"{current} {word}"
            if self.text_width(candidate, size=size, font=font) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def _fit_word(self, word: str, *, width: float, size: float, font: str, lines: list[str]) -> str:
        if self.text_width(word, size=size, font=font) <= width:
            return word

        current = ""
        for char in word:
            candidate = f"{current}{char}"
            if current and self.text_width(candidate, size=size, font=font) > width:
                lines.append(current)
                current = char
            else:
                current = candidate
        return current or word

    def text_width(self, value: str, *, size: float = 10, font: str = "F1") -> float:
        factor = 0.56 if font == "F1" else 0.60
        width = 0.0
        for char in str(value):
            if char == " ":
                width += size * 0.28
            elif char in "il.,:;|!":
                width += size * 0.22
            elif char in "MW@%#":
                width += size * 0.78
            else:
                width += size * factor
        return width

    def _append(self, *commands: str) -> None:
        self.pages[-1].commands.extend(commands)

    def _rgb(self, value: str) -> str:
        raw = value.lstrip("#")
        if len(raw) != 6:
            raw = "000000"
        rgb = tuple(int(raw[index : index + 2], 16) / 255 for index in range(0, 6, 2))
        return " ".join(f"{component:.3f}" for component in rgb)

    def _escape_text(self, value: str) -> str:
        safe = str(value)
        return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _is_hex_color(self, value: str | None) -> bool:
        if not value or not isinstance(value, str):
            return False
        raw = value.lstrip("#")
        return len(raw) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in raw)

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
