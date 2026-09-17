from src.database.connection import get_connection
import json
from src.database.connection import get_connection

def ejecutar_insercion(query, params):
    """
    Ejecuta una consulta de escritura (INSERT) y confirma los cambios.
    Retorna el id del registro insertado.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            nuevo_id = cursor.fetchone()[0]
        conn.commit()
        return nuevo_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def guardar_metricas(caso_uso, model_version, algoritmo=None, accuracy=None,
                     precision=None, recall=None, f1_score=None, roc_auc=None):
    query = """
        INSERT INTO model_metrics (caso_uso, model_version, algoritmo, accuracy,
                                   precision, recall, f1_score, roc_auc)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    params = (caso_uso, model_version, algoritmo, accuracy, precision,
              recall, f1_score, roc_auc)
    return ejecutar_insercion(query, params)


def guardar_prediccion(caso_uso, input_data, prediction, probability=None, model_version=None):
    """
    Inserta una predicción en la tabla predictions.

    caso_uso: "fraude" o "churn"
    input_data: diccionario con los datos de entrada enviados a la API
    prediction: resultado del modelo (0 o 1)
    probability: probabilidad asociada a la predicción
    model_version: versión del modelo utilizado
    """
    query = """
        INSERT INTO predictions (caso_uso, input_data, prediction, probability, model_version)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    params = (caso_uso, json.dumps(input_data), prediction, probability, model_version)
    return ejecutar_insercion(query, params)


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
        SELECT id, caso_uso, model_version, algoritmo, accuracy, precision,
               recall, f1_score, roc_auc, created_at
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

def guardar_version_modelo(caso_uso, version, algoritmo=None, metrica_principal=None,
                           valor_metrica=None, estado="historica"):
    """
    Inserta una nueva versión de modelo en la tabla model_versions.

    caso_uso: "fraude" o "churn"
    version: identificador de la versión (ej. "v1.0")
    algoritmo: "logistic_regression" o "xgboost"
    metrica_principal: métrica usada para la decisión (ej. "f1_score")
    valor_metrica: valor obtenido en esa métrica
    estado: "activa", "historica" o "degradada"
    """
    query = """
        INSERT INTO model_versions (caso_uso, version, algoritmo, metrica_principal,
                                    valor_metrica, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    params = (caso_uso, version, algoritmo, metrica_principal, valor_metrica, estado)
    return ejecutar_insercion(query, params)


def obtener_versiones(limite=20):
    """
    Consulta el historial de versiones de modelos, de la más reciente a la más antigua.
    """
    query = """
        SELECT id, caso_uso, version, algoritmo, metrica_principal,
               valor_metrica, estado, created_at
        FROM model_versions
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (limite,))


def obtener_version_activa(caso_uso):
    """
    Consulta la versión actualmente marcada como activa para un caso de uso.
    """
    query = """
        SELECT id, caso_uso, version, algoritmo, metrica_principal,
               valor_metrica, estado, created_at
        FROM model_versions
        WHERE caso_uso = %s AND estado = 'activa'
        ORDER BY created_at DESC
        LIMIT 1;
    """
    return ejecutar_consulta(query, (caso_uso,))

def obtener_comparacion_modelos(caso_uso):
    """
    Obtiene las métricas más recientes de cada algoritmo para comparar su desempeño.
    """
    query = """
        SELECT DISTINCT ON (algoritmo)
               algoritmo, model_version, accuracy, precision, recall, f1_score, roc_auc
        FROM model_metrics
        WHERE caso_uso = %s AND algoritmo IS NOT NULL
        ORDER BY algoritmo, created_at DESC;
    """
    return ejecutar_consulta(query, (caso_uso,))