from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "churn.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


def cargar_datos():
    """Carga el dataset original de churn."""
    df = pd.read_csv(INPUT_FILE)

    print("Dataset cargado correctamente.")
    print(f"Dimensión original: {df.shape}")

    return df


def limpiar_datos(df):
    """Realiza la limpieza validada durante S1-J4."""
    df_limpio = df.copy()

    # Convertir TotalCharges a formato numérico.
    # Los valores vacíos encontrados corresponden a clientes con tenure = 0.
    df_limpio["TotalCharges"] = (
        df_limpio["TotalCharges"]
        .astype(str)
        .str.strip()
        .replace("", "0")
    )

    df_limpio["TotalCharges"] = pd.to_numeric(
        df_limpio["TotalCharges"],
        errors="coerce"
    )

    if df_limpio["TotalCharges"].isnull().sum() > 0:
        raise ValueError(
            "Se encontraron valores no convertibles en TotalCharges."
        )

    # customerID es un identificador único y no se utiliza como predictor.
    if "customerID" in df_limpio.columns:
        df_limpio = df_limpio.drop(columns=["customerID"])

    print("Limpieza completada.")
    print(f"Dimensión después de limpieza: {df_limpio.shape}")
    print(f"Valores nulos: {df_limpio.isnull().sum().sum()}")

    return df_limpio


def dividir_y_codificar(df):
    """Codifica la variable objetivo y divide los datos en train/test."""
    df = df.copy()

    # Variable objetivo
    df["Churn"] = df["Churn"].map({
        "No": 0,
        "Yes": 1
    })

    if df["Churn"].isnull().any():
        raise ValueError(
            "Se encontraron valores desconocidos en la variable Churn."
        )

    X = df.drop(columns=["Churn"])
    y = df["Churn"]

    # División 80/20 estratificada
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # Identificar variables categóricas usando solo los datos de entrenamiento
    categoricas = X_train.select_dtypes(
        include=["object", "string"]
    ).columns.tolist()

    # One-Hot Encoding
    X_train = pd.get_dummies(
        X_train,
        columns=categoricas,
        dtype=int
    )

    X_test = pd.get_dummies(
        X_test,
        columns=categoricas,
        dtype=int
    )

    # Garantizar que train y test tengan exactamente las mismas columnas
    X_test = X_test.reindex(
        columns=X_train.columns,
        fill_value=0
    )

    print("Codificación completada.")
    print("Columnas no numéricas en train:",
          X_train.select_dtypes(exclude=["number"]).shape[1])
    print("Columnas no numéricas en test:",
          X_test.select_dtypes(exclude=["number"]).shape[1])

    return X_train, X_test, y_train, y_test


def guardar_datos(X_train, X_test, y_train, y_test):
    """Guarda los conjuntos preparados para entrenamiento."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    X_train.to_csv(OUTPUT_DIR / "X_train.csv", index=False)
    X_test.to_csv(OUTPUT_DIR / "X_test.csv", index=False)

    y_train.to_csv(
        OUTPUT_DIR / "y_train.csv",
        index=False,
        header=["Churn"]
    )

    y_test.to_csv(
        OUTPUT_DIR / "y_test.csv",
        index=False,
        header=["Churn"]
    )

    print("\nDatos procesados guardados en:")
    print(OUTPUT_DIR)


def main():
    print("========== PREPROCESAMIENTO CHURN ==========\n")

    df = cargar_datos()

    df_limpio = limpiar_datos(df)

    X_train, X_test, y_train, y_test = dividir_y_codificar(
        df_limpio
    )

    guardar_datos(
        X_train,
        X_test,
        y_train,
        y_test
    )

    print("\n========== RESULTADO ==========")
    print(f"X_train: {X_train.shape}")
    print(f"X_test:  {X_test.shape}")
    print(f"y_train: {y_train.shape}")
    print(f"y_test:  {y_test.shape}")

    print(
        "\nTotal registros:",
        len(X_train) + len(X_test)
    )

    print("\nPreprocesamiento completado correctamente.")


if __name__ == "__main__":
    main()