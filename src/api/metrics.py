from fastapi import APIRouter, HTTPException

from src.database.connection import get_connection


router = APIRouter(tags=["Monitoreo"])


@router.get(
    "/metrics",
    summary="Consultar métricas del modelo activo"
)
def consultar_metricas():
    """
    Consulta las métricas del modelo activo de churn
    almacenadas en PostgreSQL.
    """

    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                WITH modelo_activo AS (
                    SELECT caso_uso, version, algoritmo
                    FROM model_versions
                    WHERE caso_uso = %s
                      AND estado = 'activa'
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                )
                SELECT
                    v.version,
                    v.algoritmo,
                    m.accuracy,
                    m.precision,
                    m.recall,
                    m.f1_score,
                    m.roc_auc
                FROM modelo_activo v
                LEFT JOIN LATERAL (
                    SELECT
                        accuracy,
                        precision,
                        recall,
                        f1_score,
                        roc_auc
                    FROM model_metrics
                    WHERE caso_uso = v.caso_uso
                      AND model_version = v.version
                      AND algoritmo = v.algoritmo
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                ) m ON TRUE;
                """,
                ("churn",)
            )

            resultado = cursor.fetchone()

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar las métricas."
        ) from error

    finally:
        if conexion is not None:
            conexion.close()

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="No existe una versión activa del modelo."
        )

    if resultado[2] is None:
        raise HTTPException(
            status_code=404,
            detail="El modelo activo no tiene métricas registradas."
        )

    return {
        "caso_uso": "churn",
        "model_version": resultado[0],
        "algoritmo": resultado[1],
        "accuracy": resultado[2],
        "precision": resultado[3],
        "recall": resultado[4],
        "f1_score": resultado[5],
        "roc_auc": resultado[6]
    }