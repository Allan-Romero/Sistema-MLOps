"""Pruebas de coordinación del pipeline sin escribir en PostgreSQL real."""
import json
import pytest
from src.database import persist_results
from src.training.promotion_policy import decidir_promocion


@pytest.fixture
def entorno_simulado(monkeypatch, tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "churn_model_candidate.joblib").write_bytes(b"modelo simulado")
    comparacion = {
        "Logistic Regression": {
            "accuracy": 0.81, "precision": 0.68, "recall": 0.62,
            "f1_score": 0.65, "roc_auc": 0.85,
        },
        "XGBoost": {
            "accuracy": 0.79, "precision": 0.61, "recall": 0.58,
            "f1_score": 0.59, "roc_auc": 0.83,
        },
    }
    seleccion = {
        "selected_model": "Logistic Regression",
        "decision_metric": "f1_score", "metric_value": 0.65,
    }
    archivo_comparacion = models_dir / "model_comparison.json"
    archivo_seleccion = models_dir / "model_selection.json"
    archivo_comparacion.write_text(json.dumps(comparacion), encoding="utf-8")
    archivo_seleccion.write_text(json.dumps(seleccion), encoding="utf-8")
    monkeypatch.setattr(persist_results, "MODELS_DIR", models_dir)
    monkeypatch.setattr(persist_results, "COMPARISON_FILE", archivo_comparacion)
    monkeypatch.setattr(persist_results, "SELECTION_FILE", archivo_seleccion)
    return {"models_dir": models_dir, "comparacion": comparacion}


@pytest.mark.parametrize("f1_activo,esperado", [(0.6032, True), (0.70, False)])
def test_pipeline_decide_promocion(monkeypatch, entorno_simulado, f1_activo, esperado):
    modelos = entorno_simulado["models_dir"]
    invocaciones = []

    def registrar_candidato_simulado(**kwargs):
        invocaciones.append(kwargs)
        assert kwargs["caso_uso"] == "churn"
        assert kwargs["version"] is None
        assert kwargs["algoritmo"] == "logistic_regression"
        assert kwargs["archivo_candidato"].is_file()
        assert set(kwargs["metricas_por_algoritmo"]) == {"logistic_regression", "xgboost"}
        assert kwargs["metricas_por_algoritmo"]["logistic_regression"]["f1_score"] == 0.65
        assert kwargs["metricas_por_algoritmo"]["xgboost"]["f1_score"] == 0.59

        version = "v1.1"
        (modelos / f"churn_model_{version}.joblib").write_bytes(
            kwargs["archivo_candidato"].read_bytes()
        )
        decision = decidir_promocion(kwargs["f1_candidato"], f1_activo, kwargs["umbral"])
        return {
            "registro_id": 4, "caso_uso": "churn", "version_candidata": version,
            "version_anterior": "v1.0", "f1_candidato": decision.f1_candidato,
            "f1_activo": decision.f1_activo, "mejora": decision.mejora,
            "umbral": decision.umbral, "promovido": decision.promover,
            "estado": "activa" if decision.promover else "descartada",
            "motivo": decision.motivo,
        }

    monkeypatch.setattr(persist_results, "registrar_candidato", registrar_candidato_simulado)
    resultado = persist_results.main()
    assert resultado["promovido"] is esperado
    assert resultado["version_candidata"] == "v1.1"
    assert len(invocaciones) == 1
    assert (modelos / "churn_model_v1.1.joblib").read_bytes() == b"modelo simulado"


def test_pipeline_rechaza_metricas_inconsistentes(monkeypatch, entorno_simulado):
    persist_results.SELECTION_FILE.write_text(
        json.dumps({"selected_model": "Logistic Regression",
                    "decision_metric": "f1_score", "metric_value": 0.99}),
        encoding="utf-8",
    )

    def registro_prohibido(**kwargs):
        raise AssertionError("No debe registrar una selección inválida.")

    monkeypatch.setattr(persist_results, "registrar_candidato", registro_prohibido)
    with pytest.raises(ValueError, match="no coincide"):
        persist_results.main()
    assert not (entorno_simulado["models_dir"] / "churn_model_v1.1.joblib").exists()


def test_error_de_registro_no_guarda_metricas(monkeypatch, entorno_simulado):
    def registro_fallido(**kwargs):
        raise RuntimeError("Fallo simulado de PostgreSQL")

    monkeypatch.setattr(persist_results, "registrar_candidato", registro_fallido)
    with pytest.raises(RuntimeError, match="Fallo simulado"):
        persist_results.main()
    assert not (entorno_simulado["models_dir"] / "churn_model_v1.1.joblib").exists()
