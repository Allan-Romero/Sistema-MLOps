"""Grafica el sesgo del PSI según el tamaño de la muestra.

Lee la calibración que produce `scripts/calibrar_monitoreo.py` y dibuja el
PSI medido cuando las dos distribuciones son la misma, frente al número de
observaciones. Las líneas de umbral muestran a partir de qué volumen el
detector deja de marcar drift por puro azar.

Uso:
    python docs/figuras/sprint5/render_calibracion.py
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[3]
ENTRADA = RAIZ / "docs" / "evidencias" / "sprint5" / "calibracion_tamano_muestra.csv"
SALIDA = Path(__file__).resolve().parent / "figura-26-sesgo-psi-muestra.png"

SERIE = "#2a78d6"
BANDA = "#cde2fb"
UMBRAL_MEDIO = "#9a6207"
UMBRAL_ALTO = "#a83232"
TINTA = "#16324a"
TINTA_SUAVE = "#52606d"
REJILLA = "#e2e1dd"
SUPERFICIE = "#fcfcfb"


def leer():
    with ENTRADA.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def main():
    filas = leer()
    tamanos = [int(f["tamano_muestra"]) for f in filas]
    promedio = [float(f["psi_promedio"]) for f in filas]
    p95 = [float(f["psi_p95"]) for f in filas]
    mediana = [float(f["psi_mediana"]) for f in filas]

    figura, ejes = plt.subplots(figsize=(10, 5.6))
    figura.patch.set_facecolor(SUPERFICIE)
    ejes.set_facecolor(SUPERFICIE)

    ejes.fill_between(tamanos, mediana, p95, color=BANDA, zorder=2,
                      label="Entre la mediana y el percentil 95")
    ejes.plot(tamanos, promedio, color=SERIE, linewidth=2.4, marker="o",
              markersize=7, zorder=4, label="PSI promedio")

    for umbral, color, texto in (
        (0.10, UMBRAL_MEDIO, "Umbral de drift moderado (0,10)"),
        (0.25, UMBRAL_ALTO, "Umbral de drift significativo (0,25)"),
    ):
        ejes.axhline(umbral, color=color, linewidth=1.6, linestyle="--", zorder=3)
        ejes.text(tamanos[-1], umbral + 0.008, texto, color=color, fontsize=10,
                  ha="right", va="bottom")

    # Etiquetas directas en los puntos que sostienen la decisión
    for tamano, valor in zip(tamanos, promedio):
        if tamano in (50, 150, 300, 500):
            ejes.annotate(f"{valor:.3f}".replace(".", ","),
                          (tamano, valor), textcoords="offset points",
                          xytext=(6, 10), fontsize=10, color=TINTA_SUAVE)

    ejes.set_xscale("log")
    ejes.set_xticks(tamanos)
    ejes.set_xticklabels([str(t) for t in tamanos], fontsize=10, color=TINTA_SUAVE)
    ejes.tick_params(axis="y", colors=TINTA_SUAVE, labelsize=10)
    ejes.set_xlabel("Observaciones de producción", fontsize=11, color=TINTA_SUAVE)
    ejes.set_ylabel("PSI medido", fontsize=11, color=TINTA_SUAVE)
    ejes.set_title(
        "El PSI acusa drift con muestras pequeñas aunque no lo haya",
        fontsize=14, color=TINTA, loc="left", pad=26,
    )
    ejes.text(0, 1.015,
              "Distribuciones idénticas: la muestra se extrae del propio "
              "conjunto de referencia. 500 repeticiones por tamaño.",
              transform=ejes.transAxes, fontsize=10, color=TINTA_SUAVE)

    ejes.grid(axis="y", color=REJILLA, linewidth=0.8, zorder=0)
    ejes.set_axisbelow(True)
    for lado in ("top", "right"):
        ejes.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ejes.spines[lado].set_color("#d5d4cf")

    ejes.legend(frameon=False, fontsize=10, loc="upper right")

    figura.tight_layout()
    figura.savefig(SALIDA, dpi=200, facecolor=SUPERFICIE)
    plt.close(figura)

    print(f"Figura generada: {SALIDA}")


if __name__ == "__main__":
    main()
