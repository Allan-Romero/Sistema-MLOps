# Sistema MLOps

Estructura inicial del proyecto creada para mantener el c�digo organizado desde el inicio y facilitar el trabajo colaborativo.

## Estructura del proyecto

- src/: c�digo fuente del proyecto.
- data/: datos utilizados por el proyecto.
- models/: modelos entrenados o artefactos generados.
- dashboard/: archivos del dashboard o visualizaciones.
- tests/: pruebas del proyecto.
- docs/: documentaci�n t�cnica y funcional.
- docker/: configuraci�n relacionada con Docker.

## Archivos base

- requirements.txt
- docker-compose.yml
- .env.example
- .gitignore

## Dataset inicial del proyecto

Para la primera fase del proyecto se seleccionó el dataset público Telco Customer Churn, orientado a la predicción de abandono de clientes.

El dataset se encuentra almacenado en:

data/raw/telco_customer_churn.csv

La variable objetivo identificada es:

Churn

Este dataset será utilizado inicialmente para construir el flujo MLOps base del sistema: preprocesamiento, entrenamiento, evaluación, despliegue mediante API, almacenamiento de predicciones y visualización en dashboard.

La descripción completa del dataset se encuentra en:

docs/datasets.md

## Base de datos y dashboard

### Requisitos previos

- Docker Desktop instalado y en ejecución
- Python 3.11
- Entorno virtual creado y activado

### 1. Configurar variables de entorno

Copiar la plantilla de credenciales y ajustar los valores:

```bash
cp .env.example .env
```

### 2. Levantar la base de datos

```bash
docker-compose up -d
```

Verificar que el contenedor esté corriendo:

```bash
docker ps
```

### 3. Crear las tablas

```bash
docker exec -i mlops_postgres psql -U mlops_user -d mlops_db < src/database/schema.sql
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Verificar la conexión

```bash
python -m src.database.test_connection
```

Debe mostrar el mensaje: `Conexión exitosa`

### 6. Ejecutar el dashboard

```bash
streamlit run dashboard/app.py
```

El dashboard queda disponible en `http://localhost:8501`

Para detenerlo, presionar `Ctrl + C` en la terminal.
