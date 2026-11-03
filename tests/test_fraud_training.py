"""Pruebas del bloque de entrenamiento (sin dataset real ni DB)."""

import json
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.training.fraud_features import FEATURE_COLUMNS, TARGET_COLUMN, CASO_USO, validar_columnas
from src.training.fraud_model import ThresholdClassifier
from src.training import fraud_pipeline as fp


def dataset_sintetico(n=200):
    r = np.random.default_rng(42)
    data = pd.DataFrame(r.normal(size=(n, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
    data[TARGET_COLUMN] = ([0] * (n - 20)) + ([1] * 20)
    return data


def test_columnas_correctas():
    validar_columnas([*FEATURE_COLUMNS, TARGET_COLUMN])
    assert len(FEATURE_COLUMNS) == 30
    assert CASO_USO == 'fraude'


def test_columnas_faltantes():
    with pytest.raises(ValueError, match="faltantes"):
        validar_columnas(['Time', 'Class'])


def test_columnas_adicionales():
    with pytest.raises(ValueError, match="inesperadas"):
        validar_columnas([*FEATURE_COLUMNS, 'Class', 'prediction'])


def test_dataset_valido():
    fp.validar_dataset(dataset_sintetico())


def test_dataset_con_nulos():
    datos = dataset_sintetico()
    datos.loc[0, 'Amount'] = np.nan
    with pytest.raises(ValueError, match='nulos'):
        fp.validar_dataset(datos)


def test_dataset_con_etiqueta_no_binaria():
    datos = dataset_sintetico()
    datos.loc[0, 'Class'] = 2
    with pytest.raises(ValueError, match='binaria'):
        fp.validar_dataset(datos)


def test_split_sin_fuga_de_test():
    d = dataset_sintetico(500)
    X_train, X_val, X_test, y_train, y_val, y_test = fp.dividir_datos(d)
    assert sum(map(len, (X_train, X_val, X_test))) == 500
    assert sum(map(len, (y_train, y_val, y_test))) == 500
    assert len(set(X_train.index) & set(X_test.index)) == 0
    assert len(set(X_val.index) & set(X_test.index)) == 0
    assert len(X_train) == 350
    assert len(X_val) == len(X_test) == 75


def test_umbral_mejor_f1():
    y = [0, 0, 1, 1]
    p = [0.1, 0.2, 0.7, 0.9]
    umbral = fp.mejor_umbral(y, p)
    assert 0.2 < umbral <= 0.7
    assert fp.calcular_metricas(y, p, umbral)['f1_score'] == 1.0


def test_metricas_basicas():
    m = fp.calcular_metricas([0, 0, 1, 1], [0.1, 0.3, 0.8, 0.9], 0.5)
    assert m['f1_score'] == 1
    assert m['pr_auc'] == 1
    assert m['recall'] == 1


def test_metricas_sin_ambas_clases():
    with pytest.raises(ValueError, match='ambas clases'):
        fp.calcular_metricas([0, 0], [0.2, 0.1], 0.5)


def test_adaptador_con_umbral():
    class Falso:
        def predict_proba(self, x):
            return np.array([[.75, .25], [.25, .75]])
    mod = ThresholdClassifier(Falso(), 0.7, ('Time',))
    assert list(mod.predict(None)) == [0, 1]
    assert mod.feature_names_in_.tolist() == ['Time']


def test_adaptador_umbral_invalido():
    with pytest.raises(ValueError, match='umbral'):
        ThresholdClassifier(None, 0, ('Time',))


def test_artefacto_serializable(tmp_path):
    x = pd.DataFrame({'Time': [0., 1., 2., 3.], 'Amount': [.2, .3, .8, .9]})
    clf = LogisticRegression().fit(x, [0, 0, 1, 1])
    wrapped = ThresholdClassifier(clf, .5, x.columns)
    import joblib
    path = tmp_path / 'model.joblib'
    joblib.dump(wrapped, path)
    restored = joblib.load(path)
    assert restored.predict(x).tolist() == [0, 0, 1, 1]


def test_registro_rechaza_si_no_hay_reporte(monkeypatch, tmp_path):
    monkeypatch.setattr(fp, 'REPORT', tmp_path / 'no_existe.json')
    monkeypatch.setattr(fp, 'CANDIDATE', tmp_path / 'no_existe.joblib')
    with pytest.raises((FileNotFoundError, ModuleNotFoundError)):
        fp.registrar()


def test_multicaso_fraude_entrenamiento(monkeypatch):
    from src.training import pipeline_multicaso as pm
    monkeypatch.setattr(fp, 'entrenar', lambda: 'fraude_entrenado')
    assert pm.ejecutar('fraude') == 'fraude_entrenado'


def test_multicaso_fraude_registro(monkeypatch):
    from src.training import pipeline_multicaso as pm
    monkeypatch.setattr(fp, 'registrar', lambda: 'fraude_registrado')
    assert pm.ejecutar('fraude', True) == 'fraude_registrado'


def test_multicaso_desconocido():
    from src.training import pipeline_multicaso as pm
    with pytest.raises(ValueError, match='desconocido'):
        pm.ejecutar('xyz')
