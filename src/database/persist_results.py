import json
from pathlib import Path

from src.database.crud import guardar_metricas, guardar_version_modelo


PROJECT_ROOT = Path(__file__).resolve().parents[2]

COMPARISON_FILE = PROJECT_ROOT / "models" / "model_comparison.json"
SELECTION_FILE = PROJECT_ROOT / "models" / "model_selection.json"

CASO_USO = "churn"
VERSION = "v1.0"

# Normaliza los nombres de los algoritmos para almacenarlos de forma consistente
NOMBRES_ALGORITMOS = {
    "Logistic Regression": "logistic_regression",
    "XGBoost": "xgboost",
}


def cargar_json(ruta):
    """Lee un archivo JSON generado por el pipeline."""
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def persistir_metricas(comparacion):
    """Guarda en PostgreSQL las métricas de cada algoritmo evaluado."""
    print("\nGuardando métricas en PostgreSQL...")

    for nombre_original, metricas in comparacion.items():
        algoritmo = NOMBRES_ALGORITMOS.get(nombre_original, nombre_original)

        registro_id = guardar_metricas(
            caso_uso=CASO_USO,
            model_version=VERSION,
            algoritmo=algoritmo,
            accuracy=metricas["accuracy"],
            precision=metricas["precision"],
            recall=metricas["recall"],
            f1_score=metricas["f1_score"],
            roc_auc=metricas["roc_auc"],
        )

        print(f"  {nombre_original}: registrado con id {registro_id}")


def persistir_version(seleccion):
    """Guarda en PostgreSQL la versión del modelo seleccionado."""
    print("\nGuardando versión del modelo en PostgreSQL...")

    nombre_original = seleccion["selected_model"]
    algoritmo = NOMBRES_ALGORITMOS.get(nombre_original, nombre_original)

    registro_id = guardar_version_modelo(
        caso_uso=CASO_USO,
        version=VERSION,
        algoritmo=algoritmo,
        metrica_principal=seleccion["decision_metric"],
        valor_metrica=seleccion["metric_value"],
        estado="activa",
    )

    print(f"  {nombre_original} {VERSION}: registrado con id {registro_id}")


def main():
    """Persiste en PostgreSQL los resultados generados por el pipeline."""
    print("========== PERSISTENCIA EN POSTGRESQL ==========")

    comparacion = cargar_json(COMPARISON_FILE)
    seleccion = cargar_json(SELECTION_FILE)

    persistir_metricas(comparacion)
    persistir_version(seleccion)

    print("\nResultados persistidos correctamente.")


if __name__ == "__main__":
    main()