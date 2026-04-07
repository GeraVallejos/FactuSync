from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class Party:
    rut: str | None = None
    name: str | None = None
    giro: str | None = None
    address: str | None = None
    commune: str | None = None
    city: str | None = None


@dataclass(slots=True)
class Totals:
    net_amount: Decimal = Decimal("0")
    exempt_amount: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("19")
    vat_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")


@dataclass(slots=True)
class LineItem:
    line_number: int
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    line_amount: Decimal = Decimal("0")
    code: str | None = None
    unit_name: str | None = None
    exempt: bool = False


@dataclass(slots=True)
class Reference:
    line_number: int
    referenced_document_type: str | None = None
    referenced_folio: str | None = None
    referenced_date: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class DTEModel:
    document_type: str
    folio: str
    issue_date: str | None
    issuer: Party
    receiver: Party
    totals: Totals
    line_items: list[LineItem] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    raw_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
