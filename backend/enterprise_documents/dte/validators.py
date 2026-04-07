from __future__ import annotations

from decimal import Decimal

from enterprise_documents.dte.models import DTEModel


class DTEValidator:
    def validate(self, document: DTEModel) -> list[str]:
        errors: list[str] = []
        if not document.issuer.rut:
            errors.append("Campo obligatorio ausente: issuer.rut")
        if not document.receiver.rut:
            errors.append("Campo obligatorio ausente: receiver.rut")
        if not document.issue_date:
            errors.append("Campo obligatorio ausente: issue_date")

        lines_total = sum(line.line_amount for line in document.line_items)
        subtotal_amount = document.totals.net_amount + document.totals.exempt_amount
        tributary_total = subtotal_amount + document.totals.vat_amount

        if document.line_items and lines_total > document.totals.total_amount:
            errors.append(
                f"El total de lineas ({lines_total}) excede el total informado ({document.totals.total_amount})."
            )
        if tributary_total > document.totals.total_amount:
            errors.append(
                f"Los totales tributarios exceden el total informado: neto+exento+iva={tributary_total}, total={document.totals.total_amount}."
            )
        if document.document_type == "34" and document.totals.vat_amount != Decimal("0"):
            errors.append("Una factura exenta (34) no debe informar IVA distinto de 0.")
        if document.document_type != "34" and document.totals.net_amount > 0 and document.totals.vat_amount == 0:
            errors.append("Documento afecto sin IVA informado.")
        return errors
