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
- `docker/`: configuración relacionada con Docker.
- `notebooks/`: análisis exploratorio y experimentación.
- `reports/`: reportes de drift generados por Evidently.

## Archivos base

- `requirements.txt`
- `docker-compose.yml`
- `.env.example`
- `.gitignore`

## Documentación complementaria

- `docs/git-flow.md`: flujo de trabajo con Git y convenciones del equipo.
- `docs/definition-of-done.md`: criterios de aceptación transversales.
- `docs/datasets.md`: descripción completa del dataset.

---

# Puesta en marcha

Esta sección describe el orden recomendado para levantar el sistema completo
desde cero. Cada apartado posterior detalla los componentes de forma
individual.

| Paso | Acción | Apartado |
|---|---|---|
| 1 | Crear y activar el entorno virtual | Requisitos previos |
| 2 | Instalar dependencias | Instalar dependencias |
| 3 | Configurar variables de entorno | Configurar variables de entorno |
| 4 | Levantar PostgreSQL | Levantar PostgreSQL |
| 5 | Crear las tablas | Crear las tablas |
| 6 | Levantar MLflow | MLflow |
| 7 | Ejecutar el pipeline de entrenamiento | Ejecutar el pipeline |
| 8 | Promover el modelo candidato a modelo activo | Modelo activo para la API |
| 9 | Levantar la API | Levantar la API |
| 10 | Levantar el dashboard | Ejecutar el dashboard |

## Opcion rapida: levantar todo con Docker Compose

Los cuatro servicios estan contenerizados, asi que no hace falta una terminal
por servicio. Desde la raiz del proyecto:

```powershell
docker compose up -d --build
```

| Servicio | URL | Contenedor |
|---|---|---|
| API (FastAPI) | http://localhost:8000/docs | `mlops_api` |
| Dashboard (Streamlit) | http://localhost:8501 | `mlops_dashboard` |
| MLflow | http://localhost:5000 | `mlops_mlflow` |
| PostgreSQL | `localhost:5432` | `mlops_postgres` |

La primera ejecucion construye las imagenes y tarda varios minutos; las
siguientes reutilizan la cache. Las cuatro tablas se crean automaticamente
cuando el volumen de PostgreSQL se inicializa por primera vez
(`src/database/schema.sql` se monta como script de inicializacion). Si el
volumen ya existia, se siguen creando con el comando del apartado
*Crear las tablas*.

Comandos frecuentes:

```powershell
docker compose ps                  # estado de los servicios
docker compose logs -f api         # logs de un servicio
docker compose restart api         # reiniciar un servicio
docker compose down                # detener todo (conserva los datos)
docker compose down -v             # detener y borrar el volumen de PostgreSQL
```

El codigo de `src/` y `dashboard/` se monta dentro de los contenedores, por lo
que los cambios se recargan sin reconstruir la imagen. Solo hay que reconstruir
(`docker compose up -d --build`) al cambiar las dependencias de
`docker/requirements-*.txt`.

El pipeline de entrenamiento y la deteccion de drift se siguen ejecutando desde
el entorno virtual del host (apartados *Ejecutar el pipeline* y
*Ejecutar la deteccion*): se conectan a los contenedores por los puertos
publicados `5000` y `5432`. Los apartados siguientes describen la alternativa
manual, servicio por servicio.

## Requisitos previos

- Docker Desktop instalado y en ejecución.
- Python 3.11 instalado.
- Entorno virtual creado y activado: `py -m venv venv` y luego `venv/Scripts/activate`
- Si da error al activar: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Instalar dependencias

Desde la raíz del proyecto ejecutar:

```powershell
python -m pip install -r requirements.txt
```

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

El archivo `.env` no debe subirse al repositorio.

## Levantar PostgreSQL

```powershell
docker compose up -d
```

Verificar que el contenedor esté funcionando:

```powershell
docker compose ps
```

## Crear las tablas

Desde PowerShell ejecutar:

```powershell
Get-Content .\src\database\schema.sql -Raw | docker exec -i mlops_postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

El esquema crea cuatro tablas:

| Tabla | Contenido |
|---|---|
| `predictions` | Predicciones emitidas por la API, con sus datos de entrada |
| `model_metrics` | Métricas de evaluación de cada modelo entrenado |
| `model_versions` | Historial de versiones del modelo con su estado |
| `alerts` | Alertas generadas por el monitoreo de data drift |

## Verificar conexión a PostgreSQL

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

## Levantar MLflow

Desde la raíz del proyecto, con el entorno virtual activado:

```powershell
mlflow server --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000 --workers 1
```

La interfaz estará disponible en:

`http://127.0.0.1:5000`

> **Importante:** MLflow debe estar en ejecución antes de lanzar el pipeline.
> Si no lo está, el pipeline se interrumpe en el paso de registro de
> experimentos con un error de conexión al puerto 5000.

Para detener MLflow presionar:

`Ctrl + C`

---

# Pipeline de entrenamiento

## Ejecutar el pipeline

Con MLflow en ejecución y PostgreSQL levantado, abrir otra terminal con el
entorno virtual activado y ejecutar:

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
```

En Git Bash o Linux:

```bash
cp models/churn_model_candidate.joblib models/churn_model_v1.joblib
```

Esta promoción es manual en la versión actual. La automatización de la
selección del modelo activo, junto con las estrategias de A/B testing y
rollback, está prevista para una fase posterior del desarrollo.

> **Nota:** los archivos de la carpeta `models/` son artefactos generados y
> no se versionan en el repositorio. Si la API responde con el error
> `No se encontró el modelo`, ejecute el pipeline de entrenamiento y
> realice la promoción descrita arriba.

---

# Uso de la API

La plataforma incluye una API desarrollada con **FastAPI** para servir el modelo de predicción de churn.

## Levantar la API

```powershell
python -m uvicorn src.api.main:app --reload
```

La API estará disponible en:

`http://127.0.0.1:8000`

La documentación interactiva Swagger UI estará disponible en:

`http://127.0.0.1:8000/docs`

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
Invoke-RestMethod http://127.0.0.1:8000/health
```

> El campo `model_loaded` indica si el modelo ya fue cargado en memoria. La
> carga es diferida: el modelo se carga en la primera solicitud de
> predicción, por lo que este campo responde `false` hasta ese momento.

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

1. Ejecutar la API con Uvicorn.
2. Abrir `http://127.0.0.1:8000/docs`.
3. Seleccionar `/health` o `/predict`.
4. Presionar **Try it out**.
5. Ingresar los datos requeridos.
6. Presionar **Execute**.
7. Verificar que la respuesta sea `200 OK`.

## Detener la API

En la terminal donde se está ejecutando Uvicorn presionar:

`Ctrl + C`

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

## Ejecutar la detección

Con PostgreSQL levantado y predicciones registradas en la base:

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

## Generar tráfico de prueba

Para alimentar el análisis con datos de producción, el proyecto incluye un
generador de predicciones de prueba. Con la API en ejecución:

```powershell
python -m src.monitoring.generar_trafico
```

El script envía predicciones a la API con valores aleatorios dentro de
rangos realistas, de modo que queden registradas en la base de datos como
cualquier otra predicción.

---

# Dashboard

## Ejecutar el dashboard

```powershell
streamlit run dashboard/app.py
```

El dashboard estará disponible en:

`http://localhost:8501`

El dashboard presenta:

- Métricas del modelo activo.
- Comparación de desempeño entre Logistic Regression y XGBoost.
- Historial de versiones del modelo y evolución de la métrica principal.
- Últimas predicciones registradas.
- Alertas de data drift con indicación de severidad.
- Comparación visual de distribuciones entre referencia y producción.

Para detener el dashboard presionar:

`Ctrl + C`

---

# Pruebas

Ejecutar la suite completa desde la raíz del proyecto:

```powershell
python -m pytest -v
```

Las pruebas que requieren el modelo entrenado se omiten automáticamente
cuando el artefacto no está disponible, de modo que la suite puede
ejecutarse en entornos de integración continua sin necesidad de entrenar.
