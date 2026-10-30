import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from src.database.crud import obtener_metricas, obtener_predicciones, obtener_alertas, obtener_comparacion_modelos, obtener_versiones
import numpy as np
from src.monitoring.detect_drift import COLUMNAS_NUMERICAS, obtener_distribuciones

st.set_page_config(
    page_title="Plataforma MLOps - Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Dashboard de monitoreo - Plataforma MLOps")
st.caption("Universidad Manuela Beltrán · Ingeniería de Software")

st.divider()

# Sección de métricas del modelo (se completa en S1-A14)
st.subheader("Métricas del modelo")

metricas = obtener_metricas(limite=1)

if metricas:
    # La consulta retorna: id, caso_uso, model_version, accuracy, precision,
    # recall, f1_score, roc_auc, created_at
    registro = metricas[0]
    caso_uso = registro[1]
    version = registro[2]

    st.caption(f"Caso de uso: {caso_uso}  ·  Versión del modelo: {version}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Accuracy", f"{registro[4]:.2f}")
    col2.metric("Precision", f"{registro[5]:.2f}")
    col3.metric("Recall", f"{registro[6]:.2f}")
    col4.metric("F1-score", f"{registro[7]:.2f}")
    col5.metric("ROC-AUC", f"{registro[8]:.2f}")
else:
    st.warning("No hay métricas registradas en la base de datos")
    
st.divider()
st.subheader("Comparación de modelos")

comparacion = obtener_comparacion_modelos("churn")

if comparacion:
    columnas = ["Algoritmo", "Versión", "Accuracy", "Precision",
                "Recall", "F1-score", "ROC-AUC"]
    df_comparacion = pd.DataFrame(comparacion, columns=columnas)
    st.dataframe(df_comparacion, width='stretch', hide_index=True)

    # Identificar el mejor modelo por F1-score
    mejor = df_comparacion.loc[df_comparacion["F1-score"].idxmax()]
    st.success(
        f"Mejor desempeño: {mejor['Algoritmo']} "
        f"(F1-score: {mejor['F1-score']:.2f})"
    )
else:
    st.warning("No hay métricas registradas para comparar")
    
st.divider()
st.subheader("Historial de versiones del modelo")

versiones = obtener_versiones(limite=20)

if versiones:
    columnas = ["ID", "Caso de uso", "Versión", "Algoritmo",
                "Métrica", "Valor", "Estado", "Fecha"]
    df_versiones = pd.DataFrame(versiones, columns=columnas)

    st.dataframe(df_versiones, width='stretch', hide_index=True)

    # Evolución de la métrica principal a lo largo de las versiones
    df_evolucion = df_versiones.sort_values("Fecha")
    st.line_chart(
        df_evolucion.set_index("Versión")["Valor"],
        height=280
    )
    st.caption("Evolución de la métrica principal por versión")
else:
    st.warning("No hay versiones registradas en la base de datos")

st.divider()

# Sección de predicciones recientes (se completa en S1-A15)
st.subheader("Últimas predicciones")

predicciones = obtener_predicciones(limite=10)

if predicciones:
    columnas = ["ID", "Caso de uso", "Predicción", "Probabilidad",
                "Versión del modelo", "Fecha"]
    df_predicciones = pd.DataFrame(predicciones, columns=columnas)
    st.dataframe(df_predicciones, width='stretch', hide_index=True)
    st.caption(f"Mostrando las {len(df_predicciones)} predicciones más recientes")
else:
    st.warning("No hay predicciones registradas en la base de datos")

st.divider()
st.subheader("Alertas de drift")

alertas = obtener_alertas(limite=50)

if alertas:
    columnas = ["ID", "Caso de uso", "Variable afectada", "Nivel de drift",
                "Descripción", "Revisada", "Fecha"]
    df_alertas = pd.DataFrame(alertas, columns=columnas)

    # Resumen por severidad
    conteo = df_alertas["Nivel de drift"].value_counts()
    col1, col2, col3 = st.columns(3)
    col1.metric("Severidad alta", int(conteo.get("alto", 0)))
    col2.metric("Severidad media", int(conteo.get("medio", 0)))
    col3.metric("Pendientes de revisión",
                int((~df_alertas["Revisada"]).sum()))

    # Aviso destacado si hay alertas críticas sin revisar
    criticas = df_alertas[
        (df_alertas["Nivel de drift"] == "alto")
        & (~df_alertas["Revisada"])
    ]
    if not criticas.empty:
        variables = ", ".join(criticas["Variable afectada"].unique())
        st.error(
            f"Se detectó drift de severidad alta sin revisar en: {variables}. "
            "Se recomienda evaluar la necesidad de reentrenar el modelo."
        )

    # Indicador visual de severidad en cada fila
    iconos = {"alto": "🔴 Alto", "medio": "🟠 Medio", "bajo": "🟢 Bajo"}
    df_vista = df_alertas.copy()
    df_vista["Nivel de drift"] = df_vista["Nivel de drift"].map(
        lambda nivel: iconos.get(nivel, nivel)
    )
    df_vista["Revisada"] = df_vista["Revisada"].map(
        lambda valor: "Sí" if valor else "No"
    )

    st.dataframe(
        df_vista[["ID", "Caso de uso", "Variable afectada", "Nivel de drift",
                  "Revisada", "Fecha", "Descripción"]],
        width="stretch",
        hide_index=True,
    )
    st.caption(f"Mostrando las {len(df_vista)} alertas más recientes")

    # ----- Comparación de distribuciones -----
    st.markdown("##### Comparación de distribuciones")

    variables_con_alerta = df_alertas["Variable afectada"].unique().tolist()
    opciones = [v for v in COLUMNAS_NUMERICAS if v in variables_con_alerta]
    if not opciones:
        opciones = COLUMNAS_NUMERICAS

    variable = st.selectbox(
        "Variable a analizar",
        opciones,
        help="Se listan primero las variables que generaron alertas"
    )

    try:
        distribuciones = obtener_distribuciones(variable)
        serie_ref = distribuciones["referencia"]
        serie_act = distribuciones["actual"]

        if len(serie_act) == 0:
            st.warning(
                "No hay datos de producción suficientes para comparar. "
                "Genere predicciones desde la API para alimentar el análisis."
            )
        else:
            # Intervalos comunes para que ambas series sean comparables
            minimo = float(min(serie_ref.min(), serie_act.min()))
            maximo = float(max(serie_ref.max(), serie_act.max()))
            cortes = np.linspace(minimo, maximo, 25)

            conteo_ref, _ = np.histogram(serie_ref, bins=cortes)
            conteo_act, _ = np.histogram(serie_act, bins=cortes)

            # Normalización a proporciones para comparar conjuntos de distinto tamaño
            prop_ref = conteo_ref / max(conteo_ref.sum(), 1)
            prop_act = conteo_act / max(conteo_act.sum(), 1)

            centros = (cortes[:-1] + cortes[1:]) / 2

            df_dist = pd.DataFrame(
                {"Referencia": prop_ref, "Producción": prop_act},
                index=np.round(centros, 2),
            )
            df_dist.index.name = variable

            st.area_chart(df_dist, height=320)
            st.caption(
                f"Distribución de {variable} en el conjunto de referencia "
                f"({len(serie_ref)} registros) frente a los datos de producción "
                f"({len(serie_act)} registros). Los valores se expresan como "
                "proporción del total para permitir la comparación."
            )
    except Exception as error:
        st.warning(f"No fue posible generar la comparación: {error}")

else:
    st.info("Sin alertas registradas")