# Stack tecnológico oficial - Sistema-MLOps

## Objetivo

Definir las herramientas oficiales del proyecto Sistema-MLOps, indicando el uso de cada una y la justificación de su selección. Esto permite evitar cambios innecesarios durante el desarrollo y mantener una arquitectura coherente.

## Tabla oficial de herramientas

| Herramienta | Uso dentro del proyecto | Justificación |
|---|---|---|
| Python | Lenguaje principal de desarrollo | Permite desarrollar el procesamiento de datos, entrenamiento de modelos, API, monitoreo y automatización usando un mismo lenguaje. |
| Pandas | Procesamiento de datos | Se usará para cargar, limpiar, explorar y transformar los datasets públicos del proyecto. |
| NumPy | Operaciones numéricas | Complementa el procesamiento de datos y las operaciones matemáticas requeridas por los modelos. |
| scikit-learn | Modelos base de clasificación | Permite entrenar modelos iniciales, construir pipelines de preprocesamiento y calcular métricas de evaluación. |
| XGBoost | Modelo avanzado de clasificación | Se usará para comparar el rendimiento frente a modelos base y mejorar la capacidad predictiva. |
| FastAPI | Backend / API de predicción | Permitirá exponer el modelo mediante endpoints como /predict, /health, /metrics y /model-version. |
| Uvicorn | Servidor para FastAPI | Permitirá ejecutar localmente la API durante el desarrollo y pruebas. |
| PostgreSQL | Base de datos | Almacenará predicciones, métricas, versiones de modelos, alertas y eventos del sistema. |
| SQLAlchemy | Conexión entre Python y PostgreSQL | Permitirá manejar consultas e inserciones desde la API, scripts y dashboard. |
| Streamlit | Dashboard | Se usará para construir el tablero visual de métricas, predicciones, alertas, versiones y monitoreo. |
| Plotly | Visualización de gráficos | Permitirá crear gráficas interactivas para métricas, comparaciones de modelos y monitoreo. |
| MLflow | Registro y versionamiento de modelos | Permitirá registrar experimentos, parámetros, métricas, artefactos y versiones de modelos. |
| Evidently AI | Detección de drift | Permitirá comparar datos de referencia contra datos nuevos para identificar desviaciones en las variables. |
| Docker | Contenedores | Permitirá empaquetar servicios y asegurar que el sistema se pueda ejecutar de forma consistente. |
| Docker Compose | Orquestación local | Permitirá levantar PostgreSQL, API, dashboard y servicios relacionados desde un solo archivo de configuración. |
| Git | Control de versiones | Permitirá controlar los cambios realizados en el código fuente. |
| GitHub | Repositorio remoto | Alojará el código fuente, ramas, issues, pull requests y evidencias del proyecto. |
| GitHub Projects | Gestión Scrum | Permitirá administrar backlog, sprints, tareas, responsables y estados de avance. |
| GitHub Actions | CI/CD | Permitirá automatizar validaciones, pruebas e integración continua. |
| Pytest | Pruebas automatizadas | Se usará para validar componentes como preprocesamiento, API y funciones principales. |
| Draw.io / diagrams.net | Diagramas de arquitectura | Se usará para diseñar y exportar el diagrama de arquitectura del sistema. |
| Markdown | Documentación técnica | Se usará para documentar datasets, arquitectura, stack, instalación y uso del sistema. |
| Visual Studio Code | Entorno de desarrollo | Editor recomendado para trabajar con Python, Git, Docker, Markdown y extensiones de desarrollo. |

## Herramientas descartadas inicialmente

| Herramienta | Motivo |
|---|---|
| Kubernetes | No se usará inicialmente porque aumenta la complejidad y no es necesario para el MVP académico. |
| Kubeflow | Se considera demasiado complejo para el alcance inicial del proyecto. |
| Seldon Core | Se dejará como referencia teórica o mejora futura, pero no como herramienta principal de implementación. |
| Apache Airflow | No se usará inicialmente para evitar agregar complejidad adicional al pipeline. |

## Decisión final

El stack oficial del proyecto será:

Python, Pandas, NumPy, scikit-learn, XGBoost, FastAPI, Uvicorn, PostgreSQL, SQLAlchemy, Streamlit, Plotly, MLflow, Evidently AI, Docker, Docker Compose, Git, GitHub, GitHub Projects, GitHub Actions, Pytest, Draw.io, Markdown y Visual Studio Code.

Este conjunto de herramientas permite construir una plataforma MLOps modular, replicable y adecuada para un contexto académico. Cubre las etapas de carga de datos, preprocesamiento, entrenamiento, evaluación, versionamiento, despliegue mediante API, almacenamiento, monitoreo, dashboard y detección de drift.
