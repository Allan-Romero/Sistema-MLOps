from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main
from src.monitoring import prediction_features as features


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


def simular_base_datos(monkeypatch, registros):
    conexion = MagicMock()

    cursor = (
        conexion.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchall.return_value = registros

    monkeypatch.setattr(
        features,
        "get_connection",
        lambda: conexion
    )

    return conexion


def test_recuperar_predicciones_completas(monkeypatch):
    conexion = simular_base_datos(
        monkeypatch,
        [
            (DATOS_CLIENTE.copy(),),
            (DATOS_CLIENTE.copy(),)
        ]
    )

    df = features.obtener_predicciones_dataframe(
        limite=10
    )

    assert df.shape == (2, 19)
    assert df.isnull().sum().sum() == 0

    assert list(df.columns) == list(
        api_main.ChurnInput.model_fields.keys()
    )

    assert df.iloc[0]["gender"] == "Female"

    conexion.close.assert_called_once()


def test_prediccion_incompleta(monkeypatch):
    datos_incompletos = DATOS_CLIENTE.copy()
    datos_incompletos.pop("MonthlyCharges")

    simular_base_datos(
        monkeypatch,
        [(datos_incompletos,)]
    )

    with pytest.raises(
        ValueError,
        match="19 variables"
    ):
        features.obtener_predicciones_dataframe()


def test_recuperar_sin_registros(monkeypatch):
    simular_base_datos(monkeypatch, [])

    df = features.obtener_predicciones_dataframe()

    assert df.empty
    assert len(df.columns) == 19


def test_predict_almacena_19_variables(monkeypatch):
    modelo_simulado = MagicMock()

    modelo_simulado.feature_names_in_ = [
        "SeniorCitizen",
        "tenure",
        "MonthlyCharges",
        "TotalCharges"
    ]

    modelo_simulado.predict.return_value = [1]

    modelo_simulado.predict_proba.return_value = [
        [0.25, 0.75]
    ]

    monkeypatch.setattr(
        api_main,
        "obtener_modelo",
        lambda: modelo_simulado
    )

    datos_guardados = {}

    def guardar_prediccion_simulada(**kwargs):
        datos_guardados.update(kwargs)
        return 999

    monkeypatch.setattr(
        api_main,
        "guardar_prediccion",
        guardar_prediccion_simulada
    )

    cliente = TestClient(api_main.app)

    respuesta = cliente.post(
        "/predict",
        json=DATOS_CLIENTE
    )

    assert respuesta.status_code == 200

    assert respuesta.json()["prediction_id"] == 999

    assert datos_guardados["caso_uso"] == "churn"

    assert datos_guardados["model_version"] == "v1"

    assert len(datos_guardados["input_data"]) == 19

    assert datos_guardados["input_data"] == DATOS_CLIENTE