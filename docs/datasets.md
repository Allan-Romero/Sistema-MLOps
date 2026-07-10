# Selección de datasets del proyecto Sistema-MLOps

## Contexto del proyecto

El proyecto Sistema-MLOps tiene como objetivo desarrollar una plataforma MLOps automatizada para gestionar el ciclo de vida de modelos de clasificación. Para ello se requiere trabajar con datasets públicos que permitan entrenar, evaluar, desplegar y monitorear modelos de machine learning.

## Dataset seleccionado para iniciar

### Nombre

Telco Customer Churn

### Origen

IBM Sample Dataset / Kaggle

### Enlaces de referencia

- IBM GitHub: https://github.com/IBM/telco-customer-churn-on-icp4d
- Kaggle: https://www.kaggle.com/datasets/blastchar/telco-customer-churn

### Archivo almacenado en el repositorio

data/raw/telco_customer_churn.csv

### Descripción

El dataset contiene información de clientes de una empresa de telecomunicaciones. Incluye datos demográficos, servicios contratados, información de facturación, tipo de contrato, método de pago, cargos mensuales y cargos totales.

### Tipo de problema

Clasificación binaria.

### Variable objetivo

Churn

### Interpretación de la variable objetivo

- Yes: el cliente abandonó el servicio.
- No: el cliente no abandonó el servicio.

### Justificación de selección

Este dataset fue seleccionado porque cumple con los criterios definidos para el proyecto:

- Es público.
- Tiene suficientes registros para entrenamiento y prueba.
- Tiene variables útiles para análisis y modelado.
- Permite resolver un problema de clasificación binaria.
- Es adecuado para construir un flujo MLOps completo: carga de datos, limpieza, entrenamiento, evaluación, versionamiento, despliegue mediante API, monitoreo y dashboard.

## Dataset secundario propuesto

### Nombre

Credit Card Fraud Detection

### Origen

Kaggle

### Enlace de referencia

https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

### Tipo de problema

Clasificación binaria.

### Variable objetivo

Class

### Interpretación de la variable objetivo

- 0: transacción legítima.
- 1: transacción fraudulenta.

### Justificación

Este dataset se propone como segundo caso de validación de la plataforma, debido a que permite evaluar el sistema en un escenario de detección de fraude. Se recomienda utilizarlo en fases posteriores, después de tener funcionando el primer flujo MLOps con el dataset de churn.

## Decisión final

Para la primera fase del proyecto se utilizará el dataset Telco Customer Churn.

El dataset Credit Card Fraud Detection quedará como segundo caso de uso para validar la plataforma en una fase posterior.
