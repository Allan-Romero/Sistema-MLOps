"""Cronómetro del escenario manual del ciclo de vida del modelo.

Acompaña la medición de S5-A2: muestra qué hay que hacer a mano en cada
actividad, cronometra desde que se empieza hasta que se termina y guarda los
tiempos. El escenario automatizado lo mide `src.benchmark.medir_tiempos`;
este es el otro lado de la comparación y no puede automatizarse sin dejar de
ser manual.

Reglas de la medición, para que el dato sirva:

- Ejecutar realmente cada paso, incluido escribir las consultas y revisar
  los resultados en pantalla.
- No descontar errores de tecleo ni reintentos: son parte del costo real.
- Misma máquina y mismo dataset que el escenario automatizado.

Uso:
    python scripts/cronometro_manual.py              # una repetición
    python scripts/cronometro_manual.py --repeticiones 2
    python scripts/cronometro_manual.py --actividad "Entrenamiento"
"""

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTADOS = PROJECT_ROOT / "reports" / "tiempos_manual.csv"

ACTIVIDADES = [
    (
        "Preprocesamiento",
        [
            "Abrir data/raw/churn.csv y revisar las columnas.",
            "Limpiar TotalCharges: viene como texto y trae espacios en blanco",
            "    para los clientes con tenure cero.",
            "Codificar las variables categóricas y separar la variable Churn.",
            "Dividir en entrenamiento y prueba y guardar los cuatro CSV",
            "    en data/processed/.",
        ],
        "Desde abrir el archivo hasta tener los CSV escritos.",
    ),
    (
        "Entrenamiento",
        [
            "Ajustar la regresión logística sobre el conjunto de entrenamiento.",
            "Ajustar XGBoost sobre el mismo conjunto.",
            "Guardar los dos modelos como .joblib en models/.",
        ],
        "Desde escribir el primer ajuste hasta tener los dos archivos.",
    ),
    (
        "Evaluación comparativa",
        [
            "Calcular accuracy, precision, recall, F1 y ROC-AUC de cada modelo",
            "    sobre el conjunto de prueba.",
            "Comparar ambos resultados y decidir cuál sería el candidato.",
        ],
        "Desde la primera métrica hasta la decisión tomada.",
    ),
    (
        "Registro de la versión",
        [
            "Abrir el cliente de PostgreSQL:",
            "    docker exec -it mlops_postgres psql -U mlops_user -d mlops_db",
            "Escribir a mano el INSERT en model_metrics con las métricas.",
            "Escribir a mano el INSERT en model_versions con la versión nueva.",
            "Comprobar con un SELECT que ambos registros quedaron.",
        ],
        "Desde abrir el cliente hasta confirmar los registros.",
    ),
    (
        "Promoción a producción",
        [
            "Copiar el modelo elegido al nombre que corresponde a la versión",
            "    activa, por ejemplo models/churn_model_v1.0.joblib.",
            "Marcar a mano esa versión como activa en model_versions y la",
            "    anterior como histórica.",
            "Comprobar que /predict responde con la versión nueva.",
        ],
        "Desde la copia hasta ver la versión nueva en la respuesta.",
    ),
    (
        "Detección de drift",
        [
            "Extraer con SQL los datos de entrada de las predicciones",
            "    registradas en producción.",
            "Calcular el PSI de tenure, MonthlyCharges y TotalCharges contra",
            "    el conjunto de referencia.",
            "Clasificar cada variable e insertar a mano las alertas que",
            "    correspondan en la tabla alerts.",
        ],
        "Desde la consulta de extracción hasta las alertas escritas.",
    ),
]


def esperar(mensaje):
    """Espera a que la persona confirme con Enter."""
    try:
        input(mensaje)
    except (EOFError, KeyboardInterrupt):
        print("\nMedición interrumpida. Lo registrado hasta ahora se conserva.")
        sys.exit(1)


def formatear(segundos):
    minutos, resto = divmod(int(segundos), 60)
    return f"{minutos} min {resto:02d} s" if minutos else f"{resto} s"


def guardar(filas):
    """Agrega las mediciones al archivo de resultados."""
    RESULTADOS.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not RESULTADOS.exists()

    with RESULTADOS.open("a", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo)
        if nuevo:
            escritor.writerow(["actividad", "repeticion", "segundos", "fecha"])
        escritor.writerows(filas)


def cronometrar(nombre, pasos, limites, repeticion):
    """Muestra el protocolo de una actividad y mide cuánto toma."""
    print()
    print("=" * 70)
    print(f"  {nombre}" + (f"   (repetición {repeticion})" if repeticion > 1 else ""))
    print("=" * 70)
    for paso in pasos:
        print(f"  {paso}")
    print()
    print(f"  Cronómetro: {limites}")
    print()

    esperar("  Pulsa Enter cuando EMPIECES... ")
    inicio = time.perf_counter()
    esperar("  Trabajando. Pulsa Enter cuando TERMINES... ")
    duracion = time.perf_counter() - inicio

    print(f"  -> {nombre}: {formatear(duracion)}")
    return duracion


def main():
    parser = argparse.ArgumentParser(description="Cronómetro del escenario manual")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument(
        "--actividad",
        help="Medir solo una actividad, por su nombre exacto",
    )
    argumentos = parser.parse_args()

    pendientes = ACTIVIDADES
    if argumentos.actividad:
        pendientes = [a for a in ACTIVIDADES if a[0] == argumentos.actividad]
        if not pendientes:
            nombres = ", ".join(a[0] for a in ACTIVIDADES)
            raise SystemExit(f"Actividad desconocida. Opciones: {nombres}")

    print()
    print("CRONÓMETRO DEL ESCENARIO MANUAL")
    print("Haz cada paso de verdad; los reintentos y los errores cuentan.")
    print(f"Actividades: {len(pendientes)} · Repeticiones: {argumentos.repeticiones}")

    filas = []
    for repeticion in range(1, argumentos.repeticiones + 1):
        for nombre, pasos, limites in pendientes:
            duracion = cronometrar(nombre, pasos, limites, repeticion)
            filas.append([nombre, repeticion, round(duracion, 2),
                          datetime.now().isoformat(timespec="seconds")])
            guardar([filas[-1]])

    print()
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    total = 0.0
    for nombre, _, segundos, _ in filas:
        total += segundos
        print(f"  {nombre:<26}{formatear(segundos):>14}")
    print("-" * 70)
    print(f"  {'Ciclo completo':<26}{formatear(total):>14}")
    print()
    print(f"Guardado en {RESULTADOS}")


if __name__ == "__main__":
    main()
