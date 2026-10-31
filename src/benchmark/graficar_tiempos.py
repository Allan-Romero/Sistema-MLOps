"""Genera el gráfico comparativo de tiempos del ciclo de vida del modelo.

Lee las mediciones de reports/tiempos_ciclo.csv y produce un PNG listo para
incorporar al documento. Si todavía no se han cronometrado los tiempos del
escenario manual, dibuja solo el automatizado y lo deja indicado, en lugar de
inventar la comparación.

Uso:
    python -m src.benchmark.graficar_tiempos
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTADOS = PROJECT_ROOT / "reports" / "tiempos_ciclo.csv"
SALIDA = PROJECT_ROOT / "reports" / "tiempos_comparacion.png"

# Paleta categórica validada: separación suficiente también en daltonismo
COLOR_MANUAL = "#eb6834"
COLOR_AUTOMATIZADO = "#2a78d6"
TINTA = "#0b0b0b"
TINTA_SUAVE = "#52514e"
SUPERFICIE = "#fcfcfb"


def leer_mediciones(ruta=RESULTADOS):
    """Carga las mediciones del archivo de resultados."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"No existen mediciones en {ruta}. "
            "Ejecute primero python -m src.benchmark.medir_tiempos."
        )

    with ruta.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))

    if not filas:
        raise ValueError(f"El archivo {ruta} no contiene mediciones.")

    return filas


def a_numero(valor):
    """Convierte un campo del CSV a número, o None si está vacío."""
    if valor is None or str(valor).strip() == "":
        return None
    return float(valor)


def graficar(filas, salida=SALIDA):
    """Dibuja la comparación y retorna la ruta del archivo generado."""
    actividades = [fila["actividad"] for fila in filas]
    automatizado = [a_numero(fila["automatizado_promedio_s"]) for fila in filas]
    manual = [a_numero(fila.get("manual_s")) for fila in filas]

    hay_manual = any(valor is not None for valor in manual)
    posiciones = np.arange(len(actividades))
    alto_barra = 0.38 if hay_manual else 0.55

    figura, ejes = plt.subplots(figsize=(10, 5.5))
    figura.patch.set_facecolor(SUPERFICIE)
    ejes.set_facecolor(SUPERFICIE)

    series = [("Automatizado", automatizado, COLOR_AUTOMATIZADO)]
    if hay_manual:
        # El manual va arriba en cada par, para leerse antes que el automatizado
        series.insert(0, ("Manual", [v or 0 for v in manual], COLOR_MANUAL))

    desplazamiento = (len(series) - 1) / 2
    for indice, (nombre, valores, color) in enumerate(series):
        offset = (desplazamiento - indice) * alto_barra
        barras = ejes.barh(
            posiciones + offset,
            valores,
            height=alto_barra * 0.92,
            color=color,
            label=nombre,
            zorder=3,
        )
        # Etiqueta directa: evita que el lector tenga que seguir el eje
        for barra, valor in zip(barras, valores):
            if not valor:
                continue
            ejes.text(
                barra.get_width() + max(valores) * 0.01,
                barra.get_y() + barra.get_height() / 2,
                f"{valor:.1f} s",
                va="center",
                fontsize=9,
                color=TINTA_SUAVE,
            )

    ejes.set_yticks(posiciones, actividades, fontsize=10, color=TINTA)
    ejes.invert_yaxis()
    ejes.set_xlabel("Duración (segundos)", fontsize=10, color=TINTA_SUAVE)
    ejes.tick_params(axis="x", colors=TINTA_SUAVE, labelsize=9)

    titulo = "Duración de las actividades del ciclo de vida del modelo"
    ejes.set_title(titulo, fontsize=13, color=TINTA, pad=30, loc="left")

    if hay_manual:
        ejes.legend(frameon=False, fontsize=10, loc="lower right")
    else:
        # Aclaración bajo el título: el gráfico aún no es la comparación
        ejes.text(
            0, 1.015,
            "Escenario automatizado · los tiempos manuales aún no se han medido",
            transform=ejes.transAxes,
            fontsize=9.5, color=TINTA_SUAVE,
        )

    # Rejilla recesiva: ayuda a comparar sin competir con las barras
    ejes.grid(axis="x", color="#e2e1dd", linewidth=0.8, zorder=0)
    ejes.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ejes.spines[lado].set_visible(False)
    ejes.spines["bottom"].set_color("#d5d4cf")

    figura.tight_layout()
    salida.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(salida, dpi=200, facecolor=SUPERFICIE)
    plt.close(figura)

    return salida


def main():
    filas = leer_mediciones()
    ruta = graficar(filas)

    faltan = [f["actividad"] for f in filas if a_numero(f.get("manual_s")) is None]
    print(f"Gráfico generado: {ruta}")

    if faltan:
        print(
            "\nSin tiempo manual medido en: " + ", ".join(faltan) +
            "\nComplete la columna manual_s de reports/tiempos_ciclo.csv "
            "siguiendo docs/sprint4_a7_tiempos.md y vuelva a ejecutar."
        )


if __name__ == "__main__":
    main()
