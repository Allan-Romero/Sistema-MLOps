# S4-J5 — Registro y API de fraude

## Evidencias de entrenamiento real

Dataset Credit Card Fraud Detection, OpenML 1597: 284.807 filas, 492 positivas.
Entrenamiento estratificado 70/15/15, modelo elegido con datos de validación.

| Modelo | F1 val | PR-AUC val | F1 test | PR-AUC test |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.7778 | 0.6301 | 0.8406 | 0.7929 |
| XGBoost | 0.7840 | 0.7903 | 0.7874 | 0.8009 |

Se seleccionó XGBoost **antes de consultar los resultados de test**, usando
F1 de validación como métrica principal. PR-AUC complementa al F1 por el fuerte
desbalance de clases; accuracy aislada sería engañosa. El umbral se ajustó
sobre validación, no sobre test. La ventaja de Logistic Regression en F1 de test
se informa, no se oculta ni cambia retroactivamente la selección.

## Registro y reutilización

1. `python -m src.training.pipeline_multicaso --caso-uso fraude --registrar`
   reutiliza el servicio de promoción J2, crea `fraude_model_vX.Y.joblib`,
   registra todas las métricas `model_metrics` y audita en `promotion_decisions`.
   La primera versión del caso de uso se promueve si no hay una anterior.
2. La API **POST `/predict-fraud`** usa `obtener_modelo_activo('fraude')` de J1,
   y registra la versión utilizada en `predictions`, con `caso_uso='fraude'`.
3. **GET `/model-version/fraude`** muestra el estado actual; `GET /model-version`
   continúa informando sobre churn (sin cambios a su contrato).
4. El esquema Swagger pide 30 variables de fraude (`Time`, `V1`..`V28`, `Amount`)
   y **rechaza la etiqueta real `Class`**; evitar fuga de información.
5. Reutiliza el contrato de carga de modelos y PostgreSQL existentes. Los modelos
   binarios son artefactos locales y no deben incluirse en Git.

## Prueba real de punta a punta

En PowerShell (desde la raíz del proyecto):

```powershell
python -m src.training.pipeline_multicaso --caso-uso fraude --registrar
Invoke-RestMethod http://localhost:8000/model-version/fraude | ConvertTo-Json

$body = .\venv\Scripts\python.exe -c "import pandas as pd; d=pd.read_csv('data/raw/creditcard.csv',nrows=1).drop(columns=['Class']); print(d.iloc[0].to_json())"
Invoke-RestMethod -Uri http://localhost:8000/predict-fraud -Method Post -ContentType 'application/json' -Body $body | ConvertTo-Json
```

En Docker Compose la API tiene montado `./models:/app/models:ro` y `./src:/app/src`.
Verificar que `xgboost` esté instalado en `docker/requirements-api.txt` y que
`src/training/fraud_model.py` sea accesible en el contenedor.

Consultas útiles:

```sql
SELECT caso_uso, version, algoritmo, estado, valor_metrica
FROM model_versions WHERE caso_uso IN ('fraude','churn') ORDER BY caso_uso,id DESC;

SELECT caso_uso, model_version, algoritmo, f1_score
FROM model_metrics WHERE caso_uso='fraude' ORDER BY id DESC;

SELECT caso_uso, model_version, prediction, probability
FROM predictions WHERE caso_uso='fraude' ORDER BY id DESC LIMIT 5;
```

No registrar dos veces el mismo candidato. Los artefactos `.joblib` deben venir de
fuentes confiables (joblib usa pickle).
