"""S4-J5: entrenamiento y registro MLOps del caso de uso fraude.

Ejecución segura en dos pasos:
  python -m src.training.fraud_pipeline
  python -m src.training.fraud_pipeline --registrar

Entrena modelos con split estratificado train/validación/test, elige el
modelo y umbral usando SOLO validación y evalúa test una sola vez.
El registro reutiliza la promoción transaccional de S4-J2.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, f1_score,
    precision_recall_curve, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from src.training.fraud_features import CASO_USO, FEATURE_COLUMNS, TARGET_COLUMN, validar_columnas
from src.training.fraud_model import ThresholdClassifier

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "raw" / "creditcard.csv"
MODELS_DIR = ROOT / "models"
REPORT = ROOT / "reports" / "s4_j5_fraude_metrics.json"
CANDIDATE = MODELS_DIR / "fraude_model_candidate.joblib"
RANDOM_SEED = 42


def validar_dataset(datos):
    """Comprueba esquema, tipos y clases antes de iniciar entrenamiento."""
    validar_columnas(datos.columns)
    if len(datos) < 100:
        raise ValueError("Dataset de fraude demasiado pequeño para el pipeline.")
    for columna in FEATURE_COLUMNS:
        if not pd.api.types.is_numeric_dtype(datos[columna]):
            raise ValueError(f"La columna {columna} no es numérica.")
    if datos[list(FEATURE_COLUMNS)].isna().any().any():
        raise ValueError("Hay valores nulos entre las características.")
    if not np.isfinite(datos[list(FEATURE_COLUMNS)].to_numpy(dtype=float)).all():
        raise ValueError("Hay características infinitas o no numéricas.")
    if datos[TARGET_COLUMN].isna().any():
        raise ValueError("La etiqueta Class contiene valores nulos.")
    if not set(datos[TARGET_COLUMN].unique()).issubset({0, 1}):
        raise ValueError("Class debe ser binaria: 0 o 1.")
    if int((datos[TARGET_COLUMN] == 1).sum()) < 10:
        raise ValueError("Se requieren al menos 10 fraudes para estratificar.")
    if int((datos[TARGET_COLUMN] == 0).sum()) < 10:
        raise ValueError("Se requieren al menos 10 transacciones legítimas.")


def dividir_datos(datos):
    """70 % entrenamiento, 15 % validación, 15 % test, estratificado."""
    validar_dataset(datos)
    X = datos.loc[:, list(FEATURE_COLUMNS)]
    y = datos[TARGET_COLUMN].astype(int)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_SEED,
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=RANDOM_SEED,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def mejor_umbral(y_real, probabilidades):
    """Maximiza F1 con precisión-recall de VALIDACIÓN, sin usar test."""
    precision, recall, umbrales = precision_recall_curve(y_real, probabilidades)
    if not len(umbrales):
        return 0.5
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(
        precision[:-1] + recall[:-1], 1e-12
    )
    return float(np.clip(umbrales[int(np.argmax(f1))], 1e-8, 1.0))


def calcular_metricas(y_real, probabilidades, umbral):
    predicciones = (np.asarray(probabilidades) >= umbral).astype(int)
    if len(set(y_real)) < 2:
        raise ValueError("Las métricas requieren ambas clases.")
    return {
        "accuracy": float(accuracy_score(y_real, predicciones)),
        "precision": float(precision_score(y_real, predicciones, zero_division=0)),
        "recall": float(recall_score(y_real, predicciones, zero_division=0)),
        "f1_score": float(f1_score(y_real, predicciones, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_real, probabilidades)),
        "pr_auc": float(average_precision_score(y_real, probabilidades)),
    }


def construir_modelos(y_train):
    positivos = int(np.sum(y_train == 1))
    negativos = int(np.sum(y_train == 0))
    peso = negativos / positivos
    return {
        "logistic_regression": make_pipeline(
            StandardScaler(), LogisticRegression(
                class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED,
            ),
        ),
        "xgboost": XGBClassifier(
            n_estimators=180, max_depth=4, learning_rate=0.05,
            subsample=0.85, colsample_bytree=0.85,
            scale_pos_weight=peso, eval_metric="logloss",
            random_state=RANDOM_SEED, n_jobs=2,
        ),
    }


def sha256_archivo(ruta):
    digest = hashlib.sha256()
    with Path(ruta).open("rb") as archivo:
        for trozo in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(trozo)
    return digest.hexdigest()


def entrenar():
    if not DATASET.is_file():
        raise FileNotFoundError(
            f"No existe {DATASET}. Descarga el dataset de fraude antes de entrenar."
        )
    print("[1/5] Cargando Credit Card Fraud Detection...")
    datos = pd.read_csv(DATASET)
    X_train, X_val, X_test, y_train, y_val, y_test = dividir_datos(datos)
    print(f"Registros: {len(datos)}; fraudes: {int(datos[TARGET_COLUMN].sum())}")
    print(f"Train={len(X_train)}; validación={len(X_val)}; test={len(X_test)}")

    modelos = construir_modelos(y_train)
    resultados = {}
    entrenados = {}
    for algoritmo, estimador in modelos.items():
        print(f"[2/5] Entrenando {algoritmo}...")
        estimador.fit(X_train, y_train)
        probabilidades_val = estimador.predict_proba(X_val)[:, 1]
        umbral = mejor_umbral(y_val, probabilidades_val)
        validacion = calcular_metricas(y_val, probabilidades_val, umbral)
        entrenados[algoritmo] = (estimador, umbral)
        resultados[algoritmo] = {"umbral": umbral, "validacion": validacion}
        print(f"  validación: F1={validacion['f1_score']:.4f}; "
              f"PR-AUC={validacion['pr_auc']:.4f}; umbral={umbral:.6f}")

    # Selección independiente del conjunto test; el desempate usa PR-AUC.
    elegido = max(
        resultados,
        key=lambda a: (resultados[a]["validacion"]["f1_score"],
                       resultados[a]["validacion"]["pr_auc"]),
    )
    print(f"[3/5] Elegido en validación: {elegido}")
    for algoritmo, (estimador, umbral) in entrenados.items():
        probabilidades_test = estimador.predict_proba(X_test)[:, 1]
        resultados[algoritmo]["test"] = calcular_metricas(y_test, probabilidades_test, umbral)
        print(f"  test {algoritmo}: F1={resultados[algoritmo]['test']['f1_score']:.4f}; "
              f"PR-AUC={resultados[algoritmo]['test']['pr_auc']:.4f}")

    print("[4/5] Guardando candidato y reporte...")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    estimador, umbral = entrenados[elegido]
    adaptador = ThresholdClassifier(estimador, umbral, FEATURE_COLUMNS)
    joblib.dump(adaptador, CANDIDATE)
    reporte = {
        "caso_uso": CASO_USO,
        "dataset": "Credit Card Fraud Detection, OpenML 1597",
        "filas": len(datos),
        "fraudes": int(datos[TARGET_COLUMN].sum()),
        "proporcion_fraudes": float(datos[TARGET_COLUMN].mean()),
        "distribucion": {
            "train": len(X_train), "validacion": len(X_val), "test": len(X_test),
        },
        "algoritmo_elegido": elegido,
        "metrica_promocion": "f1_score",
        "metrica_complementaria": "pr_auc (average_precision)",
        "seleccion_realizada_sobre": "validacion",
        "resultados": resultados,
        "candidato": CANDIDATE.name,
        "sha256_candidato": sha256_archivo(CANDIDATE),
    }
    REPORT.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[5/5] Reporte: {REPORT}")
    print("Entrenamiento finalizado. NO se modificó PostgreSQL.")
    return reporte


def registrar():
    """Reutiliza J2: métricas, versión y auditoría en una transacción."""
    from src.database.model_promotion import registrar_candidato
    from src.training.promotion_policy import UMBRAL_MINIMO_F1

    if not REPORT.exists() or not CANDIDATE.exists():
        raise FileNotFoundError("Entrena primero: python -m src.training.fraud_pipeline")
    reporte = json.loads(REPORT.read_text(encoding="utf-8"))
    if reporte.get("registro"):
        raise RuntimeError("Este candidato ya fue registrado. Reentrena para generar uno nuevo.")
    if reporte.get("caso_uso") != CASO_USO:
        raise ValueError("El reporte no corresponde a fraude.")
    if reporte.get("sha256_candidato") != sha256_archivo(CANDIDATE):
        raise ValueError("El candidato fue modificado después del entrenamiento.")
    elegido = reporte["algoritmo_elegido"]
    metricas = {
        a: {k: vals["test"][k] for k in ("accuracy", "precision", "recall", "f1_score", "roc_auc")}
        for a, vals in reporte["resultados"].items()
    }
    print("Registrando fraude mediante el mecanismo transaccional de S4-J2...")
    resultado = registrar_candidato(
        caso_uso=CASO_USO,
        version=None,
        algoritmo=elegido,
        f1_candidato=metricas[elegido]["f1_score"],
        umbral=UMBRAL_MINIMO_F1,
        archivo_candidato=CANDIDATE,
        metricas_por_algoritmo=metricas,
    )
    reporte["registro"] = resultado
    REPORT.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Pipeline de fraude S4-J5")
    parser.add_argument("--registrar", action="store_true", help="Persistir el candidato en PostgreSQL")
    argumentos = parser.parse_args()
    if argumentos.registrar:
        registrar()
    else:
        entrenar()


if __name__ == "__main__":
    main()
