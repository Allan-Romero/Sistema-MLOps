from datetime import datetime
from unittest.mock import Mock

import pytest

from src.monitoring import rollback_auto as auto
from src.monitoring import rollback_observations as obs


@pytest.fixture
def contexto(monkeypatch):
    monkeypatch.setattr(obs, "obtener_contexto_promocion", lambda caso: {
        "caso_uso": caso, "version": "v2.0", "anterior": "v1.0",
        "promocion_en": datetime(2026, 11, 1)
    })
    monkeypatch.setattr(obs, "tiene_etiquetas_reales", lambda: True)
    monkeypatch.setattr(obs, "obtener_ab_finalizado", lambda caso, a, b: None)
    monkeypatch.setattr(obs, "obtener_alerta_alta_reciente", lambda caso, t: None)


def metricas(cantidad, f1):
    return obs.MetricasObservadas(cantidad, f1)


def test_f1_sin_observaciones():
    assert obs.calcular_f1_desde_etiquetas([]).f1 is None


def test_f1_perfecto():
    r = obs.calcular_f1_desde_etiquetas([(1, 1), (1, 1), (0, 0), (0, 0)])
    assert (r.cantidad, r.f1, r.tp, r.fp, r.fn) == (4, 1.0, 2, 0, 0)


def test_f1_parcial():
    r = obs.calcular_f1_desde_etiquetas([(1, 1), (1, 0), (0, 1), (0, 0)])
    assert r.f1 == 0.5


def test_f1_sin_positivos():
    assert obs.calcular_f1_desde_etiquetas([(0, 0)] * 32).f1 == 0.0


@pytest.mark.parametrize("fila", [(2, 1), (0, 4), (True, 1), (0, False)])
def test_etiqueta_invalida(fila):
    with pytest.raises(ValueError, match="0 o 1"):
        obs.calcular_f1_desde_etiquetas([fila])


def test_sin_promocion_no_hace_rollback(contexto, monkeypatch):
    monkeypatch.setattr(obs, "obtener_contexto_promocion", lambda caso: {
        "version": "v1.0", "anterior": None, "promocion_en": None})
    assert auto.revisar_rollback()["estado"] == "sin_promocion_reversible"


def test_sin_columnas_no_hace_rollback(contexto, monkeypatch):
    monkeypatch.setattr(obs, "tiene_etiquetas_reales", lambda: False)
    assert auto.revisar_rollback()["estado"] == "faltan_columnas_etiqueta_real"


def test_sin_evidencia_no_aplica(contexto, monkeypatch):
    monkeypatch.setattr(auto, "ejecutar_rollback", lambda *args: pytest.fail("No revertir"))
    assert auto.revisar_rollback(aplicar=True)["estado"] == "sin_evidencia_suficiente"


def test_ab_perdedor_modo_consulta(contexto, monkeypatch):
    t0 = datetime(2026, 11, 1)
    t1 = datetime(2026, 11, 2)
    monkeypatch.setattr(obs, "obtener_ab_finalizado", lambda *args: {"id": 7, "inicio": t0, "fin": t1})
    def fake_medicion(caso, version, inicio=None, fin=None):
        assert inicio == t0 and fin == t1
        return metricas(80, 0.67) if version == "v1.0" else metricas(40, 0.45)
    monkeypatch.setattr(obs, "obtener_metricas_reales", fake_medicion)
    monkeypatch.setattr(auto, "ejecutar_rollback", lambda *args: pytest.fail("dry-run"))
    r = auto.revisar_rollback()
    assert r["estado"] == "rollback_recomendado" and not r["rollback"]
    assert r["origen"] == "ab" and r["evidencia"]["experimento_id"] == 7


def test_ab_perdedor_modo_aplicar(contexto, monkeypatch):
    monkeypatch.setattr(obs, "obtener_ab_finalizado", lambda *args: {
        "id": 7, "inicio": datetime(2026, 11, 1), "fin": datetime(2026, 11, 2)})
    monkeypatch.setattr(obs, "obtener_metricas_reales", lambda caso, version, inicio=None, fin=None: (
        metricas(80, 0.67) if version == "v1.0" else metricas(40, 0.45)))
    servicio = Mock(return_value={"rollback": True, "despliegue_id": 23})
    monkeypatch.setattr(auto, "ejecutar_rollback", servicio)
    r = auto.revisar_rollback(aplicar=True)
    assert r["estado"] == "rollback_ejecutado"
    servicio.assert_called_once()
    assert servicio.call_args.args[1] == "v2.0"


def test_ab_muestra_insuficiente(contexto, monkeypatch):
    monkeypatch.setattr(obs, "obtener_ab_finalizado", lambda *args: {
        "id": 7, "inicio": datetime(2026, 11, 1), "fin": datetime(2026, 11, 2)})
    monkeypatch.setattr(obs, "obtener_metricas_reales", lambda caso, version, inicio=None, fin=None: (
        metricas(80, 0.67) if version == "v1.0" else metricas(20, 0.45)))
    assert auto.revisar_rollback()["estado"] == "sin_evidencia_suficiente"


def test_drift_alto_y_f1_degradado(contexto, monkeypatch):
    monkeypatch.setattr(obs, "obtener_alerta_alta_reciente", lambda caso, fecha: 12)
    monkeypatch.setattr(obs, "obtener_metricas_reales", lambda caso, version, inicio=None, fin=None: (
        metricas(45, 0.43) if version == "v2.0" else metricas(70, 0.75)))
    r = auto.revisar_rollback()
    assert r["origen"] == "drift"
    assert r["evidencia"]["alerta_id"] == 12
    assert r["evidencia"]["etiquetadas_actual"] == 45


def test_drift_sin_muestras_previas(contexto, monkeypatch):
    monkeypatch.setattr(obs, "obtener_alerta_alta_reciente", lambda caso, fecha: 12)
    monkeypatch.setattr(obs, "obtener_metricas_reales", lambda caso, version, inicio=None, fin=None: (
        metricas(45, 0.43) if version == "v2.0" else metricas(12, 0.75)))
    assert auto.revisar_rollback()["estado"] == "sin_evidencia_suficiente"


def test_validacion_caso_de_uso(contexto):
    with pytest.raises(ValueError, match="Caso de uso"):
        auto.revisar_rollback("churn; DROP TABLE")


def test_lectura_f1_usa_version_y_parametros(monkeypatch):
    llamada = []
    def fake(sql, params):
        llamada.append((sql, params))
        return [(1, 1), (0, 0)]
    monkeypatch.setattr(obs, "consultar", fake)
    r = obs.obtener_metricas_reales("churn", "v1.0", datetime(2026, 11, 1), datetime(2026, 11, 2))
    assert r.f1 == 1.0
    assert "etiqueta_real IS NOT NULL" in llamada[0][0]
    assert llamada[0][1][:2] == ("churn", "v1.0")


def test_no_activa_unica(contexto, monkeypatch):
    monkeypatch.setattr(obs, "obtener_contexto_promocion", lambda caso: None)
    assert auto.revisar_rollback()["estado"] == "sin_version_activa_unica"


def test_lectura_sin_etiquetas_migradas(monkeypatch):
    monkeypatch.setattr(obs, "consultar", lambda *args: [(0,)])
    assert not obs.tiene_etiquetas_reales()
