"""Demostracion reproducible de S4-J4 en una BASE DE DATOS AISLADA.

Uso (desde raiz del repositorio):
    python scripts/demo_rollback_j4.py --run

Crea mlops_j4_demo_<aleatorio>, inserta datos SINTETICOS, ejecuta la
politica y el rollback, consulta FastAPI ASGI antes/despues y elimina
la base de prueba. Nunca modifica mlops_db.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import secrets
import sys

from dotenv import load_dotenv
from psycopg2 import sql

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
EVIDENCE_FILE = PROJECT_ROOT / "reports" / "s4_j4_rollback_demo.json"

SCHEMA = [
    """CREATE TABLE model_versions (
        id SERIAL PRIMARY KEY, caso_uso VARCHAR(20) NOT NULL,
        version VARCHAR(20) NOT NULL, algoritmo VARCHAR(50),
        metrica_principal VARCHAR(20), valor_metrica DOUBLE PRECISION,
        estado VARCHAR(20), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE UNIQUE INDEX j4_demo_unica_activa ON model_versions(caso_uso)
       WHERE estado = 'activa'""",
    """CREATE TABLE promotion_decisions (
        id SERIAL PRIMARY KEY, caso_uso VARCHAR(20) NOT NULL,
        version_candidata VARCHAR(20) NOT NULL,
        version_anterior VARCHAR(20), resultado VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE experiments (
        id SERIAL PRIMARY KEY, caso_uso VARCHAR(20) NOT NULL,
        version_a VARCHAR(20) NOT NULL, version_b VARCHAR(20) NOT NULL,
        porcentaje_trafico_b INTEGER DEFAULT 20,
        estado VARCHAR(20) NOT NULL,
        version_ganadora VARCHAR(20),
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP
    )""",
    """CREATE TABLE deployments (
        id SERIAL PRIMARY KEY, caso_uso VARCHAR(20) NOT NULL,
        version_origen VARCHAR(20), version_destino VARCHAR(20) NOT NULL,
        tipo_operacion VARCHAR(20) NOT NULL, motivo TEXT,
        metrica_principal VARCHAR(20),
        valor_metrica_origen DOUBLE PRECISION,
        valor_metrica_destino DOUBLE PRECISION,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE predictions (
        id SERIAL PRIMARY KEY, caso_uso VARCHAR(20) NOT NULL,
        input_data JSONB NOT NULL,
        prediction INTEGER NOT NULL, probability DOUBLE PRECISION,
        model_version VARCHAR(20),
        etiqueta_real INTEGER, etiqueta_registrada_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
]

CHURN_EXAMPLE = {
    "gender": "Female", "SeniorCitizen": 0, "Partner": "Yes",
    "Dependents": "No", "tenure": 1, "PhoneService": "No",
    "MultipleLines": "No phone service", "InternetService": "DSL",
    "OnlineSecurity": "No", "OnlineBackup": "Yes",
    "DeviceProtection": "No", "TechSupport": "No",
    "StreamingTV": "No", "StreamingMovies": "No",
    "Contract": "Month-to-month", "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check", "MonthlyCharges": 29.85,
    "TotalCharges": 29.85,
}


def verificar_precondiciones():
    modelos = PROJECT_ROOT / "models"
    for version in ("v1.0", "v1.2"):
        path = modelos / f"churn_model_{version}.joblib"
        if not path.is_file():
            raise RuntimeError(f"Falta un artefacto para la demostracion: {path}")
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    from src.database.connection import get_connection
    conexion = get_connection()
    try:
        parametros = conexion.get_dsn_parameters()
        if parametros.get("dbname") != "mlops_db":
            raise RuntimeError("Proteccion activada: la conexion principal debe apuntar a mlops_db.")
    finally:
        conexion.close()
    return get_connection


def inicializar_demo(get_connection):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            for statement in SCHEMA:
                cursor.execute(statement)
            cursor.execute("""
                INSERT INTO model_versions
                  (caso_uso, version, algoritmo, metrica_principal, valor_metrica, estado)
                VALUES ('churn','v1.0','logistic_regression','f1_score',0.60,'historica'),
                       ('churn','v1.2','xgboost','f1_score',0.62,'activa');
            """)
            cursor.execute("""
                INSERT INTO promotion_decisions
                  (caso_uso, version_candidata, version_anterior, resultado, created_at)
                VALUES ('churn','v1.2','v1.0','promovida',
                        CURRENT_TIMESTAMP - INTERVAL '10 minutes');
            """)
            cursor.execute("""
                INSERT INTO experiments
                  (caso_uso, version_a, version_b, porcentaje_trafico_b,
                   estado, started_at, ended_at)
                VALUES ('churn','v1.0','v1.2',20,'finalizado',
                        CURRENT_TIMESTAMP - INTERVAL '5 minutes',
                        CURRENT_TIMESTAMP - INTERVAL '1 minute');
            """)
            cursor.execute("""
                INSERT INTO predictions
                  (caso_uso, input_data, prediction, probability,
                   model_version, etiqueta_real, etiqueta_registrada_at, created_at)
                SELECT 'churn', '{"demostracion_sintetica":true}'::jsonb,
                       1, 0.99, 'v1.0', 1,
                       CURRENT_TIMESTAMP - INTERVAL '2 minutes',
                       CURRENT_TIMESTAMP - INTERVAL '3 minutes'
                FROM generate_series(1,30);
            """)
            cursor.execute("""
                INSERT INTO predictions
                  (caso_uso, input_data, prediction, probability,
                   model_version, etiqueta_real, etiqueta_registrada_at, created_at)
                SELECT 'churn', '{"demostracion_sintetica":true}'::jsonb,
                       1, 0.99, 'v1.2', 0,
                       CURRENT_TIMESTAMP - INTERVAL '2 minutes',
                       CURRENT_TIMESTAMP - INTERVAL '3 minutes'
                FROM generate_series(1,30);
            """)
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def consultar_estados(get_connection):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT version, estado FROM model_versions
                WHERE caso_uso = 'churn' ORDER BY version
            """)
            return [{"version": r[0], "estado": r[1]} for r in cursor.fetchall()]
    finally:
        conexion.close()


def consultar_auditoria(get_connection):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT version_origen, version_destino, tipo_operacion, motivo
                FROM deployments WHERE caso_uso='churn'
                ORDER BY id DESC LIMIT 1
            """)
            fila = cursor.fetchone()
            return dict(zip(("version_origen","version_destino","tipo_operacion","motivo"), fila)) if fila else None
    finally:
        conexion.close()


def ejecutar_demo(get_connection):
    from fastapi.testclient import TestClient
    from src.api.main import app
    from src.monitoring.rollback_auto import revisar_rollback

    with TestClient(app) as cliente:
        antes_db = consultar_estados(get_connection)
        version_api_antes = cliente.get("/model-version")
        version_api_antes.raise_for_status()
        analisis = revisar_rollback("churn", aplicar=False)
        if analisis.get("estado") != "rollback_recomendado" or analisis.get("origen") != "ab":
            raise AssertionError(f"El evaluador no recomendo rollback A/B: {analisis}")

        aplicado = revisar_rollback("churn", aplicar=True)
        if aplicado.get("estado") != "rollback_ejecutado":
            raise AssertionError(f"El rollback no se aplico en la base aislada: {aplicado}")
        despues_db = consultar_estados(get_connection)
        version_api_despues = cliente.get("/model-version")
        version_api_despues.raise_for_status()
        respuesta_prediccion = cliente.post("/predict", json=CHURN_EXAMPLE)
        respuesta_prediccion.raise_for_status()
        prediccion = respuesta_prediccion.json()

    a = version_api_antes.json()
    b = version_api_despues.json()
    if a.get("model_version") != "v1.2" or b.get("model_version") != "v1.0":
        raise AssertionError(f"API no reflejo el cambio de version: {a}, {b}")
    if prediccion.get("model_version") != "v1.0":
        raise AssertionError(f"/predict no uso la version revertida: {prediccion}")
    if not ({"version":"v1.2","estado":"descartada"} in despues_db
            and {"version":"v1.0","estado":"activa"} in despues_db):
        raise AssertionError(f"Estados de version inesperados: {despues_db}")
    auditoria = consultar_auditoria(get_connection)
    if not auditoria or auditoria["tipo_operacion"] != "rollback":
        raise AssertionError(f"Falta bitacora de deployments: {auditoria}")

    return {
        "ejecucion": datetime.now().isoformat(timespec="seconds"),
        "tipo_datos": "SINTETICOS; prueba del mecanismo, no evaluacion real de modelos",
        "db_produccion_modificada": False,
        "estados_antes": antes_db,
        "api_version_antes": a["model_version"],
        "decision": analisis,
        "operacion": aplicado,
        "estados_despues": despues_db,
        "api_version_despues": b["model_version"],
        "predict_version_despues": prediccion["model_version"],
        "deployments": auditoria,
    }


def main():
    parser = argparse.ArgumentParser(description="Demo aislada y sintética de rollback S4-J4")
    parser.add_argument("--run", action="store_true", help="Crear y eliminar base de prueba aislada")
    args = parser.parse_args()
    if not args.run:
        parser.error("Agrega --run para iniciar la demostracion aislada.")

    get_connection = verificar_precondiciones()
    anterior_db = os.environ.get("POSTGRES_DB")
    nombre_demo = "mlops_j4_demo_" + secrets.token_hex(4)
    creada = False
    try:
        admin = get_connection()
        try:
            admin.autocommit = True
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(nombre_demo)))
            creada = True
        finally:
            admin.close()

        # Todos los componentes reutilizan get_connection() y van SOLO a la DB demo.
        os.environ["POSTGRES_DB"] = nombre_demo
        inicializar_demo(get_connection)
        informe = ejecutar_demo(get_connection)
        EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_FILE.write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(informe, indent=2, ensure_ascii=False))
        print(f"\nEvidencia guardada en: {EVIDENCE_FILE}")
    finally:
        if anterior_db is None:
            os.environ.pop("POSTGRES_DB", None)
        else:
            os.environ["POSTGRES_DB"] = anterior_db
        if creada:
            admin = get_connection()
            try:
                admin.autocommit = True
                with admin.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(nombre_demo)))
                print(f"Base de prueba eliminada: {nombre_demo}")
            finally:
                admin.close()


if __name__ == "__main__":
    main()
