from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

X_TEST_FILE = PROCESSED_DIR / "X_test.csv"
Y_TEST_FILE = PROCESSED_DIR / "y_test.csv"

LOGISTIC_MODEL_FILE = MODELS_DIR / "logistic_regression_v1.joblib"
XGBOOST_MODEL_FILE = MODELS_DIR / "xgboost_v1.joblib"

COMPARISON_FILE = MODELS_DIR / "model_comparison.json"


def cargar_datos_prueba():
    """Carga el mismo conjunto de prueba para ambos modelos."""

    if not X_TEST_FILE.exists() or not Y_TEST_FILE.exists():
        raise FileNotFoundError(
            "No se encontraron los datos de prueba."
        )

    X_test = pd.read_csv(X_TEST_FILE)
    y_test = pd.read_csv(Y_TEST_FILE)["Churn"]

    print("Datos de prueba cargados correctamente.")
    print(f"X_test: {X_test.shape}")
    print(f"y_test: {y_test.shape}")

    return X_test, y_test


def calcular_metricas(modelo, X_test, y_test):
    """Calcula las mismas métricas para cualquier modelo."""

    y_pred = modelo.predict(X_test)
    y_prob = modelo.predict_proba(X_test)[:, 1]

    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob))
    }


def main():
    print("========== COMPARACIÓN DE MODELOS ==========\n")

    X_test, y_test = cargar_datos_prueba()

    if not LOGISTIC_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"No existe: {LOGISTIC_MODEL_FILE}"
        )

    if not XGBOOST_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"No existe: {XGBOOST_MODEL_FILE}"
        )

    logistic_model = joblib.load(LOGISTIC_MODEL_FILE)
    xgboost_model = joblib.load(XGBOOST_MODEL_FILE)

    resultados = {
        "Logistic Regression": calcular_metricas(
            logistic_model,
            X_test,
            y_test
        ),
        "XGBoost": calcular_metricas(
            xgboost_model,
            X_test,
            y_test
        )
    }

    tabla = pd.DataFrame(resultados).T

    print("\n========== MÉTRICAS COMPARATIVAS ==========\n")
    print(tabla.to_string())

    with open(COMPARISON_FILE, "w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, indent=4)

    print("\nComparación guardada en:")
    print(COMPARISON_FILE)

    print("\nComparación completada correctamente.")


if __name__ == "__main__":
    main()