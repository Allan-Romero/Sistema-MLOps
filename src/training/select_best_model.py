from pathlib import Path
import json
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODELS_DIR = PROJECT_ROOT / "models"

COMPARISON_FILE = MODELS_DIR / "model_comparison.json"

CANDIDATE_MODEL_FILE = MODELS_DIR / "churn_model_candidate.joblib"
SELECTION_FILE = MODELS_DIR / "model_selection.json"

DECISION_METRIC = "f1_score"


MODEL_FILES = {
    "Logistic Regression": MODELS_DIR / "logistic_regression_v1.joblib",
    "XGBoost": MODELS_DIR / "xgboost_v1.joblib",
}


def cargar_resultados():
    """Carga las métricas comparativas generadas en S2-J2."""

    if not COMPARISON_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de comparación: {COMPARISON_FILE}"
        )

    with COMPARISON_FILE.open("r", encoding="utf-8") as archivo:
        resultados = json.load(archivo)

    if len(resultados) < 2:
        raise ValueError(
            "Se necesitan al menos dos modelos para realizar la selección."
        )

    return resultados


def seleccionar_mejor_modelo(resultados):
    """Selecciona automáticamente el modelo con mayor F1-score."""

    for nombre_modelo, metricas in resultados.items():
        if DECISION_METRIC not in metricas:
            raise KeyError(
                f"El modelo {nombre_modelo} no contiene "
                f"la métrica {DECISION_METRIC}."
            )

    mejor_modelo = max(
        resultados,
        key=lambda nombre: resultados[nombre][DECISION_METRIC]
    )

    mejor_valor = resultados[mejor_modelo][DECISION_METRIC]

    return mejor_modelo, mejor_valor


def marcar_como_candidato(mejor_modelo, mejor_valor):
    """Copia el modelo seleccionado y registra la decisión."""

    archivo_origen = MODEL_FILES.get(mejor_modelo)

    if archivo_origen is None:
        raise ValueError(
            f"No existe una ruta configurada para: {mejor_modelo}"
        )

    if not archivo_origen.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo seleccionado: {archivo_origen}"
        )

    shutil.copy2(
        archivo_origen,
        CANDIDATE_MODEL_FILE
    )

    seleccion = {
        "selected_model": mejor_modelo,
        "decision_metric": DECISION_METRIC,
        "metric_value": mejor_valor,
        "source_model": archivo_origen.name,
        "candidate_model": CANDIDATE_MODEL_FILE.name,
        "status": "candidate"
    }

    with SELECTION_FILE.open("w", encoding="utf-8") as archivo:
        json.dump(
            seleccion,
            archivo,
            indent=4
        )

    return seleccion


def main():
    print("========== SELECCIÓN DE MEJOR MODELO ==========\n")

    resultados = cargar_resultados()

    print(f"Métrica de decisión: {DECISION_METRIC}\n")

    for nombre_modelo, metricas in resultados.items():
        print(
            f"{nombre_modelo}: "
            f"{DECISION_METRIC} = "
            f"{metricas[DECISION_METRIC]:.6f}"
        )

    mejor_modelo, mejor_valor = seleccionar_mejor_modelo(
        resultados
    )

    seleccion = marcar_como_candidato(
        mejor_modelo,
        mejor_valor
    )

    print("\n========== MODELO SELECCIONADO ==========")
    print(f"Modelo: {seleccion['selected_model']}")
    print(f"Métrica: {seleccion['decision_metric']}")
    print(f"Valor: {seleccion['metric_value']:.6f}")
    print(f"Estado: {seleccion['status']}")

    print("\nModelo candidato guardado en:")
    print(CANDIDATE_MODEL_FILE)

    print("\nInformación de selección guardada en:")
    print(SELECTION_FILE)

    print("\nSelección completada correctamente.")


if __name__ == "__main__":
    main()