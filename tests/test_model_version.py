from datetime import datetime

from fastapi.testclient import TestClient
from src.api.main import app
from src.api import model_version

cliente = TestClient(app)


def registro_activo():
    return (
        1, "churn", "v1.0", "logistic_regression",
        "f1_score", 0.6031746031746031, "activa",
        datetime(2026, 10, 24, 21, 49, 4),
    )


def test_model_version_sin_experimento(monkeypatch):
    monkeypatch.setattr(
        model_version, "obtener_version_activa", lambda caso: [registro_activo()]
    )
    monkeypatch.setattr(
        model_version, "obtener_experimento_activo", lambda caso: None
    )
    respuesta = cliente.get("/model-version")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["model_version"] == "v1.0"
    assert datos["estado"] == "activa"
    assert datos["experimento_ab"] == {"activo": False}


def test_model_version_con_experimento(monkeypatch):
    monkeypatch.setattr(
        model_version, "obtener_version_activa", lambda caso: [registro_activo()]
    )
    monkeypatch.setattr(
        model_version,
        "obtener_experimento_activo",
        lambda caso: {
            "experimento_id": 7, "version_a": "v1.0",
            "version_b": "v1.2", "porcentaje_trafico_b": 20,
        },
    )
    respuesta = cliente.get("/model-version")
    assert respuesta.status_code == 200
    ab = respuesta.json()["experimento_ab"]
    assert ab["activo"] is True
    assert ab["version_a"] == "v1.0"
    assert ab["version_b"] == "v1.2"
    assert ab["porcentaje_trafico_a"] == 80
    assert ab["porcentaje_trafico_b"] == 20


def test_sin_version_activa(monkeypatch):
    monkeypatch.setattr(model_version, "obtener_version_activa", lambda caso: [])
    respuesta = cliente.get("/model-version")
    assert respuesta.status_code == 404


def test_error_consulta_modelo(monkeypatch):
    def error(caso):
        raise RuntimeError("PostgreSQL no disponible")

    monkeypatch.setattr(model_version, "obtener_version_activa", error)
    respuesta = cliente.get("/model-version")
    assert respuesta.status_code == 503


def test_error_consulta_experimento(monkeypatch):
    monkeypatch.setattr(
        model_version, "obtener_version_activa", lambda caso: [registro_activo()]
    )

    def error(caso):
        raise RuntimeError("PostgreSQL no disponible")

    monkeypatch.setattr(model_version, "obtener_experimento_activo", error)
    respuesta = cliente.get("/model-version")
    assert respuesta.status_code == 503
