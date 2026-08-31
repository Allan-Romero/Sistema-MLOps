from pathlib import Path

import joblib
from fastapi import FastAPI


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