"""Genera tráfico de predicciones contra la API para alimentar el monitoreo de drift.

Los clientes se muestrean del propio conjunto de referencia, de modo que el
escenario de control reproduce la distribución real del baseline. El parámetro
factor_drift permite alterar deliberadamente TotalCharges para provocar drift.

Uso:
    python -m src.monitoring.generar_trafico [cantidad] [factor_drift]

Ejemplos:
    python -m src.monitoring.generar_trafico 150 1.0    # escenario de control
    python -m src.monitoring.generar_trafico 150 1.8    # escenario con drift
"""

import os
import sys
from pathlib import Path

import pandas as pd
import requests

# Dentro de docker compose se apunta al servicio api (API_URL=http://api:8000)
API_URL = os.getenv("API_URL", "http://localhost:8000")
URL = f"{API_URL}/predict"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUTA_REFERENCIA = PROJECT_ROOT / "data" / "raw" / "churn.csv"

# Columnas que espera el endpoint /predict, en el orden del dataset original.
COLUMNAS_PAYLOAD = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
]

_referencia = None


def cargar_referencia():
    """Carga el conjunto de referencia una sola vez y lo deja utilizable.

    TotalCharges viene como texto en el dataset original y trae espacios en
    blanco para los clientes con tenure cero, de modo que se convierte a
    numérico y se descartan esas filas.
    """
    global _referencia
    if _referencia is None:
        datos = pd.read_csv(RUTA_REFERENCIA)
        datos["TotalCharges"] = pd.to_numeric(datos["TotalCharges"], errors="coerce")
        datos = datos.dropna(subset=["TotalCharges"])
        _referencia = datos[COLUMNAS_PAYLOAD].copy()
        print(f"Conjunto de referencia cargado: {len(_referencia)} registros")
    return _referencia


def cliente_aleatorio(factor_drift=1.0):
    """Toma un cliente real del baseline y le aplica el factor de drift.

    Con factor_drift = 1.0 el cliente se envía tal como aparece en el conjunto
    de referencia, por lo que no debe detectarse variación alguna.
    """
    fila = cargar_referencia().sample(1).iloc[0]
    cliente = {columna: fila[columna] for columna in COLUMNAS_PAYLOAD}

    # Los tipos de numpy no son serializables a JSON, hay que convertirlos.
    cliente["SeniorCitizen"] = int(cliente["SeniorCitizen"])
    cliente["tenure"] = int(cliente["tenure"])
    cliente["MonthlyCharges"] = round(float(cliente["MonthlyCharges"]), 2)
    cliente["TotalCharges"] = round(float(cliente["TotalCharges"]) * factor_drift, 2)

    return cliente


def main(cantidad=150, factor_drift=1.0):
    escenario = "control" if factor_drift == 1.0 else f"drift (factor {factor_drift})"
    print(f"Escenario: {escenario}")
    print(f"Destino: {URL}\n")

    exitosas = 0
    for i in range(cantidad):
        respuesta = requests.post(URL, json=cliente_aleatorio(factor_drift), timeout=10)
        if respuesta.status_code == 200:
            exitosas += 1
        else:
            print(f"Error en la petición {i + 1}: {respuesta.status_code} {respuesta.text[:200]}")

    print(f"\nPredicciones generadas correctamente: {exitosas} de {cantidad}")


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    factor = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    main(cantidad, factor)