from __future__ import annotations

import jwt
import pytest

from enterprise_documents.auth_tokens import TokenType, build_token, decode_token
from enterprise_documents.dte.parser import DTEParseError, DTEParser


def test_parser_happy_path_preserves_valid_accents_and_extracts_fields():
    xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <DTE version="1.0">
      <Documento ID="F33T99">
        <Encabezado>
          <IdDoc>
            <TipoDTE>33</TipoDTE>
            <Folio>99</Folio>
            <FchEmis>2026-04-07</FchEmis>
          </IdDoc>
          <Emisor>
            <RUTEmisor>76111111-1</RUTEmisor>
            <RznSoc>Comercial Ñandú SpA</RznSoc>
            <GiroEmis>Servicios tecnológicos</GiroEmis>
            <DirOrigen>Av. Principal 123</DirOrigen>
            <CmnaOrigen>Providencia</CmnaOrigen>
            <CiudadOrigen>Santiago</CiudadOrigen>
          </Emisor>
          <Receptor>
            <RUTRecep>76999999-9</RUTRecep>
            <RznSocRecep>Cliente de Prueba</RznSocRecep>
            <GiroRecep>Administración</GiroRecep>
          </Receptor>
          <Totales>
            <MntNeto>10000</MntNeto>
            <IVA>1900</IVA>
            <MntTotal>11900</MntTotal>
          </Totales>
        </Encabezado>
        <Detalle>
          <NroLinDet>1</NroLinDet>
          <NmbItem>Servicio mensual</NmbItem>
          <QtyItem>1</QtyItem>
          <PrcItem>10000</PrcItem>
          <MontoItem>11900</MontoItem>
        </Detalle>
      </Documento>
    </DTE>
    """.encode("iso-8859-1")

    document = DTEParser().parse(xml)

    assert document.issuer.name == "Comercial Ñandú SpA"
    assert document.issuer.giro == "Servicios tecnológicos"
    assert document.receiver.giro == "Administración"
    assert document.raw_id == "F33T99"


def test_parser_border_case_removes_question_mark_inside_word_without_crashing():
    xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <DTE version="1.0">
      <Documento ID="F33T100">
        <Encabezado>
          <IdDoc>
            <TipoDTE>33</TipoDTE>
            <Folio>100</Folio>
            <FchEmis>2026-04-07</FchEmis>
          </IdDoc>
          <Emisor>
            <RUTEmisor>76111111-1</RUTEmisor>
            <RznSoc>Proveedor Demo</RznSoc>
            <GiroEmis>COMERCIALIZACI?N DE EQUIPOS</GiroEmis>
          </Emisor>
          <Receptor>
            <RUTRecep>76999999-9</RUTRecep>
            <RznSocRecep>Cliente Demo</RznSocRecep>
          </Receptor>
          <Totales>
            <MntNeto>10000</MntNeto>
            <IVA>1900</IVA>
            <MntTotal>11900</MntTotal>
          </Totales>
        </Encabezado>
        <Detalle>
          <NroLinDet>1</NroLinDet>
          <NmbItem>Servicio mensual</NmbItem>
          <QtyItem>1</QtyItem>
          <PrcItem>10000</PrcItem>
          <MontoItem>11900</MontoItem>
        </Detalle>
      </Documento>
    </DTE>
    """.encode("iso-8859-1")

    document = DTEParser().parse(xml)

    assert document.issuer.giro == "COMERCIALIZACIN DE EQUIPOS"


def test_parser_rejects_unsupported_document_type():
    xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <DTE version="1.0">
      <Documento ID="F99T1">
        <Encabezado>
          <IdDoc>
            <TipoDTE>999</TipoDTE>
            <Folio>1</Folio>
          </IdDoc>
        </Encabezado>
      </Documento>
    </DTE>
    """.encode("iso-8859-1")

    with pytest.raises(DTEParseError, match="TipoDTE no soportado o ausente"):
        DTEParser().parse(xml)


def test_build_and_decode_access_token_happy_path(settings):
    settings.SECRET_KEY = "test-secret-with-safe-length-32!!"
    settings.JWT_ACCESS_LIFETIME_SECONDS = 900
    settings.JWT_REFRESH_LIFETIME_SECONDS = 604800

    raw_token = build_token(123, TokenType.ACCESS)
    payload = decode_token(raw_token, TokenType.ACCESS)

    assert payload["sub"] == "123"
    assert payload["type"] == TokenType.ACCESS
    assert payload["exp"] > payload["iat"]


def test_decode_token_rejects_wrong_type(settings):
    settings.SECRET_KEY = "test-secret-with-safe-length-32!!"
    settings.JWT_ACCESS_LIFETIME_SECONDS = 900
    settings.JWT_REFRESH_LIFETIME_SECONDS = 604800

    raw_token = build_token(123, TokenType.REFRESH)

    with pytest.raises(jwt.InvalidTokenError, match="Invalid token type"):
        decode_token(raw_token, TokenType.ACCESS)
