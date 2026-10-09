from pathlib import Path
import shutil

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_FILE = PROJECT_ROOT / "data" / "processed" / "X_train.csv"

REFERENCE_FILE = (
    PROJECT_ROOT / "data" / "reference" / "churn_reference.csv"
)


def validar_referencia(df):
    """Valida que los datos puedan utilizarse como baseline."""

    if df.empty:
        raise ValueError("El conjunto de referencia está vacío.")

    if df.columns.has_duplicates:
        raise ValueError("Existen columnas duplicadas.")

    if "Churn" in df.columns:
        raise ValueError(
            "El baseline debe contener predictores, no la variable objetivo."
        )

    if df.isnull().any().any():
        raise ValueError("Existen valores nulos en el baseline.")

    columnas_no_numericas = df.select_dtypes(
        exclude=["number"]
    ).columns.tolist()

    if columnas_no_numericas:
        raise ValueError(
            f"Existen columnas no numéricas: {columnas_no_numericas}"
        )


def cargar_referencia():
    """Carga el baseline utilizado para el monitoreo."""

    if not REFERENCE_FILE.exists():
        raise FileNotFoundError(
            f"No existe el baseline: {REFERENCE_FILE}"
        )

    df = pd.read_csv(REFERENCE_FILE)

    validar_referencia(df)

    return df


def preparar_referencia():
    """Crea el baseline una sola vez y conserva su contenido."""

    if not REFERENCE_FILE.exists():

        if not TRAIN_FILE.exists():
            raise FileNotFoundError(
                "No existe X_train.csv. "
                "Ejecute primero el preprocesamiento."
            )

        df_train = pd.read_csv(TRAIN_FILE)

        validar_referencia(df_train)

        REFERENCE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copyfile(
            TRAIN_FILE,
            REFERENCE_FILE
        )

        print("Baseline creado correctamente.")

    else:
        print("El baseline ya existe. Se conserva sin modificar.")

    return cargar_referencia()


def main():
    print("========== BASELINE CHURN ==========\n")

    df = preparar_referencia()

    print(f"Archivo: {REFERENCE_FILE}")
    print(f"Registros: {df.shape[0]}")
    print(f"Variables: {df.shape[1]}")
    print(f"Valores nulos: {df.isnull().sum().sum()}")

    print("\nColumnas:")
    print(df.columns.tolist())

    print("\nBASELINE VALIDADO CORRECTAMENTE")


if __name__ == "__main__":
    main()