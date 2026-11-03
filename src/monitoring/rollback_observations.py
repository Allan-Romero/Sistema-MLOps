"""Consultas de solo lectura para evaluar rollback con etiquetas verificadas.

No trata las métricas de entrenamiento ni una alerta aislada como evidencia
suficiente de degradación del modelo en producción.
"""
from dataclasses import dataclass
from datetime import datetime

from src.database.connection import get_connection


@dataclass(frozen=True)
class MetricasObservadas:
    cantidad: int
    f1: float | None
    tp: int = 0
    fp: int = 0
    fn: int = 0


def consultar(fuente_sql, parametros=()):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(fuente_sql, parametros)
            return cursor.fetchall()
    finally:
        conexion.close()


def tiene_etiquetas_reales():
    """La migración de etiquetas debe estar aplicada antes de medir F1."""
    filas = consultar(
        """SELECT COUNT(*) FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = 'predictions'
             AND column_name IN ('etiqueta_real', 'etiqueta_registrada_at');"""
    )
    return len(filas) == 1 and filas[0][0] == 2


def obtener_contexto_promocion(caso_uso):
    """Devuelve la única activa y su predecesora de la promoción auditada."""
    activas = consultar(
        """SELECT version FROM model_versions
           WHERE caso_uso = %s AND estado = 'activa'
           ORDER BY id DESC LIMIT 2;""", (caso_uso,)
    )
    if len(activas) != 1:
        return None
    version = activas[0][0]
    previas = consultar(
        """SELECT version_anterior, created_at
           FROM promotion_decisions
           WHERE caso_uso = %s AND version_candidata = %s
             AND resultado = 'promovida'
           ORDER BY id DESC LIMIT 1;""", (caso_uso, version)
    )
    if not previas or not previas[0][0] or previas[0][0] == version:
        return {"caso_uso": caso_uso, "version": version, "anterior": None,
                "promocion_en": None}
    anterior, promocion_en = previas[0]
    anteriores = consultar(
        """SELECT id FROM model_versions
           WHERE caso_uso = %s AND version = %s AND estado = 'historica'
           LIMIT 1;""", (caso_uso, anterior)
    )
    if not anteriores:
        return {"caso_uso": caso_uso, "version": version, "anterior": None,
                "promocion_en": None}
    return {"caso_uso": caso_uso, "version": version,
            "anterior": anterior, "promocion_en": promocion_en}


def calcular_f1_desde_etiquetas(filas):
    """F1 positivo binario; no inventar un puntaje si no hay observaciones."""
    tp = fp = fn = 0
    cantidad = 0
    for prediccion, real in filas:
        if isinstance(prediccion, bool) or isinstance(real, bool) or prediccion not in (0, 1) or real not in (0, 1):
            raise ValueError("Las predicciones y etiquetas reales deben ser 0 o 1.")
        cantidad += 1
        if prediccion == 1 and real == 1:
            tp += 1
        elif prediccion == 1:
            fp += 1
        elif real == 1:
            fn += 1
    if cantidad == 0:
        return MetricasObservadas(0, None)
    denominador = 2 * tp + fp + fn
    return MetricasObservadas(cantidad, 2 * tp / denominador if denominador else 0.0, tp, fp, fn)


def obtener_metricas_reales(caso_uso, version, inicio=None, fin=None, limite=1000):
    if not isinstance(limite, int) or isinstance(limite, bool) or not 30 <= limite <= 10000:
        raise ValueError("Límite de observaciones inválido.")
    # Fragmentos SQL fijos, sin interpolar valores aportados por el usuario.
    condiciones = ["caso_uso = %s", "model_version = %s", "etiqueta_real IS NOT NULL"]
    valores = [caso_uso, version]
    if inicio is not None:
        condiciones.append("created_at >= %s")
        valores.append(inicio)
    if fin is not None:
        condiciones.append("created_at <= %s")
        valores.append(fin)
    valores.append(limite)
    filas = consultar(
        "SELECT prediction, etiqueta_real FROM predictions WHERE "
        + " AND ".join(condiciones)
        + " ORDER BY created_at DESC, id DESC LIMIT %s;",
        tuple(valores),
    )
    return calcular_f1_desde_etiquetas(filas)


def obtener_ab_finalizado(caso_uso, control, candidata):
    """Solo experimentos cerrados y recientes, con fechas de inicio y fin."""
    filas = consultar(
        """SELECT id, started_at, ended_at
           FROM experiments
           WHERE caso_uso = %s AND version_a = %s AND version_b = %s
             AND estado = 'finalizado' AND ended_at IS NOT NULL
             AND started_at IS NOT NULL AND ended_at >= started_at
             AND ended_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
           ORDER BY ended_at DESC, id DESC LIMIT 1;""",
        (caso_uso, control, candidata),
    )
    if not filas:
        return None
    return {"id": filas[0][0], "inicio": filas[0][1], "fin": filas[0][2]}


def obtener_alerta_alta_reciente(caso_uso, promocion_en):
    """La alerta debe ser posterior a la promoción, reciente y no revisada."""
    if not isinstance(promocion_en, datetime):
        return None
    filas = consultar(
        """SELECT id FROM alerts
           WHERE caso_uso = %s AND nivel_drift = 'alto'
             AND revisada IS NOT TRUE AND created_at >= %s
             AND created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
           ORDER BY created_at DESC, id DESC LIMIT 1;""",
        (caso_uso, promocion_en),
    )
    return filas[0][0] if filas else None
