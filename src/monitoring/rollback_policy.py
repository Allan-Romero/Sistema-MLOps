"""Política de reversión. No consulta ni modifica PostgreSQL.

Las métricas de desempeño deben calcularse con predicciones que ya
contengan etiquetas reales; no se usan métricas de entrenamiento como
sustituto del desempeño observado.
"""

from dataclasses import dataclass
import math

MINIMO_MUESTRAS = 30
MARGEN_F1_AB = 0.01
F1_MINIMO_DRIFT = 0.55


@dataclass(frozen=True)
class DecisionRollback:
    activar: bool
    origen: str
    motivo: str
    f1_origen: float | None = None
    f1_destino: float | None = None


def validar_f1(valor, nombre):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nombre} debe ser numérico.")
    if not math.isfinite(valor) or not 0 <= valor <= 1:
        raise ValueError(f"{nombre} debe estar entre 0 y 1.")
    return float(valor)


def validar_muestra(valor):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ValueError("El tamaño de muestra debe ser entero no negativo.")
    return valor


def evaluar_ab(f1_control, f1_candidato, muestra_control, muestra_candidato,
               version_activa, version_control, version_candidata,
               minimo_muestras=MINIMO_MUESTRAS, margen=MARGEN_F1_AB):
    """Solicita rollback solo si la candidata B ya estaba activa y perdió.

    Si el control A sigue activo, no existe ninguna promoción que revertir.
    """
    a = validar_f1(f1_control, "F1 control")
    b = validar_f1(f1_candidato, "F1 candidato")
    na = validar_muestra(muestra_control)
    nb = validar_muestra(muestra_candidato)
    validar_muestra(minimo_muestras)
    margen = validar_f1(margen, "Margen")

    if version_activa != version_candidata:
        return DecisionRollback(False, "ab", "El control sigue activo; no hay promoción que revertir.", b, a)
    if na < minimo_muestras or nb < minimo_muestras:
        return DecisionRollback(False, "ab", "Muestras etiquetadas insuficientes para el A/B.", b, a)
    if b > a - margen:
        return DecisionRollback(False, "ab", "No se demuestra una degradación A/B suficiente.", b, a)
    return DecisionRollback(True, "ab", f"A/B: {version_candidata} obtuvo F1 {b:.4f} frente a {version_control} con {a:.4f}.", b, a)


def evaluar_drift(nivel_drift, f1_observado, muestra_etiquetada,
                   f1_destino, minimo_muestras=MINIMO_MUESTRAS,
                   minimo_f1=F1_MINIMO_DRIFT):
    """Requiere simultáneamente drift alto y caída real de F1."""
    actual = validar_f1(f1_observado, "F1 observado")
    previo = validar_f1(f1_destino, "F1 anterior")
    n = validar_muestra(muestra_etiquetada)
    validar_muestra(minimo_muestras)
    limite = validar_f1(minimo_f1, "F1 mínimo")

    if nivel_drift != "alto":
        return DecisionRollback(False, "drift", "No existe alerta de drift alto.", actual, previo)
    if n < minimo_muestras:
        return DecisionRollback(False, "drift", "Muestra etiquetada insuficiente.", actual, previo)
    if actual >= limite:
        return DecisionRollback(False, "drift", "El F1 observado no cayó bajo el mínimo.", actual, previo)
    if previo < limite:
        return DecisionRollback(False, "drift", "La versión anterior tampoco alcanza el F1 mínimo.", actual, previo)
    return DecisionRollback(True, "drift", f"Drift alto y F1 observado {actual:.4f} inferior a {limite:.4f}.", actual, previo)
