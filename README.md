# Sistema MLOps

Plataforma MLOps automatizada para gestionar el ciclo de vida de modelos de clasificación, incluyendo preprocesamiento, entrenamiento, evaluación, despliegue mediante API, almacenamiento de predicciones, monitoreo de data drift y visualización mediante dashboard.

[![CI - Tests](https://github.com/Allan-Romero/Sistema-MLOps/actions/workflows/ci.yml/badge.svg)](https://github.com/Allan-Romero/Sistema-MLOps/actions/workflows/ci.yml)

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Modelos | scikit-learn, XGBoost |
| Registro de experimentos | MLflow |
| API | FastAPI |
| Base de datos | PostgreSQL |
| Dashboard | Streamlit |
| Monitoreo de drift | Evidently AI |
| Contenedores | Docker Compose |
| Integración continua | GitHub Actions |

## Integración continua

El proyecto cuenta con un pipeline de integración continua en GitHub Actions
que se ejecuta automáticamente en cada push y Pull Request, instalando
dependencias y ejecutando la suite de pruebas.

El estado de la última ejecución se refleja en el badge al inicio de este
documento. El historial completo está disponible en la pestaña Actions
del repositorio.

## Estructura del proyecto

- `src/`: código fuente del proyecto.
  - `src/training/`: preprocesamiento, entrenamiento y pipeline.
  - `src/api/`: API de predicción.
  - `src/database/`: conexión, esquema y operaciones sobre la base de datos.
  - `src/monitoring/`: detección de data drift.
- `data/`: datos utilizados por el proyecto.
- `models/`: modelos entrenados y artefactos generados.
- `dashboard/`: archivos del dashboard y visualizaciones.
- `tests/`: pruebas del proyecto.
- `docs/`: documentación técnica y funcional.
- `docker/`: Dockerfiles de la API, el dashboard y MLflow, con un archivo de
  dependencias por servicio.
- `notebooks/`: análisis exploratorio y experimentación.
- `reports/`: reportes de drift generados por Evidently.

## Archivos base

- `docker-compose.yml`: orquestación de los cuatro servicios.
- `docker/*.Dockerfile`: imágenes de la API, el dashboard y MLflow.
- `docker/requirements-*.txt`: dependencias de cada imagen.
- `requirements.txt`: dependencias del entorno virtual local, usado para el
  pipeline, la detección de drift y las pruebas.
- `.env.example`
- `.gitignore`

## Documentación complementaria

- `docs/git-flow.md`: flujo de trabajo con Git y convenciones del equipo.
- `docs/definition-of-done.md`: criterios de aceptación transversales.
- `docs/datasets.md`: descripción completa del dataset.

---

# Puesta en marcha

Los cuatro servicios del sistema (PostgreSQL, MLflow, la API y el dashboard)
están contenerizados y se levantan con un solo comando. El pipeline de
entrenamiento, la detección de drift y las pruebas se ejecutan desde el
entorno virtual local y se conectan a esos servicios por los puertos
publicados.

| Paso | Acción | Apartado |
|---|---|---|
| 1 | Crear y activar el entorno virtual | Requisitos previos |
| 2 | Instalar dependencias locales | Instalar dependencias |
| 3 | Configurar variables de entorno | Configurar variables de entorno |
| 4 | Levantar los servicios | Levantar el sistema |
| 5 | Ejecutar el pipeline de entrenamiento | Ejecutar el pipeline |
| 6 | Promover el modelo candidato a modelo activo | Modelo activo para la API |
| 7 | Generar tráfico y analizar drift (opcional) | Monitoreo de data drift |

## Requisitos previos

- Docker Desktop instalado y en ejecución.
- Python 3.11 instalado.
- Entorno virtual creado y activado: `py -m venv venv` y luego `venv/Scripts/activate`
- Si da error al activar: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Instalar dependencias

El entorno virtual se utiliza para el pipeline de entrenamiento, la detección
de drift y las pruebas. Los servicios contenerizados instalan sus propias
dependencias al construir las imágenes.

```powershell
python -m pip install -r requirements.txt
```

## Levantar el sistema

Con las variables de entorno ya configuradas (apartado *Configurar variables
de entorno*), desde la raíz del proyecto:

```powershell
docker compose up -d --build
```

| Servicio | URL | Contenedor |
|---|---|---|
| API (FastAPI) | http://localhost:8000/docs | `mlops_api` |
| Dashboard (Streamlit) | http://localhost:8501 | `mlops_dashboard` |
| MLflow | http://localhost:5000 | `mlops_mlflow` |
| PostgreSQL | `localhost:5432` | `mlops_postgres` |

La primera ejecución construye las imágenes y tarda varios minutos; las
siguientes reutilizan la caché. La API y el dashboard esperan a que
PostgreSQL esté disponible antes de arrancar.

Comandos frecuentes:

```powershell
docker compose ps                  # estado de los servicios
docker compose logs -f api         # logs de un servicio
docker compose restart api         # reiniciar un servicio
docker compose down                # detener todo (conserva los datos)
docker compose down -v             # detener y borrar el volumen de PostgreSQL
```

El código de `src/` y `dashboard/` se monta dentro de los contenedores, por lo
que los cambios se recargan sin reconstruir la imagen. Solo es necesario
reconstruir (`docker compose up -d --build`) al modificar las dependencias de
`docker/requirements-*.txt`.

Los datos persisten fuera de los contenedores: la base de datos en el volumen
`postgres_data`, y el historial de MLflow en `mlflow.db` y `mlartifacts/`.

---

# Dataset inicial del proyecto

Para la primera fase del proyecto se seleccionó el dataset público **Telco Customer Churn**, orientado a la predicción de abandono de clientes.

El dataset se encuentra almacenado en:

`data/raw/churn.csv`

La variable objetivo es:

`Churn`

Sus valores representan:

- `No`: el cliente no abandonó el servicio.
- `Yes`: el cliente abandonó el servicio.

Este dataset es utilizado para construir el flujo MLOps base del sistema: preprocesamiento, entrenamiento, evaluación, despliegue mediante API, almacenamiento de predicciones y visualización mediante dashboard.

La descripción completa del dataset se encuentra en:

`docs/datasets.md`

---

# Base de datos

## Configurar variables de entorno

Copiar `.env.example` a `.env`:

```powershell
Copy-Item .env.example .env
```

Después configurar en `.env` las credenciales de PostgreSQL:

```env
POSTGRES_USER=usuario
POSTGRES_PASSWORD=contraseña
POSTGRES_DB=mlops_db
```

Docker Compose usa este archivo para crear la base de datos y para entregar
las credenciales a la API y al dashboard. Los scripts que se ejecutan desde el
entorno virtual también lo leen y, salvo que se definan `POSTGRES_HOST` y
`POSTGRES_PORT`, se conectan a `localhost:5432`.

El archivo `.env` no debe subirse al repositorio.

## Tablas

El esquema `src/database/schema.sql` se monta como script de inicialización
del contenedor de PostgreSQL, por lo que las tablas se crean
automáticamente la primera vez que se inicializa el volumen:

| Tabla | Contenido |
|---|---|
| `predictions` | Predicciones emitidas por la API, con sus datos de entrada |
| `model_metrics` | Métricas de evaluación de cada modelo entrenado |
| `model_versions` | Historial de versiones del modelo con su estado |
| `alerts` | Alertas generadas por el monitoreo de data drift |
| `deployments` | Bitácora de promociones y rollbacks de versión en producción |
| `experiments` | Configuración y resultado de los experimentos A/B entre versiones |

Si el volumen ya existía antes de incorporar el esquema, o si se modifica
`schema.sql`, las tablas pueden crearse manualmente:

```powershell
Get-Content .\src\database\schema.sql -Raw | docker exec -i mlops_postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Verificar conexión a PostgreSQL

Desde el entorno virtual, con los servicios levantados:

```powershell
python -m src.database.test_connection
```

La conexión debe completarse correctamente.

---

# MLflow

El proyecto utiliza MLflow para registrar los experimentos de entrenamiento de los modelos de churn.

MLflow almacena:

- Parámetros de entrenamiento.
- Métricas de evaluación.
- Artefactos del modelo.
- Historial de ejecuciones.

El servidor forma parte del stack y su interfaz queda disponible en:

`http://localhost:5000`

El backend de metadatos es `mlflow.db` y los artefactos se guardan en
`mlartifacts/`; ambos se montan desde el repositorio, de modo que el historial
sobrevive a `docker compose down` y a la reconstrucción de las imágenes.

> **Importante:** el pipeline de entrenamiento registra los experimentos
> contra `http://127.0.0.1:5000`. Si el stack no está levantado, el pipeline
> se interrumpe en el paso de registro de experimentos con un error de
> conexión al puerto 5000.

---

# Pipeline de entrenamiento

## Ejecutar el pipeline

Con los servicios levantados y el entorno virtual activado:

```powershell
python -m src.training.run_pipeline
```

El pipeline ejecuta ocho etapas encadenadas:

| Etapa | Acción |
|---|---|
| 1 | Preprocesamiento de los datos |
| 2 | Entrenamiento de Logistic Regression |
| 3 | Evaluación del modelo base |
| 4 | Entrenamiento de XGBoost |
| 5 | Comparación de métricas entre modelos |
| 6 | Selección automática del mejor modelo |
| 7 | Registro de experimentos en MLflow |
| 8 | Persistencia de métricas y versiones en PostgreSQL |

Los experimentos quedan registrados en MLflow bajo el nombre
`churn-model-training`, con una ejecución por cada algoritmo.

## Modelo activo para la API

El pipeline genera varios artefactos en la carpeta `models/`:

| Archivo | Contenido |
|---|---|
| `logistic_regression_v1.joblib` | Modelo base entrenado |
| `xgboost_v1.joblib` | Modelo de gradient boosting entrenado |
| `churn_model_candidate.joblib` | Modelo seleccionado por el pipeline |
| `logistic_regression_v1_metrics.json` | Métricas del modelo base |
| `model_comparison.json` | Métricas comparativas de ambos modelos |
| `model_selection.json` | Resultado de la selección automática |

La API carga el modelo desde `models/churn_model_v1.joblib`, que corresponde
al modelo activo en producción. Tras ejecutar el pipeline es necesario
promover el candidato a modelo activo:

```powershell
Copy-Item models/churn_model_candidate.joblib models/churn_model_v1.joblib
docker compose restart api
```

En Git Bash o Linux:

```bash
cp models/churn_model_candidate.joblib models/churn_model_v1.joblib
docker compose restart api
```

La carpeta `models/` se monta en el contenedor de la API en modo solo lectura,
por lo que el archivo promovido queda disponible de inmediato. El reinicio es
necesario porque la API conserva el modelo en memoria desde la primera
predicción.

Esta promoción es manual en la versión actual. La automatización de la
selección del modelo activo, junto con las estrategias de A/B testing y
rollback, está prevista para una fase posterior del desarrollo.

> **Nota:** los archivos de la carpeta `models/` son artefactos generados y
> no se versionan en el repositorio. Si la API responde con el error
> `No se encontró el modelo`, ejecute el pipeline de entrenamiento y
> realice la promoción descrita arriba.

---

# Uso de la API

La plataforma incluye una API desarrollada con **FastAPI** para servir el
modelo de predicción de churn. Se ejecuta en el contenedor `mlops_api` y está
disponible en:

`http://localhost:8000`

La documentación interactiva Swagger UI está disponible en:

`http://localhost:8000/docs`

## Endpoint raíz

### GET /

Permite comprobar que la API se encuentra en ejecución.

Ejemplo de respuesta:

```json
{
  "message": "Sistema-MLOps API",
  "model": "churn_model_v1",
  "status": "running"
}
```

## Endpoint de estado

### GET /health

Permite verificar que la API y el modelo estén funcionando correctamente.

Ejemplo de respuesta:

```json
{
  "status": "healthy",
  "model": "churn_model",
  "model_version": "v1",
  "model_loaded": true
}
```

También puede probarse desde PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

> El campo `model_loaded` indica si el modelo ya fue cargado en memoria. La
> carga es diferida: el modelo se carga en la primera solicitud de
> predicción, por lo que este campo responde `false` hasta ese momento.

Este endpoint también se usa como healthcheck del contenedor, de modo que
`docker compose ps` reporta la API como `healthy` cuando responde
correctamente.

## Endpoint de predicción

### POST /predict

Recibe los datos de un cliente en formato JSON y devuelve una predicción de churn.

Ejemplo de entrada:

```json
{
  "gender": "Female",
  "SeniorCitizen": 0,
  "Partner": "Yes",
  "Dependents": "No",
  "tenure": 1,
  "PhoneService": "No",
  "MultipleLines": "No phone service",
  "InternetService": "DSL",
  "OnlineSecurity": "No",
  "OnlineBackup": "Yes",
  "DeviceProtection": "No",
  "TechSupport": "No",
  "StreamingTV": "No",
  "StreamingMovies": "No",
  "Contract": "Month-to-month",
  "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check",
  "MonthlyCharges": 29.85,
  "TotalCharges": 29.85
}
```

Ejemplo de respuesta:

```json
{
  "prediction": 1,
  "prediction_label": "Yes",
  "churn_probability": 0.6188,
  "model_version": "v1",
  "prediction_id": 42
}
```

Donde:

- `prediction = 0`: el modelo predice que el cliente no presenta churn.
- `prediction = 1`: el modelo predice que el cliente presenta churn.
- `prediction_label`: representación textual de la predicción.
- `churn_probability`: probabilidad estimada de churn.
- `model_version`: versión del modelo utilizada para la predicción.
- `prediction_id`: identificador del registro almacenado en PostgreSQL.

Cada predicción se registra automáticamente en la tabla `predictions`, junto
con los datos de entrada recibidos. Estos datos alimentan posteriormente el
análisis de data drift.

## Probar la API con Swagger

1. Verificar que el stack esté levantado con `docker compose ps`.
2. Abrir `http://localhost:8000/docs`.
3. Seleccionar `/health` o `/predict`.
4. Presionar **Try it out**.
5. Ingresar los datos requeridos.
6. Presionar **Execute**.
7. Verificar que la respuesta sea `200 OK`.

---

# Monitoreo de data drift

El sistema monitorea los cambios de distribución entre el conjunto de datos
de entrenamiento y los datos observados en producción, utilizando
**Evidently AI** para el reporte visual y el **Population Stability Index
(PSI)** como métrica de decisión.

## Variables monitoreadas

El análisis se centra en las variables numéricas del dataset:

- `tenure`
- `MonthlyCharges`
- `TotalCharges`

## Umbrales de decisión

Se adopta la escala estándar del PSI:

| Rango de PSI | Nivel asignado | Genera alerta |
|---|---|---|
| Menor a 0.10 | Bajo | No |
| Entre 0.10 y 0.25 | Medio | Sí |
| Mayor o igual a 0.25 | Alto | Sí |

El análisis requiere un mínimo de 30 registros de producción para ejecutarse,
con el fin de evitar conclusiones sobre muestras no representativas.

## Generar tráfico de prueba

Para alimentar el análisis con datos de producción, el proyecto incluye un
generador de predicciones de prueba. Con el stack levantado:

```powershell
python -m src.monitoring.generar_trafico
```

El script toma clientes del propio conjunto de referencia y los envía a la
API, de modo que queden registrados en la base de datos como cualquier otra
predicción. Acepta dos argumentos opcionales: la cantidad de predicciones y un
factor de drift que altera deliberadamente `TotalCharges`.

```powershell
python -m src.monitoring.generar_trafico 150 1.0    # escenario de control
python -m src.monitoring.generar_trafico 150 1.8    # escenario con drift
```

Con el factor en `1.0` la distribución enviada reproduce la del baseline, por
lo que no debería generarse drift; con un factor mayor se provoca de forma
controlada para validar el monitoreo. El destino es `http://localhost:8000`
salvo que se defina otra dirección en la variable de entorno `API_URL`.

## Ejecutar la detección

Con predicciones registradas en la base:

```powershell
python -m src.monitoring.detect_drift
```

El módulo compara el conjunto de referencia contra los datos de producción,
clasifica el nivel de variación de cada variable y registra una alerta en la
tabla `alerts` por cada variable con drift detectado.

Adicionalmente genera un reporte visual en:

`reports/drift_report.html`

> **Nota:** la carpeta `reports/` contiene artefactos generados y no se
> versiona en el repositorio.

---

# Dashboard

El dashboard se ejecuta en el contenedor `mlops_dashboard` y está disponible
en:

`http://localhost:8501`

El dashboard presenta:

- Métricas del modelo activo.
- Comparación de desempeño entre Logistic Regression y XGBoost.
- Historial de versiones del modelo y evolución de la métrica principal.
- Últimas predicciones registradas.
- Alertas de data drift con indicación de severidad.
- Comparación visual de distribuciones entre referencia y producción.

Lee la información directamente de PostgreSQL, por lo que basta con recargar
la página para ver los resultados de una nueva ejecución del pipeline o de la
detección de drift.

---

# Pruebas

Ejecutar la suite completa desde la raíz del proyecto, con el entorno virtual
activado:

```powershell
python -m pytest -v
```

Las pruebas que requieren el modelo entrenado se omiten automáticamente
cuando el artefacto no está disponible, de modo que la suite puede
ejecutarse en entornos de integración continua sin necesidad de entrenar.
