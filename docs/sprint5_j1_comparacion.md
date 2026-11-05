# S5-J1 — Comparación de algoritmos y discusión de resultados

Issue #110. Fecha de preparación: 5 de noviembre de 2026. Estrategia adoptada: **reportar como hallazgo**, sin reajustar modelos para favorecer un algoritmo ni modificar producción.

## Ejecución y trazabilidad

Se entrenaron de nuevo ambos algoritmos sobre los dos CSV reales. Python 3.14.5; scikit-learn 1.9.1; XGBoost 3.2.0. Se hizo una ejecución con semilla 42 por caso, sin replicaciones ni intervalos de confianza. Los resultados no prueban superioridad general ni desempeño en una organización en operación.

Los hashes SHA-256 de datasets y fuentes, hiperparámetros completos, iteraciones, advertencias y tamaños de partición están en [comparacion_algoritmos.json](evidencias/sprint5/comparacion_algoritmos.json). La [tabla CSV](evidencias/sprint5/metricas_algoritmos.csv) conserva precisión completa. El commit base identifica el estado previo del repositorio; los hashes identifican exactamente los archivos de trabajo ejecutados.

```powershell
python -m scripts.comparar_algoritmos_s5 --churn data/raw/churn.csv --fraude data/raw/creditcard.csv
```

El script importa las factorías productivas de modelos y reutiliza la limpieza y partición existentes; captura advertencias, no las elimina. Produce reporte JSON, CSV y stdout en `reports/sprint5/comparacion/`. No inicia servicios, no llama a MLflow, no guarda modelos ni modifica PostgreSQL. El refactor `construir_modelo()` conserva todos los hiperparámetros históricos.

## Tabla final de esta ejecución

| Caso | Algoritmo | Conjunto | Accuracy | Precision | Recall | F1 | ROC-AUC | AP / PR-AUC | Umbral |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| churn | logistic_regression | test | 0.804826 | 0.655172 | 0.558824 | 0.603175 | 0.842804 | 0.636337 | 0.500000000 |
| churn | xgboost | test | 0.800568 | 0.655518 | 0.524064 | 0.582467 | 0.845148 | 0.655549 | 0.500000000 |
| fraude | logistic_regression | validacion | 0.999251 | 0.800000 | 0.756757 | 0.777778 | 0.968390 | 0.630087 | 0.999999872 |
| fraude | logistic_regression | test | 0.999485 | 0.906250 | 0.783784 | 0.840580 | 0.967972 | 0.792873 | 0.999999872 |
| fraude | xgboost | validacion | 0.999251 | 0.808824 | 0.743243 | 0.774648 | 0.985024 | 0.779360 | 0.983981192 |
| fraude | xgboost | test | 0.999391 | 0.887097 | 0.743243 | 0.808824 | 0.963687 | 0.798290 | 0.983981192 |

Las cifras se redondean solo para presentación. AP es `average_precision_score`; no se afirma que sea la integral trapezoidal de la curva precision-recall. Las filas de validación de fraude sirven para elegir; las de test sirven para informar desempeño de la selección fijada.

## Churn: modelo base competitivo y convergencia

Se limpiaron 7043 filas, con 1869 positivos. Se conserva la división estratificada 80/20: 5634 entrenamiento y 1409 test. La codificación aprende columnas del entrenamiento y alinea las de test. Ambos algoritmos se evalúan en las mismas filas y usando su `predict()` productivo (umbral nominal 0,5).

La regresión logística puede obtener mejor F1 mientras XGBoost obtiene mejor ROC-AUC: F1 depende de las decisiones binarias de un punto operativo; ROC-AUC evalúa el ordenamiento de scores a través de umbrales. Esa combinación no demuestra por sí misma que el umbral usado sea óptimo o incorrecto. No se ajusta ahora un umbral con test para mejorar retrospectivamente el resultado.

Advertencia de convergencia observada en LR: **True**. Iteraciones registradas: `[1000]`. La configuración histórica usa `LogisticRegression(max_iter=1000, random_state=42)` sin escalado. La advertencia señala que no se satisfizo el criterio de convergencia: no invalida que el código haya producido predicciones, pero limita la interpretación de los coeficientes y de la comparación. No se declara resuelta; se documenta, como admite la issue.

El pipeline histórico selecciona por F1 usando el mismo test que luego presenta. Por eso el resultado de churn es una comparación descriptiva de esa partición y tiene sesgo de selección potencial; no es una estimación independiente después de elegir modelo. El trabajo futuro es separar train/validación/test y evaluar escalado/convergencia y ajustes únicamente en train/validación. No se cambia la metodología histórica sin validación académica.

## Fraude: selección separada del test

Se usan 284807 filas y 492 fraudes, con partición estratificada 70/15/15: `{'train': 199364, 'validacion': 42721, 'test': 42722}`. LR incorpora StandardScaler y class_weight balanced; XGBoost incorpora scale_pos_weight calculado solo con entrenamiento. Ambos ajustan su umbral exclusivamente con validación y el algoritmo se elige allí por F1, con AP como desempate. Seleccionado en validación: **logistic_regression**.

Que otro algoritmo obtenga mayor F1 en test no autoriza cambiar la selección usando ese conjunto. El reporte muestra ambos resultados y conserva la decisión previa. La variación entre particiones y el escaso número de positivos aconsejan no presentar esa diferencia como evidencia de superioridad general.

La promoción operativa del código existente compara métricas de test del candidato con el histórico activo; no se modificó aquí. Repetir selecciones/promociones mirando ese mismo test puede erosionar su independencia. No confundir la regla operativa con una validación estadística ni con un experimento productivo.

## Métricas elegidas y alcance

Se conserva F1 de la clase positiva como métrica principal para interoperar con la política existente. F1 combina precisión y recall; no mide por sí sola calibración ni costes económicos. En fraude, accuracy es especialmente insuficiente por el desbalance y se reportan además recall y AP; ROC-AUC queda como complemento. En una aplicación real habría que acordar el coste de falsos positivos y falsos negativos antes de fijar umbral.

Las cifras históricas de #110 (0,6052/0,5891) no se copian como resultados de esta ejecución: los reportes locales y la nueva ejecución son fuentes distintas. La fecha, versiones y hashes permiten distinguirlas. No sobrescribir evidencia histórica ni mezclar celdas de ejecuciones diferentes.

## Texto propuesto para el documento académico

> En la comparación realizada sobre datasets públicos, el modelo de regresión logística resultó competitivo frente a XGBoost. Las diferencias observadas dependen del caso de uso, la partición y la métrica elegida. La selección de fraude se fijó mediante validación antes de observar el test; en churn se conservó el procedimiento histórico, cuya reutilización del test para seleccionar modelo se reconoce como limitación. Estos resultados demuestran la capacidad de la plataforma para comparar y registrar algoritmos sin suponer de antemano la superioridad de uno de ellos. La advertencia de convergencia de churn se conserva y declara explícitamente.

Este texto es una propuesta para revisión de los autores y del asesor; no se modificó el documento oficial de tesis ni sus cinco objetivos. Completar la aprobación/revisión cruzada y publicar evidencias antes de cerrar #110.

## Referencias técnicas

- [scikit-learn: ConvergenceWarning](https://scikit-learn.org/stable/modules/generated/sklearn.exceptions.ConvergenceWarning.html).
- [scikit-learn: umbrales de decisión y separación de datos](https://scikit-learn.org/stable/modules/classification_threshold.html).
- [scikit-learn: métricas de evaluación](https://scikit-learn.org/stable/modules/model_evaluation.html).
