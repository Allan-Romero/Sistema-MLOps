\# Arquitectura base del proyecto Sistema-MLOps



\## Objetivo



Definir la arquitectura de alto nivel del proyecto Sistema-MLOps, identificando los componentes principales, sus responsabilidades y los flujos de comunicación entre ellos.



\## Descripción general



Sistema-MLOps será una plataforma modular orientada a gestionar el ciclo de vida de modelos de clasificación. La arquitectura permitirá cargar datasets públicos, preprocesar datos, entrenar modelos, registrar métricas, exponer predicciones mediante una API, almacenar resultados, visualizar métricas en un dashboard y monitorear posibles desviaciones de datos mediante detección de drift.



\## Componentes principales



| Componente | Tecnología | Responsabilidad |

|---|---|---|

| Repositorio de código | GitHub | Alojar el código fuente, documentación, ramas y evidencias del proyecto. |

| Gestión del proyecto | GitHub Projects | Administrar tareas, sprints, responsables y estado de avance. |

| Dataset | CSV en data/raw | Almacenar los datos públicos utilizados para entrenamiento y validación. |

| Pipeline de datos | Python, Pandas, scikit-learn | Limpiar, transformar y preparar los datos para entrenamiento. |

| Entrenamiento de modelos | scikit-learn, XGBoost | Entrenar modelos de clasificación y calcular métricas. |

| Registro de modelos | MLflow | Registrar experimentos, métricas, parámetros y versiones de modelos. |

| API de predicción | FastAPI | Exponer endpoints para realizar predicciones y consultar el estado del modelo. |

| Base de datos | PostgreSQL | Guardar predicciones, métricas, versiones, alertas y eventos. |

| Dashboard | Streamlit | Mostrar métricas, predicciones, alertas, historial de modelos y estado general. |

| Monitoreo de drift | Evidently AI | Comparar datos de referencia contra datos nuevos para detectar desviaciones. |

| Contenedores | Docker y Docker Compose | Ejecutar servicios de forma ordenada y replicable. |

| CI/CD | GitHub Actions | Automatizar pruebas, validaciones y flujos básicos de integración continua. |



\## Respuestas a preguntas de arquitectura



\### ¿Dónde vive el modelo?



El modelo entrenado se almacenará inicialmente como artefacto dentro de la carpeta `models/`. Posteriormente será registrado en MLflow para mantener versiones, métricas y trazabilidad.



\### ¿Cómo llega una predicción?



Una predicción llega mediante una solicitud HTTP al endpoint `/predict` de la API desarrollada con FastAPI. El usuario o cliente envía los datos de entrada en formato JSON, la API carga el modelo activo, genera la predicción y devuelve el resultado.



\### ¿Dónde se almacenan los datos?



Los datos originales se almacenan en `data/raw`. Los datos procesados se podrán almacenar en `data/processed`. Las predicciones, métricas, alertas, versiones y eventos se almacenarán en PostgreSQL.



\### ¿Quién consume la API?



La API puede ser consumida por usuarios técnicos, pruebas desde Swagger UI, scripts de simulación y eventualmente por el dashboard o cualquier cliente externo autorizado.



\### ¿Cómo se integra el dashboard?



El dashboard en Streamlit consultará la base de datos PostgreSQL para mostrar predicciones, métricas, alertas y versiones del modelo. También podrá mostrar información generada por MLflow o archivos de métricas según la fase del proyecto.



\### ¿Cómo funcionará el monitoreo?



El monitoreo se realizará comparando datos de referencia del entrenamiento contra datos nuevos o predicciones recientes. Evidently AI generará reportes de drift y, cuando se detecten desviaciones, se registrarán alertas en PostgreSQL para ser visualizadas en el dashboard.



\## Flujo principal del sistema



1\. El dataset público se almacena en `data/raw`.

2\. El pipeline de preprocesamiento limpia y transforma los datos.

3\. El pipeline de entrenamiento entrena modelos de clasificación.

4\. Las métricas del modelo se calculan y se registran.

5\. MLflow registra experimentos, parámetros, métricas y versiones.

6\. El modelo seleccionado queda disponible como modelo activo.

7\. FastAPI expone el modelo mediante el endpoint `/predict`.

8\. El usuario o cliente envía datos a la API.

9\. La API retorna una predicción.

10\. La predicción se guarda en PostgreSQL.

11\. Streamlit consulta PostgreSQL y muestra métricas, predicciones y alertas.

12\. Evidently AI compara datos de referencia contra datos nuevos.

13\. Si se detecta drift, se registra una alerta.

14\. El dashboard muestra la alerta para apoyar la toma de decisiones.



\## Diagrama de arquitectura en formato Mermaid



```mermaid

flowchart TD

&#x20;   A\[GitHub Repository] --> B\[GitHub Actions CI/CD]

&#x20;   A --> C\[Dataset CSV data/raw]



&#x20;   C --> D\[Pipeline de Preprocesamiento Python + Pandas]

&#x20;   D --> E\[Entrenamiento de Modelos scikit-learn + XGBoost]

&#x20;   E --> F\[Evaluacion de Metricas]

&#x20;   F --> G\[MLflow Tracking y Model Registry]



&#x20;   G --> H\[Modelo Activo]

&#x20;   H --> I\[FastAPI API de Prediccion]



&#x20;   J\[Cliente / Usuario / Swagger UI] --> I

&#x20;   I --> K\[Respuesta de Prediccion]

&#x20;   I --> L\[PostgreSQL]



&#x20;   L --> M\[Streamlit Dashboard]

&#x20;   G --> M



&#x20;   L --> N\[Evidently AI Drift Detection]

&#x20;   C --> N

&#x20;   N --> O\[Alertas de Drift]

&#x20;   O --> L

&#x20;   O --> M



&#x20;   P\[Docker Compose] --> I

&#x20;   P --> L

&#x20;   P --> M

```



\## Diagrama en texto



```text

Usuario / Cliente / Swagger UI

&#x20;       |

&#x20;       v

FastAPI API de predicción

&#x20;       |

&#x20;       v

Modelo activo

&#x20;       |

&#x20;       v

PostgreSQL

&#x20;       |

&#x20;       v

Streamlit Dashboard



Dataset data/raw

&#x20;       |

&#x20;       v

Pipeline de preprocesamiento

&#x20;       |

&#x20;       v

Entrenamiento scikit-learn / XGBoost

&#x20;       |

&#x20;       v

MLflow

&#x20;       |

&#x20;       v

Modelo activo



Datos de referencia + datos nuevos

&#x20;       |

&#x20;       v

Evidently AI

&#x20;       |

&#x20;       v

Alertas de drift

&#x20;       |

&#x20;       v

PostgreSQL + Dashboard

```



\## Aprobación de arquitectura



La arquitectura será aprobada por ambos integrantes del equipo antes de iniciar el desarrollo de los módulos funcionales. Cualquier cambio posterior deberá justificarse y registrarse en la documentación del proyecto.

