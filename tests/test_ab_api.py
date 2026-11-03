"""Pruebas de integración del enrutamiento A/B en FastAPI."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main

CLIENTE = TestClient(api_main.app)

DATOS_CLIENTE = {
    "gender": "Female", "SeniorCitizen": 0, "Partner": "Yes",
    "Dependents": "No", "tenure": 1, "PhoneService": "No",
    "MultipleLines": "No phone service", "InternetService": "DSL",
    "OnlineSecurity": "No", "OnlineBackup": "Yes",
    "DeviceProtection": "No", "TechSupport": "No",
    "StreamingTV": "No", "StreamingMovies": "No",
    "Contract": "Month-to-month", "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check", "MonthlyCharges": 29.85,
    "TotalCharges": 29.85,
}


def modelo_falso():
    modelo = MagicMock()
    modelo.feature_names_in_ = [
        "SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges",
    ]
    modelo.predict.return_value = [1]
    modelo.predict_proba.return_value = [[0.25, 0.75]]
    return modelo


@pytest.fixture
def evitar_escrituras(monkeypatch):
    registros = []

    def guardar(**kwargs):
        registros.append(kwargs)
        return len(registros)

    monkeypatch.setattr(api_main, "guardar_prediccion", guardar)
    return registros


def test_sin_experimento_usa_modelo_activo(monkeypatch, evitar_escrituras):
    monkeypatch.setattr(api_main, "obtener_experimento_activo", lambda caso: None)
    monkeypatch.setattr(
        api_main, "obtener_modelo_activo",
        lambda caso: {"modelo": modelo_falso(), "version": "v1.0"},
    )

    respuesta = CLIENTE.post("/predict", json=DATOS_CLIENTE)
    assert respuesta.status_code == 200
    assert respuesta.json()["model_version"] == "v1.0"
    assert "ab_group" not in respuesta.json()
    assert evitar_escrituras[0]["model_version"] == "v1.0"
    assert len(evitar_escrituras[0]["input_data"]) == 19


@pytest.mark.parametrize("grupo,version", [("A", "v1.0"), ("B", "v1.2")])
def test_experimento_guarda_version_elegida(
    monkeypatch, evitar_escrituras, grupo, version
):
    configuracion = {
        "experimento_id": 7,
        "version_a": "v1.0",
        "version_b": "v1.2",
        "porcentaje_trafico_b": 20,
    }
    monkeypatch.setattr(
        api_main, "obtener_experimento_activo", lambda caso: configuracion
    )
    monkeypatch.setattr(
        api_main, "seleccionar_version_ab",
        lambda experimento: {
            "experimento_id": 7, "grupo": grupo, "version": version,
            "porcentaje_trafico_b": 20,
        },
    )
    llamadas = []

    def cargar(caso, version_recibida, grupo_recibido):
        llamadas.append((caso, version_recibida, grupo_recibido))
        return {"modelo": modelo_falso(), "version": version_recibida}

    monkeypatch.setattr(api_main, "obtener_modelo_ab", cargar)
    respuesta = CLIENTE.post("/predict", json=DATOS_CLIENTE)

    assert respuesta.status_code == 200
    assert respuesta.json()["ab_group"] == grupo
    assert respuesta.json()["experiment_id"] == 7
    assert respuesta.json()["model_version"] == version
    assert evitar_escrituras[0]["model_version"] == version
    assert llamadas == [("churn", version, grupo)]


def test_consulta_experimento_fallida_da_503(monkeypatch, evitar_escrituras):
    def error(caso):
        raise RuntimeError("PostgreSQL no disponible")

    monkeypatch.setattr(api_main, "obtener_experimento_activo", error)
    respuesta = CLIENTE.post("/predict", json=DATOS_CLIENTE)
    assert respuesta.status_code == 503
    assert not evitar_escrituras
