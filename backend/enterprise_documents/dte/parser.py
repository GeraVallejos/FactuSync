from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import unicodedata
from xml.etree import ElementTree as ET

from enterprise_documents.dte.models import DTEModel, LineItem, Party, Reference, Totals


class DTEParseError(ValueError):
    pass


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_child(element: ET.Element | None, name: str) -> ET.Element | None:
    if element is None:
        return None
    for child in element.iter():
        if _strip_namespace(child.tag) == name:
            return child
    return None


def _find_children(element: ET.Element | None, name: str) -> list[ET.Element]:
    if element is None:
        return []
    return [child for child in element.iter() if _strip_namespace(child.tag) == name]


def _sanitize_text(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = cleaned.replace("\ufffd", "")
    if "Ã" in cleaned or "Â" in cleaned:
        try:
            cleaned = cleaned.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    cleaned = re.sub(r"(?<=\w)\?(?=\w)", "", cleaned)
    return cleaned.strip()


def _text(element: ET.Element | None, name: str) -> str | None:
    child = _find_child(element, name)
    if child is None or child.text is None:
        return None
    return _sanitize_text(child.text)


def _decimal(value: str | None, default: str = "0") -> Decimal:
    raw = value if value not in (None, "") else default
    normalized = str(raw).replace(",", ".").strip()
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise DTEParseError(f"Valor decimal invalido: {raw}") from exc


class DTEParser:
    supported_types = {"33", "34", "52", "56", "61"}

    def parse(self, xml_content: bytes) -> DTEModel:
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            raise DTEParseError(f"XML invalido: {exc}") from exc

        documento = _find_child(root, "Documento")
        encabezado = _find_child(documento, "Encabezado")
        if documento is None or encabezado is None:
            raise DTEParseError("No se encontro el nodo Documento/Encabezado del DTE.")

        id_doc = _find_child(encabezado, "IdDoc")
        emisor = _find_child(encabezado, "Emisor")
        receptor = _find_child(encabezado, "Receptor")
        totales = _find_child(encabezado, "Totales")

        document_type = _text(id_doc, "TipoDTE")
        folio = _text(id_doc, "Folio")
        if not document_type or document_type not in self.supported_types:
            raise DTEParseError(f"TipoDTE no soportado o ausente: {document_type}")
        if not folio:
            raise DTEParseError("Folio ausente en el DTE.")

        return DTEModel(
            document_type=document_type,
            folio=folio,
            issue_date=_text(id_doc, "FchEmis"),
            issuer=Party(
                rut=_text(emisor, "RUTEmisor"),
                name=_text(emisor, "RznSoc"),
                giro=_text(emisor, "GiroEmis"),
                address=_text(emisor, "DirOrigen"),
                commune=_text(emisor, "CmnaOrigen"),
                city=_text(emisor, "CiudadOrigen"),
            ),
            receiver=Party(
                rut=_text(receptor, "RUTRecep"),
                name=_text(receptor, "RznSocRecep"),
                giro=_text(receptor, "GiroRecep"),
                address=_text(receptor, "DirRecep"),
                commune=_text(receptor, "CmnaRecep"),
                city=_text(receptor, "CiudadRecep"),
            ),
            totals=Totals(
                net_amount=_decimal(_text(totales, "MntNeto")),
                exempt_amount=_decimal(_text(totales, "MntExe")),
                vat_rate=_decimal(_text(totales, "TasaIVA"), "19"),
                vat_amount=_decimal(_text(totales, "IVA")),
                total_amount=_decimal(_text(totales, "MntTotal")),
            ),
            line_items=self._parse_lines(documento),
            references=self._parse_references(documento),
            raw_id=documento.attrib.get("ID"),
        )

    def _parse_lines(self, documento: ET.Element) -> list[LineItem]:
        lines: list[LineItem] = []
        for item in _find_children(documento, "Detalle"):
            line_number = int(_text(item, "NroLinDet") or len(lines) + 1)
            lines.append(
                LineItem(
                    line_number=line_number,
                    description=_text(item, "NmbItem") or _text(item, "DscItem") or "Sin descripcion",
                    quantity=_decimal(_text(item, "QtyItem"), "1"),
                    unit_price=_decimal(_text(item, "PrcItem")),
                    line_amount=_decimal(_text(item, "MontoItem")),
                    unit_name=_text(item, "UnmdItem"),
                    exempt=_text(item, "IndExe") == "1",
                )
            )
        return lines

    def _parse_references(self, documento: ET.Element) -> list[Reference]:
        refs: list[Reference] = []
        for item in _find_children(documento, "Referencia"):
            refs.append(
                Reference(
                    line_number=int(_text(item, "NroLinRef") or len(refs) + 1),
                    referenced_document_type=_text(item, "TpoDocRef"),
                    referenced_folio=_text(item, "FolioRef"),
                    referenced_date=_text(item, "FchRef"),
                    reason=_text(item, "RazonRef"),
                )
            )
        return refs
