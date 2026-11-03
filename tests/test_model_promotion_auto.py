
from unittest.mock import MagicMock

import pytest

from src.database import model_promotion


def preparar_entorno(monkeypatch, tmp_path, f1_activo):
    candidato = tmp_path / "churn_model_candidate.joblib"
    candidato.write_bytes(b"modelo candidato")

    monkeypatch.setattr(
        model_promotion, "MODELS_DIR", tmp_path
    )

    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value

    cursor.fetchall.side_effect = [
        [(3, "v1.0", f1_activo)],
        [("v1",), ("v1.0",)],
    ]

    cursor.fetchone.side_effect = [None, (4,)]

    monkeypatch.setattr(
        model_promotion,
        "get_connection",
        lambda: conexion,
    )

    return candidato, conexion, cursor


@pytest.mark.parametrize(
    "f1_activo, esperado",
    [(0.6032, True), (0.70, False)],
)
def test_version_automatica_y_decision(
    monkeypatch, tmp_path, f1_activo, esperado
):
    candidato, conexion, cursor = preparar_entorno(
        monkeypatch, tmp_path, f1_activo
    )

    resultado = model_promotion.registrar_candidato(
        caso_uso="churn",
        version=None,
        algoritmo="logistic_regression",
        f1_candidato=0.65,
        archivo_candidato=candidato,
    )

    assert resultado["version_candidata"] == "v1.1"
    assert resultado["promovido"] is esperado

    versionado = tmp_path / "churn_model_v1.1.joblib"
    assert versionado.read_bytes() == b"modelo candidato"

    # La primera operación debe adquirir el bloqueo.
    primera_consulta = cursor.execute.call_args_list[0].args[0]
    assert "pg_advisory_xact_lock" in primera_consulta

    conexion.commit.assert_called_once()


def test_no_sobrescribir_artefacto_existente(
    monkeypatch, tmp_path
):
    candidato, conexion, _ = preparar_entorno(
        monkeypatch, tmp_path, 0.6032
    )

    versionado = tmp_path / "churn_model_v1.1.joblib"
    versionado.write_bytes(b"modelo original")

    with pytest.raises(FileExistsError):
        model_promotion.registrar_candidato(
            "churn",
            None,
            "logistic_regression",
            0.65,
            archivo_candidato=candidato,
        )

    assert versionado.read_bytes() == b"modelo original"
    conexion.rollback.assert_called_once()


def test_error_sql_revierte_y_limpia_artefacto(
    monkeypatch, tmp_path
):
    candidato, conexion, cursor = preparar_entorno(
        monkeypatch, tmp_path, 0.6032
    )

    def ejecutar_sql(sql, params):
        if "INSERT INTO model_versions" in sql:
            raise RuntimeError("Error SQL simulado")

    cursor.execute.side_effect = ejecutar_sql

    with pytest.raises(RuntimeError, match="Error SQL"):
        model_promotion.registrar_candidato(
            "churn",
            None,
            "logistic_regression",
            0.65,
            archivo_candidato=candidato,
        )

    assert not (
        tmp_path / "churn_model_v1.1.joblib"
    ).exists()

    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()
