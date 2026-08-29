from src.database.connection import get_connection


def ejecutar_consulta(query, params=None):
    """
    Ejecuta una consulta de lectura (SELECT) y retorna los resultados.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            resultados = cursor.fetchall()
        return resultados
    finally:
        conn.close()


def obtener_predicciones(limite=10):
    """
    Consulta las últimas predicciones registradas en la base de datos.
    """
    query = """
        SELECT id, caso_uso, prediction, probability, model_version, created_at
        FROM predictions
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (limite,))


def obtener_metricas(limite=10):
    """
    Consulta las últimas métricas registradas del modelo.
    """
    query = """
        SELECT id, caso_uso, model_version, accuracy, precision, recall,
               f1_score, roc_auc, created_at
        FROM model_metrics
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (limite,))


def obtener_alertas(limite=10):
    """
    Consulta las últimas alertas de drift registradas.
    """
    query = """
        SELECT id, caso_uso, variable_afectada, nivel_drift, descripcion,
               revisada, created_at
        FROM alerts
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (limite,))