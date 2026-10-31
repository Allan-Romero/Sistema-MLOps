# Sprint 4 - A2: Registro de la etiqueta real de las predicciones

## Objetivo

Almacenar el resultado verdadero de cada predicción, de modo que se pueda
medir el desempeño real de cada versión del modelo sobre el tráfico que
atendió. Sin esta etiqueta se sabe qué predijo cada versión, pero no cuál
acertó, y la comparación A/B del Sprint 4 no es posible.

## Cambios en el esquema

La tabla `predictions` incorpora dos columnas:

| Columna | Tipo | Contenido |
|---|---|---|
| `etiqueta_real` | `INTEGER` | Resultado verdadero observado: `1` si el cliente abandonó, `0` si no |
| `etiqueta_registrada_at` | `TIMESTAMP` | Momento en que se conoció y registró esa etiqueta |

Ambas admiten nulos: en el momento de la predicción el resultado real
todavía no se conoce, y una predicción sin etiqueta es un estado válido y
esperado. Las consultas existentes no se ven afectadas, porque ninguna
depende de estas columnas.

Para las bases de datos creadas antes del Sprint 4, `schema.sql` incluye dos
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, de manera que el archivo sigue
sirviendo tanto para crear el esquema desde cero como para actualizar una
base existente.

## Función del CRUD

```python
from src.database.crud import registrar_etiqueta_real

registrar_etiqueta_real(prediction_id=42, etiqueta_real=1)
```

Actualiza la predicción indicada y fija `etiqueta_registrada_at` con la marca
de tiempo del servidor. Retorna el id actualizado, o `None` si no existe una
predicción con ese identificador, para que quien la invoque pueda distinguir
el caso sin tener que consultar antes.

## Procedimiento de etiquetado en el entorno del proyecto

La plataforma no tiene un flujo real de retroalimentación: nadie confirma
meses después si el cliente efectivamente abandonó. Por eso las etiquetas se
obtienen de una porción etiquetada del propio dataset, que es la práctica
habitual en un trabajo académico.

El dataset original `data/raw/churn.csv` conserva la columna `Churn` con el
resultado verdadero de cada cliente. El generador de tráfico
(`src/monitoring/generar_trafico.py`) toma clientes reales de ese archivo y
envía al endpoint `/predict` únicamente los 19 predictores, sin la variable
objetivo. Es decir, el modelo nunca ve la respuesta, pero quien genera el
tráfico sí la conoce.

El procedimiento es entonces:

1. Tomar un cliente del dataset, conservando su valor de `Churn`.
2. Enviar sus predictores a `/predict`. La API responde con `prediction_id`.
3. Traducir `Churn` a entero: `Yes` → `1`, `No` → `0`.
4. Registrar esa etiqueta con `registrar_etiqueta_real(prediction_id, etiqueta)`.

```python
import requests
from src.database.crud import registrar_etiqueta_real

respuesta = requests.post("http://localhost:8000/predict", json=cliente, timeout=10)
prediction_id = respuesta.json()["prediction_id"]

registrar_etiqueta_real(prediction_id, 1 if churn_real == "Yes" else 0)
```

### Qué valida y qué no

La comparación entre versiones es válida porque la etiqueta proviene del
dataset y no del modelo: ninguna de las dos versiones comparadas interviene
en su valor, de modo que la medición de aciertos es imparcial entre ambas.

Lo que esta simulación no reproduce es la **latencia de la etiqueta**. En
producción el resultado real se conoce semanas o meses después de la
predicción, mientras que aquí se registra de inmediato. Esa es la razón de
guardar `etiqueta_registrada_at` por separado de `created_at`: deja ver
cuánto tardó en conocerse cada etiqueta y permite, más adelante, restringir
la evaluación de un experimento a las predicciones cuyo resultado ya se
conocía en una fecha dada.

### Porción reservada

Para que la comparación no se apoye en clientes que el modelo ya vio durante
el entrenamiento, el tráfico etiquetado debe tomarse del conjunto de prueba,
que el pipeline aparta y nunca usa para ajustar el modelo.

`data/processed/X_test.csv` no sirve directamente como entrada de la API:
está codificado con One-Hot y la API espera los 19 campos originales. Pero la
partición es reproducible, porque `src/training/preprocess.py` divide **antes**
de codificar y con semilla fija:

```python
from sklearn.model_selection import train_test_split
from src.training.preprocess import cargar_datos, limpiar_datos

df = limpiar_datos(cargar_datos())
y = df["Churn"].map({"No": 0, "Yes": 1})
X = df.drop(columns=["Churn"])

_, X_test, _, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
```

`X_test` queda con las columnas originales, listo para enviarse a `/predict`,
y `y_test` aporta la etiqueta real de cada fila. El dataset completo se sigue
usando para las pruebas de carga y de drift, donde la identidad de los
clientes no altera la conclusión.

## Evidencia

Consulta que distingue las predicciones con y sin etiqueta registrada:

```sql
SELECT
    COUNT(*) AS total,
    COUNT(etiqueta_real) AS con_etiqueta,
    COUNT(*) - COUNT(etiqueta_real) AS sin_etiqueta
FROM predictions
WHERE caso_uso = 'churn';
```

```sql
SELECT id, prediction, probability, etiqueta_real, etiqueta_registrada_at
FROM predictions
ORDER BY id DESC
LIMIT 10;
```
