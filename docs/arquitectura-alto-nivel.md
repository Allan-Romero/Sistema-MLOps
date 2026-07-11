# Arquitectura de alto nivel — Plataforma MLOps

**Proyecto:** Desarrollo de una Plataforma MLOps Automatizada con Pipeline CI/CD
**Equipo:** Joseph Reyes · Allan Romero
**Tarea:** S0-T3 — Definir la arquitectura del sistema

---

## Descripción general

La plataforma se estructura como un conjunto de servicios ligeros e independientes que se comunican entre sí, orquestados con Docker Compose. La arquitectura integra el ciclo de vida completo de un modelo de clasificación: entrenamiento, versionamiento, despliegue vía API, almacenamiento de resultados, monitoreo de drift y visualización.

El componente central es la base de datos PostgreSQL, que actúa como punto de encuentro entre la API (que escribe), el dashboard (que lee) y el módulo de monitoreo (que registra alertas).

---

## Componentes del sistema

| Componente | Tecnología | Función |
|------------|------------|---------|
| Pipeline de entrenamiento | Python, scikit-learn, XGBoost | Entrena y evalúa los modelos de clasificación. |
| Registro de modelos | MLflow | Guarda cada versión del modelo con sus parámetros y métricas. |
| API de predicción | FastAPI | Expone el modelo mediante endpoints y sirve predicciones. |
| Base de datos | PostgreSQL | Almacena predicciones, métricas, alertas y versiones. |
| Dashboard | Streamlit | Muestra métricas, predicciones recientes y alertas. |
| Monitoreo de drift | Evidently AI | Compara datos nuevos contra el baseline y genera alertas. |
| Integración continua | GitHub Actions | Ejecuta pruebas y dispara el pipeline al subir cambios. |
| Contenerización | Docker Compose | Levanta todos los servicios de forma coordinada. |

---

## Flujos de comunicación

1. GitHub Actions dispara el pipeline de entrenamiento cuando se suben cambios al repositorio.
2. El pipeline entrena el modelo (scikit-learn / XGBoost) y registra la versión y sus métricas en MLflow.
3. FastAPI carga el modelo activo desde MLflow para servir predicciones.
4. Un cliente (o simulador de datos) envía un JSON al endpoint `/predict` de FastAPI y recibe la predicción.
5. FastAPI guarda cada predicción en PostgreSQL.
6. Streamlit lee de PostgreSQL y muestra métricas, predicciones recientes y alertas en el dashboard.
7. Evidently compara los datos nuevos contra el baseline de entrenamiento; si detecta drift, escribe una alerta en PostgreSQL, que luego aparece en el dashboard.

---

## Respuestas a las preguntas clave

- **¿Dónde vive el modelo?** Registrado en MLflow y cargado por FastAPI para su uso.
- **¿Cómo llega una predicción?** El cliente envía un JSON al endpoint `/predict` de FastAPI.
- **¿Dónde se almacenan los datos?** En PostgreSQL (predicciones, métricas, alertas, versiones).
- **¿Quién consume la API?** El cliente o simulador de datos que solicita predicciones.
- **¿Cómo se integra el dashboard?** Streamlit lee directamente de PostgreSQL (solo lectura).
- **¿Cómo funciona el monitoreo?** Evidently compara datos nuevos vs baseline y registra alertas de drift en PostgreSQL.

---

## Justificación

Se selecciona una arquitectura modular basada en servicios ligeros y herramientas open source, orientada a facilitar la automatización del ciclo de vida de modelos de clasificación. La solución mantiene una complejidad adecuada para un contexto académico, evitando infraestructuras pesadas (como Kubernetes) que dificultarían el desarrollo por un equipo pequeño, y es replicable en organizaciones de tamaño medio.

---

## Aprobación del equipo

| Integrante | Aprobación | Fecha |
|------------|------------|-------|
| Joseph Reyes | ☐ | |
| Allan Romero | ☐ | |
