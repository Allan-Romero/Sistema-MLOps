from pathlib import Path

from src.training.preprocess import main as ejecutar_preprocesamiento
from src.training.train_model import main as ejecutar_entrenamiento_logistic
from src.training.evaluate_model import main as ejecutar_evaluacion_logistic
from src.training.train_xgboost import main as ejecutar_entrenamiento_xgboost
from src.training.compare_models import main as ejecutar_comparacion
from src.training.select_best_model import main as ejecutar_seleccion
from src.training.mlflow_tracking import main as ejecutar_mlflow


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

CANDIDATE_MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "churn_model_candidate.joblib"
)

SELECTION_FILE = (
    PROJECT_ROOT
    / "models"
    / "model_selection.json"
)


def validar_salidas():
    """Verifica los artefactos principales generados por el pipeline."""

    archivos_esperados = [
        LOGISTIC_MODEL_FILE,
        XGBOOST_MODEL_FILE,
        LOGISTIC_METRICS_FILE,
        COMPARISON_FILE,
        CANDIDATE_MODEL_FILE,
        SELECTION_FILE,
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

    print("\n[1/7] PREPROCESAMIENTO")
    print("-" * 60)
    ejecutar_preprocesamiento()

    print("\n[2/7] ENTRENAMIENTO LOGISTIC REGRESSION")
    print("-" * 60)
    ejecutar_entrenamiento_logistic()

    print("\n[3/7] EVALUACIÓN LOGISTIC REGRESSION")
    print("-" * 60)
    ejecutar_evaluacion_logistic()

    print("\n[4/7] ENTRENAMIENTO XGBOOST")
    print("-" * 60)
    ejecutar_entrenamiento_xgboost()

    print("\n[5/7] COMPARACIÓN DE MODELOS")
    print("-" * 60)
    ejecutar_comparacion()

    print("\n[6/7] SELECCIÓN DEL MEJOR MODELO")
    print("-" * 60)
    ejecutar_seleccion()

    print("\n[7/7] REGISTRO DE EXPERIMENTOS EN MLFLOW")
    print("-" * 60)
    ejecutar_mlflow()

    validar_salidas()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETADO CORRECTAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    main()