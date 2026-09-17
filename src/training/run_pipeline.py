from pathlib import Path

from src.training.preprocess import main as ejecutar_preprocesamiento
from src.training.train_model import main as ejecutar_entrenamiento_logistic
from src.training.evaluate_model import main as ejecutar_evaluacion_logistic
from src.training.train_xgboost import main as ejecutar_entrenamiento_xgboost
from src.training.compare_models import main as ejecutar_comparacion


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOGISTIC_MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "logistic_regression_v1.joblib"
)

XGBOOST_MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "xgboost_v1.joblib"
)

LOGISTIC_METRICS_FILE = (
    PROJECT_ROOT
    / "models"
    / "logistic_regression_v1_metrics.json"
)

COMPARISON_FILE = (
    PROJECT_ROOT
    / "models"
    / "model_comparison.json"
)


def validar_salidas():
    """Verifica los artefactos principales generados por el pipeline."""

    archivos_esperados = [
        LOGISTIC_MODEL_FILE,
        XGBOOST_MODEL_FILE,
        LOGISTIC_METRICS_FILE,
        COMPARISON_FILE,
    ]

    for archivo in archivos_esperados:
        if not archivo.exists():
            raise FileNotFoundError(
                f"No se generó el archivo esperado: {archivo}"
            )

    print("\nArtefactos generados correctamente:")

    for archivo in archivos_esperados:
        print(f"- {archivo}")


def main():
    """Ejecuta el pipeline completo de entrenamiento de churn."""

    print("=" * 60)
    print("PIPELINE DE ENTRENAMIENTO - CHURN")
    print("=" * 60)

    print("\n[1/5] PREPROCESAMIENTO")
    print("-" * 60)
    ejecutar_preprocesamiento()

    print("\n[2/5] ENTRENAMIENTO LOGISTIC REGRESSION")
    print("-" * 60)
    ejecutar_entrenamiento_logistic()

    print("\n[3/5] EVALUACIÓN LOGISTIC REGRESSION")
    print("-" * 60)
    ejecutar_evaluacion_logistic()

    print("\n[4/5] ENTRENAMIENTO XGBOOST")
    print("-" * 60)
    ejecutar_entrenamiento_xgboost()

    print("\n[5/5] COMPARACIÓN DE MODELOS")
    print("-" * 60)
    ejecutar_comparacion()

    validar_salidas()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETADO CORRECTAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    main()