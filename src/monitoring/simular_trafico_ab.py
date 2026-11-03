"""Simula el tráfico de un experimento A/B sobre el caso de uso de churn.

El enrutamiento real del tráfico entre dos versiones del modelo llega con
S4-J3, dentro de la API. Mientras tanto este script reproduce ese
comportamiento desde el host, para poder validar las consultas de
comparación (S4-A3) y la sección del dashboard (S4-A4) con datos propios.

Lo que se simula es únicamente el reparto: las predicciones las calculan los
modelos que el pipeline ya entrenó, sobre clientes del conjunto de prueba, y
la etiqueta real proviene del dataset, igual que en el procedimiento descrito
en docs/sprint4_a2_etiquetas_reales.md. Ninguna métrica es inventada.

Uso:
    python -m src.monitoring.simular_trafico_ab [cantidad] [semilla]
"""

import random
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

from src.database.crud import (guardar_prediccion, obtener_experimento_activo,
                               registrar_etiqueta_real)
from src.training.preprocess import cargar_datos, limpiar_datos


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"

# Modelo que atiende cada versión del experimento. El control es el modelo
# activo en producción y la candidata es el otro algoritmo que el pipeline
# entrenó, de modo que la comparación enfrenta dos modelos reales.
MODELOS_POR_VERSION = {
    "v1": MODELS_DIR / "churn_model_v1.joblib",
    "v1.1": MODELS_DIR / "xgboost_v1.joblib",
}

CASO_USO = "churn"


def cargar_modelo(version):
    """Carga el modelo que atiende una versión del experimento."""
    ruta = MODELOS_POR_VERSION.get(version)

    if ruta is None:
        raise ValueError(
            f"No hay un modelo asociado a la versión {version}. "
            f"Versiones conocidas: {', '.join(MODELOS_POR_VERSION)}."
        )

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo de la versión {version}: {ruta}"
        )

    return joblib.load(ruta)


def cargar_clientes_de_prueba():
    """Recupera el conjunto de prueba con sus etiquetas, sin codificar.

    preprocess.py divide antes de aplicar el One-Hot Encoding y con semilla
    fija, de modo que repetir la partición devuelve exactamente las filas que
    el modelo nunca vio durante el entrenamiento, ya en el formato que espera
    la API.
    """
    df = limpiar_datos(cargar_datos())
    y = df["Churn"].map({"No": 0, "Yes": 1})
    X = df.drop(columns=["Churn"])

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    return X_test, y_test


def preparar_entrada(cliente, modelo):
    """Codifica un cliente igual que la API antes de pedir la predicción."""
    df_cliente = pd.get_dummies(pd.DataFrame([cliente]), dtype=int)

    return df_cliente.reindex(columns=modelo.feature_names_in_, fill_value=0)


def normalizar_cliente(fila):
    """Convierte los tipos de numpy a tipos serializables a JSON."""
    cliente = fila.to_dict()
    cliente["SeniorCitizen"] = int(cliente["SeniorCitizen"])
    cliente["tenure"] = int(cliente["tenure"])
    cliente["MonthlyCharges"] = round(float(cliente["MonthlyCharges"]), 2)
    cliente["TotalCharges"] = round(float(cliente["TotalCharges"]), 2)

    return cliente


def main(cantidad=200, semilla=7):
    experimento = obtener_experimento_activo(CASO_USO)

    if experimento is None:
        raise SystemExit(
            f"No hay un experimento activo para {CASO_USO}. "
            "Registre uno en la tabla experiments antes de simular el tráfico."
        )

    _, _, version_a, version_b, porcentaje_b, _, _, _, _ = experimento

    modelos = {
        version_a: cargar_modelo(version_a),
        version_b: cargar_modelo(version_b),
    }

    X_test, y_test = cargar_clientes_de_prueba()
    muestra = X_test.sample(n=min(cantidad, len(X_test)), random_state=semilla)

    print(f"Experimento: {version_a} (control) vs {version_b} (candidata)")
    print(f"Tráfico configurado para la candidata: {porcentaje_b} %")
    print(f"Clientes a enviar: {len(muestra)}\n")

    sorteo = random.Random(semilla)
    atendidas = {version_a: 0, version_b: 0}

    for indice, fila in muestra.iterrows():
        version = version_b if sorteo.random() * 100 < porcentaje_b else version_a
        modelo = modelos[version]

        cliente = normalizar_cliente(fila)
        entrada = preparar_entrada(cliente, modelo)

        prediccion = int(modelo.predict(entrada)[0])
        probabilidad = float(modelo.predict_proba(entrada)[0][1])

        prediccion_id = guardar_prediccion(
            caso_uso=CASO_USO,
            input_data=cliente,
            prediction=prediccion,
            probability=probabilidad,
            model_version=version,
        )

        registrar_etiqueta_real(prediccion_id, int(y_test.loc[indice]))
        atendidas[version] += 1

    total = sum(atendidas.values())
    print("Predicciones registradas y etiquetadas:")
    for version, cantidad_version in atendidas.items():
        print(f"  {version}: {cantidad_version} ({100 * cantidad_version / total:.1f} %)")


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    semilla = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    main(cantidad, semilla)
