"""Persistencia transaccional de resultados del pipeline de churn."""

import json
from pathlib import Path

from src.database.model_promotion import registrar_candidato
from src.training.promotion_policy import UMBRAL_MINIMO_F1


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
COMPARISON_FILE = MODELS_DIR / "model_comparison.json"
SELECTION_FILE = MODELS_DIR / "model_selection.json"
CASO_USO = "churn"

NOMBRES_ALGORITMOS = {
    "Logistic Regression": "logistic_regression",
    "XGBoost": "xgboost",
}


def cargar_json(ruta):
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def validar_seleccion(comparacion, seleccion):
    """Valida la selección ANTES de registrar o versionar el candidato."""
    nombre_modelo = seleccion["selected_model"]
    if nombre_modelo not in NOMBRES_ALGORITMOS:
        raise ValueError(f"Modelo no soportado: {nombre_modelo}")
    if nombre_modelo not in comparacion:
        raise ValueError("El modelo seleccionado no aparece en la comparación.")
    if seleccion["decision_metric"] != "f1_score":
        raise ValueError("La política de promoción requiere f1_score.")

    f1_comparacion = float(comparacion[nombre_modelo]["f1_score"])
    f1_seleccion = float(seleccion["metric_value"])
    if abs(f1_comparacion - f1_seleccion) > 1e-10:
        raise ValueError("El F1-score seleccionado no coincide con la comparación.")

    return {"algoritmo": NOMBRES_ALGORITMOS[nombre_modelo], "f1_score": f1_seleccion}


def persistir_version(seleccion, comparacion):
    """Asigna versión, guarda métricas y audita en una única transacción."""
    candidato = validar_seleccion(comparacion, seleccion)
    metricas_por_algoritmo = {}
    for nombre, metricas in comparacion.items():
        if nombre not in NOMBRES_ALGORITMOS:
            raise ValueError(f"Algoritmo desconocido: {nombre}")
        metricas_por_algoritmo[NOMBRES_ALGORITMOS[nombre]] = metricas

    archivo_candidato = MODELS_DIR / f"{CASO_USO}_model_candidate.joblib"
    resultado = registrar_candidato(
        caso_uso=CASO_USO,
        version=None,
        algoritmo=candidato["algoritmo"],
        f1_candidato=candidato["f1_score"],
        umbral=UMBRAL_MINIMO_F1,
        archivo_candidato=archivo_candidato,
        metricas_por_algoritmo=metricas_por_algoritmo,
    )

    print("\n========== DECISION DE PROMOCION ==========")
    print(f"Versión candidata: {resultado['version_candidata']}")
    print(f"Versión anterior: {resultado['version_anterior']}")
    print(f"F1 candidato: {resultado['f1_candidato']:.6f}")
    if resultado["f1_activo"] is not None:
        print(f"F1 activo: {resultado['f1_activo']:.6f}")
        print(f"Mejora: {resultado['mejora']:.6f}")
    print(f"Umbral mínimo: {resultado['umbral']:.4f}")
    print(f"Estado: {resultado['estado']}")
    print(f"Motivo: {resultado['motivo']}")
    return resultado


def main():
    print("========== PERSISTENCIA MLOPS ==========")
    comparacion = cargar_json(COMPARISON_FILE)
    seleccion = cargar_json(SELECTION_FILE)
    validar_seleccion(comparacion, seleccion)
    resultado = persistir_version(seleccion, comparacion)
    print("\n========== RESULTADO FINAL ==========")
    print(f"Versión: {resultado['version_candidata']}")
    print(f"Estado: {resultado['estado']}")
    print("Modelo promovido a producción." if resultado["promovido"]
          else "Modelo descartado. Producción sin cambios.")
    return resultado


if __name__ == "__main__":
    main()
