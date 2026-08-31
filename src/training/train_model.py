from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression


# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

X_TRAIN_FILE = PROCESSED_DIR / "X_train.csv"
Y_TRAIN_FILE = PROCESSED_DIR / "y_train.csv"

MODEL_FILE = MODELS_DIR / "logistic_regression_v1.joblib"


def cargar_datos_entrenamiento():
    """Carga los datos previamente generados por preprocess.py."""

    if not X_TRAIN_FILE.exists() or not Y_TRAIN_FILE.exists():
        raise FileNotFoundError(
            "No se encontraron los datos procesados. "
            "Ejecute primero: python src/training/preprocess.py"
        )

    X_train = pd.read_csv(X_TRAIN_FILE)
    y_train = pd.read_csv(Y_TRAIN_FILE)["Churn"]

    print("Datos de entrenamiento cargados correctamente.")
    print(f"X_train: {X_train.shape}")
    print(f"y_train: {y_train.shape}")

    return X_train, y_train


def entrenar_modelo(X_train, y_train):
    """Entrena el modelo base de Regresión Logística."""

    modelo = LogisticRegression(
        max_iter=1000,
        random_state=42
    )

    modelo.fit(X_train, y_train)

    print("\nModelo Logistic Regression entrenado correctamente.")

    return modelo


def guardar_modelo(modelo):
    """Guarda el modelo entrenado en formato joblib."""

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(modelo, MODEL_FILE)

    print("\nModelo guardado correctamente en:")
    print(MODEL_FILE)


def main():
    print("========== ENTRENAMIENTO MODELO BASE ==========\n")

    X_train, y_train = cargar_datos_entrenamiento()

    modelo = entrenar_modelo(
        X_train,
        y_train
    )

    guardar_modelo(modelo)

    print("\n========== RESULTADO ==========")
    print("Modelo: Logistic Regression")
    print(f"Archivo: {MODEL_FILE.name}")
    print("Entrenamiento completado correctamente.")


if __name__ == "__main__":
    main()