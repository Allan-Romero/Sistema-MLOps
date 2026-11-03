
from unittest.mock import MagicMock

import pytest

from src.database import model_promotion


def preparar_entorno(monkeypatch, tmp_path, f1_activo):
    candidato = tmp_path / "churn_model_candidate.joblib"
    candidato.write_bytes(b"modelo simulado")

    monkeypatch.setattr(
        model_promotion,
        "MODELS_DIR",
        tmp_path,
    )

    conexion = MagicMock()
    cursor = conexion.cursor.return_value.__enter__.return_value

    cursor.fetchall.side_effect = [
        [(3, "v1.0", f1_activo)],
        [("v1",), ("v1.0",)],
    ]

    cursor.fetchone.side_effect = [
        None,
        (4,),
    ]

    monkeypatch.setattr(
        model_promotion,
        "get_connection",
        lambda: conexion,
    )

    return candidato, conexion, cursor


@pytest.mark.parametrize(
    "f1_activo, f1_candidato, resultado_esperado",
    [
        (0.6032, 0.65, "promovida"),
        (0.70, 0.65, "descartada"),
    ],
)
def test_decision_se_registra_en_auditoria(
    monkeypatch,
    tmp_path,
    f1_activo,
    f1_candidato,
    resultado_esperado,
):
    candidato, conexion, cursor = preparar_entorno(
        monkeypatch,
        tmp_path,
        f1_activo,
    )

    resultado = model_promotion.registrar_candidato(
        caso_uso="churn",
        version=None,
        algoritmo="logistic_regression",
        f1_candidato=f1_candidato,
        archivo_candidato=candidato,
    )

    consultas_auditoria = [
        llamada
        for llamada in cursor.execute.call_args_list
        if "INSERT INTO promotion_decisions" in llamada.args[0]
    ]

    assert len(consultas_auditoria) == 1

    parametros = consultas_auditoria[0].args[1]

    assert parametros[0] == "churn"
    assert parametros[1] == "v1.1"
    assert parametros[2] == "v1.0"
    assert parametros[3] == "logistic_regression"
    assert parametros[4] == pytest.approx(f1_candidato)
    assert parametros[5] == pytest.approx(f1_activo)
    assert parametros[7] == pytest.approx(0.01)
    assert parametros[8] == resultado_esperado
    assert parametros[9] == resultado["motivo"]

    conexion.commit.assert_called_once()


def test_error_auditoria_revierte_promocion(
    monkeypatch,
    tmp_path,
):
    candidato, conexion, cursor = preparar_entorno(
        monkeypatch,
        tmp_path,
        0.6032,
    )

    def ejecutar_sql(sql, params):
        if "INSERT INTO promotion_decisions" in sql:
            raise RuntimeError(
                "Error simulado de auditoria"
            )

    cursor.execute.side_effect = ejecutar_sql

    with pytest.raises(
        RuntimeError,
        match="Error simulado de auditoria",
    ):
        model_promotion.registrar_candidato(
            caso_uso="churn",
            version=None,
            algoritmo="logistic_regression",
            f1_candidato=0.65,
            archivo_candidato=candidato,
        )

    # PostgreSQL no debe confirmar los cambios.
    conexion.rollback.assert_called_once()
    conexion.commit.assert_not_called()

    # El artefacto nuevo tampoco debe permanecer.
    assert not (
        tmp_path / "churn_model_v1.1.joblib"
    ).exists()
