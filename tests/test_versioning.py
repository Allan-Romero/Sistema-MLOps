
from unittest.mock import MagicMock

from src.training import versioning


# ============================================================
# SPRINT 4 - S4-J2
# PRUEBAS DEL VERSIONAMIENTO AUTOMATICO
# ============================================================


def test_primera_version():
    resultado = versioning.calcular_siguiente_version([])

    assert resultado == "v1.0"


def test_version_anterior_sin_decimal():
    resultado = versioning.calcular_siguiente_version(
        ["v1"]
    )

    assert resultado == "v1.1"


def test_siguiente_version():
    resultado = versioning.calcular_siguiente_version(
        ["v1", "v1.0", "v1.1"]
    )

    assert resultado == "v1.2"


def test_versiones_desordenadas():
    resultado = versioning.calcular_siguiente_version(
        ["v1.3", "v1.0", "v1.2", "v1.1"]
    )

    assert resultado == "v1.4"


def test_ignorar_versiones_de_otra_serie():
    resultado = versioning.calcular_siguiente_version(
        ["v2.0", "v1.2", "invalida"]
    )

    assert resultado == "v1.3"


def test_consultar_version_desde_postgresql(monkeypatch):
    conexion = MagicMock()

    cursor = (
        conexion.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchall.return_value = [
        ("v1",),
        ("v1.0",),
    ]

    monkeypatch.setattr(
        versioning,
        "get_connection",
        lambda: conexion
    )

    resultado = versioning.obtener_siguiente_version(
        caso_uso="churn"
    )

    assert resultado == "v1.1"

    conexion.close.assert_called_once()

    consulta = cursor.execute.call_args

    assert "model_versions" in consulta.args[0]
    assert consulta.args[1] == ("churn",)
