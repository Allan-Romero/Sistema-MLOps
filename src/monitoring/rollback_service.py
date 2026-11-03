"""Reversión transaccional de una promoción previa auditada.

No realiza rollback al importarse. Solo se invoca explícitamente con
una decisión de política validada. No requiere reiniciar FastAPI, pues
el endpoint /predict consulta la versión activa en PostgreSQL.
"""

from pathlib import Path
import re

from src.database.connection import get_connection
from src.monitoring.rollback_policy import DecisionRollback

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def ejecutar_rollback(caso_uso: str, version_esperada: str,
                     decision: DecisionRollback) -> dict:
    """Desactiva la versión degradada y restaura su predecesora auditada.

    La operación mantiene el mismo advisory lock que usa S4-J2. El destino
    se toma de promotion_decisions, nunca de una versión histórica arbitraria.
    Se actualiza la bitácora deployments en la misma transacción.
    """
    if not decision.activar:
        raise ValueError("La política no autorizó ejecutar el rollback.")
    if decision.origen not in {"ab", "drift"} or not decision.motivo:
        raise ValueError("Disparador o motivo de rollback inválido.")
    if not isinstance(caso_uso, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", caso_uso):
        raise ValueError("Caso de uso inválido.")
    if not isinstance(version_esperada, str) or not re.fullmatch(r"v\d+(?:\.\d+)*", version_esperada):
        raise ValueError("Versión esperada inválida.")

    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s));",
                (f"mlops_promotion:{caso_uso}",),
            )
            cursor.execute(
                """
                SELECT id, version, valor_metrica
                FROM model_versions
                WHERE caso_uso = %s AND estado = 'activa'
                ORDER BY id DESC
                FOR UPDATE;
                """,
                (caso_uso,),
            )
            activas = cursor.fetchall()
            if len(activas) != 1 or activas[0][1] != version_esperada:
                raise ValueError("La versión activa cambió; se canceló el rollback.")
            id_activo, version_actual, f1_entrenamiento = activas[0]

            # Solo se revierte a la versión que realmente precedió a la promoción.
            cursor.execute(
                """
                SELECT version_anterior
                FROM promotion_decisions
                WHERE caso_uso = %s
                  AND version_candidata = %s
                  AND resultado = 'promovida'
                ORDER BY id DESC LIMIT 1;
                """,
                (caso_uso, version_actual),
            )
            previo = cursor.fetchone()
            if not previo or not previo[0] or previo[0] == version_actual:
                raise ValueError("No existe una promoción auditada que permita regresar a una versión anterior.")
            version_destino = previo[0]

            cursor.execute(
                """
                SELECT id, version, valor_metrica
                FROM model_versions
                WHERE caso_uso = %s AND version = %s AND estado = 'historica'
                ORDER BY id DESC LIMIT 1 FOR UPDATE;
                """,
                (caso_uso, version_destino),
            )
            destino = cursor.fetchone()
            if destino is None:
                raise ValueError("La versión anterior no está disponible como histórica.")

            archivo = MODELS_DIR / f"{caso_uso}_model_{version_destino}.joblib"
            if not archivo.is_file():
                raise FileNotFoundError(f"No existe el artefacto anterior: {archivo}")

            # Desactivar antes de activar: compatible con el índice parcial único.
            cursor.execute(
                "UPDATE model_versions SET estado = 'descartada' WHERE id = %s;",
                (id_activo,),
            )
            cursor.execute(
                "UPDATE model_versions SET estado = 'activa' WHERE id = %s;",
                (destino[0],),
            )
            # Un A/B activo no debe seguir enviando tráfico a la versión retirada.
            cursor.execute(
                """
                UPDATE experiments SET estado = 'cancelado', ended_at = CURRENT_TIMESTAMP
                WHERE caso_uso = %s AND estado = 'activo';
                """,
                (caso_uso,),
            )
            cursor.execute(
                """
                INSERT INTO deployments (
                    caso_uso, version_origen, version_destino, tipo_operacion,
                    motivo, metrica_principal, valor_metrica_origen,
                    valor_metrica_destino
                ) VALUES (%s, %s, %s, 'rollback', %s, 'f1_score', %s, %s)
                RETURNING id;
                """,
                (
                    caso_uso, version_actual, version_destino, decision.motivo,
                    decision.f1_origen if decision.f1_origen is not None else f1_entrenamiento,
                    decision.f1_destino if decision.f1_destino is not None else destino[2],
                ),
            )
            despliegue_id = cursor.fetchone()[0]

        conexion.commit()
        return {
            "rollback": True,
            "caso_uso": caso_uso,
            "version_origen": version_actual,
            "version_destino": version_destino,
            "despliegue_id": despliegue_id,
            "motivo": decision.motivo,
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
