
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


UMBRAL_MINIMO_F1 = 0.01


@dataclass(frozen=True)
class DecisionPromocion:
    promover: bool
    motivo: str
    f1_candidato: float
    f1_activo: float | None
    mejora: float | None
    umbral: float


def validar_valor(nombre, valor):
    """Valida métricas y umbrales entre cero y uno."""
    if isinstance(valor, bool):
        raise ValueError(f"{nombre} no puede ser booleano.")

    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{nombre} no es numérico.") from None

    if not numero.is_finite() or not 0 <= numero <= 1:
        raise ValueError(f"{nombre} debe estar entre 0 y 1.")

    return numero


def decidir_promocion(
    f1_candidato,
    f1_activo=None,
    umbral=UMBRAL_MINIMO_F1,
):
    """
    Decide si un modelo candidato puede promoverse.

    - Primer modelo: se permite la promoción.
    - Mejora >= umbral: se permite la promoción.
    - Mejora inferior al umbral: se descarta.
    """

    candidato = validar_valor(
        "F1 del candidato", f1_candidato
    )
    margen = validar_valor("Umbral", umbral)

    if margen == 0:
        raise ValueError("El umbral debe ser mayor que cero.")

    if f1_activo is None:
        return DecisionPromocion(
            promover=True,
            motivo="Primera versión del modelo.",
            f1_candidato=float(candidato),
            f1_activo=None,
            mejora=None,
            umbral=float(margen),
        )

    activo = validar_valor("F1 activo", f1_activo)
    mejora = candidato - activo
    promover = mejora >= margen

    motivo = (
        "El candidato supera el umbral de mejora."
        if promover
        else "El candidato no alcanza la mejora mínima."
    )

    return DecisionPromocion(
        promover=promover,
        motivo=motivo,
        f1_candidato=float(candidato),
        f1_activo=float(activo),
        mejora=float(mejora),
        umbral=float(margen),
    )
