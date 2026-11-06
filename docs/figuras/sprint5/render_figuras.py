"""Genera PNG de las cuatro figuras de S5-J2 con Pillow.

Las fuentes semánticas editables son los .mmd del mismo directorio.
Este renderizador mantiene un diseño fijo para exportar figuras legibles
sin requerir navegador o un servicio externo. No ejecuta la plataforma.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1800, 1180
INK, BLUE, TEAL = '#16324a', '#eaf2fb', '#e7f5f0'


def font(size, bold=False):
    nombre = 'arialbd.ttf' if bold else 'arial.ttf'
    for ruta in (Path('C:/Windows/Fonts') / nombre, Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')):
        if ruta.exists():
            return ImageFont.truetype(str(ruta), size)
    return ImageFont.load_default()


def canvas(titulo, subtitulo):
    im = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 14), fill=INK)
    d.text((65, 40), titulo, font=font(39, True), fill=INK)
    d.text((65, 101), subtitulo, font=font(25), fill='#42586a')
    d.line((65, 1090, W-65, 1090), fill='#ccd5dc', width=2)
    d.text((65, 1110), 'Fuente: elaboración propia a partir del código inspeccionado en develop · S5-J2 · 2026-11-05', font=font(21), fill='#42586a')
    return im, d


def box(d, xy, title, lines=(), fill=BLUE):
    x1, y1, x2, y2 = xy
    d.rounded_rectangle(xy, radius=16, fill=fill, outline='#7590a7', width=2)
    d.text((x1+20, y1+16), title, font=font(27, True), fill=INK)
    for i, line in enumerate(lines):
        d.text((x1+20, y1+59+i*31), line, font=font(23), fill=INK)


def arrow(d, points, label='', dashed=False):
    for a, b in zip(points, points[1:]):
        if dashed:
            dx, dy = b[0]-a[0], b[1]-a[1]
            length = math.hypot(dx, dy)
            for n in range(0, int(length), 18):
                t1, t2 = n/length, min(n+10, length)/length
                d.line((a[0]+dx*t1, a[1]+dy*t1, a[0]+dx*t2, a[1]+dy*t2), fill='#476478', width=3)
        else:
            d.line((*a, *b), fill='#476478', width=3)
    a, b = points[-2:]
    theta = math.atan2(b[1]-a[1], b[0]-a[0])
    p = [(b[0], b[1]), (b[0]-14*math.cos(theta-.45), b[1]-14*math.sin(theta-.45)), (b[0]-14*math.cos(theta+.45), b[1]-14*math.sin(theta+.45))]
    d.polygon(p, fill='#476478')
    if label:
        x, y = points[len(points)//2]
        d.text((x+8, y-28), label, font=font(21), fill='#42586a')


def arquitectura():
    im, d = canvas('Figura S5-J2-1 · Arquitectura construida', 'Cuatro servicios permanentes en Compose; entrenamiento y administración mediante CLI')
    d.rounded_rectangle((600, 180, 1725, 800), radius=22, outline='#8da6bb', width=3)
    d.text((630, 195), 'Docker Compose · red mlops_net', font=font(28, True), fill=INK)
    box(d, (60, 190, 480, 330), 'Operador / navegador', ['Swagger, Streamlit y MLflow'])
    box(d, (60, 410, 480, 600), 'Host · Python CLI', ['Entrenar y registrar', 'Abrir / cerrar A/B', 'Revisar rollback'])
    box(d, (60, 710, 480, 865), 'Archivos del host', ['data/raw · CSV públicos', 'models · artefactos .joblib'])
    box(d, (690, 280, 1110, 435), 'FastAPI · :8000', ['Inferencia y reparto A/B', 'Persistencia de predicciones'])
    box(d, (1235, 280, 1655, 435), 'Streamlit · :8501', ['Consulta y visualización', 'Drift: CLI opcional aquí'])
    box(d, (690, 590, 1110, 750), 'MLflow · :5000', ['Tracking de churn', 'SQLite y mlartifacts'])
    box(d, (1235, 590, 1655, 750), 'PostgreSQL 16 · :5432', ['Estados, métricas y eventos', 'Volumen postgres_data'], TEAL)
    arrow(d, [(480, 260), (640, 260), (640, 355), (690, 355)])
    d.text((580, 232), 'HTTP', font=font(21), fill='#42586a')
    arrow(d, [(900, 435), (900, 500), (1445, 500), (1445, 590)], 'SQL')
    arrow(d, [(1445, 435), (1445, 590)], 'SQL')
    arrow(d, [(480, 470), (555, 470), (555, 670), (690, 670)], 'tracking')
    arrow(d, [(480, 550), (1170, 550), (1170, 670), (1235, 670)], 'SQL')
    arrow(d, [(480, 785), (570, 785), (570, 370), (690, 370)])
    d.text((490, 755), 'modelos', font=font(21), fill='#42586a')
    box(d, (600, 870, 1725, 1045), 'Integración por base de datos y artefactos', ['La API consulta la activa en PostgreSQL por petición; no sigue el alias MLflow.', 'El dashboard lee la misma base. No hay cola, clúster ni scheduler permanente.', 'CSV y reportes de drift se montan también en el contenedor del dashboard.'], TEAL)
    im.save(ROOT / 'arquitectura.png')


def pipeline():
    im, d = canvas('Figura S5-J2-2 · Pipelines y promoción', 'Los dos casos comparten registro transaccional, pero no un protocolo de evaluación idéntico')
    left = [
        ('Churn · CSV Telco', ['Limpiar TotalCharges; retirar customerID']),
        ('Partición y codificación', ['80/20 estratificado · semilla 42', 'One-hot y alineación con train']),
        ('Entrenamiento y selección', ['Logistic Regression y XGBoost', 'Mayor F1 sobre test: limitación de selección']),
        ('MLflow y registro', ['Parámetros, métricas, artefactos y candidate', 'Persistencia automática al final del pipeline']),
    ]
    right = [
        ('Fraude · CSV Credit Card', ['Validar 30 variables y Class']),
        ('Partición estratificada', ['70/15/15 · semilla 42', 'Train / validación / test']),
        ('Entrenamiento y selección', ['LR escalada/ponderada; XGBoost ponderado', 'Umbral y algoritmo por F1 de validación']),
        ('Evaluación y registro', ['Test y ThresholdClassifier + JSON', '--registrar explícito; política usa F1 de test']),
    ]
    for x, steps in [(65, left), (935, right)]:
        for i, (title, lines) in enumerate(steps):
            y = 180+i*175
            box(d, (x, y, x+800, y+145), title, lines)
            if i < 3:
                arrow(d, [(x+400, y+145), (x+400, y+175)])
    box(d, (310, 925, 1490, 1055), 'Registro común: política F1 y transacción PostgreSQL', ['Primera versión o mejora ≥ 0,01: activa y deployment. Si no: descartada.', 'Versiones + métricas + auditoría comparten commit; archivos y MLflow no.'], TEAL)
    arrow(d, [(465, 850), (465, 925)])
    arrow(d, [(1335, 850), (1335, 925)])
    im.save(ROOT / 'pipeline.png')


def datos():
    im, d = canvas('Figura S5-J2-4 · Integración lógica de datos', 'Siete tablas: seis en schema.sql y promotion_decisions en la migración 002')
    box(d, (650, 430, 1170, 605), 'model_versions', ['Caso + versión + algoritmo + F1', 'Estado activa / histórica / descartada'], TEAL)
    specs = [
        ((65, 190, 585, 345), 'predictions', ['Entrada JSON, predicción y versión', 'Etiqueta posterior opcional']),
        ((650, 190, 1170, 345), 'model_metrics', ['Métricas de clasificación', 'Caso, versión y algoritmo']),
        ((1235, 190, 1755, 345), 'experiments', ['A/B, porcentaje y período', 'Estado y ganadora']),
        ((65, 735, 585, 890), 'alerts', ['Caso, variable, nivel y descripción', 'Distribución de input_data']),
        ((650, 735, 1170, 890), 'promotion_decisions', ['Candidata, anterior, F1 y mejora', 'Umbral, resultado y motivo']),
        ((1235, 735, 1755, 890), 'deployments', ['Origen, destino y operación', 'Motivo y métricas del cambio']),
    ]
    for xy, title, lines in specs:
        box(d, xy, title, lines)
    arrow(d, [(800, 430), (325, 345)], dashed=True)
    arrow(d, [(910, 430), (910, 345)], dashed=True)
    arrow(d, [(1020, 430), (1495, 345)], dashed=True)
    arrow(d, [(910, 605), (910, 735)], dashed=True)
    arrow(d, [(1020, 605), (1495, 735)], dashed=True)
    arrow(d, [(325, 345), (325, 735)], dashed=True)
    box(d, (65, 940, 1755, 1055), 'Líneas discontinuas: correspondencias lógicas, no foreign keys declaradas', ['Índices parciales: una versión activa y un experimento activo por caso de uso.', 'Las asociaciones usan caso_uso + cadenas de versión; el código coordina consistencia.'], '#fff6df')
    im.save(ROOT / 'datos.png')


def rollback():
    im, d = canvas('Figura S5-J2-3 · A/B y rollback', 'Requiere predecesora auditada, estado compatible, artefacto disponible y etiquetas observadas')
    box(d, (65, 190, 865, 330), 'Cierre A/B explícito', ['A histórica / B activa · ≥30 etiquetas por grupo'])
    box(d, (935, 190, 1735, 365), 'rollback_auto: revisión separada', ['A/B cerrado ≤30 días: B activa y caída F1 ≥0,01', 'O drift alto reciente + métricas observadas'])
    box(d, (65, 410, 865, 585), 'Decisión sobre F1 observado', ['F1(B) ≤ F1(A) − 0,01: revertir a A', 'En otro caso conservar B y finalizar', 'Empate no demuestra superioridad de B'])
    box(d, (935, 410, 1735, 585), 'Camino drift: condiciones conjuntas', ['Alerta alta ≤7 días y posterior a promoción', 'F1 actual <0,55; anterior ≥0,55', '≥30 etiquetas de cada versión'])
    arrow(d, [(465, 330), (465, 410)])
    arrow(d, [(1335, 365), (1335, 410)])
    box(d, (935, 650, 1735, 790), 'Por defecto solo consulta', ['Con --aplicar y evidencia: ejecutar rollback', 'Sin evidencia suficiente: no cambiar la activa'], '#fff6df')
    arrow(d, [(1335, 585), (1335, 650)])
    box(d, (65, 650, 865, 790), 'Mutación bajo bloqueo por caso', ['B descartada; A activa; deployment con motivo', 'Validar de nuevo la activa antes de cambiarla'], TEAL)
    arrow(d, [(465, 585), (465, 650)])
    d.text((485, 605), 'Si revierte', font=font(21), fill='#42586a')
    arrow(d, [(935, 720), (865, 720)])
    box(d, (65, 860, 1735, 1050), 'Resultado y siguiente predicción', ['Cierre A/B: experimento finalizado con A ganadora. Servicio rollback: cancela experimentos activos.', 'La API vuelve a consultar PostgreSQL y sirve A; no requiere copiar el modelo ni reiniciar.', 'SQL es transaccional; los archivos y la totalidad de la petición HTTP no comparten esa transacción.'], TEAL)
    arrow(d, [(465, 790), (465, 860)])
    im.save(ROOT / 'rollback.png')


if __name__ == '__main__':
    arquitectura()
    pipeline()
    datos()
    rollback()
