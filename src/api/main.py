from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_FILE = PROJECT_ROOT / "models" / "churn_model_v1.joblib"


# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema-MLOps API",
    description="API para servir el modelo de predicción de churn.",
    version="1.0.0"
)


def cargar_modelo():
    """Carga el modelo oficial de churn versión 1."""

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo en: {MODEL_FILE}"
        )

    return joblib.load(MODEL_FILE)


modelo = cargar_modelo()

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
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)"
    ]
    MonthlyCharges: float
    TotalCharges: float

@app.get("/")
def root():
    return {
        "message": "Sistema-MLOps API",
        "model": "churn_model_v1",
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "churn_model",
        "model_version": "v1",
        "model_loaded": modelo is not None
    }

@app.post("/predict")
def predict(datos: ChurnInput):
    # Convertir el JSON recibido a DataFrame
    df_input = pd.DataFrame([datos.model_dump()])

    # Aplicar One-Hot Encoding igual que durante el entrenamiento
    df_input = pd.get_dummies(df_input, dtype=int)

    # Obtener las columnas exactas utilizadas por el modelo
    columnas_modelo = modelo.feature_names_in_

    # Alinear el registro recibido con las 45 variables del modelo
    df_input = df_input.reindex(
        columns=columnas_modelo,
        fill_value=0
    )

    # Realizar predicción
    prediccion = int(modelo.predict(df_input)[0])

    # Probabilidad de churn
    probabilidad = float(
        modelo.predict_proba(df_input)[0][1]
    )

    return {
        "prediction": prediccion,
        "prediction_label": "Yes" if prediccion == 1 else "No",
        "churn_probability": round(probabilidad, 4),
        "model_version": "v1"
    }