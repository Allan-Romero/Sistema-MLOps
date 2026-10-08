from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main


RUTA_MODELO = (
    Path(__file__).resolve().parents[1] / "models" / "churn_model_v1.joblib"
)

client = TestClient(
    api_main.app
)


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
    "TotalCharges": 29.85
}


def test_endpoint_root():
    response = client.get(
        "/"
    )

    assert response.status_code == 200

    data = response.json()

    assert data[
        "message"
    ] == "Sistema-MLOps API"

    assert data[
        "status"
    ] == "running"

    assert data[
        "model"
    ] == "churn_model_v1"


def test_endpoint_health():
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data[
        "status"
    ] == "healthy"

    assert data[
        "model"
    ] == "churn_model"

    assert data[
        "model_version"
    ] == "v1"
    
    assert isinstance(
        data[
            "model_loaded"
        ],
        bool
    )

@pytest.mark.skipif(
    not RUTA_MODELO.exists(),
    reason="El modelo entrenado no está disponible en este entorno"
)

def test_endpoint_predict(
    monkeypatch
):
    def guardar_prediccion_mock(
        **kwargs
    ):
        return 999

    monkeypatch.setattr(
        api_main,
        "guardar_prediccion",
        guardar_prediccion_mock
    )

    response = client.post(
        "/predict",
        json=DATOS_CLIENTE
    )

    assert response.status_code == 200

    data = response.json()

    assert data[
        "prediction"
    ] in [
        0,
        1
    ]

    assert data[
        "prediction_label"
    ] in [
        "Yes",
        "No"
    ]

    assert (
        0
        <= data[
            "churn_probability"
        ]
        <= 1
    )

    assert data[
        "model_version"
    ] == "v1"

    assert data[
        "prediction_id"
    ] == 999


def test_endpoint_predict_datos_invalidos():
    datos_invalidos = (
        DATOS_CLIENTE.copy()
    )

    datos_invalidos[
        "gender"
    ] = "ValorInvalido"

    response = client.post(
        "/predict",
        json=datos_invalidos
    )

    assert response.status_code == 422