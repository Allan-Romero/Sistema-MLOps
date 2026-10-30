
from functools import lru_cache
from pathlib import Path
import re

import joblib
from fastapi import HTTPException

from src.database.crud import obtener_version_activa


MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


@lru_cache(maxsize=10)
def cargar_archivo_modelo(ruta: str):
    """Carga un artefacto una sola vez por ruta."""
    return joblib.load(ruta)


def obtener_modelo_activo(caso_uso: str = "churn"):
    """
    Consulta PostgreSQL y carga el artefacto correspondiente
    a la versión activa del caso de uso.
    """

    try:
        registros = obtener_version_activa(caso_uso)
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar la versión activa."
        ) from error

    if not registros:
        raise HTTPException(
            status_code=404,
            detail="No existe una versión activa del modelo."
        )

    registro = registros[0]
    version = registro[2]
    algoritmo = registro[3]

    # Validar los identificadores antes de construir la ruta.
    if not (
        re.fullmatch(r"[a-z][a-z0-9_]*", caso_uso)
        and re.fullmatch(r"v\d+(?:\.\d+)*", version)
    ):
        raise HTTPException(
            status_code=503,
            detail="Identificador de modelo o versión inválido."
        )

    ruta_modelo = (
        MODELS_DIR / f"{caso_uso}_model_{version}.joblib"
    )

    if not ruta_modelo.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"No existe el artefacto de la versión {version}."
        )

    try:
        modelo = cargar_archivo_modelo(str(ruta_modelo))
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible cargar el modelo activo."
        ) from error

    return {
        "modelo": modelo,
        "caso_uso": caso_uso,
        "version": version,
        "algoritmo": algoritmo,
    }
