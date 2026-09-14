from pathlib import Path

from django.core.exceptions import ValidationError


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


EXTENSIONES_PERMITIDAS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def validar_documento(archivo):

    if not archivo:
        return

    # ------------------------------------------------------
    # Validar tamaño
    # ------------------------------------------------------

    if archivo.size > MAX_FILE_SIZE:
        raise ValidationError(
            "El archivo no puede superar los 5 MB."
        )

    # ------------------------------------------------------
    # Validar extensión
    # ------------------------------------------------------

    extension = Path(archivo.name).suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValidationError(
            "Tipo de archivo no permitido. "
            "Solo se permiten PDF, JPG, JPEG y PNG."
        )

    # ------------------------------------------------------
    # Validar MIME informado
    # ------------------------------------------------------

    content_type = getattr(
        archivo,
        "content_type",
        ""
    )

    mime_esperado = EXTENSIONES_PERMITIDAS[extension]

    if content_type and content_type != mime_esperado:
        raise ValidationError(
            "El tipo MIME del archivo no coincide con su extensión."
        )

    # ------------------------------------------------------
    # Validar firma del archivo
    # ------------------------------------------------------

    try:
        posicion = archivo.tell()

        archivo.seek(0)

        primeros_bytes = archivo.read(8)

        archivo.seek(posicion)

    except Exception:
        raise ValidationError(
            "No fue posible validar el archivo."
        )

    firma_valida = False

    if extension == ".pdf":
        firma_valida = primeros_bytes.startswith(b"%PDF")

    elif extension in [".jpg", ".jpeg"]:
        firma_valida = primeros_bytes.startswith(b"\xff\xd8\xff")

    elif extension == ".png":
        firma_valida = primeros_bytes.startswith(
            b"\x89PNG\r\n\x1a\n"
        )

    if not firma_valida:
        raise ValidationError(
            "El contenido del archivo no corresponde "
            "al tipo de archivo declarado."
        )