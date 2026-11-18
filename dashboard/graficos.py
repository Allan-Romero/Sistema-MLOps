"""Gráficos del tablero de monitoreo.

Todos comparten un mismo tema oscuro, sin rejilla vertical ni marco, para que
la lectura recaiga en los datos y no en los adornos. Cada función recibe datos
ya preparados y devuelve una figura lista para mostrar.
"""

import plotly.graph_objects as go

from estilos import PALETA

TIPOGRAFIA = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"


def _tema(figura, alto=320, margen=None):
    """Aplica el tema común a una figura."""
    figura.update_layout(
        height=alto,
        margin=margen or dict(l=52, r=16, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=TIPOGRAFIA, size=12, color=PALETA["texto_suave"]),
        hoverlabel=dict(
            bgcolor=PALETA["superficie_alta"],
            bordercolor=PALETA["borde"],
            font=dict(family=TIPOGRAFIA, size=12, color=PALETA["texto"]),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11.5),
        ),
        showlegend=figura.layout.showlegend,
    )
    figura.update_xaxes(
        showgrid=False, zeroline=False,
        linecolor=PALETA["borde_suave"],
        tickfont=dict(size=11, color=PALETA["texto_tenue"]),
    )
    figura.update_yaxes(
        showgrid=True, gridcolor=PALETA["borde_suave"], gridwidth=1,
        zeroline=False, linecolor="rgba(0,0,0,0)",
        tickfont=dict(size=11, color=PALETA["texto_tenue"]),
    )
    return figura


def evolucion_metrica(versiones, valores, estados, nombre_metrica):
    """Línea de la métrica principal a lo largo de las versiones.

    La versión activa se destaca con un marcador mayor: es la única que
    está respondiendo peticiones.
    """
    colores = [
        PALETA["verde"] if estado == "activa"
        else PALETA["rojo"] if estado == "descartada"
        else PALETA["acento"]
        for estado in estados
    ]
    tamanos = [13 if estado == "activa" else 8 for estado in estados]

    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=versiones, y=valores,
        mode="lines+markers",
        line=dict(color=PALETA["acento"], width=2.4, shape="spline",
                  smoothing=0.6),
        marker=dict(size=tamanos, color=colores,
                    line=dict(width=2, color=PALETA["fondo"])),
        customdata=estados,
        hovertemplate=("<b>%{x}</b><br>" + nombre_metrica +
                       ": %{y:.4f}<br>Estado: %{customdata}<extra></extra>"),
        name=nombre_metrica,
    ))
    figura.update_layout(showlegend=False)

    # Las versiones suelen diferir en milésimas: con el eje anclado en cero la
    # serie se aplastaría contra el borde y no se vería nada. Se encuadra el
    # rango alrededor de los valores observados.
    observados = [valor for valor in valores if valor is not None]
    if observados:
        minimo, maximo = min(observados), max(observados)
        holgura = max((maximo - minimo) * 0.8, 0.01)
        figura.update_yaxes(range=[max(0.0, minimo - holgura),
                                   min(1.0, maximo + holgura)])
    figura.update_yaxes(title=None, tickformat=".4f")
    return _tema(figura, alto=300, margen=dict(l=58, r=18, t=24, b=10))


def comparacion_algoritmos(df, metricas):
    """Barras agrupadas con las métricas de cada algoritmo."""
    tonos = [PALETA["acento"], PALETA["violeta"], PALETA["verde"]]
    figura = go.Figure()
    for indice, (_, fila) in enumerate(df.iterrows()):
        figura.add_trace(go.Bar(
            name=str(fila["Algoritmo"]),
            x=metricas,
            y=[float(fila[m]) for m in metricas],
            marker=dict(color=tonos[indice % len(tonos)],
                        line=dict(width=0)),
            text=[f"{float(fila[m]):.3f}" for m in metricas],
            textposition="outside",
            textfont=dict(size=10.5, color=PALETA["texto_suave"]),
            hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:.4f}"
                          "<extra></extra>",
        ))
    figura.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08,
                         showlegend=True)
    figura.update_yaxes(range=[0, 1.18], tickformat=".1f", title=None)
    return _tema(figura, alto=330, margen=dict(l=52, r=16, t=46, b=10))


def distribuciones(centros, proporcion_referencia, proporcion_produccion,
                   variable):
    """Superposición de la distribución de referencia y la de producción."""
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=centros, y=proporcion_referencia,
        name="Referencia (entrenamiento)",
        mode="lines", line=dict(color=PALETA["acento"], width=2,
                                shape="spline", smoothing=0.7),
        fill="tozeroy", fillcolor="rgba(76,141,255,.22)",
        hovertemplate="%{x}<br>Referencia: %{y:.3f}<extra></extra>",
    ))
    figura.add_trace(go.Scatter(
        x=centros, y=proporcion_produccion,
        name="Producción (observado)",
        mode="lines", line=dict(color=PALETA["ambar"], width=2,
                                shape="spline", smoothing=0.7),
        fill="tozeroy", fillcolor="rgba(242,181,68,.20)",
        hovertemplate="%{x}<br>Producción: %{y:.3f}<extra></extra>",
    ))
    figura.update_xaxes(title=dict(text=variable,
                                   font=dict(size=11.5,
                                             color=PALETA["texto_tenue"])))
    figura.update_yaxes(title=None, tickformat=".2f")
    return _tema(figura, alto=340, margen=dict(l=52, r=16, t=46, b=34))


def reparto_trafico(version_a, predicciones_a, version_b, predicciones_b):
    """Anillo con el reparto real de peticiones entre las dos versiones."""
    figura = go.Figure(go.Pie(
        labels=[f"{version_a} · control", f"{version_b} · candidata"],
        values=[predicciones_a, predicciones_b],
        hole=0.66,
        marker=dict(colors=[PALETA["acento"], PALETA["violeta"]],
                    line=dict(color=PALETA["fondo"], width=3)),
        textinfo="percent",
        textfont=dict(size=12.5, color=PALETA["texto"]),
        hovertemplate="<b>%{label}</b><br>%{value} predicciones"
                      "<br>%{percent}<extra></extra>",
        sort=False,
    ))
    total = predicciones_a + predicciones_b
    figura.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:11px'>peticiones</span>",
        showarrow=False, font=dict(size=20, color=PALETA["texto"],
                                   family=TIPOGRAFIA),
    )
    figura.update_layout(showlegend=True)
    return _tema(figura, alto=300, margen=dict(l=10, r=10, t=46, b=10))


def desempeno_experimento(versiones, valores, roles, destacada):
    """Barras horizontales con el F1 observado de cada versión."""
    colores = [PALETA["violeta"] if version == destacada else PALETA["acento"]
               for version in versiones]
    etiquetas = [f"{v} · {r}" for v, r in zip(versiones, roles)]

    figura = go.Figure(go.Bar(
        x=valores, y=etiquetas, orientation="h",
        marker=dict(color=colores, line=dict(width=0)),
        text=[f"{valor:.3f}" if valor is not None else "sin datos"
              for valor in valores],
        textposition="outside",
        textfont=dict(size=11.5, color=PALETA["texto_suave"]),
        hovertemplate="<b>%{y}</b><br>F1 observado: %{x:.4f}<extra></extra>",
    ))
    figura.update_layout(showlegend=False, bargap=0.45)
    maximo = max([v for v in valores if v is not None], default=1) or 1
    figura.update_xaxes(range=[0, maximo * 1.25], tickformat=".2f",
                        showgrid=True, gridcolor=PALETA["borde_suave"])
    figura.update_yaxes(showgrid=False, autorange="reversed")
    return _tema(figura, alto=220, margen=dict(l=130, r=40, t=20, b=10))


def volumen_por_version(versiones, con_etiqueta, sin_etiqueta):
    """Barras apiladas: cuántas predicciones tienen resultado conocido."""
    figura = go.Figure()
    figura.add_trace(go.Bar(
        name="Con resultado conocido", x=versiones, y=con_etiqueta,
        marker=dict(color=PALETA["verde"], line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Con etiqueta: %{y}<extra></extra>",
    ))
    figura.add_trace(go.Bar(
        name="Pendientes de etiqueta", x=versiones, y=sin_etiqueta,
        marker=dict(color=PALETA["borde"], line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Sin etiqueta: %{y}<extra></extra>",
    ))
    figura.update_layout(barmode="stack", bargap=0.45, showlegend=True)
    figura.update_yaxes(title=None)
    return _tema(figura, alto=280, margen=dict(l=52, r=16, t=46, b=10))


def alertas_por_nivel(conteos):
    """Barras horizontales con el número de alertas de cada severidad."""
    orden = [("alto", "Alta", PALETA["rojo"]),
             ("medio", "Media", PALETA["ambar"]),
             ("bajo", "Baja", PALETA["verde"])]
    etiquetas = [rotulo for _, rotulo, _ in orden]
    valores = [int(conteos.get(clave, 0)) for clave, _, _ in orden]
    colores = [color for _, _, color in orden]

    figura = go.Figure(go.Bar(
        x=valores, y=etiquetas, orientation="h",
        marker=dict(color=colores, line=dict(width=0)),
        text=valores, textposition="outside",
        textfont=dict(size=12, color=PALETA["texto_suave"]),
        hovertemplate="Severidad %{y}: %{x} alertas<extra></extra>",
    ))
    figura.update_layout(showlegend=False, bargap=0.45)
    figura.update_xaxes(range=[0, max(valores + [1]) * 1.3], showgrid=True,
                        gridcolor=PALETA["borde_suave"], dtick=1)
    # Sin invertir, Plotly dibuja la primera categoría abajo; la severidad
    # alta debe quedar arriba porque es la que exige atención.
    figura.update_yaxes(showgrid=False, autorange="reversed")
    return _tema(figura, alto=210, margen=dict(l=70, r=40, t=20, b=10))
