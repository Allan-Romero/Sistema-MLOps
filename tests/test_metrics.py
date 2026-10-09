from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.main import app
from src.api import metrics


client = TestClient(app)


def simular_base_datos(monkeypatch, resultado):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = resultado

    monkeypatch.setattr(
        metrics,
        "get_connection",
        lambda: conexion
    )

    return conexion


def test_metrics_modelo_activo(monkeypatch):
    simular_base_datos(
        monkeypatch,
        (
            "v1",
            "logistic_regression",
            0.8048,
            0.6551,
            0.5588,
            0.6031,
            0.8428
        )
    )

    respuesta = client.get("/metrics")

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["caso_uso"] == "churn"
    assert datos["model_version"] == "v1"
    assert datos["algoritmo"] == "logistic_regression"

    for metrica in [
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "roc_auc"
    ]:
        assert isinstance(datos[metrica], float)


def test_metrics_sin_modelo_activo(monkeypatch):
    simular_base_datos(monkeypatch, None)

    respuesta = client.get("/metrics")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == (
        "No existe una versión activa del modelo."
    )


def test_metrics_sin_metricas(monkeypatch):
    simular_base_datos(
        monkeypatch,
        ("v1", "logistic_regression", None, None, None, None, None)
    )

    respuesta = client.get("/metrics")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == (
        "El modelo activo no tiene métricas registradas."
    )