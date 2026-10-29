from pathlib import Path

import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUTA_DATOS = PROJECT_ROOT / "data" / "raw" / "churn.csv"
RUTA_REPORTE = PROJECT_ROOT / "reports" / "drift_report.html"

COLUMNAS_NUMERICAS = ["tenure", "MonthlyCharges", "TotalCharges"]


def cargar_datos():
    """Carga el dataset y lo divide en referencia y datos de producción."""
    df = pd.read_csv(RUTA_DATOS)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=COLUMNAS_NUMERICAS)

    mitad = len(df) // 2
    referencia = df.iloc[:mitad].copy()
    actual = df.iloc[mitad:].copy()
    return referencia, actual


def introducir_drift(df):
    """Altera una variable numérica para simular un cambio de distribución."""
    df = df.copy()
    df["MonthlyCharges"] = df["MonthlyCharges"] * 1.45
    return df


def generar_reporte(referencia, actual, ruta_salida):
    """Genera el reporte de drift comparando ambos conjuntos."""
    esquema = DataDefinition(numerical_columns=COLUMNAS_NUMERICAS)

    ds_referencia = Dataset.from_pandas(
        referencia[COLUMNAS_NUMERICAS], data_definition=esquema
    )
    ds_actual = Dataset.from_pandas(
        actual[COLUMNAS_NUMERICAS], data_definition=esquema
    )

    reporte = Report([DataDriftPreset()])
    resultado = reporte.run(ds_actual, ds_referencia)

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.save_html(str(ruta_salida))

    return resultado


def main():
    print("========== PRUEBA DE EVIDENTLY ==========\n")

    referencia, actual = cargar_datos()
    print(f"Referencia: {len(referencia)} registros")
    print(f"Actual:     {len(actual)} registros\n")

    actual_con_drift = introducir_drift(actual)
    print("Se alteró la variable MonthlyCharges en un 45%\n")

    resultado = generar_reporte(referencia, actual_con_drift, RUTA_REPORTE)

    print(f"Reporte generado en:\n{RUTA_REPORTE}\n")
    print("Resultado del análisis:")
    print(resultado.dict())


if __name__ == "__main__":
    main()