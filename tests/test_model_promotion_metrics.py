"""Confirma que métricas y auditoría comparten la misma transacción."""
from unittest.mock import MagicMock
import pytest
from src.database import model_promotion


METRICAS = {
    "logistic_regression": {
        "accuracy": 0.81, "precision": 0.68, "recall": 0.62,
        "f1_score": 0.65, "roc_auc": 0.85,
    },
    "xgboost": {
        "accuracy": 0.79, "precision": 0.61, "recall": 0.58,
        "f1_score": 0.59, "roc_auc": 0.83,
    },
}


def preparar_entorno(monkeypatch, tmp_path):
    candidato = tmp_path / "churn_model_candidate.joblib"
    candidato.write_bytes(b"modelo candidato")
    monkeypatch.setattr(model_promotion, "MODELS_DIR", tmp_path)
    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value
    cursor.fetchall.side_effect = [
        [(3, "v1.0", 0.6032)],
        [("v1",), ("v1.0",)],
    ]
    cursor.fetchone.side_effect = [None, (4,)]
    monkeypatch.setattr(model_promotion, "get_connection", lambda: conexion)
    return candidato, conexion, cursor


def test_metricas_y_auditoria_en_mismo_commit(monkeypatch, tmp_path):
    candidato, conexion, cursor = preparar_entorno(monkeypatch, tmp_path)
    resultado = model_promotion.registrar_candidato(
        "churn", None, "logistic_regression", 0.65,
        archivo_candidato=candidato, metricas_por_algoritmo=METRICAS,
    )
    assert resultado["promovido"] is True
    assert conexion.commit.call_count == 1
    assert conexion.rollback.call_count == 0
    inserciones = [
        c.args[0] for c in cursor.execute.call_args_list
        if "INSERT INTO model_metrics" in c.args[0]
    ]
    assert len(inserciones) == 2
    auditoria = [
        c.args[0] for c in cursor.execute.call_args_list
        if "INSERT INTO promotion_decisions" in c.args[0]
    ]
    assert len(auditoria) == 1
    assert (tmp_path / "churn_model_v1.1.joblib").is_file()


def test_error_en_metricas_revierte_todo(monkeypatch, tmp_path):
    candidato, conexion, cursor = preparar_entorno(monkeypatch, tmp_path)

    def ejecutar_sql(sql, params):
        if "INSERT INTO model_metrics" in sql:
            raise RuntimeError("Error insertando métricas")

    cursor.execute.side_effect = ejecutar_sql
    with pytest.raises(RuntimeError, match="Error insertando métricas"):
        model_promotion.registrar_candidato(
            "churn", None, "logistic_regression", 0.65,
            archivo_candidato=candidato, metricas_por_algoritmo=METRICAS,
        )
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
    assert not (tmp_path / "churn_model_v1.1.joblib").exists()


def test_rechaza_metricas_que_no_coinciden(monkeypatch, tmp_path):
    monkeypatch.setattr(model_promotion, "MODELS_DIR", tmp_path)
    with pytest.raises(ValueError, match="no coincide"):
        model_promotion.registrar_candidato(
            "churn", None, "logistic_regression", 0.9,
            archivo_candidato=tmp_path / "no-existe.joblib",
            metricas_por_algoritmo=METRICAS,
        )
