from pathlib import Path
import json
import os

import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost

from src.training.model_registry import (
    REGISTERED_MODEL_NAME,
    listar_versiones,
    registrar_version_candidata,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODELS_DIR = PROJECT_ROOT / "models"

COMPARISON_FILE = MODELS_DIR / "model_comparison.json"
SELECTION_FILE = MODELS_DIR / "model_selection.json"

LOGISTIC_MODEL_FILE = (
    MODELS_DIR
    / "logistic_regression_v1.joblib"
)

XGBOOST_MODEL_FILE = (
    MODELS_DIR
    / "xgboost_v1.joblib"
)

TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000"
)

EXPERIMENT_NAME = os.getenv(
    "MLFLOW_EXPERIMENT_NAME",
    "churn-model-training"
)


MODELOS = {
    "Logistic Regression": {
        "archivo": LOGISTIC_MODEL_FILE,
        "run_name": "logistic-regression",
        "tipo": "sklearn",
    },
    "XGBoost": {
        "archivo": XGBOOST_MODEL_FILE,
        "run_name": "xgboost",
        "tipo": "xgboost",
    },
}


def cargar_json(archivo):
    """Carga un archivo JSON."""

    if not archivo.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo requerido: {archivo}"
        )

    with archivo.open(
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def obtener_parametros(modelo):
    """Obtiene los parámetros configurados del modelo."""

    if not hasattr(modelo, "get_params"):
        return {}

    return {
        nombre: str(valor)
        for nombre, valor
        in modelo.get_params().items()
    }


def registrar_modelo_mlflow(
    nombre_modelo,
    configuracion,
    metricas,
    seleccion
):
    """
    Registra parámetros, métricas y artefactos del modelo.
    Si el modelo es el candidato seleccionado,
    también crea una nueva versión en Model Registry.
    """

    archivo_modelo = configuracion["archivo"]

    if not archivo_modelo.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo: {archivo_modelo}"
        )

    modelo = joblib.load(
        archivo_modelo
    )

    parametros = obtener_parametros(
        modelo
    )

    es_candidato = (
        seleccion["selected_model"]
        == nombre_modelo
    )

    estado = (
        "candidate"
        if es_candidato
        else "evaluated"
    )

    with mlflow.start_run(
        run_name=configuracion["run_name"]
    ) as run:

        mlflow.log_params(
            parametros
        )

        mlflow.log_metrics({
            nombre: float(valor)
            for nombre, valor
            in metricas.items()
        })

        mlflow.set_tags({
            "algorithm": nombre_modelo,
            "model_status": estado,
            "pipeline": "churn-training",
            "decision_metric": seleccion[
                "decision_metric"
            ],
        })

        # Modelo original en formato joblib.
        mlflow.log_artifact(
            str(archivo_modelo),
            artifact_path="joblib"
        )

        # Metadatos generados por el pipeline.
        mlflow.log_artifact(
            str(COMPARISON_FILE),
            artifact_path="metadata"
        )

        mlflow.log_artifact(
            str(SELECTION_FILE),
            artifact_path="metadata"
        )

        # Solo el mejor modelo entra al Model Registry.
        if configuracion["tipo"] == "sklearn":

            if es_candidato:
                model_info = mlflow.sklearn.log_model(
                    sk_model=modelo,
                    name="model",
                    registered_model_name=REGISTERED_MODEL_NAME
                )
            else:
                model_info = mlflow.sklearn.log_model(
                    sk_model=modelo,
                    name="model"
                )

        elif configuracion["tipo"] == "xgboost":

            if es_candidato:
                model_info = mlflow.xgboost.log_model(
                    xgb_model=modelo,
                    name="model",
                    registered_model_name=REGISTERED_MODEL_NAME
                )
            else:
                model_info = mlflow.xgboost.log_model(
                    xgb_model=modelo,
                    name="model"
                )

        else:
            raise ValueError(
                f"Tipo de modelo no soportado: "
                f"{configuracion['tipo']}"
            )

        print(
            f"\n{nombre_modelo} registrado correctamente."
        )
        print(f"Run ID: {run.info.run_id}")
        print(f"Estado: {estado}")

        if es_candidato:

            version = registrar_version_candidata(
                model_info=model_info,
                nombre_modelo=nombre_modelo,
                seleccion=seleccion,
            )

            mlflow.set_tag(
                "semantic_version",
                version["semantic_version"]
            )


def main():
    print("========== REGISTRO MLFLOW ==========\n")

    mlflow.set_tracking_uri(
        TRACKING_URI
    )

    print(
        f"Tracking URI: {TRACKING_URI}"
    )

    print(
        f"Experimento: {EXPERIMENT_NAME}\n"
    )

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    comparacion = cargar_json(
        COMPARISON_FILE
    )

    seleccion = cargar_json(
        SELECTION_FILE
    )

    for nombre_modelo, configuracion in MODELOS.items():

        if nombre_modelo not in comparacion:
            raise KeyError(
                f"No existen métricas para: "
                f"{nombre_modelo}"
            )

        registrar_modelo_mlflow(
            nombre_modelo=nombre_modelo,
            configuracion=configuracion,
            metricas=comparacion[nombre_modelo],
            seleccion=seleccion,
        )

    listar_versiones()

    print("\n========== RESULTADO ==========")
    print(
        "Modelos registrados en MLflow correctamente."
    )
    print(
        f"Experimento: {EXPERIMENT_NAME}"
    )
    print(
        f"Model Registry: {REGISTERED_MODEL_NAME}"
    )
    print(
        "Registro MLflow completado."
    )


if __name__ == "__main__":
    main()