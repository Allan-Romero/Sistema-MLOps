import json

import pandas as pd

from src.database.connection import get_connection
from src.api.main import ChurnInput


def obtener_predicciones_dataframe(limite=100):
    """
    Recupera los datos originales de las predicciones
    almacenadas en PostgreSQL y los convierte en DataFrame.
    """

    if limite < 1:
        raise ValueError("El limite debe ser mayor que cero.")

    columnas_esperadas = list(ChurnInput.model_fields.keys())

    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            cursor.execute(
                """
                SELECT input_data
                FROM predictions
                WHERE caso_uso = %s
                ORDER BY id DESC
                LIMIT %s;
                """,
                ("churn", limite)
            )

            resultados = cursor.fetchall()

    finally:
        conexion.close()

    registros = []

    for fila in resultados:

        datos = fila[0]

        if isinstance(datos, str):
            datos = json.loads(datos)

        if not isinstance(datos, dict):
            raise ValueError(
                "Formato invalido en input_data."
            )

        if set(datos.keys()) != set(columnas_esperadas):
            raise ValueError(
                "Una prediccion no contiene "
                "exactamente las 19 variables esperadas."
            )

        # Validar los datos usando el esquema de FastAPI
        datos_validados = ChurnInput.model_validate(datos)

        registros.append(datos_validados.model_dump())

    df = pd.DataFrame(
        registros,
        columns=columnas_esperadas
    )

    return df


def main():

    print("========== SPRINT 3 - J5 ==========")
    print("RECUPERACION DE FEATURES\n")

    df = obtener_predicciones_dataframe()

    print(f"Predicciones recuperadas: {len(df)}")
    print(f"Variables por prediccion: {len(df.columns)}")

    print("\nColumnas:")
    print(df.columns.tolist())

    print("\nPrimeros registros:")
    print(df.head(3).to_string(index=False))

    print("\nValores nulos:")
    print(df.isnull().sum().sum())

    if df.empty:
        print("\nNo existen predicciones registradas.")
    else:
        print("\nDATAFRAME GENERADO CORRECTAMENTE")


if __name__ == "__main__":
    main()