"""Tablero de monitoreo de la plataforma MLOps.

Presenta, para el caso de uso seleccionado, el desempeño del modelo activo,
el historial de versiones, el tráfico atendido, las alertas de deriva y las
operaciones de despliegue. Lee directamente de PostgreSQL y no invoca a
ningún otro servicio.

Las ocho secciones conservan su orden y su nombre; se agrupan en cuatro
pestañas para que cada pregunta del operador se responda sin recorrer toda
la página.
"""

import os
import sys
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(AQUI))
sys.path.append(AQUI)

import numpy as np
import pandas as pd
import streamlit as st

import estilos
import graficos
from src.casos_uso import columnas_monitoreadas, etiqueta, listar_casos
from src.database.crud import (obtener_alertas, obtener_comparacion_modelos,
                               obtener_desempeno_por_version,
                               obtener_experimento_activo,
                               obtener_historial_despliegues, obtener_metricas,
                               obtener_predicciones,
                               obtener_ultimo_experimento,
                               obtener_versiones,
                               obtener_volumen_por_version)
from src.monitoring.detect_drift import obtener_distribuciones

# Muestra mínima por grupo para considerar concluyente una diferencia.
# Se mantiene el mismo umbral que usa el monitoreo de drift.
MUESTRA_MINIMA = 30

GRAFICO = {"displayModeBar": False, "responsive": True}


# --------------------------------------------------------------------------
# Configuración y estilo
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Plataforma MLOps · Monitoreo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
estilos.inyectar_estilos()


def mostrar(figura, alto=None):
    """Dibuja una figura de Plotly con el tema propio del tablero."""
    st.plotly_chart(figura, use_container_width=True, theme=None,
                    config=GRAFICO)


def sin_datos(mensaje):
    """Aviso uniforme para las secciones que todavía no tienen información."""
    st.info(mensaje, icon=":material/info:")


# --------------------------------------------------------------------------
# Barra lateral
# --------------------------------------------------------------------------
with st.sidebar:
    estilos.marca_lateral("Plataforma MLOps", "Monitoreo de modelos")

    CASO_USO = st.selectbox(
        "Caso de uso",
        listar_casos(),
        format_func=etiqueta,
        help="Las métricas, predicciones, alertas y experimentos "
             "corresponden al caso seleccionado",
    )

    if st.button("Actualizar datos", width="stretch",
                 icon=":material/refresh:"):
        st.rerun()

    st.caption("El tablero no se actualiza solo: muestra el estado del "
               "momento en que se cargó la página.")

# --------------------------------------------------------------------------
# Carga de datos
# --------------------------------------------------------------------------
try:
    # Se piden varias filas porque la consulta devuelve las más recientes y
    # la versión en producción no tiene por qué ser la última entrenada.
    metricas = obtener_metricas(CASO_USO, limite=60)
    comparacion = obtener_comparacion_modelos(CASO_USO)
    versiones = obtener_versiones(CASO_USO, limite=20)
    predicciones = obtener_predicciones(CASO_USO, limite=10)
    alertas = obtener_alertas(CASO_USO, limite=50)
    volumen_total = obtener_volumen_por_version(CASO_USO)
    despliegues = obtener_historial_despliegues(CASO_USO, limite=50)
    experimento = obtener_experimento_activo(CASO_USO)
    historico = (obtener_ultimo_experimento(CASO_USO)
                 if experimento is None else None)
except Exception as error:  # noqa: BLE001 - se informa, no se oculta
    st.error(
        f"No fue posible consultar la base de datos: {error}\n\n"
        "Compruebe que el contenedor de PostgreSQL esté en marcha y que las "
        "credenciales del entorno sean las correctas.",
        icon=":material/database_off:",
    )
    st.stop()

# --------------------------------------------------------------------------
# Estado resumido
# --------------------------------------------------------------------------
df_versiones = pd.DataFrame(
    versiones,
    columns=["ID", "Caso de uso", "Versión", "Algoritmo", "Métrica", "Valor",
             "Estado", "Fecha"],
) if versiones else pd.DataFrame()

activas = (df_versiones[df_versiones["Estado"] == "activa"]
           if not df_versiones.empty else pd.DataFrame())
version_activa = activas.iloc[0] if not activas.empty else None

df_alertas = pd.DataFrame(
    alertas,
    columns=["ID", "Caso de uso", "Variable afectada", "Nivel de drift",
             "Descripción", "Revisada", "Fecha"],
) if alertas else pd.DataFrame()

pendientes = int((~df_alertas["Revisada"]).sum()) if not df_alertas.empty else 0
altas_sin_revisar = 0
if not df_alertas.empty:
    altas_sin_revisar = int((
        (df_alertas["Nivel de drift"] == "alto") & (~df_alertas["Revisada"])
    ).sum())

total_predicciones = sum(int(fila[1]) for fila in volumen_total) if volumen_total else 0
etiquetadas = sum(int(fila[2]) for fila in volumen_total) if volumen_total else 0

df_despliegues = pd.DataFrame(
    despliegues,
    columns=["ID", "Caso de uso", "Versión de origen", "Versión de destino",
             "Operación", "Motivo", "Métrica", "Valor en origen",
             "Valor en destino", "Fecha"],
) if despliegues else pd.DataFrame()
ultimo_despliegue = df_despliegues.iloc[0] if not df_despliegues.empty else None

# --------------------------------------------------------------------------
# Encabezado
# --------------------------------------------------------------------------
chips = [estilos.insignia(etiqueta(CASO_USO), "neutro")]

if version_activa is not None:
    chips.append(estilos.insignia(
        f"{version_activa['Versión']} en producción", "exito"))
else:
    chips.append(estilos.insignia("Sin versión activa", "peligro", vivo=True))

if experimento is not None:
    chips.append(estilos.insignia("Experimento A/B en curso", "violeta",
                                  vivo=True))

if altas_sin_revisar:
    chips.append(estilos.insignia(
        f"{altas_sin_revisar} alerta(s) alta(s) sin revisar", "peligro",
        vivo=True))
elif pendientes:
    chips.append(estilos.insignia(f"{pendientes} alerta(s) pendientes",
                                  "aviso"))
else:
    chips.append(estilos.insignia("Sin alertas pendientes", "exito"))

# Resumen del estado en la barra lateral, una vez consultados los datos
with st.sidebar:
    st.markdown("###### Estado del caso de uso")
    estilos.dato_lateral(
        "Versión activa",
        version_activa["Versión"] if version_activa is not None else "—")
    estilos.dato_lateral(
        "Algoritmo",
        version_activa["Algoritmo"] if version_activa is not None else "—")
    estilos.dato_lateral("Versiones", len(df_versiones))
    estilos.dato_lateral("Predicciones", total_predicciones)
    estilos.dato_lateral("Alertas pendientes", pendientes)
    estilos.dato_lateral(
        "Experimento", "en curso" if experimento is not None else "ninguno")
    st.markdown(
        '<div class="lateral-pie">Universidad Manuela Beltrán<br>'
        'Ingeniería de Software<br>Trabajo de grado · 2026</div>',
        unsafe_allow_html=True)

estilos.encabezado(
    "Tablero de monitoreo",
    "Estado del ciclo de vida del modelo: desempeño, tráfico atendido, "
    "deriva de los datos y operaciones de despliegue.",
    chips,
)

# --------------------------------------------------------------------------
# Franja de indicadores
# --------------------------------------------------------------------------
if version_activa is not None:
    valor_activa = f"{float(version_activa['Valor']):.4f}"
    tarjeta_version = {
        "rotulo": "Versión en producción",
        "valor": version_activa["Versión"],
        "pie": version_activa["Algoritmo"],
        "tono": "exito",
    }
    tarjeta_metrica = {
        "rotulo": str(version_activa["Métrica"]).replace("_", " "),
        "valor": valor_activa,
        "pie": "Conjunto de prueba al entrenar",
        "tono": "neutro",
    }
else:
    tarjeta_version = {"rotulo": "Versión en producción", "valor": "—",
                       "pie": "Ninguna versión activa", "tono": "peligro"}
    tarjeta_metrica = {"rotulo": "Métrica principal", "valor": "—",
                       "pie": "Sin versión activa", "tono": "peligro"}

if ultimo_despliegue is not None:
    es_rollback = ultimo_despliegue["Operación"] == "rollback"
    tarjeta_operacion = {
        "rotulo": "Última operación",
        "valor": "Rollback" if es_rollback else "Promoción",
        "pie": f"{ultimo_despliegue['Fecha']:%d/%m/%Y %H:%M}",
        "tono": "peligro" if es_rollback else "exito",
    }
else:
    tarjeta_operacion = {"rotulo": "Última operación", "valor": "—",
                         "pie": "Sin despliegues registrados",
                         "tono": "neutro"}

estilos.fila_kpis([
    tarjeta_version,
    tarjeta_metrica,
    {"rotulo": "Predicciones registradas", "valor": f"{total_predicciones:,}"
        .replace(",", "."),
     "pie": f"{etiquetadas} con resultado conocido", "tono": "violeta"},
    {"rotulo": "Alertas pendientes", "valor": pendientes,
     "pie": (f"{altas_sin_revisar} de severidad alta" if altas_sin_revisar
             else "Ninguna de severidad alta"),
     "tono": "peligro" if altas_sin_revisar else
             "aviso" if pendientes else "exito"},
    {"rotulo": "Versiones registradas",
     "valor": len(df_versiones) if not df_versiones.empty else 0,
     "pie": f"{int((df_versiones['Estado'] == 'descartada').sum())} descartadas"
            if not df_versiones.empty else "Sin versiones",
     "tono": "neutro"},
])

pestana_modelo, pestana_produccion, pestana_monitoreo, pestana_despliegue = \
    st.tabs(["Modelo", "Producción", "Monitoreo", "Despliegue"])


# ==========================================================================
# MODELO
# ==========================================================================
with pestana_modelo:
    # ---------- 1. Métricas del modelo ----------
    estilos.titulo_seccion(
        1, "Métricas del modelo",
        "Resultado de la versión activa sobre el conjunto de prueba, "
        "calculado cuando se entrenó. No es el desempeño en producción: ese "
        "se calcula en la pestaña de despliegue.")

    if metricas:
        # Columnas: id, caso_uso, model_version, algoritmo, accuracy,
        # precision, recall, f1_score, roc_auc, created_at
        registro = None
        if version_activa is not None:
            # La consulta devuelve las métricas más recientes, que pueden
            # pertenecer a una versión descartada. Se busca primero la fila
            # que corresponde a la versión que está sirviendo.
            candidatas = [fila for fila in metricas
                          if fila[2] == version_activa["Versión"]]
            del_algoritmo = [fila for fila in candidatas
                             if fila[3] == version_activa["Algoritmo"]]
            registro = (del_algoritmo or candidatas or [None])[0]

        corresponde = registro is not None
        if registro is None:
            registro = metricas[0]

        st.caption(f"Caso de uso: {registro[1]} · Versión del modelo: "
                   f"{registro[2]} · Algoritmo: {registro[3]}")

        columnas = st.columns(5)
        etiquetas = ["Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC"]
        for indice, (columna, nombre) in enumerate(zip(columnas, etiquetas)):
            columna.metric(nombre, f"{registro[4 + indice]:.3f}")

        if not corresponde:
            st.warning(
                f"Estas métricas son las últimas registradas, no las de la "
                f"versión en producción. No se encontraron métricas de la "
                f"versión "
                f"{version_activa['Versión'] if version_activa is not None else '—'}.",
                icon=":material/report:")

        st.caption("La métrica de decisión del proyecto es el F1-score, "
                   "porque las clases están desbalanceadas y la accuracy "
                   "sola resultaría engañosa.")
    else:
        sin_datos("No hay métricas registradas para este caso de uso. "
                  "Ejecute el pipeline de entrenamiento para generarlas.")

    st.divider()

    # ---------- 2. Comparación de modelos ----------
    estilos.titulo_seccion(
        2, "Comparación de modelos",
        "Los dos algoritmos que el pipeline entrena en cada ejecución, "
        "evaluados sobre las mismas filas.")

    if comparacion:
        df_comparacion = pd.DataFrame(
            comparacion,
            columns=["Algoritmo", "Versión", "Accuracy", "Precision",
                     "Recall", "F1-score", "ROC-AUC"])

        mostrar(graficos.comparacion_algoritmos(
            df_comparacion,
            ["Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC"]))

        st.dataframe(df_comparacion, width="stretch", hide_index=True,
                     column_config={
                         columna: st.column_config.NumberColumn(
                             format="%.3f")
                         for columna in ["Accuracy", "Precision", "Recall",
                                         "F1-score", "ROC-AUC"]})
        mejor = df_comparacion.loc[df_comparacion["F1-score"].idxmax()]
        st.success(
            f"Mejor desempeño: {mejor['Algoritmo']} "
            f"(F1-score {mejor['F1-score']:.3f})",
            icon=":material/trophy:")

        st.caption("Es normal que un algoritmo gane en una métrica y pierda "
                   "en otra: el F1 depende del umbral de decisión y el "
                   "ROC-AUC no.")
    else:
        sin_datos("No hay métricas registradas para comparar.")

    st.divider()

    # ---------- 3. Historial de versiones ----------
    estilos.titulo_seccion(
        3, "Historial de versiones del modelo",
        "Todas las versiones entrenadas con su estado. Una activa por caso "
        "de uso; las descartadas no superaron el umbral de mejora y nunca "
        "sirvieron tráfico.")

    if not df_versiones.empty:
        df_evolucion = df_versiones.sort_values("Fecha")
        mostrar(graficos.evolucion_metrica(
            df_evolucion["Versión"].tolist(),
            [float(valor) for valor in df_evolucion["Valor"]],
            df_evolucion["Estado"].tolist(),
            str(df_evolucion["Métrica"].iloc[0]).replace("_", " ")))
        st.caption("Evolución de la métrica principal. El punto grande y "
                   "verde señala la versión que está en producción.")

        iconos = {"activa": "🟢 Activa", "historica": "⚪ Histórica",
                  "descartada": "🔴 Descartada"}
        df_vista = df_versiones.copy()
        df_vista["Estado"] = df_vista["Estado"].map(
            lambda estado: iconos.get(estado, estado))
        st.dataframe(
            df_vista[["Versión", "Algoritmo", "Métrica", "Valor", "Estado",
                      "Fecha"]],
            width="stretch", hide_index=True,
            column_config={"Valor": st.column_config.NumberColumn(
                format="%.4f")})
    else:
        sin_datos("No hay versiones registradas para este caso de uso.")


# ==========================================================================
# PRODUCCIÓN
# ==========================================================================
with pestana_produccion:
    # ---------- 4. Últimas predicciones ----------
    estilos.titulo_seccion(
        4, "Últimas predicciones",
        "Comprobación rápida de que el servicio responde y de que lo hace "
        "con la versión esperada.")

    if predicciones:
        df_predicciones = pd.DataFrame(
            predicciones,
            columns=["ID", "Caso de uso", "Predicción", "Probabilidad",
                     "Versión del modelo", "Fecha"])
        st.dataframe(
            df_predicciones[["Fecha", "Predicción", "Probabilidad",
                             "Versión del modelo", "ID"]],
            width="stretch", hide_index=True,
            column_config={
                "Probabilidad": st.column_config.ProgressColumn(
                    format="%.3f", min_value=0, max_value=1),
            })
        st.caption(f"Las {len(df_predicciones)} predicciones más recientes. "
                   "Si aparece una versión distinta de la activa, hay un "
                   "experimento repartiendo el tráfico.")
    else:
        sin_datos("No hay predicciones registradas. Genere tráfico contra la "
                  "API para alimentar esta sección.")

    st.divider()

    # ---------- Volumen por versión ----------
    estilos.titulo_seccion(
        "+", "Tráfico atendido por versión",
        "Cuántas peticiones respondió cada versión y de cuántas se conoce ya "
        "el resultado verdadero, que es lo que permite medir el desempeño "
        "real.")

    if volumen_total:
        df_volumen = pd.DataFrame(
            volumen_total,
            columns=["Versión", "Predicciones", "Con etiqueta", "Sin etiqueta",
                     "Porcentaje del tráfico", "Primera", "Última"])

        izquierda, derecha = st.columns([3, 2], gap="medium")
        with izquierda:
            mostrar(graficos.volumen_por_version(
                df_volumen["Versión"].tolist(),
                [int(valor) for valor in df_volumen["Con etiqueta"]],
                [int(valor) for valor in df_volumen["Sin etiqueta"]]))
        with derecha:
            st.dataframe(
                df_volumen[["Versión", "Predicciones", "Con etiqueta",
                            "Porcentaje del tráfico"]],
                width="stretch", hide_index=True,
                column_config={
                    "Porcentaje del tráfico": st.column_config.NumberColumn(
                        format="%.1f %%")})
            cobertura = (100 * etiquetadas / total_predicciones
                         if total_predicciones else 0)
            st.metric("Cobertura de etiquetas", f"{cobertura:.1f} %",
                      help="Proporción de predicciones cuyo resultado "
                           "verdadero ya se conoce")
    else:
        sin_datos("Todavía no hay tráfico registrado para este caso de uso.")


# ==========================================================================
# MONITOREO
# ==========================================================================
with pestana_monitoreo:
    # ---------- 5. Alertas de drift ----------
    estilos.titulo_seccion(
        5, "Alertas de drift",
        "Una alerta significa que la distribución de una variable en "
        "producción se alejó de la que tenía el modelo al entrenarse.")

    if not df_alertas.empty:
        conteo = df_alertas["Nivel de drift"].value_counts()

        izquierda, derecha = st.columns([2, 3], gap="medium")
        with izquierda:
            columna_a, columna_b = st.columns(2)
            columna_a.metric("Severidad alta", int(conteo.get("alto", 0)))
            columna_b.metric("Severidad media", int(conteo.get("medio", 0)))
            st.metric("Pendientes de revisión", pendientes)
        with derecha:
            mostrar(graficos.alertas_por_nivel(conteo.to_dict()))

        if altas_sin_revisar:
            criticas = df_alertas[(df_alertas["Nivel de drift"] == "alto")
                                  & (~df_alertas["Revisada"])]
            variables = ", ".join(criticas["Variable afectada"].unique())
            st.error(
                f"Drift de severidad alta sin revisar en: {variables}. "
                "Compare las distribuciones y evalúe la necesidad de "
                "reentrenar.",
                icon=":material/priority_high:")

        st.warning(
            "Antes de reaccionar, mire el volumen. El índice exagera con "
            "muestras pequeñas: con 150 predicciones mide 0,06 en promedio "
            "aunque no haya cambio alguno. Una alerta media calculada sobre "
            "menos de 300 predicciones es un indicio, no una conclusión.",
            icon=":material/query_stats:")

        iconos = {"alto": "🔴 Alto", "medio": "🟠 Medio", "bajo": "🟢 Bajo"}
        df_vista = df_alertas.copy()
        df_vista["Nivel de drift"] = df_vista["Nivel de drift"].map(
            lambda nivel: iconos.get(nivel, nivel))
        df_vista["Revisada"] = df_vista["Revisada"].map(
            lambda valor: "Sí" if valor else "No")

        st.dataframe(
            df_vista[["Fecha", "Variable afectada", "Nivel de drift",
                      "Revisada", "Descripción"]],
            width="stretch", hide_index=True)
        st.caption(f"Mostrando las {len(df_vista)} alertas más recientes.")
    else:
        sin_datos("Sin alertas registradas. Ejecute la detección de drift "
                  "después de acumular tráfico.")

    st.divider()

    # ---------- 6. Comparación de distribuciones ----------
    estilos.titulo_seccion(
        6, "Comparación de distribuciones",
        "La explicación visual de la alerta. Un desplazamiento en bloque "
        "suele ser un cambio real del negocio; otra forma, con picos nuevos, "
        "suele indicar un problema en la fuente de datos.")

    monitoreadas = columnas_monitoreadas(CASO_USO)
    if not df_alertas.empty:
        con_alerta = df_alertas["Variable afectada"].unique().tolist()
        opciones = [v for v in monitoreadas if v in con_alerta] or monitoreadas
    else:
        opciones = monitoreadas

    if opciones:
        variable = st.selectbox(
            "Variable a analizar", opciones,
            help="Se listan primero las variables que generaron alertas")

        try:
            distribuciones = obtener_distribuciones(variable, CASO_USO)
            serie_ref = distribuciones["referencia"]
            serie_act = distribuciones["actual"]

            if len(serie_act) == 0:
                sin_datos(
                    "No hay datos de producción suficientes para comparar. "
                    "Genere predicciones desde la API para alimentar el "
                    "análisis.")
            else:
                minimo = float(min(serie_ref.min(), serie_act.min()))
                maximo = float(max(serie_ref.max(), serie_act.max()))
                cortes = np.linspace(minimo, maximo, 25)

                conteo_ref, _ = np.histogram(serie_ref, bins=cortes)
                conteo_act, _ = np.histogram(serie_act, bins=cortes)

                # Proporciones para comparar conjuntos de distinto tamaño
                prop_ref = conteo_ref / max(conteo_ref.sum(), 1)
                prop_act = conteo_act / max(conteo_act.sum(), 1)
                centros = np.round((cortes[:-1] + cortes[1:]) / 2, 2)

                mostrar(graficos.distribuciones(
                    centros.tolist(), prop_ref.tolist(), prop_act.tolist(),
                    variable))
                st.caption(
                    f"Distribución de {variable} en el conjunto de "
                    f"referencia ({len(serie_ref)} registros) frente a los "
                    f"datos de producción ({len(serie_act)} registros). Los "
                    "valores se expresan como proporción del total para "
                    "permitir la comparación.")
        except Exception as error:  # noqa: BLE001 - se informa al operador
            st.warning(f"No fue posible generar la comparación: {error}",
                       icon=":material/warning:")
    else:
        sin_datos("Este caso de uso no declara variables numéricas "
                  "monitoreadas.")


# ==========================================================================
# DESPLIEGUE
# ==========================================================================
with pestana_despliegue:
    # ---------- 7. Experimento A/B ----------
    estilos.titulo_seccion(
        7, "Experimento A/B",
        "La única sección que muestra desempeño real en producción, "
        "calculado sobre predicciones cuyo resultado verdadero se conoce.")

    datos = experimento or historico

    if datos is None:
        sin_datos(
            f"No hay experimentos A/B registrados para el caso de uso "
            f"{CASO_USO}. La sección se activa cuando se configure el "
            "primero.")
    else:
        (_, caso_uso, version_a, version_b, porcentaje_b,
         estado, ganadora, inicio, fin) = datos

        if experimento is not None:
            st.caption(f"Experimento en curso · control {version_a} frente a "
                       f"candidata {version_b} · inicio "
                       f"{inicio:%Y-%m-%d %H:%M}")
        else:
            cierre = f"{fin:%Y-%m-%d %H:%M}" if fin else "sin fecha de cierre"
            st.info(
                f"No hay experimento activo. El último ({estado}) comparó "
                f"{version_a} con {version_b} y cerró el {cierre}. "
                f"Versión ganadora: {ganadora or 'sin definir'}.",
                icon=":material/history:")

        # Un experimento cerrado no debe arrastrar el tráfico posterior a su fin
        volumen = {fila[0]: fila for fila in
                   obtener_volumen_por_version(caso_uso, desde=inicio,
                                               hasta=fin)}
        predicciones_a = volumen[version_a][1] if version_a in volumen else 0
        predicciones_b = volumen[version_b][1] if version_b in volumen else 0
        total_experimento = predicciones_a + predicciones_b
        real_b = (100 * predicciones_b / total_experimento
                  if total_experimento else 0.0)

        izquierda, derecha = st.columns([2, 3], gap="medium")
        with izquierda:
            st.metric("Tráfico configurado a la candidata", f"{porcentaje_b} %")
            st.metric("Tráfico obtenido por la candidata", f"{real_b:.1f} %",
                      delta=f"{real_b - float(porcentaje_b):+.1f} pp",
                      delta_color="off")
        with derecha:
            if total_experimento:
                mostrar(graficos.reparto_trafico(
                    version_a, predicciones_a, version_b, predicciones_b))
            else:
                sin_datos("El experimento todavía no registró peticiones.")

        st.caption("Una diferencia de pocos puntos entre el reparto "
                   "configurado y el obtenido es normal: la asignación se "
                   "sortea en cada petición.")

        desempeno = {fila[0]: fila for fila in
                     obtener_desempeno_por_version(caso_uso, desde=inicio,
                                                   hasta=fin)}

        def fila_version(version, rol, cantidad):
            """Arma la fila de la tabla comparativa para una de las versiones."""
            medidas = desempeno.get(version)
            if medidas is None:
                return {"Versión": version, "Rol": rol,
                        "Predicciones": cantidad, "Muestra etiquetada": 0,
                        "Accuracy": None, "Precision": None, "Recall": None,
                        "F1-score": None, "ROC-AUC": None}
            _, muestra, accuracy, precision, recall, f1, roc_auc = medidas
            return {
                "Versión": version, "Rol": rol, "Predicciones": cantidad,
                "Muestra etiquetada": muestra,
                "Accuracy": float(accuracy) if accuracy is not None else None,
                "Precision": float(precision) if precision is not None else None,
                "Recall": float(recall) if recall is not None else None,
                "F1-score": float(f1) if f1 is not None else None,
                "ROC-AUC": float(roc_auc) if roc_auc is not None else None,
            }

        df_experimento = pd.DataFrame([
            fila_version(version_a, "Control", predicciones_a),
            fila_version(version_b, "Candidata", predicciones_b),
        ])

        st.dataframe(
            df_experimento, width="stretch", hide_index=True,
            column_config={
                columna: st.column_config.NumberColumn(format="%.3f")
                for columna in ["Accuracy", "Precision", "Recall", "F1-score",
                                "ROC-AUC"]})

        muestra_a = df_experimento.loc[0, "Muestra etiquetada"]
        muestra_b = df_experimento.loc[1, "Muestra etiquetada"]
        f1_a = df_experimento.loc[0, "F1-score"]
        f1_b = df_experimento.loc[1, "F1-score"]

        if muestra_a < MUESTRA_MINIMA or muestra_b < MUESTRA_MINIMA:
            st.warning(
                f"Muestra insuficiente para concluir: {muestra_a} "
                f"predicciones etiquetadas en {version_a} y {muestra_b} en "
                f"{version_b}. Se requieren al menos {MUESTRA_MINIMA} por "
                "grupo, porque una diferencia calculada sobre pocos casos no "
                "es concluyente.",
                icon=":material/pending:")
        else:
            diferencia = f1_b - f1_a
            if diferencia > 0:
                st.success(
                    f"La candidata {version_b} lleva ventaja: F1-score "
                    f"{f1_b:.3f} frente a {f1_a:.3f} del control "
                    f"({diferencia:+.3f}).",
                    icon=":material/trending_up:")
            elif diferencia < 0:
                st.error(
                    f"La candidata {version_b} va por debajo del control: "
                    f"F1-score {f1_b:.3f} frente a {f1_a:.3f} "
                    f"({diferencia:+.3f}). Se recomienda evaluar el rollback.",
                    icon=":material/trending_down:")
            else:
                st.info(
                    f"Ambas versiones empatan en F1-score ({f1_a:.3f}). "
                    "Conviene prolongar el experimento.",
                    icon=":material/drag_handle:")

            ganadora_grafico = version_b if diferencia > 0 else version_a
            mostrar(graficos.desempeno_experimento(
                [version_a, version_b],
                [f1_a, f1_b],
                ["control", "candidata"],
                ganadora_grafico))
            st.caption("F1-score real de cada versión sobre las predicciones "
                       "del experimento con etiqueta conocida. Es la métrica "
                       "de decisión del proyecto.")

    st.divider()

    # ---------- 8. Historial de despliegues ----------
    estilos.titulo_seccion(
        8, "Historial de despliegues",
        "El registro de qué estuvo sirviendo y por qué dejó de hacerlo. El "
        "motivo dice si la versión entró por superar el umbral o salió por "
        "degradación medida.")

    if df_despliegues.empty:
        sin_datos("Sin despliegues registrados. La bitácora se alimenta "
                  "cuando se promueve una versión o se revierte a la "
                  "anterior.")
    else:
        promociones = int((df_despliegues["Operación"] == "promocion").sum())
        rollbacks = int((df_despliegues["Operación"] == "rollback").sum())

        columna_a, columna_b, columna_c = st.columns(3)
        columna_a.metric("Promociones", promociones)
        columna_b.metric("Rollbacks", rollbacks)
        columna_c.metric("Versión en producción",
                         ultimo_despliegue["Versión de destino"])

        if ultimo_despliegue["Operación"] == "rollback":
            st.error(
                f"La última operación fue un rollback: se revirtió de "
                f"{ultimo_despliegue['Versión de origen']} a "
                f"{ultimo_despliegue['Versión de destino']} el "
                f"{ultimo_despliegue['Fecha']:%Y-%m-%d %H:%M}. "
                f"Motivo: {ultimo_despliegue['Motivo']}",
                icon=":material/undo:")
        else:
            origen = ultimo_despliegue["Versión de origen"] or "sin versión previa"
            st.success(
                f"La última operación fue una promoción: {origen} → "
                f"{ultimo_despliegue['Versión de destino']} el "
                f"{ultimo_despliegue['Fecha']:%Y-%m-%d %H:%M}. "
                f"Motivo: {ultimo_despliegue['Motivo']}",
                icon=":material/rocket_launch:")

        iconos = {"promocion": "🟢 Promoción", "rollback": "🔴 Rollback"}
        df_vista = df_despliegues.copy()
        df_vista["Operación"] = df_vista["Operación"].map(
            lambda operacion: iconos.get(operacion, operacion))
        df_vista["Versión de origen"] = df_vista["Versión de origen"].fillna("—")

        st.dataframe(
            df_vista[["Fecha", "Operación", "Versión de origen",
                      "Versión de destino", "Métrica", "Valor en origen",
                      "Valor en destino", "Motivo"]],
            width="stretch", hide_index=True,
            column_config={
                "Valor en origen": st.column_config.NumberColumn(
                    format="%.3f"),
                "Valor en destino": st.column_config.NumberColumn(
                    format="%.3f")})
        st.caption(f"Mostrando {len(df_vista)} operaciones, de la más "
                   "reciente a la más antigua, según lo registrado en "
                   "PostgreSQL.")


# --------------------------------------------------------------------------
# Pie
# --------------------------------------------------------------------------
estilos.pie_pagina(
    "Universidad Manuela Beltrán · Ingeniería de Software",
    f"Datos leídos de PostgreSQL el {datetime.now():%d/%m/%Y a las %H:%M}",
)
