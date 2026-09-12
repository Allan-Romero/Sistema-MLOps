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


# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

X_TEST_FILE = PROCESSED_DIR / "X_test.csv"
Y_TEST_FILE = PROCESSED_DIR / "y_test.csv"

MODEL_FILE = MODELS_DIR / "logistic_regression_v1.joblib"
METRICS_FILE = MODELS_DIR / "logistic_regression_v1_metrics.json"


def cargar_datos_prueba():
    """Carga los datos reservados para evaluación."""

    if not X_TEST_FILE.exists() or not Y_TEST_FILE.exists():
        raise FileNotFoundError(
            "No se encontraron los datos de prueba. "
            "Ejecute primero: python src/training/preprocess.py"
        )

    X_test = pd.read_csv(X_TEST_FILE)
    y_test = pd.read_csv(Y_TEST_FILE)["Churn"]

    print("Datos de prueba cargados correctamente.")
    print(f"X_test: {X_test.shape}")
    print(f"y_test: {y_test.shape}")

    return X_test, y_test


def cargar_modelo():
    """Carga el modelo entrenado."""

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            "No se encontró el modelo entrenado. "
            "Ejecute primero: python src/training/train_model.py"
        )

    modelo = joblib.load(MODEL_FILE)

    print("\nModelo cargado correctamente:")
    print(MODEL_FILE.name)

    return modelo


def calcular_metricas(modelo, X_test, y_test):
    """Calcula las métricas de clasificación."""

    y_pred = modelo.predict(X_test)
    y_prob = modelo.predict_proba(X_test)[:, 1]

    metricas = {
        "model": "Logistic Regression",
        "version": "v1",
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob))
    }

    return metricas


def guardar_metricas(metricas):
    """Guarda las métricas en formato JSON."""

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    with open(METRICS_FILE, "w", encoding="utf-8") as archivo:
        json.dump(metricas, archivo, indent=4)

    print("\nMétricas guardadas en:")
    print(METRICS_FILE)


def main():
    print("========== EVALUACIÓN MODELO BASE ==========\n")

    X_test, y_test = cargar_datos_prueba()

    modelo = cargar_modelo()

    metricas = calcular_metricas(
        modelo,
        X_test,
        y_test
    )

    print("\n========== MÉTRICAS ==========")
    print(f"Accuracy:  {metricas['accuracy']:.4f}")
    print(f"Precision: {metricas['precision']:.4f}")
    print(f"Recall:    {metricas['recall']:.4f}")
    print(f"F1-score:  {metricas['f1_score']:.4f}")
    print(f"ROC-AUC:   {metricas['roc_auc']:.4f}")

    guardar_metricas(metricas)

    print("\nEvaluación completada correctamente.")


if __name__ == "__main__":
    main()