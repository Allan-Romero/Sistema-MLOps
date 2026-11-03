# S4-J5 — Entrenamiento reproducible de fraude

## Dataset y motivación

Credit Card Fraud Detection (OpenML 1597), archivo local `data/raw/creditcard.csv`.
284 807 transacciones y 492 fraudes (~0,173 %). No versionar este CSV.
Con este desbalance, una precisión global (accuracy) alta no significa detección de fraude.

## Reutilización de MLOps

Se incorporó un preprocesamiento específico del caso de uso porque las columnas
`Time`, `V1` ... `V28`, `Amount` y `Class` no son las de churn. No se sustituyó
ningún módulo existente de churn. La selección de algoritmos, evaluación y creación
de un modelo candidato mantienen el contrato `predict` / `predict_proba`.
El registro transaccional de versiones, métricas y decisiones de promoción es
**exactamente el servicio `registrar_candidato` de S4-J2**, con `caso_uso='fraude'`.
No se insertan versiones a mano ni se utiliza la versión activa de churn.

## Diseño de evaluación

- Separación estratificada reproducible (seed=42) 70 % entrenamiento, 15 % validación, 15 % prueba.
- Regresión logística con `class_weight='balanced'` y normalización; XGBoost con `scale_pos_weight=negativos/positivos`.
- El umbral de decisión se selecciona exclusivamente en validación para maximizar F1.
- El algoritmo ganador se elige en validación por F1, desempate con average precision.
- El test queda reservado para reportar métricas finales de manera independiente.
- **F1** es la métrica principal de promoción por compatibilidad con S4-J2;
  **PR-AUC/average precision** y **recall** se reportan para interpretar clases
  muy desbalanceadas. No se usan umbrales elegidos sobre el conjunto test.
- El F1 de test del ganador se usa para la política automática J2 (mejora mínima de 0,01).
- Los resultados finales de ambos algoritmos (accuracy, precision, recall, F1, ROC-AUC)
  se almacenan en `model_metrics` cuando se registra el candidato. PR-AUC queda
  en el reporte JSON porque no existe una columna específica en el esquema base.

## Ejecución

1. `python -m src.training.pipeline_multicaso --caso-uso fraude` — entrena y deja candidato/reporte local, no toca PostgreSQL.
2. `python -m src.training.pipeline_multicaso --caso-uso fraude --registrar` — registra en PostgreSQL usando J2.
3. `python -m src.training.pipeline_multicaso --caso-uso churn` mantiene el flujo tradicional de churn sin modificaciones.
4. Comprobar `model_versions`, `model_metrics` y `promotion_decisions` filtrando `caso_uso = 'fraude'`.
5. El siguiente bloque incorpora la API `/predict-fraud` y Swagger.

Artefactos: `models/fraude_model_candidate.joblib`, `models/fraude_model_vX.Y.joblib`,
`reports/s4_j5_fraude_metrics.json`. No versionar modelos binarios ni datos crudos.
