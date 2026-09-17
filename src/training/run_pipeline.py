from pathlib import Path

from src.training.preprocess import main as ejecutar_preprocesamiento
from src.training.train_model import main as ejecutar_entrenamiento
from src.training.evaluate_model import main as ejecutar_evaluacion


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "logistic_regression_v1.joblib"
)

METRICS_FILE = (
    PROJECT_ROOT
    / "models"
    / "logistic_regression_v1_metrics.json"
)


def validar_salidas():
    """Verifica que el pipeline haya generado sus artefactos principales."""

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"No se generó el modelo esperado: {MODEL_FILE}"
        )

    if not METRICS_FILE.exists():
        raise FileNotFoundError(
            f"No se generó el archivo de métricas esperado: {METRICS_FILE}"
        )

    print("\nArtefactos generados correctamente:")
    print(f"- Modelo: {MODEL_FILE}")
    print(f"- Métricas: {METRICS_FILE}")


def main():
    """Ejecuta el pipeline completo de entrenamiento del modelo de churn."""

    print("=" * 60)
    print("PIPELINE DE ENTRENAMIENTO - CHURN")
    print("=" * 60)

    print("\n[1/3] PREPROCESAMIENTO")
    print("-" * 60)
    ejecutar_preprocesamiento()

    print("\n[2/3] ENTRENAMIENTO")
    print("-" * 60)
    ejecutar_entrenamiento()

    print("\n[3/3] EVALUACIÓN")
    print("-" * 60)
    ejecutar_evaluacion()

    validar_salidas()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETADO CORRECTAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    main()