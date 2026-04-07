from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from lxml import etree
from requests import RequestException, Response, Session
from signxml import XMLSigner, methods

from enterprise_documents.models import TaxServiceProfile
from enterprise_documents.sii.exceptions import SIIAuthError, SIIClientError, SIIConfigurationError

SOAP_ENVELOPE = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
  SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <SOAP-ENV:Body>
    {body}
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""


@dataclass(slots=True)
class SIIAuthResult:
    environment: str
    host: str
    seed: str
    token: str
    seed_endpoint: str
    token_endpoint: str

    @property
    def token_preview(self) -> str:
        if len(self.token) <= 8:
            return self.token
        return f"{self.token[:4]}...{self.token[-4:]}"


class SIIClient:
    HOSTS = {
        TaxServiceProfile.Environment.CERTIFICATION: "maullin.sii.cl",
        TaxServiceProfile.Environment.PRODUCTION: "palena.sii.cl",
    }

    def __init__(self, profile: TaxServiceProfile, *, session: Session | None = None, timeout: int = 30) -> None:
        self.profile = profile
        self.session = session or Session()
        self.timeout = timeout

    def authenticate(self) -> SIIAuthResult:
        self._validate_profile()
        seed = self._request_seed()
        signed_seed = self._build_signed_seed_xml(seed)
        token = self._request_token(signed_seed)
        host = self.HOSTS[self.profile.sii_environment]
        return SIIAuthResult(
            environment=self.profile.sii_environment,
            host=host,
            seed=seed,
            token=token,
            seed_endpoint=self.seed_endpoint,
            token_endpoint=self.token_endpoint,
        )

    @property
    def host(self) -> str:
        try:
            return self.HOSTS[self.profile.sii_environment]
        except KeyError as exc:
            raise SIIConfigurationError("Ambiente SII no soportado.") from exc

    @property
    def namespace(self) -> str:
        return f"https://{self.host}/DTEWS"

    @property
    def seed_endpoint(self) -> str:
        return f"{self.namespace}/CrSeed.jws"

    @property
    def token_endpoint(self) -> str:
        return f"{self.namespace}/GetTokenFromSeed.jws"

    def _validate_profile(self) -> None:
        if not self.profile.certificate_path:
            raise SIIConfigurationError("Debes configurar la ruta del certificado del SII.")
        if not self.profile.certificate_password:
            raise SIIConfigurationError("Debes configurar la clave del certificado del SII.")
        if not Path(self.profile.certificate_path).exists():
            raise SIIConfigurationError("No existe el archivo de certificado configurado.")

    def _request_seed(self) -> str:
        body = f'<m:getSeed xmlns:m="{self.seed_endpoint}"/>'
        response = self._post_soap(self.seed_endpoint, body)
        inner_xml = self._extract_inner_xml(response, "getSeedReturn")
        root = self._parse_xml(inner_xml)
        state = self._find_text(root, "ESTADO")
        if state != "00":
            raise SIIAuthError(self._format_sii_error(root, "No fue posible obtener una semilla del SII."))
        seed = self._find_text(root, "SEMILLA")
        if not seed:
            raise SIIAuthError("El SII no devolvio una semilla valida.")
        return seed

    def _request_token(self, signed_seed_xml: str) -> str:
        escaped_xml = (
            signed_seed_xml.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        body = (
            f'<m:getToken xmlns:m="{self.token_endpoint}">'
            f'<pszXml xsi:type="xsd:string">{escaped_xml}</pszXml>'
            "</m:getToken>"
        )
        response = self._post_soap(self.token_endpoint, body)
        inner_xml = self._extract_inner_xml(response, "getTokenReturn")
        root = self._parse_xml(inner_xml)
        state = self._find_text(root, "ESTADO")
        if state != "00":
            raise SIIAuthError(self._format_sii_error(root, "El SII rechazo la semilla firmada."))
        token = self._find_text(root, "TOKEN")
        if not token:
            raise SIIAuthError("El SII no devolvio un token de autenticacion.")
        return token

    def _build_signed_seed_xml(self, seed: str) -> str:
        private_key_pem, certificate_pem = self._load_certificate_material()
        root = etree.fromstring(f"<getToken><item><Semilla>{seed}</Semilla></item></getToken>")
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )
        signed_root = signer.sign(root, key=private_key_pem, cert=certificate_pem)
        signed_xml = etree.tostring(
            signed_root,
            encoding="utf-8",
            xml_declaration=True,
        )
        return signed_xml.decode("utf-8")

    def _load_certificate_material(self) -> tuple[bytes, bytes]:
        certificate_bytes = Path(self.profile.certificate_path).read_bytes()
        password = self.profile.certificate_password.encode("utf-8")
        private_key, certificate, additional_certificates = load_key_and_certificates(certificate_bytes, password)
        if private_key is None or certificate is None:
            raise SIIConfigurationError("No se pudo leer la llave privada o el certificado desde el archivo configurado.")
        private_key_pem = private_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            NoEncryption(),
        )
        certificate_parts = [
            certificate.public_bytes(Encoding.PEM),
            *[item.public_bytes(Encoding.PEM) for item in additional_certificates or []],
        ]
        return private_key_pem, b"".join(certificate_parts)

    def _post_soap(self, url: str, body: str) -> Response:
        try:
            response = self.session.post(
                url,
                data=SOAP_ENVELOPE.format(body=body),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "Accept": "text/xml",
                },
                timeout=self.timeout,
            )
        except RequestException as exc:
            raise SIIClientError("No fue posible conectar con los servicios del SII.") from exc
        try:
            response.raise_for_status()
        except Exception as exc:
            raise SIIClientError(f"El SII respondio con HTTP {response.status_code}.") from exc
        return response

    def _extract_inner_xml(self, response: Response, tag_name: str) -> str:
        root = self._parse_xml(response.content)
        matches = root.xpath(f"//*[local-name()='{tag_name}']")
        inner = matches[0] if matches else None
        if inner is None or not inner.text:
            raise SIIClientError(f"No se encontro {tag_name} en la respuesta SOAP del SII.")
        return inner.text.strip()

    def _parse_xml(self, xml_text: str | bytes):
        try:
            if isinstance(xml_text, str):
                xml_text = xml_text.encode("utf-8")
            return etree.fromstring(xml_text)
        except etree.XMLSyntaxError as exc:
            raise SIIClientError("El XML recibido desde SII no es valido.") from exc

    def _find_text(self, root, tag_name: str) -> str:
        matches = root.xpath(f"//*[local-name()='{tag_name}']")
        node = matches[0] if matches else None
        return node.text.strip() if node is not None and node.text else ""

    def _format_sii_error(self, root, fallback: str) -> str:
        state = self._find_text(root, "ESTADO")
        glosa = self._find_text(root, "GLOSA")
        if state and glosa:
            return f"{fallback} Codigo {state}: {glosa}."
        if state:
            return f"{fallback} Codigo {state}."
        return fallback
