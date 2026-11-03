"""Evaluación automática de rollback, segura por defecto (solo lectura).

Uso: python -m src.monitoring.rollback_auto --caso-uso churn
     python -m src.monitoring.rollback_auto --caso-uso churn --aplicar

Para automatización desatendida, programar la ejecución del segundo
comando en un scheduler externo DESPUÉS de recibir etiquetas reales.
"""
import argparse
import json
import re

from src.monitoring.rollback_policy import evaluar_ab, evaluar_drift
from src.monitoring.rollback_service import ejecutar_rollback
from src.monitoring import rollback_observations as obs


def revisar_rollback(caso_uso="churn", aplicar=False):
    if not isinstance(caso_uso, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", caso_uso):
        raise ValueError("Caso de uso inválido.")

    contexto = obs.obtener_contexto_promocion(caso_uso)
    if contexto is None:
        return {"estado": "sin_version_activa_unica", "rollback": False}
    activa = contexto["version"]
    anterior = contexto["anterior"]
    if anterior is None:
        return {"estado": "sin_promocion_reversible", "rollback": False, "activa": activa}
    if not obs.tiene_etiquetas_reales():
        return {"estado": "faltan_columnas_etiqueta_real", "rollback": False, "activa": activa}

    def resultado(decision, origen, evidencia):
        salida = {"estado": "rollback_recomendado", "rollback": False,
                  "activa": activa, "anterior": anterior, "origen": origen,
                  "motivo": decision.motivo, "evidencia": evidencia}
        if aplicar:
            transaccion = ejecutar_rollback(caso_uso, activa, decision)
            salida.update(transaccion)
            salida["estado"] = "rollback_ejecutado"
        return salida

    ab = obs.obtener_ab_finalizado(caso_uso, anterior, activa)
    if ab is not None:
        control = obs.obtener_metricas_reales(caso_uso, anterior, ab["inicio"], ab["fin"])
        candidata = obs.obtener_metricas_reales(caso_uso, activa, ab["inicio"], ab["fin"])
        # Nunca usar métricas del entrenamiento como etiquetas reales.
        if control.f1 is not None and candidata.f1 is not None:
            decision_ab = evaluar_ab(
                control.f1, candidata.f1, control.cantidad, candidata.cantidad,
                activa, anterior, activa,
            )
            if decision_ab.activar:
                return resultado(decision_ab, "ab", {
                    "experimento_id": ab["id"], "f1_control": control.f1,
                    "f1_candidata": candidata.f1,
                    "etiquetadas_control": control.cantidad,
                    "etiquetadas_candidata": candidata.cantidad,
                })

    alerta_id = obs.obtener_alerta_alta_reciente(caso_uso, contexto["promocion_en"])
    if alerta_id is not None:
        # Métrica actual solo desde el momento en que la versión fue promovida.
        actual = obs.obtener_metricas_reales(
            caso_uso, activa, inicio=contexto["promocion_en"]
        )
        # Métrica previa desde observaciones históricas de la versión anterior.
        previo = obs.obtener_metricas_reales(
            caso_uso, anterior, fin=contexto["promocion_en"]
        )
        if actual.f1 is not None and previo.f1 is not None and previo.cantidad >= 30:
            decision_drift = evaluar_drift("alto", actual.f1, actual.cantidad, previo.f1)
            if decision_drift.activar:
                return resultado(decision_drift, "drift", {
                    "alerta_id": alerta_id, "f1_actual": actual.f1,
                    "f1_anterior": previo.f1,
                    "etiquetadas_actual": actual.cantidad,
                    "etiquetadas_anterior": previo.cantidad,
                })

    return {"estado": "sin_evidencia_suficiente", "rollback": False,
            "activa": activa, "anterior": anterior,
            "motivo": "No se cumplen conjuntamente los umbrales y muestras verificadas."}


def main():
    parser = argparse.ArgumentParser(description="Revisión de rollback de un modelo MLOps")
    parser.add_argument("--caso-uso", default="churn")
    parser.add_argument("--aplicar", action="store_true", help="Ejecuta la reversión si la política la autoriza")
    argumentos = parser.parse_args()
    print(json.dumps(revisar_rollback(argumentos.caso_uso, argumentos.aplicar),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
