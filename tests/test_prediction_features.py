
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api import main as api_main
from src.monitoring import prediction_features as features


# ============================================================
# DATOS DE PRUEBA - CLIENTE CHURN
# ============================================================

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


# ============================================================
# SIMULACION DE BASE DE DATOS
# ============================================================

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


# ============================================================
# TEST 1 - RECUPERAR PREDICCIONES COMPLETAS
# ============================================================

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


# ============================================================
# TEST 2 - DETECTAR PREDICCION INCOMPLETA
# ============================================================

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


# ============================================================
# TEST 3 - CONSULTA SIN REGISTROS
# ============================================================

def test_recuperar_sin_registros(monkeypatch):
    simular_base_datos(monkeypatch, [])

    df = features.obtener_predicciones_dataframe()

    assert df.empty
    assert len(df.columns) == 19


# ============================================================
# TEST 4 - GUARDAR 19 VARIABLES CON VERSION DINAMICA
# SPRINT 4 - S4-J1
# ============================================================

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

    # Simular el nuevo comportamiento del cargador:
    # modelo + version activa consultada en PostgreSQL.

    informacion_modelo = {
        "modelo": modelo_simulado,
        "caso_uso": "churn",
        "version": "v1.0",
        "algoritmo": "logistic_regression"
    }

    monkeypatch.setattr(
        api_main,
        "obtener_modelo",
        lambda: informacion_modelo
    )

    # Capturar los datos enviados a PostgreSQL.
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

    # Verificar respuesta de la API.
    assert respuesta.status_code == 200

    resultado = respuesta.json()

    assert resultado["prediction_id"] == 999
    assert resultado["prediction"] == 1
    assert resultado["prediction_label"] == "Yes"
    assert resultado["churn_probability"] == 0.75

    # Verificar que la API utilice la version activa.
    assert resultado["model_version"] == "v1.0"

    # Verificar los datos guardados en PostgreSQL.
    assert datos_guardados["caso_uso"] == "churn"
    assert datos_guardados["prediction"] == 1
    assert datos_guardados["probability"] == 0.75

    # Sprint 4: ya no se registra una version fija.
    assert datos_guardados["model_version"] == "v1.0"

    # Sprint 3: se conservan las 19 variables originales.
    assert len(datos_guardados["input_data"]) == 19

    assert datos_guardados["input_data"] == DATOS_CLIENTE
