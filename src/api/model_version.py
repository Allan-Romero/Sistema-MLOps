from fastapi import APIRouter, HTTPException

from src.database.crud import obtener_version_activa


router = APIRouter(tags=["Monitoreo"])


@router.get(
    "/model-version",
    summary="Consultar la versión activa del modelo"
)
def consultar_version_modelo():
    """
    Consulta PostgreSQL e identifica la versión activa
    del modelo de predicción de churn.
    """

    try:
        registros = obtener_version_activa("churn")

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar la versión del modelo."
        ) from error

    if not registros:
        raise HTTPException(
            status_code=404,
            detail="No existe una versión activa del modelo."
        )

    registro = registros[0]

    return {
        "caso_uso": registro[1],
        "model_version": registro[2],
        "algoritmo": registro[3],
        "estado": registro[6],
        "fecha_promocion": registro[7]
    }