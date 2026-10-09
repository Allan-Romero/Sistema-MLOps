from pathlib import Path

import pandas as pd

from src.monitoring.reference_data import cargar_referencia


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "simulated"

CONTROL_FILE = OUTPUT_DIR / "churn_control.csv"
DRIFT_FILE = OUTPUT_DIR / "churn_drift.csv"

VARIABLES_ALTERADAS = ["MonthlyCharges", "tenure"]


def generar_datos_simulados():
    """
    Genera dos escenarios reproducibles:
    1. Control: distribuciones idénticas al baseline.
    2. Drift: modificaciones controladas en dos variables.
    """

    print("========== SIMULACION DE DATA DRIFT ==========\n")

    referencia = cargar_referencia()

    for columna in VARIABLES_ALTERADAS:
        if columna not in referencia.columns:
            raise ValueError(f"Falta la columna: {columna}")

    # ESCENARIO 1: SIN DRIFT
    control = referencia.copy(deep=True)

    # ESCENARIO 2: CON DRIFT
    drift = referencia.copy(deep=True)

    # Aumento de 30 unidades monetarias
    drift["MonthlyCharges"] = (
        drift["MonthlyCharges"] + 30
    ).round(2)

    # Aumento simulado de 18 meses,
    # limitado a 72 meses
    drift["tenure"] = (
        drift["tenure"] + 18
    ).clip(upper=72).astype(int)

    # Verificar que no cambien las otras variables
    columnas_sin_cambios = [
        columna
        for columna in referencia.columns
        if columna not in VARIABLES_ALTERADAS
    ]

    pd.testing.assert_frame_equal(
        referencia[columnas_sin_cambios],
        drift[columnas_sin_cambios]
    )

    if control.equals(drift):
        raise ValueError(
            "El escenario drift no presenta modificaciones."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    control.to_csv(CONTROL_FILE, index=False)
    drift.to_csv(DRIFT_FILE, index=False)

    print(f"Registros: {len(referencia)}")
    print(f"Variables: {len(referencia.columns)}")

    print("\nESCENARIO CONTROL")
    print("Sin modificaciones.")
    print(f"Archivo: {CONTROL_FILE}")

    print("\nESCENARIO CON DRIFT")
    print("MonthlyCharges: +30")
    print("tenure: +18 meses, maximo 72")
    print(f"Archivo: {DRIFT_FILE}")

    print("\nCOMPROBACION DE CAMBIOS")

    for columna in VARIABLES_ALTERADAS:
        cantidad = (
            referencia[columna] != drift[columna]
        ).sum()

        print(f"{columna}: {cantidad} registros modificados")

    print("\nESCENARIOS GENERADOS CORRECTAMENTE")


if __name__ == "__main__":
    generar_datos_simulados()