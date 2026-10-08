import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.training.train_model import entrenar_modelo


def test_entrenar_modelo_logistic_regression():
    X_train = pd.DataFrame({
        "feature_1": [
            0,
            0,
            0,
            1,
            1,
            1
        ],
        "feature_2": [
            1,
            2,
            3,
            7,
            8,
            9
        ]
    })

    y_train = pd.Series([
        0,
        0,
        0,
        1,
        1,
        1
    ])

    modelo = entrenar_modelo(
        X_train,
        y_train
    )

    assert isinstance(
        modelo,
        LogisticRegression
    )

    assert modelo.max_iter == 1000

    assert modelo.random_state == 42

    predicciones = modelo.predict(
        X_train
    )

    assert len(
        predicciones
    ) == len(
        X_train
    )

    assert set(
        predicciones
    ).issubset({
        0,
        1
    })