from pathlib import Path
from typing import Literal

import joblib
import pandas as pd

from fastapi import FastAPI
from pydantic import BaseModel

from src.database.crud import guardar_prediccion
from src.api.metrics import router as metrics_router
from src.api.model_version import router as model_version_router


# ============================================================
# CONFIGURACION DEL PROYECTO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT / "models" / "churn_model_v1.joblib"
)


# ============================================================
# CREACION DE LA API
# ============================================================

app = FastAPI(
    title="Sistema-MLOps API",
    description=(
        "API para prediccion de churn, monitoreo "
        "de metricas y gestion de versiones del modelo."
    ),
    version="1.0.0"
)


# ============================================================
# CARGA DEL MODELO
# ============================================================

def cargar_modelo():
    """
    Carga el modelo oficial de churn version 1.
    """

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"No se encontro el modelo en: {MODEL_FILE}"
        )

    return joblib.load(MODEL_FILE)


modelo = None


def obtener_modelo():
    """
    Carga el modelo la primera vez que se solicita
    y lo mantiene en memoria para las siguientes llamadas.
    """

    global modelo

    if modelo is None:
        modelo = cargar_modelo()

    return modelo


# ============================================================
# ESQUEMA DE ENTRADA PARA PREDICCIONES
# ============================================================

class ChurnInput(BaseModel):

    gender: Literal[
        "Female",
        "Male"
    ]

    SeniorCitizen: Literal[0, 1]

    Partner: Literal[
        "Yes",
        "No"
    ]

    Dependents: Literal[
        "Yes",
        "No"
    ]

    tenure: int

    PhoneService: Literal[
        "Yes",
        "No"
    ]

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

    PaperlessBilling: Literal[
        "Yes",
        "No"
    ]

    PaymentMethod: Literal[
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)"
    ]

    MonthlyCharges: float

    TotalCharges: float


# ============================================================
# ENDPOINT PRINCIPAL
# GET /
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Sistema-MLOps API",
        "model": "churn_model_v1",
        "status": "running"
    }


# ============================================================
# ENDPOINT DE SALUD
# GET /health
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model": "churn_model",
        "model_version": "v1",
        "model_loaded": modelo is not None
    }


# ============================================================
# ENDPOINT DE PREDICCION
# POST /predict
# ============================================================

@app.post("/predict")
def predict(datos: ChurnInput):

    # Obtener modelo entrenado
    modelo_activo = obtener_modelo()

    # Convertir datos recibidos a DataFrame
    df_input = pd.DataFrame(
        [datos.model_dump()]
    )

    # Aplicar One-Hot Encoding
    df_input = pd.get_dummies(
        df_input,
        dtype=int
    )

    # Obtener columnas utilizadas durante entrenamiento
    columnas_modelo = modelo_activo.feature_names_in_

    # Alinear variables con el modelo
    df_input = df_input.reindex(
        columns=columnas_modelo,
        fill_value=0
    )

    # Ejecutar prediccion
    prediccion = int(
        modelo_activo.predict(df_input)[0]
    )

    # Obtener probabilidad
    probabilidad = float(
        modelo_activo.predict_proba(df_input)[0][1]
    )

    # Guardar prediccion en PostgreSQL
    prediccion_id = guardar_prediccion(
        caso_uso="churn",
        input_data=datos.model_dump(),
        prediction=prediccion,
        probability=probabilidad,
        model_version="v1"
    )

    # Retornar resultado
    return {
        "prediction": prediccion,
        "prediction_label": (
            "Yes" if prediccion == 1 else "No"
        ),
        "churn_probability": round(
            probabilidad,
            4
        ),
        "model_version": "v1",
        "prediction_id": prediccion_id
    }


# ============================================================
# SPRINT 3 - J3
# ENDPOINT DE METRICAS DEL MODELO ACTIVO
# GET /metrics
# ============================================================

app.include_router(metrics_router)


# ============================================================
# SPRINT 3 - J4
# ENDPOINT DE VERSION ACTIVA DEL MODELO
# GET /model-version
# ============================================================

app.include_router(model_version_router)