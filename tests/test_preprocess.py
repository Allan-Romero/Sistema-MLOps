import pandas as pd

from src.training.preprocess import (
    limpiar_datos,
    dividir_y_codificar,
)


def test_limpiar_datos_elimina_customer_id():
    df = pd.DataFrame({
        "customerID": [
            "0001-A",
            "0002-B"
        ],
        "TotalCharges": [
            "",
            "25.5"
        ],
        "tenure": [
            0,
            1
        ],
        "Churn": [
            "No",
            "Yes"
        ]
    })

    resultado = limpiar_datos(df)

    assert "customerID" not in resultado.columns

    assert resultado["TotalCharges"].isnull().sum() == 0

    assert resultado.loc[
        0,
        "TotalCharges"
    ] == 0

    assert resultado.loc[
        1,
        "TotalCharges"
    ] == 25.5


def test_dividir_y_codificar():
    df = pd.DataFrame({
        "gender": [
            "Male",
            "Female"
        ] * 10,

        "Contract": [
            "Month-to-month",
            "One year"
        ] * 10,

        "tenure": list(
            range(1, 21)
        ),

        "MonthlyCharges": [
            50.0 + i
            for i in range(20)
        ],

        "TotalCharges": [
            100.0 + i
            for i in range(20)
        ],

        "Churn": [
            "No",
            "Yes"
        ] * 10
    })

    (
        X_train,
        X_test,
        y_train,
        y_test
    ) = dividir_y_codificar(df)

    assert len(X_train) == 16
    assert len(X_test) == 4

    assert len(y_train) == 16
    assert len(y_test) == 4

    assert list(
        X_train.columns
    ) == list(
        X_test.columns
    )

    assert (
        X_train
        .select_dtypes(
            exclude=["number"]
        )
        .shape[1]
        == 0
    )

    assert (
        X_test
        .select_dtypes(
            exclude=["number"]
        )
        .shape[1]
        == 0
    )

    assert set(
        y_train.unique()
    ).issubset({
        0,
        1
    })

    assert set(
        y_test.unique()
    ).issubset({
        0,
        1
    })