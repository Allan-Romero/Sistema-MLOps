import os
from datetime import datetime

import mlflow
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException


TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000"
)

REGISTERED_MODEL_NAME = os.getenv(
    "MLFLOW_REGISTERED_MODEL_NAME",
    "churn-model"
)


def obtener_version_semantica(version_mlflow):
    """
    Convierte la versión interna de MLflow
    a una versión legible para el proyecto.

    MLflow 1 -> v1.0
    MLflow 2 -> v1.1
    MLflow 3 -> v1.2
    """

    return f"v1.{int(version_mlflow) - 1}"


def registrar_version_candidata(
    model_info,
    nombre_modelo,
    seleccion
):
    """
    Registra metadatos de la nueva versión candidata
    y actualiza el alias 'candidate'.
    """

    version_mlflow = model_info.registered_model_version

    if version_mlflow is None:
        raise ValueError(
            "MLflow no retornó una versión registrada del modelo."
        )

    version_mlflow = str(version_mlflow)

    client = MlflowClient()

    # Si ya existía un candidato anterior,
    # se conserva como versión histórica.
    try:
        version_anterior = client.get_model_version_by_alias(
            REGISTERED_MODEL_NAME,
            "candidate"
        )

        if str(version_anterior.version) != version_mlflow:
            client.set_model_version_tag(
                REGISTERED_MODEL_NAME,
                str(version_anterior.version),
                "status",
                "historical"
            )

    except MlflowException:
        # Primera versión:
        # todavía no existe alias candidate.
        pass

    version_semantica = obtener_version_semantica(
        version_mlflow
    )

    fecha = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    metrica_principal = seleccion["decision_metric"]

    valor_metrica = float(
        seleccion["metric_value"]
    )

    tags = {
        "semantic_version": version_semantica,
        "algorithm": nombre_modelo,
        "decision_metric": metrica_principal,
        "metric_value": str(valor_metrica),
        "status": "candidate",
        "created_at": fecha,
        "use_case": "churn",
    }

    for clave, valor in tags.items():
        client.set_model_version_tag(
            REGISTERED_MODEL_NAME,
            version_mlflow,
            clave,
            valor
        )

    # El alias siempre apunta
    # al candidato más reciente.
    client.set_registered_model_alias(
        REGISTERED_MODEL_NAME,
        "candidate",
        version_mlflow
    )

    print("\n========== VERSIÓN REGISTRADA ==========")
    print(f"Modelo registrado: {REGISTERED_MODEL_NAME}")
    print(f"Versión MLflow: {version_mlflow}")
    print(f"Versión proyecto: {version_semantica}")
    print(f"Algoritmo: {nombre_modelo}")
    print(f"Métrica: {metrica_principal}")
    print(f"Valor: {valor_metrica:.6f}")
    print("Estado: candidate")
    print(f"Fecha: {fecha}")

    return {
        "mlflow_version": version_mlflow,
        "semantic_version": version_semantica,
        "algorithm": nombre_modelo,
        "decision_metric": metrica_principal,
        "metric_value": valor_metrica,
        "status": "candidate",
        "created_at": fecha,
    }


def listar_versiones():
    """
    Muestra las versiones existentes
    del modelo registrado en MLflow.
    """

    client = MlflowClient()

    versiones = client.search_model_versions(
        f"name = '{REGISTERED_MODEL_NAME}'"
    )

    versiones = sorted(
        versiones,
        key=lambda version: int(version.version)
    )

    print("\n========== HISTORIAL DE VERSIONES ==========\n")

    if not versiones:
        print("No existen versiones registradas.")
        return []

    print(
        f"{'MLflow':<10}"
        f"{'Versión':<12}"
        f"{'Algoritmo':<25}"
        f"{'Métrica':<15}"
        f"{'Valor':<15}"
        f"{'Estado'}"
    )

    print("-" * 95)

    for version in versiones:
        tags = version.tags or {}

        valor = tags.get(
            "metric_value",
            "-"
        )

        try:
            valor = f"{float(valor):.6f}"

        except (ValueError, TypeError):
            pass

        print(
            f"{version.version:<10}"
            f"{tags.get('semantic_version', '-'):<12}"
            f"{tags.get('algorithm', '-'):<25}"
            f"{tags.get('decision_metric', '-'):<15}"
            f"{valor:<15}"
            f"{tags.get('status', '-')}"
        )

    return versiones


def main():
    mlflow.set_tracking_uri(
        TRACKING_URI
    )

    print("========== MODEL REGISTRY ==========\n")

    print(
        f"Tracking URI: {TRACKING_URI}"
    )

    print(
        f"Modelo registrado: {REGISTERED_MODEL_NAME}"
    )

    listar_versiones()


if __name__ == "__main__":
    main()