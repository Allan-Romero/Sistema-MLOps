import json
import pytest

from src.monitoring import rollback_job


def test_job_consulta_no_aplica(monkeypatch, tmp_path):
    recibidos = []
    def revisar_rollback(caso_uso, aplicar):
        recibidos.append((caso_uso, aplicar))
        return {"estado": "sin_promocion_reversible", "rollback": False}
    monkeypatch.setattr(rollback_job, "revisar_rollback", revisar_rollback)
    ruta = tmp_path / "carpeta" / "evaluaciones.jsonl"
    salida = rollback_job.ejecutar_job(ruta_log=ruta)
    assert recibidos == [("churn", False)]
    assert salida["modo"] == "consulta"
    assert json.loads(ruta.read_text(encoding="utf-8").strip()) == salida


def test_job_aplicar_explicitamente(monkeypatch, tmp_path):
    recibidos = []
    monkeypatch.setattr(
        rollback_job, "revisar_rollback",
        lambda caso_uso, aplicar: recibidos.append((caso_uso, aplicar)) or {"rollback": True},
    )
    salida = rollback_job.ejecutar_job("churn", aplicar=True, ruta_log=tmp_path / "out.jsonl")
    assert recibidos == [("churn", True)]
    assert salida["modo"] == "aplicar"
    assert salida["resultado"]["rollback"] is True


def test_fallo_no_se_silencia_ni_registra_exito(monkeypatch, tmp_path):
    def fallo(*args, **kwargs):
        raise RuntimeError("base no disponible")
    monkeypatch.setattr(rollback_job, "revisar_rollback", fallo)
    ruta = tmp_path / "out.jsonl"
    with pytest.raises(RuntimeError, match="base no disponible"):
        rollback_job.ejecutar_job(ruta_log=ruta)
    assert not ruta.exists()


def test_main_sin_aplicar(monkeypatch, tmp_path, capsys):
    ruta = tmp_path / "registro.jsonl"
    monkeypatch.setattr(rollback_job, "revisar_rollback", lambda caso_uso, aplicar: {"estado": "ok", "rollback": aplicar})
    salida = rollback_job.main(["--caso-uso", "churn", "--log", str(ruta)])
    assert salida["resultado"]["rollback"] is False
    assert json.loads(capsys.readouterr().out)["resultado"]["estado"] == "ok"
