
import re

from fastapi import HTTPException

from src.api.model_loader import (
    MODELS_DIR,
    cargar_archivo_modelo,
)
from src.database.crud import ejecutar_consulta


def obtener_modelo_ab(caso_uso, version, grupo):
    """
    Carga la versión seleccionada para un experimento A/B.

    Grupo A: modelo activo en producción.
    Grupo B: modelo registrado como candidato.

    No permite servir modelos descartados.
    """

    if grupo not in ("A", "B"):
        raise HTTPException(
            status_code=400,
            detail="Grupo A/B inválido.",
        )

    if not isinstance(caso_uso, str) or not re.fullmatch(
        r"[a-z][a-z0-9_]*", caso_uso
    ):
        raise HTTPException(
            status_code=400,
            detail="Caso de uso inválido.",
        )

    if not isinstance(version, str) or not re.fullmatch(
        r"v\d+(?:\.\d+)*", version
    ):
        raise HTTPException(
            status_code=400,
            detail="Versión de modelo inválida.",
        )

    try:
        registros = ejecutar_consulta(
            """
            SELECT version, algoritmo, estado
            FROM model_versions
            WHERE caso_uso = %s
              AND version = %s
            ORDER BY id DESC
            LIMIT 1;
            """,
            (caso_uso, version),
        )
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar el modelo A/B.",
        ) from error

    if not registros:
        raise HTTPException(
            status_code=404,
            detail=f"No existe la versión {version}.",
        )

    version_db, algoritmo, estado = registros[0]

    if grupo == "A" and estado != "activa":
        raise HTTPException(
            status_code=409,
            detail="El grupo A debe usar la versión activa.",
        )

    if grupo == "B" and estado != "candidata":
        raise HTTPException(
            status_code=409,
            detail="El grupo B requiere una versión candidata.",
        )

    ruta = MODELS_DIR / (
        f"{caso_uso}_model_{version_db}.joblib"
    )

    if not ruta.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"No existe el artefacto {version_db}.",
        )

    try:
        modelo = cargar_archivo_modelo(str(ruta))
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible cargar el modelo A/B.",
        ) from error

    return {
        "modelo": modelo,
        "caso_uso": caso_uso,
        "version": version_db,
        "algoritmo": algoritmo,
        "estado": estado,
        "grupo": grupo,
    }
