"""Endpoint del modelo activo y de la configuración de tráfico A/B."""

from fastapi import APIRouter, HTTPException

from src.api.ab_routing import obtener_experimento_activo
from src.database.crud import obtener_version_activa

router = APIRouter(tags=["Monitoreo"])


@router.get(
    "/model-version",
    summary="Consultar modelo activo y distribución A/B",
)
def consultar_version_modelo():
    try:
        registros = obtener_version_activa("churn")
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar la versión del modelo.",
        ) from error

    if not registros:
        raise HTTPException(
            status_code=404,
            detail="No existe una versión activa del modelo.",
        )

    try:
        experimento = obtener_experimento_activo("churn")
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar el experimento A/B.",
        ) from error

    registro = registros[0]
    ab = {"activo": False}

    if experimento is not None:
        ab = {
            "activo": True,
            "experimento_id": experimento["experimento_id"],
            "version_a": experimento["version_a"],
            "version_b": experimento["version_b"],
            "porcentaje_trafico_b": experimento["porcentaje_trafico_b"],
            "porcentaje_trafico_a": 100 - experimento["porcentaje_trafico_b"],
        }

    return {
        "caso_uso": registro[1],
        "model_version": registro[2],
        "algoritmo": registro[3],
        "estado": registro[6],
        "fecha_promocion": registro[7],
        "experimento_ab": ab,
    }
