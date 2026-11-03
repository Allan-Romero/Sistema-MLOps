
import pytest
from fastapi import HTTPException

from src.api import model_loader


def registro_activo(version="v1.0"):
    """Simula un registro de model_versions."""
    return (
        3,
        "churn",
        version,
        "logistic_regression",
        "f1_score",
        0.6032,
        "activa",
        None,
    )


@pytest.fixture(autouse=True)
def limpiar_cache():
    """Evita que las pruebas compartan modelos en memoria."""
    model_loader.cargar_archivo_modelo.cache_clear()
    yield
    model_loader.cargar_archivo_modelo.cache_clear()


def test_carga_modelo_activo(monkeypatch, tmp_path):
    archivo = tmp_path / "churn_model_v1.0.joblib"
    archivo.write_bytes(b"modelo simulado")

    monkeypatch.setattr(model_loader, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(
        model_loader,
        "obtener_version_activa",
        lambda caso_uso: [registro_activo()],
    )

    modelo_simulado = object()

    monkeypatch.setattr(
        model_loader.joblib,
        "load",
        lambda ruta: modelo_simulado,
    )

    resultado = model_loader.obtener_modelo_activo("churn")

    assert resultado["modelo"] is modelo_simulado
    assert resultado["version"] == "v1.0"
    assert resultado["caso_uso"] == "churn"


def test_modelo_se_mantiene_en_cache(monkeypatch, tmp_path):
    archivo = tmp_path / "churn_model_v1.0.joblib"
    archivo.write_bytes(b"modelo simulado")

    monkeypatch.setattr(model_loader, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(
        model_loader,
        "obtener_version_activa",
        lambda caso_uso: [registro_activo()],
    )

    llamadas = []

    def cargar_simulado(ruta):
        llamadas.append(ruta)
        return object()

    monkeypatch.setattr(
        model_loader.joblib,
        "load",
        cargar_simulado,
    )

    primero = model_loader.obtener_modelo_activo()
    segundo = model_loader.obtener_modelo_activo()

    assert primero["modelo"] is segundo["modelo"]
    assert len(llamadas) == 1


def test_cambio_de_version(monkeypatch, tmp_path):
    for version in ("v1.0", "v2"):
        (tmp_path / f"churn_model_{version}.joblib").write_bytes(
            b"modelo simulado"
        )

    monkeypatch.setattr(model_loader, "MODELS_DIR", tmp_path)

    version_actual = ["v1.0"]

    monkeypatch.setattr(
        model_loader,
        "obtener_version_activa",
        lambda caso_uso: [
            registro_activo(version_actual[0])
        ],
    )

    monkeypatch.setattr(
        model_loader.joblib,
        "load",
        lambda ruta: str(ruta),
    )

    primero = model_loader.obtener_modelo_activo()

    version_actual[0] = "v2"

    segundo = model_loader.obtener_modelo_activo()

    assert primero["version"] == "v1.0"
    assert segundo["version"] == "v2"
    assert primero["modelo"] != segundo["modelo"]


def test_sin_version_activa(monkeypatch):
    monkeypatch.setattr(
        model_loader,
        "obtener_version_activa",
        lambda caso_uso: [],
    )

    with pytest.raises(HTTPException) as error:
        model_loader.obtener_modelo_activo()

    assert error.value.status_code == 404


def test_artefacto_inexistente(monkeypatch, tmp_path):
    monkeypatch.setattr(model_loader, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(
        model_loader,
        "obtener_version_activa",
        lambda caso_uso: [registro_activo()],
    )

    with pytest.raises(HTTPException) as error:
        model_loader.obtener_modelo_activo()

    assert error.value.status_code == 503


def test_error_base_datos(monkeypatch):
    def simular_error(caso_uso):
        raise RuntimeError("PostgreSQL no disponible")

    monkeypatch.setattr(
        model_loader,
        "obtener_version_activa",
        simular_error,
    )

    with pytest.raises(HTTPException) as error:
        model_loader.obtener_modelo_activo()

    assert error.value.status_code == 503
