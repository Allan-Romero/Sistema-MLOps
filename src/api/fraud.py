"""API S4-J5: segundo caso de uso, sin alterar predicciones de churn.

El mismo cargador dinámico de S4-J1 consulta PostgreSQL para obtener la
versión activa de `fraude`. Su artefacto es el que registró S4-J2.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat
import pandas as pd

from src.api.model_loader import obtener_modelo_activo
from src.api.ab_models import obtener_modelo_ab
from src.api.ab_routing import obtener_experimento_activo, seleccionar_version_ab
from src.database.crud import guardar_prediccion, obtener_version_activa
from src.training.fraud_features import FEATURE_COLUMNS

router = APIRouter(tags=["Fraude"])


class FraudInput(BaseModel):
    """30 variables del dataset Credit Card Fraud Detection, sin la etiqueta Class."""

    model_config = ConfigDict(extra="forbid")

    Time: FiniteFloat = Field(ge=0, description="Segundos transcurridos")
    V1: FiniteFloat
    V2: FiniteFloat
    V3: FiniteFloat
    V4: FiniteFloat
    V5: FiniteFloat
    V6: FiniteFloat
    V7: FiniteFloat
    V8: FiniteFloat
    V9: FiniteFloat
    V10: FiniteFloat
    V11: FiniteFloat
    V12: FiniteFloat
    V13: FiniteFloat
    V14: FiniteFloat
    V15: FiniteFloat
    V16: FiniteFloat
    V17: FiniteFloat
    V18: FiniteFloat
    V19: FiniteFloat
    V20: FiniteFloat
    V21: FiniteFloat
    V22: FiniteFloat
    V23: FiniteFloat
    V24: FiniteFloat
    V25: FiniteFloat
    V26: FiniteFloat
    V27: FiniteFloat
    V28: FiniteFloat
    Amount: FiniteFloat = Field(ge=0, description="Importe de la transacción")


@router.post(
    "/predict-fraud",
    summary="Predecir fraude con la versión activa registrada en PostgreSQL",
)
def predecir_fraude(datos: FraudInput):
    # No fijar ni la versión ni la ruta del .joblib; soporte de J1/J2.
    try:
        experimento = obtener_experimento_activo("fraude")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="No fue posible consultar el experimento A/B.") from exc
    if experimento is None:
        informacion = obtener_modelo_activo("fraude")
    else:
        asignacion = seleccionar_version_ab(experimento)
        informacion = obtener_modelo_ab("fraude", asignacion["version"], asignacion["grupo"])
    modelo = informacion["modelo"]
    version = informacion["version"]

    entrada = datos.model_dump()
    x = pd.DataFrame([entrada], columns=list(FEATURE_COLUMNS))
    prediccion = int(modelo.predict(x)[0])
    probabilidad = float(modelo.predict_proba(x)[0][1])

    # No devolver 200 si no pudimos auditar la predicción.
    try:
        prediccion_id = guardar_prediccion(
            caso_uso="fraude",
            input_data=entrada,
            prediction=prediccion,
            probability=probabilidad,
            model_version=version,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="No fue posible registrar la predicción de fraude.",
        ) from exc

    return {
        "prediction": prediccion,
        "prediction_label": "Fraude" if prediccion == 1 else "Legítima",
        "fraud_probability": round(probabilidad, 6),
        "model_version": version,
        "caso_uso": "fraude",
        "prediction_id": prediccion_id,
    }


@router.get(
    "/model-version/fraude",
    summary="Consultar la versión activa del modelo de fraude",
)
def consultar_version_fraude():
    try:
        registros = obtener_version_activa("fraude")
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar la versión del modelo de fraude.",
        ) from exc

    if not registros:
        raise HTTPException(
            status_code=404,
            detail="No existe una versión activa del modelo de fraude.",
        )

    registro = registros[0]
    return {
        "caso_uso": "fraude",
        "model_version": registro[2],
        "algoritmo": registro[3],
        "metrica_principal": registro[4],
        "valor_metrica": registro[5],
        "estado": registro[6],
        "fecha_promocion": registro[7],
    }
