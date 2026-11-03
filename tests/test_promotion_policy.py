
import pytest

from src.training.promotion_policy import (
    decidir_promocion,
    UMBRAL_MINIMO_F1,
)


def test_primer_modelo_se_promueve():
    resultado = decidir_promocion(0.6032)

    assert resultado.promover is True
    assert resultado.f1_activo is None


def test_candidato_mejor_se_promueve():
    resultado = decidir_promocion(
        f1_candidato=0.65,
        f1_activo=0.6032,
    )

    assert resultado.promover is True
    assert resultado.mejora > UMBRAL_MINIMO_F1


def test_mejora_insuficiente_se_descarta():
    resultado = decidir_promocion(
        f1_candidato=0.607,
        f1_activo=0.6032,
    )

    assert resultado.promover is False


def test_candidato_igual_se_descarta():
    resultado = decidir_promocion(
        f1_candidato=0.6032,
        f1_activo=0.6032,
    )

    assert resultado.promover is False
    assert resultado.mejora == 0


def test_candidato_peor_se_descarta():
    resultado = decidir_promocion(
        f1_candidato=0.57,
        f1_activo=0.6032,
    )

    assert resultado.promover is False
    assert resultado.mejora < 0


def test_mejora_exacta_al_umbral():
    resultado = decidir_promocion(
        f1_candidato=0.62,
        f1_activo=0.61,
    )

    assert resultado.promover is True
    assert resultado.mejora == pytest.approx(0.01)


def test_metricas_invalidas():
    with pytest.raises(ValueError):
        decidir_promocion(1.5, 0.60)

    with pytest.raises(ValueError):
        decidir_promocion(0.65, float("nan"))

    with pytest.raises(ValueError):
        decidir_promocion(0.65, 0.60, umbral=0)
