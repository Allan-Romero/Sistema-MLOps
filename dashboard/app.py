import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from src.database.crud import obtener_metricas, obtener_predicciones, obtener_alertas

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
    col1.metric("Accuracy", f"{registro[3]:.2f}")
    col2.metric("Precision", f"{registro[4]:.2f}")
    col3.metric("Recall", f"{registro[5]:.2f}")
    col4.metric("F1-score", f"{registro[6]:.2f}")
    col5.metric("ROC-AUC", f"{registro[7]:.2f}")
else:
    st.warning("No hay métricas registradas en la base de datos")

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

# Sección de alertas de drift (se completa en S1-A16)
st.subheader("Alertas de drift")

alertas = obtener_alertas(limite=10)

if alertas:
    columnas = ["ID", "Caso de uso", "Variable afectada", "Nivel de drift",
                "Descripción", "Revisada", "Fecha"]
    df_alertas = pd.DataFrame(alertas, columns=columnas)
    st.dataframe(df_alertas, width='stretch', hide_index=True)
else:
    st.info("Sin alertas registradas")