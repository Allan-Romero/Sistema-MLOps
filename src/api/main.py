"""API de predicción de churn con carga dinámica y enrutamiento A/B."""

from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.api.ab_models import obtener_modelo_ab
from src.api.ab_routing import obtener_experimento_activo, seleccionar_version_ab
from src.api.metrics import router as metrics_router
from src.api.fraud import router as fraud_router
from src.api.model_loader import obtener_modelo_activo
from src.api.model_version import router as model_version_router
from src.database.crud import guardar_prediccion

app = FastAPI(
    title="Sistema-MLOps API",
    description="API para predicción de churn, monitoreo y experimentos A/B.",
    version="1.2.0",
)

# Mantener las variables de salud de S4-J1.
modelo = None
version_cargada = None


def obtener_modelo():
    """Selecciona la versión de cada petición sin fijar rutas a modelos.

    Sin experimento sirve la versión activa. Con experimento, sirve A o B
    según la distribución registrada. Nunca usa un modelo descartado.
    """
    global modelo, version_cargada

    try:
        experimento = obtener_experimento_activo("churn")
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar el experimento A/B.",
        ) from error

    if experimento is None:
        informacion = obtener_modelo_activo("churn")
        asignacion = None
    else:
        asignacion = seleccionar_version_ab(experimento)
        informacion = obtener_modelo_ab(
            "churn",
            asignacion["version"],
            asignacion["grupo"],
        )

    modelo = informacion["modelo"]
    version_cargada = informacion["version"]

    return {
        **informacion,
        "experimento_id": (
            asignacion["experimento_id"] if asignacion else None
        ),
        "grupo_ab": asignacion["grupo"] if asignacion else None,
    }


class ChurnInput(BaseModel):
    gender: Literal["Female", "Male"]
    SeniorCitizen: Literal[0, 1]
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int
    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]
    PaymentMethod: Literal[
        "Electronic check", "Mailed check",
        "Bank transfer (automatic)", "Credit card (automatic)",
    ]
    MonthlyCharges: float
    TotalCharges: float


@app.get("/")
def root():
    return {
        "message": "Sistema-MLOps API",
        "model": "churn_model",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "churn_model",
        "model_version": version_cargada,
        "model_loaded": modelo is not None,
    }


@app.post("/predict")
def predict(datos: ChurnInput):
    informacion = obtener_modelo()
    modelo_seleccionado = informacion["modelo"]
    version_seleccionada = informacion["version"]

    # Conservar las 19 variables originales en el registro de predicción.
    datos_entrada = datos.model_dump()
    df_input = pd.DataFrame([datos_entrada])
    df_input = pd.get_dummies(df_input, dtype=int)
    df_input = df_input.reindex(
        columns=modelo_seleccionado.feature_names_in_, fill_value=0
    )

    prediccion = int(modelo_seleccionado.predict(df_input)[0])
    probabilidad = float(modelo_seleccionado.predict_proba(df_input)[0][1])

    prediccion_id = guardar_prediccion(
        caso_uso="churn",
        input_data=datos_entrada,
        prediction=prediccion,
        probability=probabilidad,
        model_version=version_seleccionada,
    )

    respuesta = {
        "prediction": prediccion,
        "prediction_label": "Yes" if prediccion == 1 else "No",
        "churn_probability": round(probabilidad, 4),
        "model_version": version_seleccionada,
        "prediction_id": prediccion_id,
    }

    if informacion.get("experimento_id") is not None:
        respuesta["experiment_id"] = informacion["experimento_id"]
        respuesta["ab_group"] = informacion["grupo_ab"]

    return respuesta


app.include_router(metrics_router)
app.include_router(model_version_router)
app.include_router(fraud_router)
