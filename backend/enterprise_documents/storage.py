from __future__ import annotations

from hashlib import sha256
from pathlib import Path


class DocumentStorage:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.xml_path = base_path / "xml"
        self.pdf_path = base_path / "pdf"
        self.audit_path = base_path / "audit"

    def initialize(self) -> None:
        self.xml_path.mkdir(parents=True, exist_ok=True)
        self.pdf_path.mkdir(parents=True, exist_ok=True)
        self.audit_path.mkdir(parents=True, exist_ok=True)

    def compute_hash(self, content: bytes) -> str:
        return sha256(content).hexdigest()

    def write_xml(self, tenant_id: str, document_id: str, content: bytes, digest: str | None = None) -> tuple[str, str]:
        digest = digest or self.compute_hash(content)
        path = self.xml_path / tenant_id / f"{document_id}.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return digest, str(path)

    def write_pdf(self, tenant_id: str, document_id: str, content: bytes, version: int) -> str:
        path = self.pdf_path / tenant_id / f"{document_id}-v{version}.pdf"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def delete_document_assets(self, tenant_id: str, document_id: str) -> None:
        xml_file = self.xml_path / tenant_id / f"{document_id}.xml"
        if xml_file.exists():
            xml_file.unlink()

        pdf_directory = self.pdf_path / tenant_id
        if pdf_directory.exists():
            for pdf_file in pdf_directory.glob(f"{document_id}-v*.pdf"):
                if pdf_file.is_file():
                    pdf_file.unlink()
