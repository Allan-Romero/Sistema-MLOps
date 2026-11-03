"""Punto de entrada para revisar o aplicar rollback desde un programador de tareas.

Sin --aplicar: evalúa y registra el resultado, pero no modifica versiones.
Con --aplicar: delega la decisión en la política de rollback y su transacción.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from src.monitoring.rollback_auto import revisar_rollback

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG = PROJECT_ROOT / "reports" / "s4_j4_monitoring.jsonl"


def ejecutar_job(caso_uso="churn", aplicar=False, ruta_log=None):
    """Ejecuta una revisión y registra resultados; propaga fallos para el scheduler."""
    resultado = revisar_rollback(caso_uso=caso_uso, aplicar=aplicar)
    evento = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "caso_uso": caso_uso,
        "modo": "aplicar" if aplicar else "consulta",
        "resultado": resultado,
    }
    destino = DEFAULT_LOG if ruta_log is None else Path(ruta_log)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return evento


def main(argv=None):
    parser = argparse.ArgumentParser(description="Monitoreo programable para S4-J4")
    parser.add_argument("--caso-uso", default="churn")
    parser.add_argument("--aplicar", action="store_true", help="Permite efectuar rollback si la política lo indica")
    parser.add_argument("--log", default=None, help="Archivo JSONL para auditoría de evaluaciones")
    args = parser.parse_args(argv)
    resultado = ejecutar_job(args.caso_uso, args.aplicar, args.log)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    return resultado


if __name__ == "__main__":
    main()
