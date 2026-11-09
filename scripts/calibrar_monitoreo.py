"""Calibración empírica del detector de drift.

Produce las dos mediciones que justifican los parámetros del monitoreo:

1. **Sensibilidad.** Cuánto PSI acusa el detector ante alteraciones de
   magnitud creciente sobre una variable, y en qué nivel las clasifica.
2. **Sesgo por tamaño de muestra.** Cuánto PSI mide el detector cuando las
   dos distribuciones son la misma, en función del número de observaciones.
   Sirve para separar el mínimo técnico del volumen defendible.

Usa `calcular_psi` y `clasificar_nivel` del propio detector, de modo que lo
calibrado es el sistema y no una reimplementación.

Uso:
    python scripts/calibrar_monitoreo.py
"""

import csv
from pathlib import Path

import numpy as np

from src.casos_uso import CASO_USO_POR_DEFECTO, columnas_monitoreadas
from src.monitoring.detect_drift import (UMBRAL_MODERADO, UMBRAL_SIGNIFICATIVO,
                                         calcular_psi, cargar_referencia,
                                         clasificar_nivel)

SALIDA = Path(__file__).resolve().parents[1] / "docs" / "evidencias" / "sprint5"

SEMILLA = 42
VARIABLE = "TotalCharges"
FACTORES = [1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0, 2.5]
MUESTRA_SENSIBILIDAD = 1000

TAMANOS = [50, 100, 150, 200, 300, 500, 1000, 2000]
REPETICIONES = 500


def calibrar_sensibilidad(referencia, generador):
    """Mide el PSI ante alteraciones de magnitud creciente."""
    valores = referencia[VARIABLE].to_numpy()
    muestra = generador.choice(valores, size=MUESTRA_SENSIBILIDAD, replace=False)

    filas = []
    for factor in FACTORES:
        psi = calcular_psi(valores, muestra * factor)
        filas.append({
            "factor": factor,
            "psi": round(psi, 4),
            "nivel": clasificar_nivel(psi),
            "genera_alerta": clasificar_nivel(psi) != "bajo",
        })
    return filas


def calibrar_tamano_muestra(referencia, generador):
    """Mide el PSI cuando ambas distribuciones son la misma."""
    valores = referencia[VARIABLE].to_numpy()

    filas = []
    for tamano in TAMANOS:
        medidas = np.array([
            calcular_psi(valores, generador.choice(valores, size=tamano, replace=True))
            for _ in range(REPETICIONES)
        ])
        filas.append({
            "tamano_muestra": tamano,
            "psi_promedio": round(float(medidas.mean()), 4),
            "psi_mediana": round(float(np.median(medidas)), 4),
            "psi_p95": round(float(np.percentile(medidas, 95)), 4),
            "supera_0_10_pct": round(100 * float((medidas >= UMBRAL_MODERADO).mean()), 1),
            "supera_0_25_pct": round(100 * float((medidas >= UMBRAL_SIGNIFICATIVO).mean()), 1),
        })
    return filas


def calibrar_escenario_control(referencia, generador):
    """Compara los dos diseños del escenario de control.

    El generador de tráfico original sorteaba cada variable dentro de rangos
    plausibles con distribución uniforme; el actual muestrea clientes del
    propio conjunto de referencia. La diferencia explica por qué el primero
    disparaba alertas sin que hubiera drift real.
    """
    filas = []

    # Diseño original: tenure uniforme 1-72 y cargo mensual uniforme 20-120
    tenure_uniforme = generador.integers(1, 73, size=MUESTRA_SENSIBILIDAD)
    mensual_uniforme = generador.uniform(20, 120, size=MUESTRA_SENSIBILIDAD)
    sintetico = {
        "tenure": tenure_uniforme,
        "MonthlyCharges": mensual_uniforme,
        "TotalCharges": mensual_uniforme * tenure_uniforme,
    }

    for variable, valores in sintetico.items():
        psi = calcular_psi(referencia[variable].to_numpy(), valores)
        filas.append({
            "escenario": "control con valores uniformes",
            "variable": variable,
            "psi": round(psi, 4),
            "nivel": clasificar_nivel(psi),
        })

    # Diseño actual: los clientes salen del propio baseline
    indices = generador.choice(len(referencia), size=MUESTRA_SENSIBILIDAD,
                               replace=False)
    muestreado = referencia.iloc[indices]

    for variable in sintetico:
        psi = calcular_psi(referencia[variable].to_numpy(),
                           muestreado[variable].to_numpy())
        filas.append({
            "escenario": "control muestreado del baseline",
            "variable": variable,
            "psi": round(psi, 4),
            "nivel": clasificar_nivel(psi),
        })

    return filas


def guardar(filas, nombre):
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / nombre
    with destino.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    return destino


def main():
    generador = np.random.default_rng(SEMILLA)
    referencia = cargar_referencia(CASO_USO_POR_DEFECTO)

    print(f"Caso de uso: {CASO_USO_POR_DEFECTO}")
    print(f"Variables monitoreadas: {', '.join(columnas_monitoreadas(CASO_USO_POR_DEFECTO))}")
    print(f"Conjunto de referencia: {len(referencia)} registros")
    print(f"Umbrales vigentes: medio {UMBRAL_MODERADO} · alto {UMBRAL_SIGNIFICATIVO}")

    print(f"\n1. SENSIBILIDAD ante alteración de {VARIABLE} "
          f"(muestra de {MUESTRA_SENSIBILIDAD})")
    print(f"{'Factor':>8}{'PSI':>10}{'Nivel':>10}{'Alerta':>10}")
    sensibilidad = calibrar_sensibilidad(referencia, generador)
    for fila in sensibilidad:
        print(f"{fila['factor']:>8}{fila['psi']:>10.4f}{fila['nivel']:>10}"
              f"{('sí' if fila['genera_alerta'] else 'no'):>10}")

    print(f"\n2. SESGO POR TAMAÑO DE MUESTRA con distribuciones idénticas "
          f"({REPETICIONES} repeticiones)")
    print(f"{'n':>8}{'PSI medio':>12}{'mediana':>10}{'p95':>10}"
          f"{'>=0.10':>9}{'>=0.25':>9}")
    tamanos = calibrar_tamano_muestra(referencia, generador)
    for fila in tamanos:
        print(f"{fila['tamano_muestra']:>8}{fila['psi_promedio']:>12.4f}"
              f"{fila['psi_mediana']:>10.4f}{fila['psi_p95']:>10.4f}"
              f"{fila['supera_0_10_pct']:>8.1f}%{fila['supera_0_25_pct']:>8.1f}%")

    print("\n3. DISEÑO DEL ESCENARIO DE CONTROL "
          f"(muestra de {MUESTRA_SENSIBILIDAD})")
    print(f"{'Escenario':<34}{'Variable':<18}{'PSI':>9}{'Nivel':>9}")
    control = calibrar_escenario_control(referencia, generador)
    for fila in control:
        print(f"{fila['escenario']:<34}{fila['variable']:<18}"
              f"{fila['psi']:>9.4f}{fila['nivel']:>9}")

    print()
    print("Evidencia:", guardar(sensibilidad, "calibracion_sensibilidad.csv"))
    print("Evidencia:", guardar(tamanos, "calibracion_tamano_muestra.csv"))
    print("Evidencia:", guardar(control, "calibracion_escenario_control.csv"))


if __name__ == "__main__":
    main()
