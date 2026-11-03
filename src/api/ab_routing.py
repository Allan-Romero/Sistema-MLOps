
import random

from src.database.connection import get_connection


def obtener_experimento_activo(caso_uso="churn"):
    """Consulta la configuración A/B activa en PostgreSQL."""

    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, version_a, version_b,
                       porcentaje_trafico_b
                FROM experiments
                WHERE caso_uso = %s
                  AND estado = 'activo'
                LIMIT 1;
                """,
                (caso_uso,),
            )

            fila = cursor.fetchone()

        if fila is None:
            return None

        return {
            "experimento_id": fila[0],
            "version_a": fila[1],
            "version_b": fila[2],
            "porcentaje_trafico_b": fila[3],
        }

    finally:
        conexion.close()


def seleccionar_version_ab(experimento, valor_aleatorio=None):
    """
    Selecciona una versión según el porcentaje configurado.

    Si no existe experimento activo, devuelve None.
    En ese caso, la API utilizará el modelo activo normal.
    """

    if experimento is None:
        return None

    porcentaje_b = experimento["porcentaje_trafico_b"]

    if not isinstance(porcentaje_b, int) or not (
        0 <= porcentaje_b <= 100
    ):
        raise ValueError(
            "El porcentaje de tráfico B debe estar entre 0 y 100."
        )

    if valor_aleatorio is None:
        valor_aleatorio = random.random()

    if not 0 <= valor_aleatorio < 1:
        raise ValueError(
            "El valor aleatorio debe estar entre 0 y 1."
        )

    grupo = (
        "B"
        if valor_aleatorio < porcentaje_b / 100
        else "A"
    )

    version = (
        experimento["version_b"]
        if grupo == "B"
        else experimento["version_a"]
    )

    return {
        "experimento_id": experimento["experimento_id"],
        "grupo": grupo,
        "version": version,
        "porcentaje_trafico_b": porcentaje_b,
    }
