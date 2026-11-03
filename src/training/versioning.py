
import re

from src.database.connection import get_connection


CASO_USO = "churn"
VERSION_MAYOR = 1


def calcular_siguiente_version(versiones):
    """
    Calcula la siguiente versión disponible.

    Ejemplos:
    [] -> v1.0
    ['v1', 'v1.0'] -> v1.1
    ['v1.0', 'v1.1'] -> v1.2
    """

    menores = []

    patron = rf"v{VERSION_MAYOR}(?:\.(\d+))?"

    for version in versiones:
        coincidencia = re.fullmatch(
            patron,
            str(version)
        )

        if coincidencia:
            numero = coincidencia.group(1)

            menores.append(
                int(numero) if numero is not None else 0
            )

    siguiente = max(menores, default=-1) + 1

    return f"v{VERSION_MAYOR}.{siguiente}"


def obtener_siguiente_version(caso_uso=CASO_USO):
    """
    Consulta PostgreSQL y calcula el siguiente
    identificador de versión del modelo.
    """

    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            cursor.execute(
                """
                SELECT version
                FROM model_versions
                WHERE caso_uso = %s;
                """,
                (caso_uso,)
            )

            registros = cursor.fetchall()

        versiones = [
            registro[0]
            for registro in registros
        ]

        return calcular_siguiente_version(versiones)

    finally:
        conexion.close()


def main():
    version = obtener_siguiente_version()

    print("========== VERSIONAMIENTO ==========")
    print(f"Caso de uso: {CASO_USO}")
    print(f"Siguiente versión: {version}")


if __name__ == "__main__":
    main()
