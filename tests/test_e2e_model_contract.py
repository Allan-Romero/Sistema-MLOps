"""Verifica artefactos reales del ensayo contra los dos endpoints HTTP."""
import joblib
import pytest
from fastapi.testclient import TestClient
from scripts.e2e_deployment import entrenar_modelos, entrada
from src.api.main import app
from src.api import main, fraud
from src.training.fraud_features import FEATURE_COLUMNS


@pytest.mark.parametrize("caso", ["churn", "fraude"])
@pytest.mark.parametrize("indice_modelo", [0, 1])
def test_modelo_del_ensayo_es_compatible_con_api(caso, indice_modelo, monkeypatch, tmp_path):
    modelos = entrenar_modelos(caso)
    ruta = tmp_path / "modelo.joblib"
    joblib.dump(modelos[indice_modelo], ruta)
    modelo = joblib.load(ruta)
    if caso == "fraude":
        assert list(modelo.feature_names_in_) == list(FEATURE_COLUMNS)
        monkeypatch.setattr(fraud, "obtener_experimento_activo", lambda caso: None)
        monkeypatch.setattr(fraud, "obtener_modelo_activo", lambda caso: {"modelo": modelo, "version": "v1"})
        monkeypatch.setattr(fraud, "guardar_prediccion", lambda **kwargs: 1)
    else:
        monkeypatch.setattr(main, "obtener_modelo", lambda: {"modelo": modelo, "version": "v1"})
        monkeypatch.setattr(main, "guardar_prediccion", lambda **kwargs: 1)
    cliente = TestClient(app)
    endpoint = "/predict-fraud" if caso == "fraude" else "/predict"
    for valor, etiqueta in [(20, 0), (80, 1)]:
        respuesta = cliente.post(endpoint, json=entrada(caso, valor))
        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json()["prediction"] == (1 if indice_modelo == 0 else etiqueta)
