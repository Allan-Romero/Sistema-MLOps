# Sistema MLOps

Plataforma MLOps automatizada para gestionar el ciclo de vida de modelos de clasificación, incluyendo preprocesamiento, entrenamiento, evaluación, despliegue mediante API, almacenamiento de predicciones y visualización mediante dashboard.

## Estructura del proyecto

- `src/`: código fuente del proyecto.
- `data/`: datos utilizados por el proyecto.
- `models/`: modelos entrenados y artefactos generados.
- `dashboard/`: archivos del dashboard y visualizaciones.
- `tests/`: pruebas del proyecto.
- `docs/`: documentación técnica y funcional.
- `docker/`: configuración relacionada con Docker.
- `notebooks/`: análisis exploratorio y experimentación.

## Archivos base

- `requirements.txt`
- `docker-compose.yml`
- `.env.example`
- `.gitignore`

## Dataset inicial del proyecto

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

# Uso de la API

La plataforma incluye una API desarrollada con **FastAPI** para servir el modelo de predicción de churn.

## Instalar dependencias

Desde la raíz del proyecto ejecutar:

```powershell
python -m pip install -r requirements.txt
```

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
  "model_version": "v1"
}
```

Donde:

- `prediction = 0`: el modelo predice que el cliente no presenta churn.
- `prediction = 1`: el modelo predice que el cliente presenta churn.
- `prediction_label`: representación textual de la predicción.
- `churn_probability`: probabilidad estimada de churn.
- `model_version`: versión del modelo utilizada para la predicción.

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

# Base de datos y dashboard

## Requisitos previos

- Docker Desktop instalado y en ejecución.
- Python instalado.
- Entorno virtual creado y activado: command `py -m venv venv` y luego `venv/Scripts/activate`
- Si te da error `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

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

## Verificar conexión a PostgreSQL

```powershell
python -m src.database.test_connection
```

La conexión debe completarse correctamente.

## Ejecutar el dashboard

```powershell
streamlit run dashboard/app.py
```

El dashboard estará disponible en:

`http://localhost:8501`

Para detener el dashboard presionar:

`Ctrl + C`