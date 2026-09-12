from pathlib import Path
import json

from src.database.crud import guardar_metricas


PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICS_FILE = PROJECT_ROOT / "models" / "logistic_regression_v1_metrics.json"


def main():
    """Carga las métricas del modelo y las guarda en PostgreSQL."""

    if not METRICS_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de métricas: {METRICS_FILE}"
        )

    with METRICS_FILE.open("r", encoding="utf-8") as archivo:
        metricas = json.load(archivo)

    metricas_id = guardar_metricas(
        caso_uso="churn",
        model_version=metricas["version"],
        accuracy=metricas.get("accuracy"),
        precision=metricas.get("precision"),
        recall=metricas.get("recall"),
        f1_score=metricas.get("f1_score"),
        roc_auc=metricas.get("roc_auc"),
    )

    print("Métricas guardadas correctamente.")
    print(f"ID: {metricas_id}")
    print(f"Modelo: {metricas['model']}")
    print(f"Versión: {metricas['version']}")
    print(f"Accuracy: {metricas['accuracy']}")
    print(f"Precision: {metricas['precision']}")
    print(f"Recall: {metricas['recall']}")
    print(f"F1-score: {metricas['f1_score']}")
    print(f"ROC-AUC: {metricas['roc_auc']}")


if __name__ == "__main__":
    main()