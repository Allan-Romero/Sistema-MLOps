"""Protecciones críticas: un fallo no puede dejar un despliegue a medias.

Las conexiones son dobles controlados; la integración PostgreSQL/HTTP real
se valida por separado en el job delivery, no por estas pruebas unitarias.
"""
from unittest.mock import MagicMock

import pytest

from src.database import model_promotion
from src.monitoring import experiment_service, rollback_service
from src.monitoring.rollback_policy import DecisionRollback


def conexion_falsa(monkeypatch, modulo):
    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value
    monkeypatch.setattr(modulo, "get_connection", lambda: conexion)
    return conexion, cursor


def comprobar_sin_actualizaciones(cursor):
    assert not any(
        llamada.args[0].lstrip().startswith(("UPDATE", "INSERT"))
        for llamada in cursor.execute.call_args_list
    )


def test_promocion_fallo_historial_revierte_bd_y_artefacto(monkeypatch, tmp_path):
    conexion, cursor = conexion_falsa(monkeypatch, model_promotion)
    monkeypatch.setattr(model_promotion, "MODELS_DIR", tmp_path)
    candidato = tmp_path / "candidate.joblib"
    candidato.write_bytes(b"candidato controlado")
    cursor.fetchall.side_effect = [[(1, "v1.0", 0.6)], [("v1.0",)]]
    cursor.fetchone.side_effect = [None, (2,)]

    def ejecutar(sql, parametros):
        if "INSERT INTO deployments" in sql:
            raise RuntimeError("Historial no disponible")

    cursor.execute.side_effect = ejecutar
    with pytest.raises(RuntimeError, match="Historial"):
        model_promotion.registrar_candidato(
            "churn", None, "logistic_regression", 0.8,
            archivo_candidato=candidato,
        )
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()
    conexion.close.assert_called_once()
    assert candidato.exists()
    assert not (tmp_path / "churn_model_v1.1.joblib").exists()


def test_rollback_sin_artefacto_no_cambia_versiones(monkeypatch, tmp_path):
    conexion, cursor = conexion_falsa(monkeypatch, rollback_service)
    monkeypatch.setattr(rollback_service, "MODELS_DIR", tmp_path)
    cursor.fetchall.return_value = [(2, "v1.1", 0.8)]
    cursor.fetchone.side_effect = [("v1.0",), (1, "v1.0", 0.7)]
    with pytest.raises(FileNotFoundError, match="artefacto anterior"):
        rollback_service.ejecutar_rollback(
            "churn", "v1.1", DecisionRollback(True, "ab", "Degradación observada", 0.5, 0.7))
    comprobar_sin_actualizaciones(cursor)
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()
    conexion.close.assert_called_once()


def test_cierre_sin_artefacto_no_finaliza_ni_reasigna_activa(monkeypatch, tmp_path):
    conexion, cursor = conexion_falsa(monkeypatch, experiment_service)
    monkeypatch.setattr(rollback_service, "MODELS_DIR", tmp_path)
    cursor.fetchone.side_effect = [(8, "v1.0", "v1.1", "2026-11-05"), (3,)]
    cursor.fetchall.side_effect = [
        [("v1.1",)], [(1, 1)] * 30, [(0, 1)] * 30,
    ]
    with pytest.raises(FileNotFoundError, match="artefacto de retorno"):
        experiment_service.finalizar_experimento("fraude")
    comprobar_sin_actualizaciones(cursor)
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()


def test_cierre_sin_experimento_no_modifica_bd(monkeypatch):
    conexion, cursor = conexion_falsa(monkeypatch, experiment_service)
    cursor.fetchone.return_value = None
    with pytest.raises(ValueError, match="No hay experimento"):
        experiment_service.finalizar_experimento("churn")
    comprobar_sin_actualizaciones(cursor)
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()


def test_cierre_sin_pareja_auditada_cancela_operacion(monkeypatch):
    conexion, cursor = conexion_falsa(monkeypatch, experiment_service)
    cursor.fetchone.side_effect = [(8, "v1.0", "v1.1", "2026-11-05"), None]
    cursor.fetchall.return_value = [("v1.1",)]
    with pytest.raises(ValueError, match="promoción reversible"):
        experiment_service.finalizar_experimento("churn")
    comprobar_sin_actualizaciones(cursor)
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()


@pytest.mark.parametrize("porcentaje", [-1, 101, True, 50.5, "50"])
def test_apertura_porcentaje_invalido_no_conecta(monkeypatch, porcentaje):
    monkeypatch.setattr(experiment_service, "get_connection", lambda: pytest.fail("No debe conectar"))
    with pytest.raises(ValueError, match="Porcentaje"):
        experiment_service.abrir_experimento("churn", porcentaje)


def test_apertura_fallo_insert_revierte_y_cierra_conexion(monkeypatch):
    conexion, cursor = conexion_falsa(monkeypatch, experiment_service)
    cursor.fetchone.return_value = ("v1.0", "v1.1")

    def ejecutar(sql, parametros):
        if "INSERT INTO experiments" in sql:
            raise RuntimeError("Experimento activo duplicado")

    cursor.execute.side_effect = ejecutar
    with pytest.raises(RuntimeError, match="duplicado"):
        experiment_service.abrir_experimento("fraude", 50)
    conexion.commit.assert_not_called()
    conexion.rollback.assert_called_once()
    conexion.close.assert_called_once()
