"""Entrada de entrenamiento reutilizable para churn y fraude.

Conserva intacto el pipeline legado de churn; delega el entrenamiento del
caso de fraude a su adaptador de datos y modelos. Ambos comparten registro
transaccional de versiones y métrica F1 para la política de promoción.
"""

import argparse

from src.consola import usar_utf8


def ejecutar(caso_uso, registrar=False):
    if caso_uso == "churn":
        if registrar:
            raise ValueError("El pipeline de churn ya registra automáticamente al ejecutarse.")
        from src.training.run_pipeline import main as run_churn
        return run_churn()
    if caso_uso == "fraude":
        from src.training.fraud_pipeline import entrenar, registrar as registrar_fraude
        return registrar_fraude() if registrar else entrenar()
    raise ValueError(f"Caso de uso desconocido: {caso_uso}")


def main():
    usar_utf8()
    parser = argparse.ArgumentParser(description="Pipeline MLOps multi-caso de uso")
    parser.add_argument("--caso-uso", required=True, choices=("churn", "fraude"))
    parser.add_argument("--registrar", action="store_true", help="Registrar modelo de fraude entrenado")
    args = parser.parse_args()
    ejecutar(args.caso_uso, args.registrar)


if __name__ == "__main__":
    main()
