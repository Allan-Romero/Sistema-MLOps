"""Configuración de los casos de uso que atiende la plataforma.

Todo lo que cambia entre un caso de uso y otro vive en este módulo: la
etiqueta que se muestra, el conjunto de referencia del monitoreo, las
variables numéricas que se vigilan y la ruta del reporte de drift. El resto
del código consulta esta configuración en lugar de tener constantes propias,
de modo que atender un segundo caso no obliga a duplicar nada.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CASOS_USO = {
    "churn": {
        "etiqueta": "Churn de clientes",
        "referencia": PROJECT_ROOT / "data" / "raw" / "churn.csv",
        # Variables numéricas del dataset de Telco que se vigilan por drift
        "columnas_numericas": ["tenure", "MonthlyCharges", "TotalCharges"],
        "reporte_drift": PROJECT_ROOT / "reports" / "drift_report_churn.html",
    },
    "fraude": {
        "etiqueta": "Fraude en transacciones",
        "referencia": PROJECT_ROOT / "data" / "raw" / "fraude.csv",
        # Variables interpretables del dataset de tarjetas de crédito. Las
        # componentes V1..V28 son resultado de un PCA y no se vigilan hasta
        # que S4-J5 defina cuáles usa el modelo.
        "columnas_numericas": ["Time", "Amount"],
        "reporte_drift": PROJECT_ROOT / "reports" / "drift_report_fraude.html",
    },
}

CASO_USO_POR_DEFECTO = "churn"


def listar_casos():
    """Retorna los identificadores de los casos de uso configurados."""
    return list(CASOS_USO)


def obtener_config(caso_uso):
    """Retorna la configuración de un caso de uso."""
    if caso_uso not in CASOS_USO:
        raise ValueError(
            f"El caso de uso {caso_uso} no está configurado. "
            f"Casos disponibles: {', '.join(CASOS_USO)}."
        )

    return CASOS_USO[caso_uso]


def etiqueta(caso_uso):
    """Retorna el nombre legible de un caso de uso."""
    return obtener_config(caso_uso)["etiqueta"]


def columnas_monitoreadas(caso_uso):
    """Retorna las variables numéricas que el monitoreo vigila."""
    return list(obtener_config(caso_uso)["columnas_numericas"])


def ruta_referencia(caso_uso):
    """Retorna la ruta del conjunto de referencia del caso de uso."""
    return obtener_config(caso_uso)["referencia"]


def ruta_reporte_drift(caso_uso):
    """Retorna la ruta del reporte de drift del caso de uso."""
    return obtener_config(caso_uso)["reporte_drift"]
