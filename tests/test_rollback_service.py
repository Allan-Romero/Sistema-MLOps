from unittest.mock import MagicMock

import pytest

from src.monitoring.rollback_policy import evaluar_ab, evaluar_drift, DecisionRollback
from src.monitoring import rollback_service as service


def test_ab_degradado_con_muestras_suficientes():
    d = evaluar_ab(0.65, 0.55, 100, 100, "v1.3", "v1.0", "v1.3")
    assert d.activar is True
    assert d.origen == "ab"


def test_ab_control_activo_no_requiere_rollback():
    d = evaluar_ab(0.65, 0.55, 100, 100, "v1.0", "v1.0", "v1.3")
    assert d.activar is False


def test_ab_pocas_etiquetas_no_dispara():
    d = evaluar_ab(0.65, 0.55, 20, 100, "v1.3", "v1.0", "v1.3")
    assert d.activar is False


def test_ab_igual_no_dispara():
    d = evaluar_ab(0.65, 0.65, 100, 100, "v1.3", "v1.0", "v1.3")
    assert d.activar is False


def test_drift_alto_y_f1_bajo_dispara():
    d = evaluar_drift("alto", 0.48, 60, 0.63)
    assert d.activar is True


@pytest.mark.parametrize("nivel,f1,n,previo", [
    ("medio", 0.40, 100, 0.70),
    ("alto", 0.70, 100, 0.80),
    ("alto", 0.30, 10, 0.80),
    ("alto", 0.30, 100, 0.40),
])
def test_drift_no_dispara_sin_doble_condicion(nivel, f1, n, previo):
    assert not evaluar_drift(nivel, f1, n, previo).activar


def preparar_bd(monkeypatch, tmp_path):
    monkeypatch.setattr(service, "MODELS_DIR", tmp_path)
    (tmp_path / "churn_model_v1.0.joblib").write_bytes(b"artefacto")
    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [(8, "v1.3", 0.62)]
    cursor.fetchone.side_effect = [("v1.0",), (3, "v1.0", 0.63), (40,)]
    monkeypatch.setattr(service, "get_connection", lambda: conexion)
    return conexion, cursor


def decision():
    return DecisionRollback(True, "drift", "Drift alto y F1 observado 0.48", 0.48, 0.63)


def test_rollback_atomico_y_bitacora(monkeypatch, tmp_path):
    conexion, cursor = preparar_bd(monkeypatch, tmp_path)
    resultado = service.ejecutar_rollback("churn", "v1.3", decision())
    assert resultado["version_origen"] == "v1.3"
    assert resultado["version_destino"] == "v1.0"
    assert resultado["despliegue_id"] == 40
    sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
    assert "pg_advisory_xact_lock" in sql
    assert "INSERT INTO deployments" in sql
    assert "UPDATE experiments" in sql
    assert sql.index("UPDATE model_versions SET estado = 'descartada'") < sql.index("UPDATE model_versions SET estado = 'activa'")
    conexion.commit.assert_called_once()
    conexion.close.assert_called_once()


def test_cambio_de_version_cancela_operacion(monkeypatch, tmp_path):
    conexion, cursor = preparar_bd(monkeypatch, tmp_path)
    cursor.fetchall.return_value = [(9, "v1.4", 0.68)]
    with pytest.raises(ValueError, match="versión activa cambió"):
        service.ejecutar_rollback("churn", "v1.3", decision())
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()


def test_sin_promocion_auditada_no_rollback(monkeypatch, tmp_path):
    conexion, cursor = preparar_bd(monkeypatch, tmp_path)
    cursor.fetchone.side_effect = [None]
    with pytest.raises(ValueError, match="promoción auditada"):
        service.ejecutar_rollback("churn", "v1.3", decision())
    conexion.rollback.assert_called_once()


def test_error_bitacora_revierte_toda_la_transaccion(monkeypatch, tmp_path):
    conexion, cursor = preparar_bd(monkeypatch, tmp_path)
    def ejecutar(sql, params):
        if "INSERT INTO deployments" in sql:
            raise RuntimeError("Falló auditoría")
    cursor.execute.side_effect = ejecutar
    with pytest.raises(RuntimeError, match="Falló auditoría"):
        service.ejecutar_rollback("churn", "v1.3", decision())
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()


def test_sin_autorizacion_no_toca_bd(monkeypatch):
    monkeypatch.setattr(service, "get_connection", lambda: pytest.fail("No conectar"))
    with pytest.raises(ValueError, match="no autorizó"):
        service.ejecutar_rollback("churn", "v1.3", DecisionRollback(False, "drift", "Sin datos"))
