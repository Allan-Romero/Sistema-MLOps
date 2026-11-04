
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

    # Un experimento pospromoción compara la activa B con su predecesora A.
    # La pareja debe corresponder a una promoción auditada, no a una histórica cualquiera.
    pospromocion = False
    if (grupo == "A" and estado == "historica") or (grupo == "B" and estado == "activa"):
        try:
            parejas = ejecutar_consulta(
                """SELECT e.id FROM experiments e
                   JOIN promotion_decisions p ON p.caso_uso = e.caso_uso
                     AND p.version_anterior = e.version_a
                     AND p.version_candidata = e.version_b AND p.resultado = 'promovida'
                   JOIN model_versions a ON a.caso_uso = e.caso_uso AND a.version = e.version_a
                   JOIN model_versions b ON b.caso_uso = e.caso_uso AND b.version = e.version_b
                   WHERE e.caso_uso = %s AND e.estado = 'activo'
                     AND a.estado = 'historica' AND b.estado = 'activa'
                     AND (CASE WHEN %s = 'A' THEN e.version_a ELSE e.version_b END) = %s;""",
                (caso_uso, grupo, version_db),
            )
            pospromocion = bool(parejas)
        except Exception as error:
            raise HTTPException(status_code=503, detail="No fue posible validar la promoción A/B.") from error

    if grupo == "A" and estado != "activa" and not pospromocion:
        raise HTTPException(
            status_code=409,
            detail="El grupo A debe usar la versión activa.",
        )

    if grupo == "B" and estado != "candidata" and not pospromocion:
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
