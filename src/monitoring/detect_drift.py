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

import sys

import numpy as np
import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

from src.casos_uso import (CASO_USO_POR_DEFECTO, columnas_monitoreadas,
                           ruta_referencia, ruta_reporte_drift)
from src.database.crud import obtener_datos_entrada, guardar_alerta

UMBRAL_MODERADO = 0.10
UMBRAL_SIGNIFICATIVO = 0.25

MINIMO_REGISTROS = 30


def cargar_referencia(caso_uso=CASO_USO_POR_DEFECTO):
    """Carga el conjunto de referencia y lo deja listo para el análisis."""
    columnas = columnas_monitoreadas(caso_uso)
    ruta = ruta_referencia(caso_uso)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el conjunto de referencia del caso de uso "
            f"{caso_uso}: {ruta}"
        )

    df = pd.read_csv(ruta)

    # Algunas columnas llegan como texto: TotalCharges trae espacios en
    # blanco para los clientes con tenure cero.
    for columna in columnas:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    return df.dropna(subset=columnas)[columnas]


def cargar_produccion(caso_uso=CASO_USO_POR_DEFECTO, limite=1000):
    """Carga los datos de entrada de las predicciones registradas en la base."""
    columnas = columnas_monitoreadas(caso_uso)
    registros = obtener_datos_entrada(caso_uso=caso_uso, limite=limite)

    if not registros:
        return pd.DataFrame(columns=columnas)

    df = pd.DataFrame(registros)
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        raise ValueError(
            f"Los datos de producción no contienen las columnas: {faltantes}"
        )

    for columna in columnas:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    return df[columnas].dropna()


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


def generar_reporte_html(referencia, actual, caso_uso=CASO_USO_POR_DEFECTO,
                         ruta_salida=None):
    """Genera el reporte visual de Evidently y retorna su ruta."""
    ruta_salida = ruta_salida or ruta_reporte_drift(caso_uso)
    esquema = DataDefinition(numerical_columns=columnas_monitoreadas(caso_uso))

    ds_referencia = Dataset.from_pandas(referencia, data_definition=esquema)
    ds_actual = Dataset.from_pandas(actual, data_definition=esquema)

    resultado = Report([DataDriftPreset()]).run(ds_actual, ds_referencia)

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.save_html(str(ruta_salida))
    return ruta_salida


def detectar_drift(referencia=None, actual=None, caso_uso=CASO_USO_POR_DEFECTO,
                   generar_reporte=True):
    """
    Ejecuta el análisis de drift y retorna el resultado estructurado.

    Si no se entregan los conjuntos, la referencia se toma del dataset de
    entrenamiento y los datos actuales de las predicciones registradas en
    la base de datos.
    """
    if referencia is None:
        referencia = cargar_referencia(caso_uso)
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
    for columna in columnas_monitoreadas(caso_uso):
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
        ruta_reporte = str(generar_reporte_html(referencia, actual, caso_uso))

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

def registrar_alertas(resultado):
    """
    Registra en la base de datos una alerta por cada variable donde se
    detectó drift. Retorna la lista de identificadores generados.
    """
    if not resultado.get("analisis_realizado"):
        return []

    ids = []
    for variable in resultado["variables"]:
        if not variable["drift"]:
            continue

        descripcion = (
            f"Se detectó un cambio de distribución en la variable "
            f"{variable['variable']}. PSI = {variable['psi']} "
            f"(umbral de referencia: {UMBRAL_SIGNIFICATIVO})."
        )

        alerta_id = guardar_alerta(
            caso_uso=resultado["caso_uso"],
            variable_afectada=variable["variable"],
            nivel_drift=variable["nivel"],
            descripcion=descripcion,
        )
        ids.append(alerta_id)

    return ids

def obtener_distribuciones(variable, caso_uso=CASO_USO_POR_DEFECTO):
    """
    Retorna los valores de una variable en el conjunto de referencia y en
    los datos de producción, para su comparación visual.
    """
    referencia = cargar_referencia(caso_uso)
    actual = cargar_produccion(caso_uso=caso_uso)

    if variable not in columnas_monitoreadas(caso_uso):
        raise ValueError(f"La variable {variable} no es analizada por el sistema.")

    return {
        "referencia": referencia[variable].dropna(),
        "actual": actual[variable].dropna() if not actual.empty else actual,
    }

def main(caso_uso=CASO_USO_POR_DEFECTO):
    """Ejecuta la detección de drift y muestra el resultado en consola."""
    print("========== DETECCIÓN DE DATA DRIFT ==========\n")

    print(f"Caso de uso: {caso_uso}")

    try:
        resultado = detectar_drift(caso_uso=caso_uso)
    except (FileNotFoundError, ValueError) as error:
        print(f"No fue posible ejecutar el análisis: {error}")
        return

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
        ids = registrar_alertas(resultado)
        print(f"Alertas registradas en la base de datos: {len(ids)}")
        if ids:
            print(f"Identificadores: {ids}")
    else:
        print("Resultado: no se detectó drift.")
        print("No se generaron alertas.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else CASO_USO_POR_DEFECTO)