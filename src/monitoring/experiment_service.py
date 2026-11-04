"""A/B pospromoción: comparar la activa con su predecesora auditada.

El cierre requiere 30 etiquetas por versión. La decisión y su historial
se confirman juntos bajo el mismo bloqueo que promoción y rollback.
"""
from src.database.connection import get_connection
from src.monitoring.rollback_observations import calcular_f1_desde_etiquetas


def abrir_experimento(caso_uso, porcentaje_b=50):
    if type(porcentaje_b) is not int or not 0 <= porcentaje_b <= 100:
        raise ValueError("Porcentaje B inválido.")
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s));", (f"mlops_promotion:{caso_uso}",))
            cursor.execute(
                """SELECT p.version_anterior, p.version_candidata
                   FROM promotion_decisions p
                   JOIN model_versions b ON b.caso_uso = p.caso_uso
                     AND b.version = p.version_candidata AND b.estado = 'activa'
                   JOIN model_versions a ON a.caso_uso = p.caso_uso
                     AND a.version = p.version_anterior AND a.estado = 'historica'
                   WHERE p.caso_uso = %s AND p.resultado = 'promovida'
                   ORDER BY p.id DESC LIMIT 1;""", (caso_uso,))
            pareja = cursor.fetchone()
            if pareja is None:
                raise ValueError("No hay promoción reversible para comparar.")
            cursor.execute(
                """INSERT INTO experiments (caso_uso, version_a, version_b, porcentaje_trafico_b)
                   VALUES (%s, %s, %s, %s) RETURNING id;""",
                (caso_uso, *pareja, porcentaje_b))
            identificador = cursor.fetchone()[0]
        conexion.commit()
        return identificador
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def finalizar_experimento(caso_uso):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s));", (f"mlops_promotion:{caso_uso}",))
            cursor.execute(
                """SELECT id, version_a, version_b, started_at FROM experiments
                   WHERE caso_uso = %s AND estado = 'activo' FOR UPDATE;""", (caso_uso,))
            experimento = cursor.fetchone()
            if experimento is None:
                raise ValueError("No hay experimento activo.")
            identificador, a, b, inicio = experimento
            cursor.execute("SELECT version FROM model_versions WHERE caso_uso = %s AND estado = 'activa' FOR UPDATE;", (caso_uso,))
            if cursor.fetchall() != [(b,)]:
                raise ValueError("La versión activa cambió durante el experimento.")
            cursor.execute(
                """SELECT p.id FROM promotion_decisions p JOIN model_versions a
                   ON a.caso_uso = p.caso_uso AND a.version = p.version_anterior
                   WHERE p.caso_uso = %s AND p.version_anterior = %s
                     AND p.version_candidata = %s AND p.resultado = 'promovida'
                     AND a.estado = 'historica';""", (caso_uso, a, b))
            if cursor.fetchone() is None:
                raise ValueError("La pareja no corresponde a una promoción reversible.")
            metricas = {}
            for version in (a, b):
                cursor.execute(
                    """SELECT prediction, etiqueta_real FROM predictions
                       WHERE caso_uso = %s AND model_version = %s
                         AND created_at >= %s AND created_at <= CURRENT_TIMESTAMP
                         AND etiqueta_real IS NOT NULL;""", (caso_uso, version, inicio))
                metricas[version] = calcular_f1_desde_etiquetas(cursor.fetchall())
            if min(m.cantidad for m in metricas.values()) < 30:
                raise ValueError("Se requieren al menos 30 etiquetas verificadas por versión.")
            fa, fb = metricas[a].f1, metricas[b].f1
            revertir = fb <= fa - 0.01
            ganadora = a if revertir else b
            motivo = f"A/B observado: {a} F1={fa:.6f}; {b} F1={fb:.6f}. " + (
                "Rollback por degradación >= 0.01." if revertir else "Se conserva la versión promovida; sin degradación suficiente.")
            if revertir:
                from src.monitoring.rollback_service import MODELS_DIR
                if not (MODELS_DIR / f"{caso_uso}_model_{a}.joblib").is_file():
                    raise FileNotFoundError("No está disponible el artefacto de retorno.")
                cursor.execute("UPDATE model_versions SET estado = 'descartada' WHERE caso_uso = %s AND version = %s;", (caso_uso, b))
                cursor.execute("UPDATE model_versions SET estado = 'activa' WHERE caso_uso = %s AND version = %s;", (caso_uso, a))
                cursor.execute(
                    """INSERT INTO deployments (caso_uso, version_origen, version_destino,
                       tipo_operacion, motivo, metrica_principal, valor_metrica_origen, valor_metrica_destino)
                       VALUES (%s, %s, %s, 'rollback', %s, 'f1_score', %s, %s);""",
                    (caso_uso, b, a, motivo, fb, fa))
            cursor.execute(
                """UPDATE experiments SET estado = 'finalizado', ended_at = CURRENT_TIMESTAMP,
                   version_ganadora = %s WHERE id = %s;""", (ganadora, identificador))
        conexion.commit()
        return {"experimento_id": identificador, "caso_uso": caso_uso,
                "version_ganadora": ganadora, "rollback": revertir,
                "f1_control": fa, "f1_candidata": fb, "motivo": motivo}
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accion", choices=["abrir", "cerrar"])
    parser.add_argument("--caso-uso", choices=["churn", "fraude"], required=True)
    args = parser.parse_args()
    resultado = abrir_experimento(args.caso_uso) if args.accion == "abrir" else finalizar_experimento(args.caso_uso)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
