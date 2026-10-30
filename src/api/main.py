
from typing import Literal

import pandas as pd

from fastapi import FastAPI
from pydantic import BaseModel

from src.api.model_loader import obtener_modelo_activo
from src.database.crud import guardar_prediccion
from src.api.metrics import router as metrics_router
from src.api.model_version import router as model_version_router


# ============================================================
# CREACION DE LA API
# ============================================================

app = FastAPI(
    title="Sistema-MLOps API",
    description=(
        "API para prediccion de churn, monitoreo "
        "de metricas y gestion dinamica de modelos."
    ),
    version="1.1.0"
)


# ============================================================
# ESTADO DEL MODELO CARGADO
# ============================================================

# La API no carga modelos al iniciar.
# Se conserva el lazy loading del Sprint 2.

modelo = None
version_cargada = None


def obtener_modelo():
    """
    Consulta PostgreSQL para identificar la version activa.

    El cargador mantiene los artefactos en cache por ruta.
    Si cambia la version activa, carga el nuevo artefacto.
    """
    global modelo, version_cargada

    informacion = obtener_modelo_activo("churn")

    modelo = informacion["modelo"]
    version_cargada = informacion["version"]

    return informacion


# ============================================================
# ESQUEMA DE ENTRADA
# ============================================================

class ChurnInput(BaseModel):

    gender: Literal["Female", "Male"]

    SeniorCitizen: Literal[0, 1]

    Partner: Literal["Yes", "No"]

    Dependents: Literal["Yes", "No"]

    tenure: int

    PhoneService: Literal["Yes", "No"]

    MultipleLines: Literal[
        "Yes",
        "No",
        "No phone service"
    ]

    InternetService: Literal[
        "DSL",
        "Fiber optic",
        "No"
    ]

    OnlineSecurity: Literal[
        "Yes",
        "No",
        "No internet service"
    ]

    OnlineBackup: Literal[
        "Yes",
        "No",
        "No internet service"
    ]

    DeviceProtection: Literal[
        "Yes",
        "No",
        "No internet service"
    ]

    TechSupport: Literal[
        "Yes",
        "No",
        "No internet service"
    ]

    StreamingTV: Literal[
        "Yes",
        "No",
        "No internet service"
    ]

    StreamingMovies: Literal[
        "Yes",
        "No",
        "No internet service"
    ]

    Contract: Literal[
        "Month-to-month",
        "One year",
        "Two year"
    ]

    PaperlessBilling: Literal["Yes", "No"]

    PaymentMethod: Literal[
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)"
    ]

    MonthlyCharges: float

    TotalCharges: float


# ============================================================
# GET /
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Sistema-MLOps API",
        "model": "churn_model",
        "status": "running"
    }


# ============================================================
# GET /health
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model": "churn_model",
        "model_version": version_cargada,
        "model_loaded": modelo is not None
    }


# ============================================================
# POST /predict
# ============================================================

@app.post("/predict")
def predict(datos: ChurnInput):

    # Consultar la version activa desde PostgreSQL.
    informacion = obtener_modelo()

    modelo_activo = informacion["modelo"]
    version_activa = informacion["version"]

    # Convertir la entrada a DataFrame.
    df_input = pd.DataFrame([
        datos.model_dump()
    ])

    # Aplicar One-Hot Encoding.
    df_input = pd.get_dummies(
        df_input,
        dtype=int
    )

    # Alinear las columnas con el modelo entrenado.
    columnas_modelo = modelo_activo.feature_names_in_

    df_input = df_input.reindex(
        columns=columnas_modelo,
        fill_value=0
    )

    # Generar prediccion.
    prediccion = int(
        modelo_activo.predict(df_input)[0]
    )

    # Calcular probabilidad.
    probabilidad = float(
        modelo_activo.predict_proba(df_input)[0][1]
    )

    # Guardar la prediccion con la version real utilizada.
    prediccion_id = guardar_prediccion(
        caso_uso="churn",
        input_data=datos.model_dump(),
        prediction=prediccion,
        probability=probabilidad,
        model_version=version_activa
    )

    return {
        "prediction": prediccion,
        "prediction_label": (
            "Yes" if prediccion == 1 else "No"
        ),
        "churn_probability": round(
            probabilidad,
            4
        ),
        "model_version": version_activa,
        "prediction_id": prediccion_id
    }


# ============================================================
# GET /metrics
# ============================================================

app.include_router(metrics_router)


# ============================================================
# GET /model-version
# ============================================================

app.include_router(model_version_router)
