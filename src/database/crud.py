import json

from src.casos_uso import CASO_USO_POR_DEFECTO
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


def obtener_predicciones(caso_uso=CASO_USO_POR_DEFECTO, limite=10):
    """
    Consulta las últimas predicciones registradas para un caso de uso.
    """
    query = """
        SELECT id, caso_uso, prediction, probability, model_version, created_at
        FROM predictions
        WHERE caso_uso = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (caso_uso, limite))


def obtener_metricas(caso_uso=CASO_USO_POR_DEFECTO, limite=10):
    """
    Consulta las últimas métricas registradas del modelo de un caso de uso.
    """
    query = """
        SELECT id, caso_uso, model_version, algoritmo, accuracy, precision,
               recall, f1_score, roc_auc, created_at
        FROM model_metrics
        WHERE caso_uso = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (caso_uso, limite))


def obtener_alertas(caso_uso=CASO_USO_POR_DEFECTO, limite=10):
    """
    Consulta las últimas alertas de drift registradas para un caso de uso.
    """
    query = """
        SELECT id, caso_uso, variable_afectada, nivel_drift, descripcion,
               revisada, created_at
        FROM alerts
        WHERE caso_uso = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (caso_uso, limite))

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

def guardar_alerta(caso_uso, variable_afectada, nivel_drift,
                   descripcion=None, revisada=False):
    """
    Inserta una alerta de drift en la tabla alerts.

    caso_uso: "fraude" o "churn"
    variable_afectada: nombre de la variable donde se detectó el cambio
    nivel_drift: "bajo", "medio" o "alto"
    descripcion: detalle de la alerta, incluido el valor de la métrica
    revisada: indica si la alerta ya fue atendida
    """
    query = """
        INSERT INTO alerts (caso_uso, variable_afectada, nivel_drift,
                            descripcion, revisada)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    params = (caso_uso, variable_afectada, nivel_drift, descripcion, revisada)
    return ejecutar_insercion(query, params)


def obtener_versiones(caso_uso=CASO_USO_POR_DEFECTO, limite=20):
    """
    Consulta el historial de versiones de un caso de uso, de la más reciente
    a la más antigua.
    """
    query = """
        SELECT id, caso_uso, version, algoritmo, metrica_principal,
               valor_metrica, estado, created_at
        FROM model_versions
        WHERE caso_uso = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (caso_uso, limite))


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

def obtener_datos_entrada(caso_uso=CASO_USO_POR_DEFECTO, limite=1000):
    """
    Recupera los datos de entrada de las predicciones registradas,
    para el análisis de drift.
    """
    query = """
        SELECT input_data
        FROM predictions
        WHERE caso_uso = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """
    filas = ejecutar_consulta(query, (caso_uso, limite))
    return [fila[0] for fila in filas]


def registrar_etiqueta_real(prediction_id, etiqueta_real):
    """
    Registra el resultado verdadero de una predicción ya almacenada.

    prediction_id: identificador de la predicción en la tabla predictions
    etiqueta_real: valor observado (0 o 1)

    Retorna el id de la predicción actualizada, o None si no existe ninguna
    con ese identificador.
    """
    query = """
        UPDATE predictions
        SET etiqueta_real = %s,
            etiqueta_registrada_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING id;
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (etiqueta_real, prediction_id))
            fila = cursor.fetchone()
        conn.commit()
        return fila[0] if fila else None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def obtener_desempeno_por_version(caso_uso=CASO_USO_POR_DEFECTO, desde=None, hasta=None):
    """
    Calcula el desempeño real de cada versión del modelo sobre las
    predicciones cuya etiqueta verdadera ya se conoce.

    Retorna, por versión: tamaño de la muestra, accuracy, precision, recall,
    f1_score y roc_auc, las mismas métricas que el proyecto registra durante
    el entrenamiento, de modo que ambos números sean comparables.

    desde y hasta: si se indican, acotan el cálculo a esa ventana de
    tiempo, que es como se restringe a las predicciones de un experimento.
    Un experimento cerrado no debe incluir el tráfico posterior a su fin.

    El tamaño de la muestra se informa siempre: una diferencia calculada
    sobre pocas predicciones no permite concluir nada.
    """
    query = """
        WITH etiquetadas AS (
            SELECT model_version, prediction, etiqueta_real, probability
            FROM predictions
            WHERE caso_uso = %s
              AND etiqueta_real IS NOT NULL
              AND created_at >= COALESCE(%s::timestamp, created_at)
              AND created_at <= COALESCE(%s::timestamp, created_at)
        ),
        matriz AS (
            SELECT model_version,
                   COUNT(*) AS muestra,
                   COUNT(*) FILTER (WHERE prediction = 1 AND etiqueta_real = 1) AS vp,
                   COUNT(*) FILTER (WHERE prediction = 1 AND etiqueta_real = 0) AS fp,
                   COUNT(*) FILTER (WHERE prediction = 0 AND etiqueta_real = 1) AS fn,
                   COUNT(*) FILTER (WHERE prediction = 0 AND etiqueta_real = 0) AS vn
            FROM etiquetadas
            GROUP BY model_version
        ),
        rangos AS (
            -- Rango de cada probabilidad dentro de su versión. Ante empates
            -- corresponde el rango promedio, de ahí el ajuste por el conteo.
            SELECT model_version,
                   etiqueta_real,
                   RANK() OVER (PARTITION BY model_version ORDER BY probability)
                       + (COUNT(*) OVER (PARTITION BY model_version, probability) - 1) / 2.0
                       AS rango
            FROM etiquetadas
            WHERE probability IS NOT NULL
        ),
        auc AS (
            -- ROC-AUC por el estadístico de Mann-Whitney sobre esos rangos.
            SELECT model_version,
                   COUNT(*) FILTER (WHERE etiqueta_real = 1) AS positivos,
                   COUNT(*) FILTER (WHERE etiqueta_real = 0) AS negativos,
                   SUM(rango) FILTER (WHERE etiqueta_real = 1) AS suma_positivos
            FROM rangos
            GROUP BY model_version
        )
        SELECT m.model_version,
               m.muestra,
               (m.vp + m.vn)::float / NULLIF(m.muestra, 0) AS accuracy,
               m.vp::float / NULLIF(m.vp + m.fp, 0) AS precision,
               m.vp::float / NULLIF(m.vp + m.fn, 0) AS recall,
               (2.0 * m.vp) / NULLIF(2 * m.vp + m.fp + m.fn, 0) AS f1_score,
               (a.suma_positivos - a.positivos * (a.positivos + 1) / 2.0)
                   / NULLIF(a.positivos * a.negativos, 0) AS roc_auc
        FROM matriz m
        LEFT JOIN auc a ON a.model_version = m.model_version
        ORDER BY m.model_version;
    """
    return ejecutar_consulta(query, (caso_uso, desde, hasta))


def obtener_volumen_por_version(caso_uso=CASO_USO_POR_DEFECTO, desde=None, hasta=None):
    """
    Consulta el volumen de tráfico que atendió cada versión del modelo.

    Retorna, por versión: total de predicciones, cuántas tienen etiqueta
    real, cuántas no, el porcentaje del tráfico total y las fechas de la
    primera y la última predicción.

    desde y hasta: si se indican, acotan el conteo a esa ventana de
    tiempo, para que el reparto corresponda al periodo del experimento.
    """
    query = """
        SELECT model_version,
               COUNT(*) AS predicciones,
               COUNT(etiqueta_real) AS con_etiqueta,
               COUNT(*) - COUNT(etiqueta_real) AS sin_etiqueta,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS porcentaje_trafico,
               MIN(created_at) AS primera_prediccion,
               MAX(created_at) AS ultima_prediccion
        FROM predictions
        WHERE caso_uso = %s
          AND created_at >= COALESCE(%s::timestamp, created_at)
          AND created_at <= COALESCE(%s::timestamp, created_at)
        GROUP BY model_version
        ORDER BY predicciones DESC;
    """
    return ejecutar_consulta(query, (caso_uso, desde, hasta))


def obtener_historial_despliegues(caso_uso=CASO_USO_POR_DEFECTO, limite=20):
    """
    Consulta la bitácora de despliegues, de la más reciente a la más antigua.

    Incluye el motivo de cada promoción o rollback y la métrica de las dos
    versiones involucradas, que es lo que permite reconstruir por qué una
    versión dejó de estar en producción.
    """
    query = """
        SELECT id, caso_uso, version_origen, version_destino, tipo_operacion,
               motivo, metrica_principal, valor_metrica_origen,
               valor_metrica_destino, created_at
        FROM deployments
        WHERE caso_uso = %s
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return ejecutar_consulta(query, (caso_uso, limite))


def obtener_experimento_activo(caso_uso=CASO_USO_POR_DEFECTO):
    """
    Consulta el experimento A/B vigente para un caso de uso.

    Retorna la fila del experimento activo, o None si no hay ninguno en
    curso. El esquema garantiza que exista a lo sumo uno por caso de uso.
    """
    query = """
        SELECT id, caso_uso, version_a, version_b, porcentaje_trafico_b,
               estado, version_ganadora, started_at, ended_at
        FROM experiments
        WHERE caso_uso = %s AND estado = 'activo'
        LIMIT 1;
    """
    filas = ejecutar_consulta(query, (caso_uso,))
    return filas[0] if filas else None


def obtener_ultimo_experimento(caso_uso=CASO_USO_POR_DEFECTO):
    """
    Consulta el experimento A/B más reciente, esté activo o cerrado.

    Permite que el dashboard muestre el último resultado conocido cuando no
    hay ningún experimento en curso.
    """
    query = """
        SELECT id, caso_uso, version_a, version_b, porcentaje_trafico_b,
               estado, version_ganadora, started_at, ended_at
        FROM experiments
        WHERE caso_uso = %s
        ORDER BY started_at DESC
        LIMIT 1;
    """
    filas = ejecutar_consulta(query, (caso_uso,))
    return filas[0] if filas else None
