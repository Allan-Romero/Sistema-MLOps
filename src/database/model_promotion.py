"""Asignación transaccional de versiones y decisiones de promoción."""

from pathlib import Path
import re
import shutil

from src.database.connection import get_connection
from src.training.promotion_policy import decidir_promocion, validar_valor
from src.training.versioning import calcular_siguiente_version


MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
METRICAS_REQUERIDAS = ("accuracy", "precision", "recall", "f1_score", "roc_auc")


def _normalizar_metricas(metricas_por_algoritmo):
    """Valida las métricas antes de iniciar una transacción con escrituras."""
    if metricas_por_algoritmo is None:
        return []  # Compatibilidad con consumidores previos de registrar_candidato.

    if not isinstance(metricas_por_algoritmo, dict) or not metricas_por_algoritmo:
        raise ValueError("Las métricas por algoritmo deben ser un diccionario no vacío.")

    registros = []
    for algoritmo, metricas in metricas_por_algoritmo.items():
        if not isinstance(algoritmo, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", algoritmo):
            raise ValueError("Identificador de algoritmo inválido en las métricas.")
        if not isinstance(metricas, dict):
            raise ValueError(f"Las métricas de {algoritmo} deben ser un diccionario.")

        valores = [
            float(validar_valor(f"{algoritmo}.{metrica}", metricas[metrica]))
            for metrica in METRICAS_REQUERIDAS
        ]
        registros.append((algoritmo, *valores))

    return registros


def registrar_candidato(
    caso_uso,
    version,
    algoritmo,
    f1_candidato,
    umbral=0.01,
    archivo_candidato=None,
    metricas_por_algoritmo=None,
):
    """
    Registra en una transacción la versión, todas las métricas y la auditoría.

    Cuando version es None, obtiene la siguiente versión bajo un bloqueo por
    caso de uso y crea un artefacto inmutable con ese identificador.
    """
    if not isinstance(caso_uso, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", caso_uso):
        raise ValueError("Caso de uso inválido.")
    if not isinstance(algoritmo, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", algoritmo):
        raise ValueError("Algoritmo inválido.")

    metricas = _normalizar_metricas(metricas_por_algoritmo)
    if metricas:
        seleccionadas = [fila[4] for fila in metricas if fila[0] == algoritmo]
        if len(seleccionadas) != 1 or abs(seleccionadas[0] - float(validar_valor("F1 candidato", f1_candidato))) > 1e-10:
            raise ValueError("El F1 del candidato no coincide con las métricas registradas.")

    automatico = version is None
    destino = None
    destino_creado = False

    if automatico:
        if archivo_candidato is None:
            raise ValueError("Falta el archivo candidato.")
        origen = Path(archivo_candidato)
        if not origen.is_file():
            raise FileNotFoundError(f"No existe el candidato: {origen}")
    else:
        if not isinstance(version, str) or not re.fullmatch(r"v\d+(?:\.\d+)*", version):
            raise ValueError("Formato de versión inválido.")
        destino = MODELS_DIR / f"{caso_uso}_model_{version}.joblib"
        if not destino.is_file():
            raise FileNotFoundError(f"No existe el artefacto: {destino}")

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
                ORDER BY created_at DESC, id DESC
                FOR UPDATE;
                """,
                (caso_uso,),
            )
            activas = cursor.fetchall()
            if len(activas) > 1:
                raise ValueError("Existen varias versiones activas.")

            activa = activas[0] if activas else None
            if activa and activa[2] is None:
                raise ValueError("La versión activa no tiene métrica F1.")

            version_anterior = activa[1] if activa else None
            f1_activo = activa[2] if activa else None

            if automatico:
                cursor.execute(
                    "SELECT version FROM model_versions WHERE caso_uso = %s;",
                    (caso_uso,),
                )
                version = calcular_siguiente_version([fila[0] for fila in cursor.fetchall()])
                destino = MODELS_DIR / f"{caso_uso}_model_{version}.joblib"
                if destino.exists():
                    raise FileExistsError(f"El artefacto {version} ya existe.")

            cursor.execute(
                """
                SELECT id FROM model_versions
                WHERE caso_uso = %s AND version = %s LIMIT 1;
                """,
                (caso_uso, version),
            )
            if cursor.fetchone() is not None:
                raise ValueError(f"La versión {version} ya está registrada.")

            decision = decidir_promocion(
                f1_candidato=f1_candidato,
                f1_activo=f1_activo,
                umbral=umbral,
            )

            if automatico:
                with origen.open("rb") as fuente:
                    with destino.open("xb") as salida:
                        destino_creado = True
                        shutil.copyfileobj(fuente, salida)

            estado = "activa" if decision.promover else "descartada"
            resultado_auditoria = "promovida" if decision.promover else "descartada"

            if decision.promover:
                cursor.execute(
                    """
                    UPDATE model_versions SET estado = 'historica'
                    WHERE caso_uso = %s AND estado = 'activa';
                    """,
                    (caso_uso,),
                )

            cursor.execute(
                """
                INSERT INTO model_versions (
                    caso_uso, version, algoritmo, metrica_principal,
                    valor_metrica, estado
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (caso_uso, version, algoritmo, "f1_score", decision.f1_candidato, estado),
            )
            registro_id = cursor.fetchone()[0]

            # Estas métricas comparten el MISMO commit que la decisión.
            for nombre, accuracy, precision, recall, f1_score, roc_auc in metricas:
                cursor.execute(
                    """
                    INSERT INTO model_metrics (
                        caso_uso, model_version, algoritmo, accuracy,
                        precision, recall, f1_score, roc_auc
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (caso_uso, version, nombre, accuracy, precision, recall, f1_score, roc_auc),
                )

            cursor.execute(
                """
                INSERT INTO promotion_decisions (
                    caso_uso, version_candidata, version_anterior,
                    algoritmo, f1_candidato, f1_activo, mejora,
                    umbral, resultado, motivo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    caso_uso,
                    version,
                    version_anterior,
                    algoritmo,
                    decision.f1_candidato,
                    decision.f1_activo,
                    decision.mejora,
                    decision.umbral,
                    resultado_auditoria,
                    decision.motivo,
                ),
            )

            if decision.promover:
                cursor.execute(
                    """INSERT INTO deployments (
                        caso_uso, version_origen, version_destino, tipo_operacion,
                        motivo, metrica_principal, valor_metrica_origen, valor_metrica_destino
                    ) VALUES (%s, %s, %s, 'promocion', %s, 'f1_score', %s, %s);""",
                    (caso_uso, version_anterior, version, decision.motivo,
                     f1_activo, decision.f1_candidato),
                )

        conexion.commit()
        return {
            "registro_id": registro_id,
            "caso_uso": caso_uso,
            "version_candidata": version,
            "version_anterior": version_anterior,
            "f1_candidato": decision.f1_candidato,
            "f1_activo": decision.f1_activo,
            "mejora": decision.mejora,
            "umbral": decision.umbral,
            "promovido": decision.promover,
            "estado": estado,
            "motivo": decision.motivo,
        }
    except Exception:
        conexion.rollback()
        if destino_creado and destino is not None:
            destino.unlink(missing_ok=True)
        raise
    finally:
        conexion.close()
