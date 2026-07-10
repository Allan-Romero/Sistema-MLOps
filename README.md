# Sistema MLOps

Estructura inicial del proyecto creada para mantener el c骴igo organizado desde el inicio y facilitar el trabajo colaborativo.

## Estructura del proyecto

- src/: c骴igo fuente del proyecto.
- data/: datos utilizados por el proyecto.
- models/: modelos entrenados o artefactos generados.
- dashboard/: archivos del dashboard o visualizaciones.
- tests/: pruebas del proyecto.
- docs/: documentaci髇 t閏nica y funcional.
- docker/: configuraci髇 relacionada con Docker.

## Archivos base

- requirements.txt
- docker-compose.yml
- .env.example
- .gitignore

## Dataset inicial del proyecto

Para la primera fase del proyecto se seleccion贸 el dataset p煤blico Telco Customer Churn, orientado a la predicci贸n de abandono de clientes.

El dataset se encuentra almacenado en:

data/raw/telco_customer_churn.csv

La variable objetivo identificada es:

Churn

Este dataset ser谩 utilizado inicialmente para construir el flujo MLOps base del sistema: preprocesamiento, entrenamiento, evaluaci贸n, despliegue mediante API, almacenamiento de predicciones y visualizaci贸n en dashboard.

La descripci贸n completa del dataset se encuentra en:

docs/datasets.md
