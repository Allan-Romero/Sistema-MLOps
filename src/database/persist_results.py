
import filecmp
import json
import shutil
from pathlib import Path

from src.database.crud import (
    guardar_metricas,
    guardar_version_modelo,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"

COMPARISON_FILE = MODELS_DIR / "model_comparison.json"
SELECTION_FILE = MODELS_DIR / "model_selection.json"

CASO_USO = "churn"
VERSION = "v1.0"

NOMBRES_ALGORITMOS = {
    "Logistic Regression": "logistic_regression",
    "XGBoost": "xgboost",
}


def cargar_json(ruta):
    """Lee un archivo JSON generado por el pipeline."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}"
        )

    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def persistir_metricas(comparacion):
    """Guarda en PostgreSQL las métricas de los modelos."""
    print("\nGuardando métricas en PostgreSQL...")

    for nombre_original, metricas in comparacion.items():
        algoritmo = NOMBRES_ALGORITMOS.get(
            nombre_original, nombre_original
        )

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

        print(
            f"  {nombre_original}: registrado con id {registro_id}"
        )


def guardar_artefacto_versionado():
    """
    Conserva el modelo candidato con el nombre de su versión.

    Una versión publicada no debe sobrescribirse con
    un modelo diferente.
    """
    archivo_candidato = (
        MODELS_DIR / f"{CASO_USO}_model_candidate.joblib"
    )

    archivo_versionado = (
        MODELS_DIR / f"{CASO_USO}_model_{VERSION}.joblib"
    )

    if not archivo_candidato.is_file():
        raise FileNotFoundError(
            f"No existe el modelo candidato: {archivo_candidato}"
        )

    if archivo_versionado.exists():
        if not filecmp.cmp(
            archivo_candidato,
            archivo_versionado,
            shallow=False
        ):
            raise FileExistsError(
                f"La versión {VERSION} ya tiene un artefacto "
                "diferente. Debe generarse una nueva versión."
            )
    else:
        shutil.copy2(
            archivo_candidato,
            archivo_versionado
        )

    print(
        f"  Artefacto versionado: {archivo_versionado.name}"
    )

    return archivo_versionado


def persistir_version(seleccion):
    """Registra la versión seleccionada en PostgreSQL."""
    print("\nGuardando versión del modelo...")

    guardar_artefacto_versionado()

    nombre_original = seleccion["selected_model"]
    algoritmo = NOMBRES_ALGORITMOS.get(
        nombre_original,
        nombre_original
    )

    registro_id = guardar_version_modelo(
        caso_uso=CASO_USO,
        version=VERSION,
        algoritmo=algoritmo,
        metrica_principal=seleccion["decision_metric"],
        valor_metrica=seleccion["metric_value"],
        estado="activa",
    )

    print(
        f"  {nombre_original} {VERSION}: "
        f"registrado con id {registro_id}"
    )


def main():
    """Persiste los resultados generados por el pipeline."""
    print("========== PERSISTENCIA EN POSTGRESQL ==========")

    comparacion = cargar_json(COMPARISON_FILE)
    seleccion = cargar_json(SELECTION_FILE)

    persistir_metricas(comparacion)
    persistir_version(seleccion)

    print("\nResultados persistidos correctamente.")


if __name__ == "__main__":
    main()
