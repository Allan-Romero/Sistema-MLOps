"""Dibuja el modelo entidad-relación leyéndolo del catálogo de PostgreSQL.

El diagrama no se mantiene a mano: se genera consultando `information_schema`
de la base creada con `schema.sql` y sus migraciones, de modo que lo dibujado
corresponde al esquema vigente por construcción. Si el esquema cambia, basta
con volver a ejecutar este script.

Uso, con los servicios levantados:
    python docs/figuras/sprint5/render_erd.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.database.connection import get_connection

SALIDA = Path(__file__).resolve().parent / "figura-25-modelo-entidad-relacion.png"

FONDO = "#ffffff"
TINTA = "#16324a"
TINTA_SUAVE = "#52606d"
BORDE = "#c6d2dc"
CABECERA = "#e7eef6"
CABECERA_CENTRO = "#dbeadd"
LINEA = "#9fb3c4"

ANCHO_CAJA = 520
CANAL = 320          # espacio entre columnas, donde van las etiquetas
ALTO_CABECERA = 40
ALTO_FILA = 23
RELLENO = 12
SEPARACION = 46      # espacio vertical entre cajas de una columna
MARGEN_X = 56
TOPE = 150

IZQUIERDA = ["model_metrics", "predictions", "alerts"]
CENTRO = "model_versions"
DERECHA = ["experiments", "deployments", "promotion_decisions"]

ETIQUETAS = {
    "model_metrics": "caso_uso + model_version",
    "predictions": "caso_uso + model_version",
    "experiments": "caso_uso + version_a / version_b",
    "deployments": "caso_uso + version_origen / destino",
    "promotion_decisions": "caso_uso + version_candidata / anterior",
}

PROPOSITOS = {
    "model_versions": "Versión de cada modelo y su estado",
    "model_metrics": "Métricas de evaluación por versión",
    "predictions": "Predicciones servidas y su etiqueta real",
    "alerts": "Alertas de drift detectadas",
    "experiments": "Configuración y resultado del A/B",
    "deployments": "Bitácora de promociones y rollbacks",
    "promotion_decisions": "Auditoría de las decisiones de promoción",
}

ABREVIATURAS = {
    "character varying": "varchar",
    "timestamp without time zone": "timestamp",
    "double precision": "float",
    "integer": "int",
    "bigint": "bigint",
    "boolean": "bool",
    "jsonb": "jsonb",
    "text": "text",
}


def fuente(tamano, negrita=False):
    for nombre in (("arialbd.ttf", "DejaVuSans-Bold.ttf") if negrita
                   else ("arial.ttf", "DejaVuSans.ttf")):
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def leer_esquema():
    """Trae columnas, tipos y obligatoriedad de cada tabla del catálogo."""
    consulta = """
        SELECT table_name, column_name, data_type,
               character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(consulta)
            filas = cursor.fetchall()
    finally:
        conexion.close()

    tablas = {}
    for tabla, columna, tipo, longitud, nulo in filas:
        abreviado = ABREVIATURAS.get(tipo, tipo)
        if longitud:
            abreviado = f"{abreviado}({longitud})"
        tablas.setdefault(tabla, []).append((columna, abreviado, nulo == "NO"))
    return tablas


def alto_de(columnas):
    return ALTO_CABECERA + len(columnas) * ALTO_FILA + RELLENO


def dibujar_tabla(lienzo, x, y, nombre, columnas, destacada=False):
    """Dibuja una entidad con sus campos y retorna su rectángulo."""
    alto = alto_de(columnas)
    lienzo.rectangle([x, y, x + ANCHO_CAJA, y + alto], fill="#ffffff",
                     outline=BORDE, width=2)
    lienzo.rectangle([x, y, x + ANCHO_CAJA, y + ALTO_CABECERA],
                     fill=CABECERA_CENTRO if destacada else CABECERA,
                     outline=BORDE, width=2)

    lienzo.text((x + 14, y + 10), nombre, font=fuente(19, True), fill=TINTA)
    lienzo.text((x + ANCHO_CAJA - 14, y + 14), PROPOSITOS.get(nombre, ""),
                font=fuente(12), fill=TINTA_SUAVE, anchor="ra")

    fila_y = y + ALTO_CABECERA + 6
    for columna, tipo, obligatoria in columnas:
        marca = "PK" if columna == "id" else ("*" if obligatoria else "")
        if marca:
            lienzo.text((x + 14, fila_y), marca, font=fuente(12, True),
                        fill=TINTA_SUAVE)
        lienzo.text((x + 44, fila_y), columna, font=fuente(14), fill=TINTA)
        lienzo.text((x + ANCHO_CAJA - 14, fila_y), tipo, font=fuente(13),
                    fill=TINTA_SUAVE, anchor="ra")
        fila_y += ALTO_FILA

    return (x, y, x + ANCHO_CAJA, y + alto)


def apilar(lienzo, tablas, nombres, x, tope):
    """Dibuja una columna de tablas y retorna sus rectángulos."""
    rectangulos = {}
    y = tope
    for nombre in nombres:
        rectangulos[nombre] = dibujar_tabla(lienzo, x, y, nombre, tablas[nombre])
        y += alto_de(tablas[nombre]) + SEPARACION
    return rectangulos


def conectar(lienzo, origen, destino, x_canal, etiqueta, desde_izquierda):
    """Une dos cajas con un conector ortogonal y rotula el canal."""
    y_origen = (origen[1] + origen[3]) / 2
    y_destino = (destino[1] + destino[3]) / 2
    x_origen = origen[2] if desde_izquierda else origen[0]
    x_destino = destino[0] if desde_izquierda else destino[2]

    lienzo.line([(x_origen, y_origen), (x_canal, y_origen)], fill=LINEA, width=2)
    lienzo.line([(x_canal, y_origen), (x_canal, y_destino)], fill=LINEA, width=2)
    lienzo.line([(x_canal, y_destino), (x_destino, y_destino)], fill=LINEA, width=2)

    texto = fuente(12)
    punto = ((x_origen + x_canal) / 2, y_origen - 11)
    caja = lienzo.textbbox(punto, etiqueta, font=texto, anchor="mm")
    lienzo.rectangle([caja[0] - 5, caja[1] - 2, caja[2] + 5, caja[3] + 2],
                     fill="#ffffff")
    lienzo.text(punto, etiqueta, font=texto, fill=TINTA_SUAVE, anchor="mm")


def main():
    tablas = leer_esquema()
    esperadas = set(IZQUIERDA + DERECHA + [CENTRO])
    faltantes = esperadas - set(tablas)
    if faltantes:
        raise SystemExit(f"Faltan tablas en la base: {sorted(faltantes)}")

    alto_izquierda = sum(alto_de(tablas[n]) for n in IZQUIERDA) + SEPARACION * 2
    alto_derecha = sum(alto_de(tablas[n]) for n in DERECHA) + SEPARACION * 2
    alto_contenido = max(alto_izquierda, alto_derecha)

    ancho = MARGEN_X * 2 + ANCHO_CAJA * 3 + CANAL * 2
    alto = TOPE + alto_contenido + 96

    imagen = Image.new("RGB", (ancho, alto), FONDO)
    lienzo = ImageDraw.Draw(imagen)

    lienzo.rectangle([0, 0, ancho, 10], fill=TINTA)
    lienzo.text((MARGEN_X, 38), "Modelo entidad-relación de la plataforma",
                font=fuente(34, True), fill=TINTA)
    lienzo.text((MARGEN_X, 88),
                "Siete tablas en PostgreSQL. Las relaciones son lógicas: el "
                "esquema no declara claves foráneas.",
                font=fuente(18), fill=TINTA_SUAVE)

    x_izquierda = MARGEN_X
    x_centro = MARGEN_X + ANCHO_CAJA + CANAL
    x_derecha = x_centro + ANCHO_CAJA + CANAL

    rect = {}
    rect.update(apilar(lienzo, tablas, IZQUIERDA, x_izquierda, TOPE))
    rect.update(apilar(lienzo, tablas, DERECHA, x_derecha, TOPE))

    y_centro = TOPE + (alto_contenido - alto_de(tablas[CENTRO])) / 2
    rect[CENTRO] = dibujar_tabla(lienzo, x_centro, y_centro, CENTRO,
                                 tablas[CENTRO], destacada=True)

    canal_izquierdo = x_izquierda + ANCHO_CAJA + CANAL / 2
    canal_derecho = x_centro + ANCHO_CAJA + CANAL / 2

    for nombre in ("model_metrics", "predictions"):
        conectar(lienzo, rect[nombre], rect[CENTRO], canal_izquierdo,
                 ETIQUETAS[nombre], desde_izquierda=True)

    for nombre in DERECHA:
        conectar(lienzo, rect[nombre], rect[CENTRO], canal_derecho,
                 ETIQUETAS[nombre], desde_izquierda=False)

    # alerts no referencia versiones: se alimenta de los datos de entrada
    pred, alertas = rect["predictions"], rect["alerts"]
    x_union = (pred[0] + pred[2]) / 2
    lienzo.line([(x_union, pred[3]), (x_union, alertas[1])], fill=LINEA, width=2)
    punto = (x_union, (pred[3] + alertas[1]) / 2)
    etiqueta = "input_data analizado por el monitoreo"
    caja = lienzo.textbbox(punto, etiqueta, font=fuente(12), anchor="mm")
    lienzo.rectangle([caja[0] - 6, caja[1] - 3, caja[2] + 6, caja[3] + 3],
                     fill="#ffffff")
    lienzo.text(punto, etiqueta, font=fuente(12), fill=TINTA_SUAVE, anchor="mm")

    leyenda = ("PK clave primaria   ·   * campo obligatorio   ·   índices "
               "únicos parciales: una versión activa y un experimento activo "
               "por caso de uso")
    lienzo.line([MARGEN_X, alto - 56, ancho - MARGEN_X, alto - 56],
                fill=BORDE, width=2)
    lienzo.text((MARGEN_X, alto - 42), leyenda, font=fuente(15), fill=TINTA_SUAVE)

    imagen.save(SALIDA)
    print(f"Figura generada: {SALIDA} ({imagen.width}x{imagen.height} px)")


if __name__ == "__main__":
    main()
