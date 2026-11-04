"""
Validación de uploads Excel (reporte gerencial) para auditoría remota — SCRUM-24.
"""

from __future__ import annotations

import io
import os
from typing import Tuple

import pandas as pd
from django.conf import settings
from django.core.exceptions import ValidationError

GERENCIAL_SHEET_NAME = "Hoja1"
GERENCIAL_REQUIRED_COLUMN_INDEXES = (3, 23, 32)
GERENCIAL_CONTRACT_COL = 32
GERENCIAL_DATE_COL = 3
ALLOWED_EXTENSIONS = {".xlsx", ".xls"}
XLSX_MAGIC = b"PK\x03\x04"
XLS_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
DEFAULT_MAX_BYTES = 15 * 1024 * 1024


def _max_upload_bytes() -> int:
    return int(
        getattr(settings, "SINDYBOT_MAX_EXCEL_UPLOAD_BYTES", DEFAULT_MAX_BYTES)
    )


def _read_upload_bounded(uploaded_file, max_bytes: int) -> Tuple[bytes, str]:
    """Lee el upload con tope de tamaño; devuelve bytes y extensión validada."""
    raw_name = uploaded_file.name or ""
    if "\x00" in raw_name:
        raise ValidationError("Nombre de archivo no válido.")
    basename = os.path.basename(raw_name.replace("\\", "/"))
    ext = os.path.splitext(basename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("Solo se permiten archivos Excel (.xlsx o .xls).")

    chunks = []
    total = 0
    for chunk in uploaded_file.chunks():
        total += len(chunk)
        if total > max_bytes:
            mb = max_bytes // (1024 * 1024)
            raise ValidationError(
                f"El archivo supera el tamaño máximo permitido ({mb} MB)."
            )
        chunks.append(chunk)
    data = b"".join(chunks)

    if ext == ".xlsx" and not data.startswith(XLSX_MAGIC):
        raise ValidationError("El archivo no parece un Excel válido (.xlsx).")
    if ext == ".xls" and not data.startswith(XLS_MAGIC):
        raise ValidationError("El archivo no parece un Excel válido (.xls).")
    if len(data) == 0:
        raise ValidationError("El archivo está vacío.")

    return data, ext


def _validate_gerencial_structure(data: bytes) -> None:
    buffer = io.BytesIO(data)
    try:
        workbook = pd.ExcelFile(buffer)
    except Exception as exc:
        raise ValidationError(
            "No se pudo leer el Excel. Verifique que no esté corrupto."
        ) from exc

    if GERENCIAL_SHEET_NAME not in workbook.sheet_names:
        raise ValidationError(
            f'El Excel debe incluir la hoja "{GERENCIAL_SHEET_NAME}".'
        )

    buffer.seek(0)
    df = pd.read_excel(buffer, sheet_name=GERENCIAL_SHEET_NAME, header=None)
    missing = [
        col
        for col in GERENCIAL_REQUIRED_COLUMN_INDEXES
        if col >= len(df.columns)
    ]
    if missing:
        raise ValidationError(
            "El reporte gerencial no tiene el formato esperado "
            f"(faltan columnas requeridas: {missing})."
        )

    has_contract_row = False
    for _, row in df.iterrows():
        contrato = row.iloc[GERENCIAL_CONTRACT_COL]
        fecha = row.iloc[GERENCIAL_DATE_COL]
        if pd.isna(contrato) or pd.isna(fecha):
            continue
        if str(contrato).strip() and str(fecha).strip():
            has_contract_row = True
            break
    if not has_contract_row:
        raise ValidationError(
            "El Excel no contiene filas con contrato (columna 33) y fecha "
            "(columna 4) para procesar la auditoria."
        )


def validation_error_message(exc: ValidationError) -> str:
    messages = getattr(exc, "messages", None)
    if messages:
        return str(messages[0])
    return str(exc)


def validate_archivo_excel_upload(uploaded_file) -> Tuple[str, bytes]:
    """
    Valida extensión, tamaño, firma binaria y estructura del gerencial.

    Returns:
        (ext, bytes) para escribir una sola vez el temporal.
    """
    max_bytes = _max_upload_bytes()
    data, ext = _read_upload_bounded(uploaded_file, max_bytes)
    _validate_gerencial_structure(data)
    return ext, data

# Desarrollado por: hcastro
