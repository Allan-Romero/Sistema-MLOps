"""S5-J1: repite la comparación real sin tocar BD, MLflow ni modelos activos.

Estrategia elegida: reportar el hallazgo del pipeline existente, sin ajustar
hiperparámetros sobre el test ni ocultar advertencias de convergencia.
Ejecutar como python -m scripts.comparar_algoritmos_s5 --help.
"""
import argparse
import contextlib
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import warnings

import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score
from src.training.compare_models import calcular_metricas as metricas_churn
from src.training import fraud_pipeline as fraude
from src.training.preprocess import limpiar_datos, dividir_y_codificar
from src.training.train_model import construir_modelo as construir_lr
from src.training.train_xgboost import construir_modelo as construir_xgb


def hash_archivo(ruta):
    digest = hashlib.sha256()
    with ruta.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            digest.update(bloque)
    return digest.hexdigest()


def evaluar_modelos(modelos, xtrain, ytrain, xval, yval, xtest, ytest, ajustar_umbral):
    resultados = {}
    for nombre, modelo in modelos.items():
        print(f'Entrenando {nombre}: train={len(xtrain)}, test={len(xtest)}', flush=True)
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter('always')
            modelo.fit(xtrain, ytrain)
        pval = modelo.predict_proba(xval)[:, 1] if ajustar_umbral else None
        umbral = fraude.mejor_umbral(yval, pval) if ajustar_umbral else 0.5
        resultado = {
            'umbral': umbral,
            'hiperparametros': modelo.get_params(deep=True),
            'advertencias_fit': [{'categoria': type(a.message).__name__, 'mensaje': str(a.message)} for a in avisos],
            'convergence_warning': any(issubclass(a.category, ConvergenceWarning) for a in avisos),
            'test': fraude.calcular_metricas(ytest, modelo.predict_proba(xtest)[:, 1], umbral),
        }
        if not ajustar_umbral:
            # Reproduce predict() del pipeline histórico incluso en probabilidad
            # exactamente 0.5, donde la regla de desempate puede diferir de >=.
            resultado['test'] = {
                **metricas_churn(modelo, xtest, ytest),
                'pr_auc': float(average_precision_score(ytest, modelo.predict_proba(xtest)[:, 1])),
            }
        lr = modelo.steps[-1][1] if hasattr(modelo, 'steps') else modelo
        if hasattr(lr, 'n_iter_'):
            resultado['iteraciones'] = lr.n_iter_.tolist()
        if ajustar_umbral:
            resultado['validacion'] = fraude.calcular_metricas(yval, pval, umbral)
        resultados[nombre] = resultado
        print(f"{nombre}: F1={resultado['test']['f1_score']:.6f}; ROC-AUC={resultado['test']['roc_auc']:.6f}; convergencia_aviso={resultado['convergence_warning']}", flush=True)
    return resultados


def comparar_churn(ruta):
    datos = limpiar_datos(pd.read_csv(ruta))
    xtrain, xtest, ytrain, ytest = dividir_y_codificar(datos)
    modelos = {'logistic_regression': construir_lr(), 'xgboost': construir_xgb()}
    resultados = evaluar_modelos(modelos, xtrain, ytrain, None, None, xtest, ytest, False)
    return {'filas': len(datos), 'positivos': int(ytrain.sum() + ytest.sum()),
            'particiones': {'train': len(xtrain), 'test': len(xtest)},
            'seleccion_sobre': 'test_historico_no_validacion_independiente',
            'algoritmo_elegido': max(resultados, key=lambda a: resultados[a]['test']['f1_score']),
            'resultados': resultados}


def comparar_fraude(ruta):
    datos = pd.read_csv(ruta)
    xtrain, xval, xtest, ytrain, yval, ytest = fraude.dividir_datos(datos)
    resultados = evaluar_modelos(fraude.construir_modelos(ytrain), xtrain, ytrain, xval, yval, xtest, ytest, True)
    elegido = max(resultados, key=lambda a: (resultados[a]['validacion']['f1_score'], resultados[a]['validacion']['pr_auc']))
    return {'filas': len(datos), 'positivos': int(datos['Class'].sum()),
            'particiones': {'train': len(xtrain), 'validacion': len(xval), 'test': len(xtest)},
            'seleccion_sobre': 'validacion', 'algoritmo_elegido': elegido, 'resultados': resultados}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--churn', type=Path, default=Path('data/raw/churn.csv'))
    parser.add_argument('--fraude', type=Path, default=Path('data/raw/creditcard.csv'))
    parser.add_argument('--salida', type=Path, default=Path('reports/sprint5/comparacion'))
    args = parser.parse_args()
    for ruta in (args.churn, args.fraude):
        if not ruta.is_file():
            parser.error(f'No existe el dataset: {ruta.name}')
    args.salida.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    fuentes = ['src/training/train_model.py', 'src/training/train_xgboost.py', 'src/training/preprocess.py',
               'src/training/fraud_pipeline.py', 'scripts/comparar_algoritmos_s5.py']
    reporte = {
        'tipo': 'entrenamiento_real_offline_no_cambia_produccion',
        'estrategia': 'reportar_hallazgo_sin_ajuste',
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(),
        'versiones': {nombre: importlib.metadata.version(nombre) for nombre in ['scikit-learn', 'xgboost', 'pandas', 'numpy']},
        'commit_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        'sha256_fuentes': {nombre: hash_archivo(root / nombre) for nombre in fuentes},
        'datasets': {nombre: {'archivo': ruta.name, 'sha256': hash_archivo(ruta)} for nombre, ruta in [('churn', args.churn), ('fraude', args.fraude)]},
    }
    with (args.salida / 'ejecucion.txt').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log):
        reporte['churn'] = comparar_churn(args.churn)
        reporte['fraude'] = comparar_fraude(args.fraude)
    (args.salida / 'comparacion.json').write_text(json.dumps(reporte, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    with (args.salida / 'metricas.csv').open('w', newline='', encoding='utf-8') as archivo:
        campos = ['caso', 'algoritmo', 'conjunto', 'umbral', 'accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'pr_auc', 'convergence_warning']
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        for caso in ('churn', 'fraude'):
            for nombre, resultado in reporte[caso]['resultados'].items():
                for conjunto in ('validacion', 'test'):
                    if conjunto in resultado:
                        writer.writerow({'caso': caso, 'algoritmo': nombre, 'conjunto': conjunto,
                                         'umbral': resultado['umbral'], **resultado[conjunto],
                                         'convergence_warning': resultado['convergence_warning']})
    print(f'Comparación guardada en {args.salida}; no se modificaron BD ni modelos activos.')


if __name__ == '__main__':
    main()
