"""Convierte una salida de consola guardada en una figura PNG legible.

Las evidencias de ejecución (pipeline, esquema de base de datos, detección de
drift) se capturan primero como texto, que es verificable y se versiona, y
después se renderizan como figura para el documento. Así la imagen y el texto
que la respalda provienen del mismo archivo.

Uso:
    python docs/figuras/sprint5/render_consola.py entrada.txt salida.png --titulo "Figura 12 ..."
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# Colores de una terminal clara, legible al imprimir el documento
FONDO = (250, 250, 248)
MARCO = (219, 218, 212)
TINTA = (24, 26, 30)
TITULO = (37, 70, 90)

MARGEN = 22
INTERLINEA = 4
TAMANO_FUENTE = 15


def cargar_fuente(tamano, negrita=False):
    """Busca una monoespaciada del sistema y cae en la de PIL si no hay."""
    candidatas = [
        "consolab.ttf" if negrita else "consola.ttf",
        "DejaVuSansMono-Bold.ttf" if negrita else "DejaVuSansMono.ttf",
    ]

    for nombre in candidatas:
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue

    return ImageFont.load_default()


def renderizar(texto, destino, titulo=None, ancho_maximo=120):
    """Dibuja el texto en una imagen y la guarda."""
    lineas = [linea.rstrip()[:ancho_maximo] for linea in texto.splitlines()]

    fuente = cargar_fuente(TAMANO_FUENTE)
    fuente_titulo = cargar_fuente(TAMANO_FUENTE + 2, negrita=True)

    medidor = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    caja = medidor.textbbox((0, 0), "M", font=fuente)
    ancho_caracter = caja[2] - caja[0]
    alto_linea = (caja[3] - caja[1]) + INTERLINEA

    columnas = max((len(linea) for linea in lineas), default=0)
    if titulo:
        columnas = max(columnas, len(titulo))

    ancho = MARGEN * 2 + max(columnas, 40) * ancho_caracter
    alto = MARGEN * 2 + (len(lineas) + (2 if titulo else 0)) * alto_linea

    imagen = Image.new("RGB", (int(ancho), int(alto)), FONDO)
    lienzo = ImageDraw.Draw(imagen)
    lienzo.rectangle([0, 0, imagen.width - 1, imagen.height - 1], outline=MARCO, width=1)

    y = MARGEN
    if titulo:
        lienzo.text((MARGEN, y), titulo, font=fuente_titulo, fill=TITULO)
        y += alto_linea * 2

    for linea in lineas:
        lienzo.text((MARGEN, y), linea, font=fuente, fill=TINTA)
        y += alto_linea

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(destino)

    return destino, imagen.size


def main():
    parser = argparse.ArgumentParser(description="Renderiza una salida de consola como figura")
    parser.add_argument("entrada", help="Archivo de texto con la salida capturada")
    parser.add_argument("salida", help="Ruta del PNG a generar")
    parser.add_argument("--titulo", default=None, help="Rótulo que encabeza la figura")
    parser.add_argument("--ancho", type=int, default=120, help="Máximo de caracteres por línea")
    argumentos = parser.parse_args()

    texto = Path(argumentos.entrada).read_text(encoding="utf-8")
    destino, tamano = renderizar(texto, argumentos.salida, argumentos.titulo, argumentos.ancho)

    print(f"Figura generada: {destino} ({tamano[0]}x{tamano[1]} px)")


if __name__ == "__main__":
    main()
