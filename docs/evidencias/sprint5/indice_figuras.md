# S5-A1 — Índice de evidencias visuales

Issue #114. Capturas tomadas el 6 de noviembre de 2026 sobre la rama
`feature/results-doc`, con base en `develop` (`3dfec6d`).

Todas las figuras provienen de ejecuciones del sistema, no de registros
insertados a mano. Antes de capturar se eliminaron de la base de desarrollo
los despliegues, el experimento y las predicciones que se habían insertado
durante las pruebas del Sprint 4, y se volvió a ejecutar el pipeline y a
generar tráfico contra la API.

## Numeración

Las figuras 11 a 20 corresponden a los marcadores de posición del documento
de grado. La 21 es el gráfico de tiempos que produce S5-A2. Las tres
evidencias del Sprint 4 se numeran a continuación, de la 22 a la 24; si el
documento usa otra numeración, basta con renombrar los archivos.

## Figuras

| Figura | Archivo | Qué evidencia | Cómo se generó |
|---|---|---|---|
| 11 | `figuras/sprint5/figura-11-esquema-base-datos.png` | Las siete tablas del esquema con sus columnas, tipos y obligatoriedad | Consulta a `information_schema.columns` en el contenedor `mlops_postgres` |
| 12 | `figuras/sprint5/figura-12-ejecucion-pipeline.png` | Las ocho etapas del pipeline de churn y la decisión de promoción | `python -m src.training.run_pipeline` |
| 13 | `figuras/sprint5/figura-13-mlflow-experimentos.png` | Las 19 ejecuciones registradas con accuracy, F1 y ROC-AUC, y las versiones del modelo asociadas | Interfaz de MLflow, `http://localhost:5000` |
| 14 | `figuras/sprint5/figura-14-model-registry.png` | El modelo registrado `churn-model` con sus versiones y etiquetas de algoritmo, métrica y estado | Model Registry de MLflow |
| 15 | `figuras/sprint5/figura-15-swagger-endpoints.png` | Los siete endpoints publicados, incluidos los de fraude | Swagger UI, `http://localhost:8000/docs` |
| 16 | `figuras/sprint5/figura-16-respuesta-prediccion.png` | Petición y respuesta reales de `/predict`, con la versión que atendió y el identificador persistido | Ejecución desde Swagger |
| 17 | `figuras/sprint5/figura-17-dashboard-general.png` | Selector de caso de uso y métricas del modelo activo | Dashboard, `http://localhost:8501` |
| 18 | `figuras/sprint5/figura-18-comparacion-modelos.png` | Comparación de Logistic Regression y XGBoost con la métrica de decisión | Dashboard |
| 19 | `figuras/sprint5/figura-19-historial-versiones.png` | Historial de versiones con sus estados: una activa y las demás descartadas o históricas | Dashboard |
| 20 | `figuras/sprint5/figura-20-workflow-ci.png` | Ejecuciones del workflow de integración continua en verde | GitHub Actions del repositorio |
| 22 | `figuras/sprint5/figura-22-experimento-ab.png` | Experimento A/B en curso: tráfico configurado frente al obtenido, desempeño de cada grupo con su muestra y la ventaja señalada | Entorno de validación aislado (ver nota) |
| 23 | `figuras/sprint5/figura-23-historial-despliegues.png` | Bitácora con cinco promociones y un rollback, con el motivo de cada operación y la versión en producción | Entorno de validación aislado (ver nota) |
| 24 | `figuras/sprint5/figura-24-dashboard-fraude.png` | El dashboard operando sobre el segundo caso de uso: promociones, rollback y versión en producción de fraude | Entorno de validación aislado (ver nota) |

## Nota sobre las figuras 22 y 23

El experimento A/B y el rollback no pueden reproducirse con los datos reales
de churn: la versión activa `v1.0` tiene un F1 de 0,6052 y ningún candidato
del pipeline lo supera por el umbral de 0,01 exigido, de modo que no hay
promoción que revertir. Forzar una sería fabricar la evidencia.

Esas dos figuras se tomaron entonces en el **entorno de validación aislado**
del proyecto (`docker-compose.ci.yml` con `scripts/e2e_deployment.py`), donde
los servicios, la API, la base de datos y el dashboard son los mismos del
sistema y las operaciones las ejecutan los servicios reales de promoción,
experimento y reversión. Lo sintético ahí son los modelos y el tráfico, que
son pequeños y están construidos para que una versión gane y otra pierda.

Al presentarlas conviene decirlo así: evidencian que el mecanismo de
despliegue inteligente opera, no el desempeño de los modelos del proyecto,
que está en las figuras 13, 14 y 18.

El reparto observado fue de 219 predicciones para el control y 101 para la
candidata sobre 320 peticiones, frente al 30 % configurado.

### Para rehacer la figura 24 con el modelo real de fraude

Hace falta el CSV de tarjetas de crédito, que no se versiona. Descargarlo de
OpenML con `fetch_openml(data_id=1597)` **no sirve**: esa copia trae 29
variables y el contrato del pipeline exige 30, porque le falta `Time`.

```
ValueError -> Columnas de fraude faltantes: ['Time']
```

El archivo que usó S5-J5 para entrenar sí la incluye; su SHA-256 está en
`comparacion_algoritmos.json`. Con ese archivo en `data/raw/creditcard.csv`:

```powershell
python -m src.training.pipeline_multicaso --caso-uso fraude --registrar
```

y después capturar el dashboard con el caso de fraude seleccionado.

## Evidencias en texto

El texto que respalda las figuras generadas a partir de salidas de consola se
versiona junto a ellas, de modo que la imagen pueda reconstruirse:

| Archivo | Contenido |
|---|---|
| `figura-11-esquema-base-datos.txt` | Salida de la consulta al catálogo de PostgreSQL |
| `figura-12-pipeline-churn.txt` | Salida completa del pipeline |
| `figura-12-pipeline-churn-resumen.txt` | Extracto que se usó para la figura |
| `deteccion-drift-churn.txt` | Ejecución del detector de drift sobre el tráfico de control |

Las figuras de consola se regeneran con:

```powershell
python docs/figuras/sprint5/render_consola.py <entrada.txt> <salida.png> --titulo "<rótulo>"
```

## Tratamiento de datos sensibles

- Las rutas absolutas del equipo se sustituyeron por `<ruta-del-proyecto>` en
  las evidencias de texto antes de renderizar las figuras.
- En la figura 13 se ocultaron las columnas `Source` y `Dataset` de MLflow,
  que mostraban rutas locales.
- Ninguna captura incluye credenciales: el contenido de `.env` no aparece en
  ninguna pantalla capturada.
