"""
Módulo de detección de data drift.

Compara la distribución de las variables numéricas del conjunto de
referencia (datos de entrenamiento) contra los datos observados en
producción, utilizando el Population Stability Index (PSI) como métrica
de decisión y Evidently AI para la generación del reporte visual.

Umbrales adoptados (escala estándar del PSI):
    PSI <  0.10  → sin cambio significativo
    PSI <  0.25  → cambio moderado
    PSI >= 0.25  → cambio significativo
"""

from pathlib import Path

import numpy as np
import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

from src.database.crud import obtener_datos_entrada

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUTA_REFERENCIA = PROJECT_ROOT / "data" / "raw" / "churn.csv"
RUTA_REPORTE = PROJECT_ROOT / "reports" / "drift_report.html"

COLUMNAS_NUMERICAS = ["tenure", "MonthlyCharges", "TotalCharges"]

UMBRAL_MODERADO = 0.10
UMBRAL_SIGNIFICATIVO = 0.25

MINIMO_REGISTROS = 30


def cargar_referencia():
    """Carga el conjunto de referencia y lo deja listo para el análisis."""
    df = pd.read_csv(RUTA_REFERENCIA)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=COLUMNAS_NUMERICAS)
    return df[COLUMNAS_NUMERICAS]


def cargar_produccion(caso_uso="churn", limite=1000):
    """Carga los datos de entrada de las predicciones registradas en la base."""
    registros = obtener_datos_entrada(caso_uso=caso_uso, limite=limite)

    if not registros:
        return pd.DataFrame(columns=COLUMNAS_NUMERICAS)

    df = pd.DataFrame(registros)
    faltantes = [c for c in COLUMNAS_NUMERICAS if c not in df.columns]
    if faltantes:
        raise ValueError(
            f"Los datos de producción no contienen las columnas: {faltantes}"
        )

    for columna in COLUMNAS_NUMERICAS:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    return df[COLUMNAS_NUMERICAS].dropna()


def calcular_psi(referencia, actual, bins=10):
    """
    Calcula el Population Stability Index entre dos distribuciones.

    Se construyen los intervalos a partir de los cuantiles del conjunto de
    referencia y se compara la proporción de observaciones que cae en cada
    uno. Un valor alto indica que la distribución se desplazó.
    """
    referencia = np.asarray(referencia, dtype=float)
    actual = np.asarray(actual, dtype=float)

    cortes = np.quantile(referencia, np.linspace(0, 1, bins + 1))
    cortes = np.unique(cortes)

    if len(cortes) < 3:
        return 0.0

    cortes[0] = -np.inf
    cortes[-1] = np.inf

    prop_ref = np.histogram(referencia, bins=cortes)[0] / len(referencia)
    prop_act = np.histogram(actual, bins=cortes)[0] / len(actual)

    # Se evita la división por cero sustituyendo las proporciones nulas
    epsilon = 1e-6
    prop_ref = np.where(prop_ref == 0, epsilon, prop_ref)
    prop_act = np.where(prop_act == 0, epsilon, prop_act)

    psi = np.sum((prop_act - prop_ref) * np.log(prop_act / prop_ref))
    return float(psi)


def clasificar_nivel(psi):
    """Traduce el valor de PSI a un nivel de drift."""
    if psi >= UMBRAL_SIGNIFICATIVO:
        return "alto"
    if psi >= UMBRAL_MODERADO:
        return "medio"
    return "bajo"


def generar_reporte_html(referencia, actual, ruta_salida=RUTA_REPORTE):
    """Genera el reporte visual de Evidently y retorna su ruta."""
    esquema = DataDefinition(numerical_columns=COLUMNAS_NUMERICAS)

    ds_referencia = Dataset.from_pandas(referencia, data_definition=esquema)
    ds_actual = Dataset.from_pandas(actual, data_definition=esquema)

    resultado = Report([DataDriftPreset()]).run(ds_actual, ds_referencia)

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.save_html(str(ruta_salida))
    return ruta_salida


def detectar_drift(referencia=None, actual=None, caso_uso="churn",
                   generar_reporte=True):
    """
    Ejecuta el análisis de drift y retorna el resultado estructurado.

    Si no se entregan los conjuntos, la referencia se toma del dataset de
    entrenamiento y los datos actuales de las predicciones registradas en
    la base de datos.
    """
    if referencia is None:
        referencia = cargar_referencia()
    if actual is None:
        actual = cargar_produccion(caso_uso=caso_uso)

    if len(actual) < MINIMO_REGISTROS:
        return {
            "caso_uso": caso_uso,
            "analisis_realizado": False,
            "motivo": (
                f"Se requieren al menos {MINIMO_REGISTROS} registros de "
                f"producción y solo hay {len(actual)}."
            ),
            "variables": [],
            "drift_detectado": False,
        }

    variables = []
    for columna in COLUMNAS_NUMERICAS:
        psi = calcular_psi(referencia[columna], actual[columna])
        nivel = clasificar_nivel(psi)
        variables.append({
            "variable": columna,
            "psi": round(psi, 4),
            "nivel": nivel,
            "drift": nivel != "bajo",
        })

    ruta_reporte = None
    if generar_reporte:
        ruta_reporte = str(generar_reporte_html(referencia, actual))

    return {
        "caso_uso": caso_uso,
        "analisis_realizado": True,
        "registros_referencia": len(referencia),
        "registros_actuales": len(actual),
        "umbral": UMBRAL_SIGNIFICATIVO,
        "variables": variables,
        "drift_detectado": any(v["drift"] for v in variables),
        "reporte": ruta_reporte,
    }


def main():
    """Ejecuta la detección de drift y muestra el resultado en consola."""
    print("========== DETECCIÓN DE DATA DRIFT ==========\n")

    resultado = detectar_drift()

    if not resultado["analisis_realizado"]:
        print(f"Análisis no realizado: {resultado['motivo']}")
        return

    print(f"Registros de referencia: {resultado['registros_referencia']}")
    print(f"Registros de producción: {resultado['registros_actuales']}")
    print(f"Umbral de decisión (PSI): {resultado['umbral']}\n")

    print(f"{'Variable':<20}{'PSI':>10}{'Nivel':>12}")
    print("-" * 42)
    for v in resultado["variables"]:
        print(f"{v['variable']:<20}{v['psi']:>10.4f}{v['nivel']:>12}")

    print()
    if resultado["drift_detectado"]:
        print("Resultado: se detectó drift en una o más variables.")
    else:
        print("Resultado: no se detectó drift.")

    if resultado["reporte"]:
        print(f"\nReporte generado en:\n{resultado['reporte']}")


if __name__ == "__main__":
    main()