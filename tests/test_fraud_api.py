"""Pruebas HTTP del caso fraude, sin PostgreSQL ni modelos reales."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api import fraud
from src.training.fraud_features import FEATURE_COLUMNS

CLIENT = TestClient(app)


def entrada():
    return {col: 1.0 for col in FEATURE_COLUMNS}


@pytest.fixture
def entorno_falso(monkeypatch):
    llamadas = []
    modelo = MagicMock()
    modelo.predict.return_value = [1]
    modelo.predict_proba.return_value = [[0.05, 0.95]]
    modelo.feature_names_in_ = list(FEATURE_COLUMNS)

    def cargar(caso):
        assert caso == "fraude"
        return {"modelo": modelo, "version": "v1.0"}

    def guardar(**kwargs):
        llamadas.append(kwargs)
        return 17

    monkeypatch.setattr(fraud, "obtener_modelo_activo", cargar)
    monkeypatch.setattr(fraud, "guardar_prediccion", guardar)
    return modelo, llamadas


def test_fraude_responde_y_audita(entorno_falso):
    modelo, llamadas = entorno_falso
    r = CLIENT.post('/predict-fraud', json=entrada())
    assert r.status_code == 200, r.text
    assert r.json() == {
        'prediction': 1, 'prediction_label': 'Fraude',
        'fraud_probability': .95, 'model_version': 'v1.0',
        'caso_uso': 'fraude', 'prediction_id': 17,
    }
    assert len(llamadas) == 1
    assert llamadas[0]['caso_uso'] == 'fraude'
    assert llamadas[0]['model_version'] == 'v1.0'
    assert len(llamadas[0]['input_data']) == 30
    assert list(modelo.predict.call_args.args[0].columns) == list(FEATURE_COLUMNS)


def test_fraude_no_registra_clase_real(entorno_falso):
    _, llamadas = entorno_falso
    r = CLIENT.post('/predict-fraud', json={**entrada(), 'Class': 1})
    assert r.status_code == 422
    assert not llamadas


def test_fraude_falta_columna(entorno_falso):
    payload = entrada()
    payload.pop('V16')
    r = CLIENT.post('/predict-fraud', json=payload)
    assert r.status_code == 422


@pytest.mark.parametrize('campo,valor', [('Amount',-1),('Time',-1),('Amount',None),('V4','no valido')])
def test_fraude_rechaza_dato_invalido(entorno_falso,campo,valor):
    r = CLIENT.post('/predict-fraud', json={**entrada(),campo:valor})
    assert r.status_code == 422


def test_fraude_no_persiste_y_retorna_503(entorno_falso, monkeypatch):
    def error(**kwargs):
        raise RuntimeError('base no disponible')
    monkeypatch.setattr(fraud,'guardar_prediccion',error)
    r=CLIENT.post('/predict-fraud',json=entrada())
    assert r.status_code==503


def test_fraude_prediccion_negativa(entorno_falso):
    modelo,_=entorno_falso
    modelo.predict.return_value=[0]
    r=CLIENT.post('/predict-fraud',json=entrada())
    assert r.status_code==200
    assert r.json()['prediction_label']=='Legítima'


def test_version_fraude(monkeypatch):
    monkeypatch.setattr(fraud,'obtener_version_activa',lambda caso: [(1,'fraude','v1.0','xgboost','f1_score',.78,'activa',None)])
    r=CLIENT.get('/model-version/fraude')
    assert r.status_code==200
    assert r.json()['model_version']=='v1.0'
    assert r.json()['caso_uso']=='fraude'


def test_version_fraude_inexistente(monkeypatch):
    monkeypatch.setattr(fraud,'obtener_version_activa',lambda caso: [])
    r=CLIENT.get('/model-version/fraude')
    assert r.status_code==404


def test_swagger_publica_fraude():
    r=CLIENT.get('/openapi.json')
    assert r.status_code==200
    assert '/predict-fraud' in r.json()['paths']
    assert '/model-version/fraude' in r.json()['paths']
