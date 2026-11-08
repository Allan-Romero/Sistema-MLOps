"""Mide la duración real de cada actividad del ciclo de vida del modelo.

Cronometra el escenario automatizado: cada actividad se ejecuta a través de
la plataforma, tal como la invoca el pipeline, y se registra el tiempo de
reloj de cada repetición. Los valores que produce este módulo son medidos,
nunca estimados.

El escenario manual no se mide aquí, porque consiste en tiempo humano
—escribir consultas, copiar archivos, revisar resultados— y debe
cronometrarse ejecutando efectivamente los pasos a mano. El procedimiento
está descrito en docs/sprint5_a2_tiempos.md y sus tiempos se agregan al
mismo archivo de resultados, en la columna manual_s.

Desde el Sprint 4 la promoción dejó de ser una acción aparte: el pipeline
decide y escribe el cambio de versión dentro del registro, y la API sirve la
versión nueva en la siguiente petición, sin reinicio. Por eso esa actividad
se mide como el tiempo que tarda la API en atender con la versión activa.

Uso:
    python -m src.benchmark.medir_tiempos [repeticiones]
"""

import csv
import io
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

import requests

from src.database.crud import obtener_historial_despliegues, obtener_version_activa
from src.monitoring.detect_drift import detectar_drift, registrar_alertas
from src.training.compare_models import main as comparar_modelos
from src.training.evaluate_model import main as evaluar_modelo
from src.training.mlflow_tracking import main as registrar_en_mlflow
from src.training.preprocess import main as preprocesar
from src.training.select_best_model import main as seleccionar_modelo
from src.training.train_model import main as entrenar_logistic
from src.training.train_xgboost import main as entrenar_xgboost
from src.database.persist_results import main as persistir_resultados


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
RESULTADOS = PROJECT_ROOT / "reports" / "tiempos_ciclo.csv"

API_HEALTH = "http://localhost:8000/health"
API_PREDICT = "http://localhost:8000/predict"

# Cliente de referencia para comprobar qué versión atiende la petición
CLIENTE_DE_PRUEBA = {
    "gender": "Female", "SeniorCitizen": 0, "Partner": "Yes",
    "Dependents": "No", "tenure": 12, "PhoneService": "Yes",
    "MultipleLines": "No", "InternetService": "Fiber optic",
    "OnlineSecurity": "No", "OnlineBackup": "Yes",
    "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
    "StreamingMovies": "No", "Contract": "Month-to-month",
    "PaperlessBilling": "Yes", "PaymentMethod": "Electronic check",
    "MonthlyCharges": 85.5, "TotalCharges": 1026.0,
}


def promover_modelo():
    """Comprueba que la API atienda con la versión activa del registro.

    La decisión de promoción ocurre dentro del registro de la versión, en una
    sola transacción, y el cargador de la API consulta `model_versions` en
    cada petición. Promover no exige copiar archivos ni reiniciar el
    servicio: lo que cuesta es la primera petición atendida con la versión
    nueva, que es lo que se mide aquí.
    """
    version_activa = obtener_version_activa("churn")
    if not version_activa:
        raise RuntimeError("No hay una versión activa registrada para churn.")

    respuesta = requests.post(API_PREDICT, json=CLIENTE_DE_PRUEBA, timeout=60)
    respuesta.raise_for_status()

    servida = respuesta.json()["model_version"]
    if servida != version_activa[0][2]:
        raise RuntimeError(
            f"La API sirvió {servida} y el registro marca "
            f"{version_activa[0][2]} como activa."
        )


def analizar_drift():
    """Ejecuta la detección de drift y registra las alertas resultantes."""
    resultado = detectar_drift()
    registrar_alertas(resultado)


def entrenar():
    """Entrena los dos algoritmos que el proyecto compara."""
    entrenar_logistic()
    entrenar_xgboost()


def evaluar_y_comparar():
    """Evalúa el modelo base, compara ambos algoritmos y selecciona uno."""
    evaluar_modelo()
    comparar_modelos()
    seleccionar_modelo()


def registrar_version():
    """Registra la ejecución en MLflow y persiste métricas y versión."""
    registrar_en_mlflow()
    persistir_resultados()


# Cada actividad del ciclo, en el orden en que ocurre
ACTIVIDADES = [
    ("Preprocesamiento", preprocesar),
    ("Entrenamiento", entrenar),
    ("Evaluación comparativa", evaluar_y_comparar),
    ("Registro de la versión", registrar_version),
    ("Promoción a producción", promover_modelo),
    ("Detección de drift", analizar_drift),
]


def cronometrar(funcion):
    """Ejecuta una actividad y retorna cuánto tardó, en segundos.

    La salida de consola de la actividad se descarta para que no se mezcle
    con la de la medición; el tiempo incluye todo su trabajo.
    """
    silencio = io.StringIO()
    inicio = time.perf_counter()
    with redirect_stdout(silencio):
        funcion()
    return time.perf_counter() - inicio


def medir(repeticiones=3):
    """Mide todas las actividades y retorna los tiempos por actividad."""
    medidas = {}

    for nombre, funcion in ACTIVIDADES:
        tiempos = []
        for repeticion in range(1, repeticiones + 1):
            duracion = cronometrar(funcion)
            tiempos.append(duracion)
            print(f"{nombre:<26} repetición {repeticion}: {duracion:7.2f} s")
        medidas[nombre] = tiempos

    return medidas


def leer_tiempos_manuales():
    """Recupera los tiempos manuales ya registrados, si los hay."""
    if not RESULTADOS.exists():
        return {}

    with RESULTADOS.open(encoding="utf-8", newline="") as archivo:
        return {
            fila["actividad"]: fila.get("manual_s", "")
            for fila in csv.DictReader(archivo)
        }


def guardar(medidas):
    """Escribe los resultados conservando los tiempos manuales existentes."""
    manuales = leer_tiempos_manuales()
    RESULTADOS.parent.mkdir(parents=True, exist_ok=True)

    with RESULTADOS.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([
            "actividad", "repeticiones", "automatizado_promedio_s",
            "automatizado_min_s", "automatizado_max_s", "manual_s",
        ])
        for nombre, tiempos in medidas.items():
            escritor.writerow([
                nombre,
                len(tiempos),
                round(sum(tiempos) / len(tiempos), 2),
                round(min(tiempos), 2),
                round(max(tiempos), 2),
                manuales.get(nombre, ""),
            ])

    return RESULTADOS


def main(repeticiones=3):
    print("========== MEDICIÓN DE TIEMPOS DEL CICLO ==========")
    print(f"Escenario automatizado · {repeticiones} repeticiones por actividad\n")

    despliegues_previos = len(obtener_historial_despliegues("churn", limite=100))

    medidas = medir(repeticiones)
    ruta = guardar(medidas)

    print(f"\n{'Actividad':<26}{'Promedio':>10}{'Mín':>10}{'Máx':>10}")
    print("-" * 56)
    total = 0.0
    for nombre, tiempos in medidas.items():
        promedio = sum(tiempos) / len(tiempos)
        total += promedio
        print(f"{nombre:<26}{promedio:>10.2f}{min(tiempos):>10.2f}{max(tiempos):>10.2f}")
    print("-" * 56)
    print(f"{'Ciclo completo':<26}{total:>10.2f}")

    print(f"\nResultados guardados en: {ruta}")
    print(
        "Los tiempos del escenario manual se agregan a la columna manual_s "
        "siguiendo el procedimiento de docs/sprint4_a7_tiempos.md."
    )

    if despliegues_previos:
        print(
            f"\nNota: la bitácora de despliegues ya tenía "
            f"{despliegues_previos} registros antes de esta medición."
        )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
