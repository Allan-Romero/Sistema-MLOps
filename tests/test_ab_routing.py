
from unittest.mock import MagicMock

import pytest

from src.api import ab_routing


@pytest.fixture
def experimento():
    return {
        "experimento_id": 1,
        "version_a": "v1.0",
        "version_b": "v1.2",
        "porcentaje_trafico_b": 20,
    }


@pytest.mark.parametrize(
    "aleatorio, grupo, version",
    [
        (0.0, "B", "v1.2"),
        (0.19, "B", "v1.2"),
        (0.20, "A", "v1.0"),
        (0.99, "A", "v1.0"),
    ],
)
def test_distribucion_80_20(
    experimento, aleatorio, grupo, version
):
    resultado = ab_routing.seleccionar_version_ab(
        experimento,
        valor_aleatorio=aleatorio,
    )

    assert resultado["grupo"] == grupo
    assert resultado["version"] == version
    assert resultado["experimento_id"] == 1


def test_sin_experimento():
    resultado = ab_routing.seleccionar_version_ab(None)

    assert resultado is None


@pytest.mark.parametrize(
    "porcentaje, version",
    [
        (0, "v1.0"),
        (100, "v1.2"),
    ],
)
def test_porcentajes_extremos(
    experimento, porcentaje, version
):
    experimento["porcentaje_trafico_b"] = porcentaje

    resultado = ab_routing.seleccionar_version_ab(
        experimento,
        valor_aleatorio=0.5,
    )

    assert resultado["version"] == version


@pytest.mark.parametrize("porcentaje", [-1, 101])
def test_porcentaje_invalido(experimento, porcentaje):
    experimento["porcentaje_trafico_b"] = porcentaje

    with pytest.raises(ValueError):
        ab_routing.seleccionar_version_ab(
            experimento,
            valor_aleatorio=0.5,
        )


@pytest.mark.parametrize("aleatorio", [-0.1, 1.0])
def test_aleatorio_invalido(experimento, aleatorio):
    with pytest.raises(ValueError):
        ab_routing.seleccionar_version_ab(
            experimento,
            valor_aleatorio=aleatorio,
        )


def test_obtener_experimento_desde_postgresql(monkeypatch):
    conexion = MagicMock()

    cursor = (
        conexion.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (
        4,
        "v1.0",
        "v1.2",
        25,
    )

    monkeypatch.setattr(
        ab_routing,
        "get_connection",
        lambda: conexion,
    )

    resultado = ab_routing.obtener_experimento_activo(
        "churn"
    )

    assert resultado == {
        "experimento_id": 4,
        "version_a": "v1.0",
        "version_b": "v1.2",
        "porcentaje_trafico_b": 25,
    }

    conexion.close.assert_called_once()


def test_postgresql_sin_experimento(monkeypatch):
    conexion = MagicMock()

    cursor = (
        conexion.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = None

    monkeypatch.setattr(
        ab_routing,
        "get_connection",
        lambda: conexion,
    )

    resultado = ab_routing.obtener_experimento_activo(
        "churn"
    )

    assert resultado is None
    conexion.close.assert_called_once()
