from unittest.mock import MagicMock
import pytest
from src.monitoring import experiment_service as servicio


def entorno(monkeypatch, tmp_path, pierde=False, muestras=40):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = [(1, "v1", "v2", "2026-11-03"), (7,)]
    control = [(1, i % 2) for i in range(muestras)]
    candidata = [(1 - i % 2 if pierde else i % 2, i % 2) for i in range(muestras)]
    cursor.fetchall.side_effect = [[("v2",)], control, candidata]
    monkeypatch.setattr(servicio, "get_connection", lambda: conexion)
    from src.monitoring import rollback_service
    monkeypatch.setattr(rollback_service, "MODELS_DIR", tmp_path)
    (tmp_path / "churn_model_v1.joblib").write_bytes(b"modelo")
    return conexion, cursor


@pytest.mark.parametrize("pierde", [False, True])
def test_cierre_atomico_con_metricas_observadas(monkeypatch, tmp_path, pierde):
    conexion, cursor = entorno(monkeypatch, tmp_path, pierde)
    resultado = servicio.finalizar_experimento("churn")
    assert resultado["rollback"] is pierde
    assert resultado["version_ganadora"] == ("v1" if pierde else "v2")
    sql = [llamada.args[0] for llamada in cursor.execute.call_args_list]
    assert any("INSERT INTO deployments" in q for q in sql) is pierde
    assert any("version_ganadora" in q for q in sql)
    conexion.commit.assert_called_once()
    conexion.rollback.assert_not_called()


def test_muestras_insuficientes_no_cierran_experimento(monkeypatch, tmp_path):
    conexion, _ = entorno(monkeypatch, tmp_path, muestras=20)
    with pytest.raises(ValueError, match="30 etiquetas"):
        servicio.finalizar_experimento("churn")
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()


def test_fallo_de_bitacora_revierte_cierre_y_rollback(monkeypatch, tmp_path):
    conexion, cursor = entorno(monkeypatch, tmp_path, pierde=True)
    def ejecutar(sql, params):
        if "INSERT INTO deployments" in sql:
            raise RuntimeError("fallo bitácora")
    cursor.execute.side_effect = ejecutar
    with pytest.raises(RuntimeError, match="bitácora"):
        servicio.finalizar_experimento("churn")
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()


def test_activa_modificada_cancela_cierre(monkeypatch, tmp_path):
    conexion, cursor = entorno(monkeypatch, tmp_path)
    cursor.fetchall.side_effect = [[("v3",)]]
    with pytest.raises(ValueError, match="activa cambió"):
        servicio.finalizar_experimento("churn")
    conexion.commit.assert_not_called()


def test_abrir_solo_promocion_reversible(monkeypatch):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None
    monkeypatch.setattr(servicio, "get_connection", lambda: conexion)
    with pytest.raises(ValueError, match="reversible"):
        servicio.abrir_experimento("fraude")
    conexion.commit.assert_not_called()
