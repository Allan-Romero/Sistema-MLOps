"""Contrato de columnas del dataset Credit Card Fraud Detection (OpenML 1597)."""

FEATURE_COLUMNS = ("Time", *(f"V{i}" for i in range(1, 29)), "Amount")
TARGET_COLUMN = "Class"
CASO_USO = "fraude"


def validar_columnas(columnas):
    """No acepta fugas de la etiqueta ni esquemas incompletos."""
    observadas = set(columnas)
    faltantes = (set(FEATURE_COLUMNS) | {TARGET_COLUMN}) - observadas
    if faltantes:
        raise ValueError(f"Columnas de fraude faltantes: {sorted(faltantes)}")
    extras = observadas - (set(FEATURE_COLUMNS) | {TARGET_COLUMN})
    if extras:
        raise ValueError(f"Columnas de fraude inesperadas: {sorted(extras)}")
