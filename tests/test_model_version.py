from datetime import datetime

from fastapi.testclient import TestClient

from src.api.main import app
from src.api import model_version


client = TestClient(app)


def test_model_version_activa(monkeypatch):

    fecha = datetime(2026, 10, 9, 6, 25, 26)

    registro = (
        1,
        "churn",
        "v1",
        "logistic_regression",
        "f1_score",
        0.6031746031746031,
        "activa",
        fecha
    )

    monkeypatch.setattr(
        model_version,
        "obtener_version_activa",
        lambda caso_uso: [registro]
    )

    respuesta = client.get("/model-version")

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["caso_uso"] == "churn"
    assert datos["model_version"] == "v1"
    assert datos["algoritmo"] == "logistic_regression"
    assert datos["estado"] == "activa"
    assert datos["fecha_promocion"] == fecha.isoformat()


def test_model_version_sin_version_activa(monkeypatch):

    monkeypatch.setattr(
        model_version,
        "obtener_version_activa",
        lambda caso_uso: []
    )

    respuesta = client.get("/model-version")

    assert respuesta.status_code == 404

    assert respuesta.json()["detail"] == (
        "No existe una versión activa del modelo."
    )


def test_model_version_error_base_datos(monkeypatch):

    def simular_error(caso_uso):
        raise RuntimeError("Error de conexión")

    monkeypatch.setattr(
        model_version,
        "obtener_version_activa",
        simular_error
    )

    respuesta = client.get("/model-version")

    assert respuesta.status_code == 503