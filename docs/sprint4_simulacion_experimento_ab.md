# Sprint 4: Simulación del tráfico de un experimento A/B

## Objetivo

Validar las consultas de comparación (S4-A3) y la sección de A/B testing del
dashboard (S4-A4) antes de que exista el enrutamiento real de tráfico, que
llega con S4-J3 dentro de la API.

## Qué se simula y qué no

Lo único simulado es **el reparto del tráfico**: el sorteo que decide qué
versión atiende a cada cliente, que hoy hace el script y mañana hará la API.

Todo lo demás son datos reales del proyecto:

| Elemento | Origen |
|---|---|
| Clientes | Conjunto de prueba, el 20 % que el pipeline aparta y el modelo nunca vio |
| Predicción de la versión de control | `models/churn_model_v1.joblib`, el modelo activo en producción |
| Predicción de la versión candidata | `models/xgboost_v1.joblib`, el otro algoritmo que entrenó el pipeline |
| Etiqueta real | Columna `Churn` del dataset, según el procedimiento de `sprint4_a2_etiquetas_reales.md` |

Ninguna métrica se inventa: las que muestra el dashboard son el desempeño
efectivo de Logistic Regression y XGBoost sobre datos que ninguno de los dos
vio durante el entrenamiento.

## Reproducibilidad

Requiere un experimento activo en la tabla `experiments`, cuyas dos versiones
estén mapeadas a un modelo en `MODELOS_POR_VERSION`:

```sql
INSERT INTO experiments (caso_uso, version_a, version_b, porcentaje_trafico_b)
VALUES ('churn', 'v1', 'v1.1', 20);
```

```powershell
python -m src.monitoring.simular_trafico_ab 300
```

El script lee el experimento activo, reparte los clientes según el porcentaje
configurado, guarda cada predicción con la versión que la atendió y registra
la etiqueta real. Acepta la cantidad de clientes y la semilla del sorteo como
argumentos, de modo que una misma semilla produce siempre el mismo reparto.

## Resultado observado

Con 300 clientes y un 20 % de tráfico configurado para la candidata:

| Versión | Rol | Muestra etiquetada | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---|---|---|---|---|---|---|
| v1 | Control | 322 | 0.792 | 0.613 | 0.548 | 0.579 | 0.829 |
| v1.1 | Candidata | 66 | 0.864 | 0.733 | 0.688 | 0.710 | 0.924 |

La candidata queda por encima en todas las métricas, lo que es coherente con
la comparación de modelos del Sprint 2: XGBoost obtuvo mejor desempeño que
Logistic Regression, y aun así el modelo promovido fue el segundo por la
regla de selección vigente.

El control acumula más muestra que el 80 % configurado porque la ventana del
experimento incluye predicciones anteriores a la simulación, atendidas por la
versión activa. Es la misma situación que se dará en producción cuando un
experimento arranque sobre una versión que ya venía atendiendo tráfico.

## Limpieza

Las predicciones simuladas quedan registradas como cualquier otra. Para
descartarlas basta con cerrar el experimento y borrar las predicciones de la
versión candidata:

```sql
UPDATE experiments SET estado = 'cancelado', ended_at = NOW() WHERE id = 1;
DELETE FROM predictions WHERE model_version = 'v1.1';
```
