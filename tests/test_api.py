
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api import main as api_main


client = TestClient(api_main.app)


DATOS_CLIENTE = {
    "gender": "Female",
    "SeniorCitizen": 0,
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": 1,
    "PhoneService": "No",
    "MultipleLines": "No phone service",
    "InternetService": "DSL",
    "OnlineSecurity": "No",
    "OnlineBackup": "Yes",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "No",
    "StreamingMovies": "No",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 29.85,
    "TotalCharges": 29.85,
}


class ModeloSimulado:
    """Modelo de prueba: no necesita archivos joblib."""

    feature_names_in_ = [
        "tenure",
        "MonthlyCharges",
        "TotalCharges",
        "gender_Female",
    ]

    def predict(self, datos):
        return [1]

    def predict_proba(self, datos):
        return [[0.38, 0.62]]


def test_endpoint_root():
    respuesta = client.get("/")

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["message"] == "Sistema-MLOps API"
    assert datos["model"] == "churn_model"
    assert datos["status"] == "running"


def test_endpoint_health_sin_modelo(monkeypatch):
    monkeypatch.setattr(api_main, "modelo", None)
    monkeypatch.setattr(api_main, "version_cargada", None)

    respuesta = client.get("/health")

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["status"] == "healthy"
    assert datos["model_loaded"] is False
    assert datos["model_version"] is None


def test_endpoint_health_con_modelo(monkeypatch):
    monkeypatch.setattr(
        api_main, "modelo", ModeloSimulado()
    )
    monkeypatch.setattr(
        api_main, "version_cargada", "v1.0"
    )

    respuesta = client.get("/health")

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["model_loaded"] is True
    assert datos["model_version"] == "v1.0"


def test_endpoint_predict_version_dinamica(monkeypatch):
    """
    Verifica que la predicción use y almacene
    la versión activa, sin conectarse a PostgreSQL.
    """

    informacion_modelo = {
        "modelo": ModeloSimulado(),
        "caso_uso": "churn",
        "version": "v1.0",
        "algoritmo": "logistic_regression",
    }

    monkeypatch.setattr(
        api_main,
        "obtener_modelo",
        lambda: informacion_modelo
    )

    registro = {}

    def guardar_prediccion_simulada(**kwargs):
        registro.update(kwargs)
        return 999

    monkeypatch.setattr(
        api_main,
        "guardar_prediccion",
        guardar_prediccion_simulada
    )

    respuesta = client.post(
        "/predict",
        json=DATOS_CLIENTE
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["prediction"] == 1
    assert datos["prediction_label"] == "Yes"
    assert datos["churn_probability"] == 0.62
    assert datos["model_version"] == "v1.0"
    assert datos["prediction_id"] == 999

    assert registro["caso_uso"] == "churn"
    assert registro["model_version"] == "v1.0"
    assert registro["prediction"] == 1


def test_endpoint_predict_sin_version_activa(monkeypatch):
    """La API debe responder con un error controlado."""

    def simular_sin_modelo():
        raise HTTPException(
            status_code=404,
            detail="No existe una versión activa del modelo."
        )

    monkeypatch.setattr(
        api_main,
        "obtener_modelo",
        simular_sin_modelo
    )

    respuesta = client.post(
        "/predict",
        json=DATOS_CLIENTE
    )

    assert respuesta.status_code == 404

    assert respuesta.json()["detail"] == (
        "No existe una versión activa del modelo."
    )


def test_endpoint_predict_datos_invalidos():
    datos_invalidos = DATOS_CLIENTE.copy()
    datos_invalidos["gender"] = "ValorInvalido"

    respuesta = client.post(
        "/predict",
        json=datos_invalidos
    )

    assert respuesta.status_code == 422
