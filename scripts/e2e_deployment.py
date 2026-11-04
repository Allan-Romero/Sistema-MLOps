"""Validación funcional controlada; NO son resultados experimentales de tesis.

Ejecutar exclusivamente dentro de docker-compose.ci.yml. Entrena modelos
pequeños con datos sintéticos y usa HTTP real, PostgreSQL y los servicios
reales de promoción, A/B y cierre. No manipula archivos tras registrarlos.
"""
import json
import os
from pathlib import Path
import urllib.request

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score

from src.database.connection import get_connection
from src.database.crud import (
    registrar_etiqueta_real, obtener_historial_despliegues,
    obtener_ultimo_experimento, obtener_version_activa,
)
from src.database.model_promotion import registrar_candidato
from src.monitoring.experiment_service import abrir_experimento, finalizar_experimento
from src.training.fraud_features import FEATURE_COLUMNS


def http(path, payload=None, host="http://localhost:8000"):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(host + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def entrada(caso, valor):
    if caso == "fraude":
        return {col: float(valor if col == "Amount" else 1) for col in FEATURE_COLUMNS}
    return dict(gender="Female", SeniorCitizen=0, Partner="Yes", Dependents="No",
                tenure=valor, PhoneService="Yes", MultipleLines="No", InternetService="DSL",
                OnlineSecurity="No", OnlineBackup="Yes", DeviceProtection="No", TechSupport="No",
                StreamingTV="No", StreamingMovies="No", Contract="Month-to-month",
                PaperlessBilling="Yes", PaymentMethod="Electronic check",
                MonthlyCharges=30.0, TotalCharges=30.0)


def entrenar_modelos(caso):
    """Entrena artefactos con el mismo esquema que recibe cada endpoint."""
    columna = "Amount" if caso == "fraude" else "tenure"
    columnas = list(FEATURE_COLUMNS) if caso == "fraude" else [columna]
    x = pd.DataFrame(1.0, index=range(100), columns=columnas)
    x[columna] = np.arange(100)
    y = (x[columna] >= 50).astype(int)
    control = DummyClassifier(strategy="constant", constant=1).fit(x, y)
    candidata = DecisionTreeClassifier(max_depth=1, random_state=42).fit(x, y)
    validacion = pd.DataFrame(1.0, index=range(4), columns=columnas)
    validacion[columna] = [10, 20, 70, 80]
    return control, candidata, validacion, np.array([0, 0, 1, 1])


def ejecutar(caso, pierde):
    # Entrenamiento de control imperfecto y candidata sobre validación separada.
    # En el desenlace adverso se introduce concept shift EN LAS ENTRADAS,
    # nunca se alteran predicciones o etiquetas después de observar resultados.
    control, candidata, validacion, verdad = entrenar_modelos(caso)
    modelos = Path("/app/models")
    modelos.mkdir(exist_ok=True)
    resultados = []
    for modelo in (control, candidata):
        temporal = modelos / f"{caso}_candidate.joblib"
        joblib.dump(modelo, temporal)
        # El servicio asigna y conserva el artefacto de cada versión.
        resultado = registrar_candidato(
            caso, None, "decision_tree" if modelo is candidata else "dummy",
            float(f1_score(verdad, modelo.predict(validacion))), archivo_candidato=temporal)
        if not resultado["promovido"]:
            raise AssertionError(resultado)
        resultados.append(resultado)
    a, b = [r["version_candidata"] for r in resultados]
    identificador = abrir_experimento(caso)
    endpoint = "/predict-fraud" if caso == "fraude" else "/predict"
    conteos = {a: 0, b: 0}
    # Cantidad acotada, distribución A/B real. Se exige cobertura por versión.
    for numero in range(1200):
        etiqueta = numero % 2
        valor = (80 if etiqueta else 20)
        if pierde:
            valor = 100 - valor  # concept shift: regla original deja de generalizar
        respuesta = http(endpoint, entrada(caso, valor))
        version = respuesta["model_version"]
        if version not in conteos:
            raise AssertionError(respuesta)
        registrar_etiqueta_real(respuesta["prediction_id"], etiqueta)
        conteos[version] += 1
        if min(conteos.values()) >= 80:
            break
    else:
        raise AssertionError("No hubo cobertura A/B suficiente.")
    decision = finalizar_experimento(caso)
    esperada = a if pierde else b
    assert decision["rollback"] == pierde, decision
    assert decision["version_ganadora"] == esperada, decision
    # La siguiente llamada debe servir la versión elegida sin reiniciar la API.
    assert http(endpoint, entrada(caso, 80))["model_version"] == esperada
    assert obtener_version_activa(caso)[0][2] == esperada
    ultimo = obtener_ultimo_experimento(caso)
    assert ultimo[0] == identificador and ultimo[5] == "finalizado" and ultimo[6] == esperada
    historial = obtener_historial_despliegues(caso)
    assert historial and historial[0][4] == ("rollback" if pierde else "promocion"), historial
    return {"caso_uso": caso, "escenario": "degradacion_controlada" if pierde else "mejora",
            "conteos_http": conteos, "decision": decision,
            "historial": historial, "experimento": ultimo}


def main():
    if os.getenv("MLOPS_E2E_ISOLATED") != "1" or os.getenv("POSTGRES_DB") != "mlops_ci":
        raise RuntimeError("Ejecute exclusivamente en el entorno desechable mlops_ci.")
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM model_versions;")
            if cursor.fetchone()[0]:
                raise RuntimeError("La validación requiere un entorno nuevo y vacío.")
    finally:
        conexion.close()
    assert http("/health")["status"] == "healthy"
    for host, path in [("http://dashboard:8501", "/_stcore/health"), ("http://mlflow:5000", "/health")]:
        with urllib.request.urlopen(host + path, timeout=15) as response:
            assert response.status == 200
    evidencia = []
    for caso in ("churn", "fraude"):
        evidencia.append(ejecutar(caso, False))
        # La segunda pareja usa un caso limpio, sin borrar bases ajenas.
        # Se conserva el historial de la primera secuencia en la evidencia exportada.
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE model_versions SET estado = 'historica' WHERE caso_uso = %s;", (caso,))
            conexion.commit()
        finally:
            conexion.close()
        evidencia.append(ejecutar(caso, True))
    print(json.dumps({"tipo": "prueba_funcional_sintetica_no_resultado_academico", "escenarios": evidencia},
                     ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
