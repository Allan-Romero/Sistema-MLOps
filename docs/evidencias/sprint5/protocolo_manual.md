# Protocolo del escenario manual

Guía de las seis actividades del ciclo de vida del modelo hechas a mano, sin
el pipeline. Acompaña a `scripts/cronometro_manual.py`, que las cronometra.

**Cómo usarla.** El cronómetro va en una pestaña, el trabajo en otras dos: una
consola de Python y una sesión de `psql`. Para cada actividad: pulsas Enter en
el cronómetro, haces el trabajo escribiéndolo tú, y pulsas Enter al terminar.

**Lo que se mide.** El tiempo de ejecutar el procedimiento conocido,
escribiéndolo a mano. No incluye diseñar la solución ni depurar errores de
concepto, de modo que el número es una **cota inferior** del costo real del
trabajo manual: en la práctica, quien no tenga el procedimiento delante
tardará más.

**Qué no hacer.** Copiar y pegar de `src/`, ni ejecutar los módulos del
proyecto. La comparación pierde sentido si el escenario manual usa la
automatización que se quiere comparar.

## Preparación, antes de arrancar el cronómetro

Las pestañas abiertas y una carpeta para no pisar los artefactos del pipeline:

```powershell
mkdir data\processed\manual
```

---

## 1. Preprocesamiento

En la consola de Python. Carga el dataset, limpia, codifica, divide y guarda.

```python
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("data/raw/churn.csv")
df = df.drop(columns=["customerID"])
df["TotalCharges"] = pd.to_numeric(
    df["TotalCharges"].astype(str).str.strip().replace("", "0")
)
df["Churn"] = df["Churn"].map({"No": 0, "Yes": 1})

y = df["Churn"]
X = df.drop(columns=["Churn"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

categoricas = X_train.select_dtypes(include="object").columns.tolist()
X_train = pd.get_dummies(X_train, columns=categoricas, dtype=int)
X_test = pd.get_dummies(X_test, columns=categoricas, dtype=int)
X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

X_train.to_csv("data/processed/manual/X_train.csv", index=False)
X_test.to_csv("data/processed/manual/X_test.csv", index=False)
y_train.to_csv("data/processed/manual/y_train.csv", index=False)
y_test.to_csv("data/processed/manual/y_test.csv", index=False)

print(X_train.shape, X_test.shape)
```

Termina cuando los cuatro archivos están escritos.

---

## 2. Entrenamiento

Misma consola, aprovechando las variables que ya tienes en memoria.

```python
import joblib
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

logistica = LogisticRegression(max_iter=1000)
logistica.fit(X_train, y_train)

xgboost = XGBClassifier(eval_metric="logloss", random_state=42)
xgboost.fit(X_train, y_train)

joblib.dump(logistica, "models/manual_logistic.joblib")
joblib.dump(xgboost, "models/manual_xgboost.joblib")
```

Termina cuando los dos `.joblib` están en disco.

---

## 3. Evaluación comparativa

Las cinco métricas de cada algoritmo sobre el conjunto de prueba, y la
decisión de cuál sería el candidato.

```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score)

for nombre, modelo in [("logistica", logistica), ("xgboost", xgboost)]:
    pred = modelo.predict(X_test)
    prob = modelo.predict_proba(X_test)[:, 1]
    print(nombre,
          round(accuracy_score(y_test, pred), 4),
          round(precision_score(y_test, pred), 4),
          round(recall_score(y_test, pred), 4),
          round(f1_score(y_test, pred), 4),
          round(roc_auc_score(y_test, prob), 4))
```

Anota las cifras del ganador por F1: las necesitas en la actividad 4.
Termina cuando tengas la decisión tomada.

---

## 4. Registro de la versión

En `psql`. Se usa la versión `v9.9` para no chocar con las del pipeline, y
estado `historica` porque la base solo admite una versión activa por caso de
uso; la activación es la actividad siguiente.

```sql
INSERT INTO model_metrics
    (caso_uso, model_version, algoritmo, accuracy, precision, recall, f1_score, roc_auc)
VALUES ('churn', 'v9.9', 'logistic_regression', 0.8055, 0.6563, 0.5615, 0.6052, 0.8428);

INSERT INTO model_versions
    (caso_uso, version, algoritmo, metrica_principal, valor_metrica, estado)
VALUES ('churn', 'v9.9', 'logistic_regression', 'f1_score', 0.6052, 'historica');

SELECT id, version, algoritmo, valor_metrica, estado
FROM model_versions ORDER BY id DESC LIMIT 3;
```

Sustituye las cifras por las que midió tu modelo. Termina cuando el `SELECT`
confirme los dos registros.

---

## 5. Promoción a producción

Tres pasos: dejar el artefacto con el nombre que la API espera, cambiar los
estados en la base y comprobar que la API responde con la versión nueva.

En PowerShell:

```powershell
Copy-Item models\manual_logistic.joblib models\churn_model_v9.9.joblib
```

En `psql`:

```sql
UPDATE model_versions SET estado = 'historica'
WHERE caso_uso = 'churn' AND estado = 'activa';

UPDATE model_versions SET estado = 'activa'
WHERE caso_uso = 'churn' AND version = 'v9.9';
```

En PowerShell, para comprobar:

```powershell
Invoke-RestMethod http://localhost:8000/model-version | Select-Object model_version
```

Termina cuando la respuesta diga `v9.9`.

---

## 6. Detección de drift

Extraer los datos de producción, calcular el PSI de las tres variables
numéricas y registrar las alertas.

En PowerShell, para sacar los datos:

```powershell
docker exec mlops_postgres psql -U mlops_user -d mlops_db -t -A -c "SELECT input_data FROM predictions WHERE caso_uso = 'churn' ORDER BY created_at DESC LIMIT 1000" > produccion.json
```

En la consola de Python:

```python
import json
import numpy as np
import pandas as pd

# PowerShell 5.1 escribe las redirecciones con > en UTF-16, no en UTF-8
filas = [json.loads(l) for l in open("produccion.json", encoding="utf-16") if l.strip()]
actual = pd.DataFrame(filas)

referencia = pd.read_csv("data/raw/churn.csv")
referencia["TotalCharges"] = pd.to_numeric(referencia["TotalCharges"], errors="coerce")
referencia = referencia.dropna(subset=["TotalCharges"])

def psi(ref, act, bins=10):
    cortes = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    cortes[0], cortes[-1] = -np.inf, np.inf
    p = np.histogram(ref, bins=cortes)[0] / len(ref)
    q = np.histogram(act, bins=cortes)[0] / len(act)
    p, q = np.clip(p, 1e-6, None), np.clip(q, 1e-6, None)
    return float(np.sum((q - p) * np.log(q / p)))

for columna in ["tenure", "MonthlyCharges", "TotalCharges"]:
    valor = psi(referencia[columna], pd.to_numeric(actual[columna]))
    nivel = "alto" if valor >= 0.25 else "medio" if valor >= 0.10 else "bajo"
    print(columna, round(valor, 4), nivel)
```

En `psql`, una alerta por cada variable con nivel medio o alto:

```sql
INSERT INTO alerts (caso_uso, variable_afectada, nivel_drift, descripcion)
VALUES ('churn', 'TotalCharges', 'medio', 'PSI = 0.13 calculado a mano');
```

Si ninguna variable supera 0.10, no se inserta nada y se anota que no hubo
drift. Termina cuando las alertas estén escritas o se confirme que no hay.

---

## Limpieza posterior

La medición deja rastro en la base y en disco. Para devolver el sistema a su
estado anterior:

```sql
UPDATE model_versions SET estado = 'historica' WHERE caso_uso = 'churn' AND version = 'v9.9';
UPDATE model_versions SET estado = 'activa' WHERE caso_uso = 'churn' AND version = 'v1.0';
DELETE FROM model_metrics WHERE model_version = 'v9.9';
DELETE FROM model_versions WHERE version = 'v9.9';
```

Y en disco: `models\churn_model_v9.9.joblib`, `models\manual_*.joblib`,
`data\processed\manual\` y `produccion.json`.
