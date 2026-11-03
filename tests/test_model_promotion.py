
from unittest.mock import MagicMock

import pytest

from src.database import model_promotion


def preparar_prueba(
    monkeypatch,
    tmp_path,
    versiones_activas,
    existe_version=False,
):
    archivo = tmp_path / "churn_model_v1.1.joblib"
    archivo.write_bytes(b"modelo de prueba")

    monkeypatch.setattr(
        model_promotion,
        "MODELS_DIR",
        tmp_path,
    )

    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value

    cursor.fetchall.return_value = versiones_activas

    cursor.fetchone.side_effect = [
        (99,) if existe_version else None,
        (4,),
    ]

    monkeypatch.setattr(
        model_promotion,
        "get_connection",
        lambda: conexion,
    )

    return conexion, cursor


def test_candidato_mejor_se_promueve(monkeypatch, tmp_path):
    conexion, cursor = preparar_prueba(
        monkeypatch,
        tmp_path,
        [(3, "v1.0", 0.6032)],
    )

    resultado = model_promotion.registrar_candidato(
        "churn", "v1.1", "logistic_regression", 0.65
    )

    assert resultado["promovido"] is True
    assert resultado["estado"] == "activa"
    assert resultado["version_anterior"] == "v1.0"

    sql = " ".join(
        llamada.args[0]
        for llamada in cursor.execute.call_args_list
    )

    assert "UPDATE model_versions" in sql
    conexion.commit.assert_called_once()
    conexion.rollback.assert_not_called()


def test_candidato_peor_se_descarta(monkeypatch, tmp_path):
    conexion, cursor = preparar_prueba(
        monkeypatch,
        tmp_path,
        [(3, "v1.0", 0.6032)],
    )

    resultado = model_promotion.registrar_candidato(
        "churn", "v1.1", "logistic_regression", 0.57
    )

    assert resultado["promovido"] is False
    assert resultado["estado"] == "descartada"

    sql = " ".join(
        llamada.args[0]
        for llamada in cursor.execute.call_args_list
    )

    assert "UPDATE model_versions" not in sql
    conexion.commit.assert_called_once()


def test_varias_versiones_activas_provocan_error(
    monkeypatch, tmp_path
):
    conexion, _ = preparar_prueba(
        monkeypatch,
        tmp_path,
        [
            (3, "v1.0", 0.6032),
            (2, "v1.0", 0.6032),
        ],
    )

    with pytest.raises(ValueError, match="varias versiones"):
        model_promotion.registrar_candidato(
            "churn", "v1.1", "logistic_regression", 0.65
        )

    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()


def test_version_duplicada_se_rechaza(monkeypatch, tmp_path):
    conexion, _ = preparar_prueba(
        monkeypatch,
        tmp_path,
        [(3, "v1.0", 0.6032)],
        existe_version=True,
    )

    with pytest.raises(ValueError, match="ya está registrada"):
        model_promotion.registrar_candidato(
            "churn", "v1.1", "logistic_regression", 0.65
        )

    conexion.rollback.assert_called_once()


def test_artefacto_inexistente(monkeypatch, tmp_path):
    monkeypatch.setattr(
        model_promotion,
        "MODELS_DIR",
        tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        model_promotion.registrar_candidato(
            "churn", "v1.1", "logistic_regression", 0.65
        )
