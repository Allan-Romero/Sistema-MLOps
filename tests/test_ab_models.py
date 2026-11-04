
import pytest

from fastapi import HTTPException
from src.api import ab_models


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ab_models,
        "MODELS_DIR",
        tmp_path,
    )

    (tmp_path / "churn_model_v1.0.joblib").write_bytes(
        b"modelo activo"
    )

    (tmp_path / "churn_model_v1.2.joblib").write_bytes(
        b"modelo candidato"
    )

    modelo_simulado = object()

    monkeypatch.setattr(
        ab_models,
        "cargar_archivo_modelo",
        lambda ruta: modelo_simulado,
    )

    return modelo_simulado


def test_cargar_modelo_activo(
    monkeypatch, entorno
):
    monkeypatch.setattr(
        ab_models,
        "ejecutar_consulta",
        lambda query, params: [
            ("v1.0", "logistic_regression", "activa")
        ],
    )

    resultado = ab_models.obtener_modelo_ab(
        "churn", "v1.0", "A"
    )

    assert resultado["modelo"] is entorno
    assert resultado["version"] == "v1.0"
    assert resultado["grupo"] == "A"


def test_cargar_modelo_candidato(
    monkeypatch, entorno
):
    monkeypatch.setattr(
        ab_models,
        "ejecutar_consulta",
        lambda query, params: [
            ("v1.2", "logistic_regression", "candidata")
        ],
    )

    resultado = ab_models.obtener_modelo_ab(
        "churn", "v1.2", "B"
    )

    assert resultado["modelo"] is entorno
    assert resultado["version"] == "v1.2"
    assert resultado["grupo"] == "B"


def test_no_servir_modelo_descartado(
    monkeypatch, entorno
):
    monkeypatch.setattr(
        ab_models,
        "ejecutar_consulta",
        lambda query, params: [
            ("v1.2", "logistic_regression", "descartada")
        ],
    )

    with pytest.raises(HTTPException) as error:
        ab_models.obtener_modelo_ab(
            "churn", "v1.2", "B"
        )

    assert error.value.status_code == 409


def test_version_inexistente(monkeypatch, entorno):
    monkeypatch.setattr(
        ab_models,
        "ejecutar_consulta",
        lambda query, params: [],
    )

    with pytest.raises(HTTPException) as error:
        ab_models.obtener_modelo_ab(
            "churn", "v1.9", "B"
        )

    assert error.value.status_code == 404


def test_version_invalida():
    with pytest.raises(HTTPException) as error:
        ab_models.obtener_modelo_ab(
            "churn", "../../secreto", "B"
        )

    assert error.value.status_code == 400


def test_grupo_invalido():
    with pytest.raises(HTTPException) as error:
        ab_models.obtener_modelo_ab(
            "churn", "v1.0", "C"
        )

    assert error.value.status_code == 400


def test_error_base_datos(monkeypatch, entorno):
    def consulta_fallida(query, params):
        raise RuntimeError("PostgreSQL no disponible")

    monkeypatch.setattr(
        ab_models,
        "ejecutar_consulta",
        consulta_fallida,
    )

    with pytest.raises(HTTPException) as error:
        ab_models.obtener_modelo_ab(
            "churn", "v1.0", "A"
        )

    assert error.value.status_code == 503


@pytest.mark.parametrize("grupo,estado,version", [("A", "historica", "v1.0"), ("B", "activa", "v1.2")])
@pytest.mark.parametrize("auditada", [False, True])
def test_pospromocion_exige_pareja_auditada(monkeypatch, entorno, grupo, estado, version, auditada):
    respuestas = iter([[(version, "logistic_regression", estado)], [(7,)] if auditada else []])
    monkeypatch.setattr(ab_models, "ejecutar_consulta", lambda query, params: next(respuestas))
    if auditada:
        assert ab_models.obtener_modelo_ab("churn", version, grupo)["modelo"] is entorno
    else:
        with pytest.raises(HTTPException) as error:
            ab_models.obtener_modelo_ab("churn", version, grupo)
        assert error.value.status_code == 409
