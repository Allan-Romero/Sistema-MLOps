# S4-J2 — Promoción automática

La métrica principal para churn es **F1-score**. El umbral mínimo de mejora es
**0.01 puntos absolutos** (un punto porcentual de F1), definido en
`src/training/promotion_policy.py`. Este es un criterio operativo para
versionar y desplegar, no equivale a una prueba de significancia estadística.

- Si no existe versión activa, se promueve la primera candidata.
- Si F1(candidato) - F1(activa) >= 0.01, se promueve el candidato.
- En caso contrario, la candidata se registra como `descartada` y la versión
  activa sigue atendiendo tráfico.
- La versión se genera bajo bloqueo consultando `model_versions` y el artefacto
  se guarda como `models/churn_model_vX.Y.joblib`, sin sobrescribir versiones.
- Versión, métricas comparativas de los dos algoritmos y auditoría
  (`promotion_decisions`) se escriben en **una única transacción**.
- El índice parcial `uq_model_versions_active_caso` impide tener más de un
  registro activo por caso de uso.

## Preparación de una base existente

En PowerShell, desde la raíz del proyecto, con PostgreSQL activo:

```powershell
Get-Content .\src\database\migrations\001_unique_active_model.sql -Raw | docker compose exec -T postgres psql -U joseph -d mlops_db -v ON_ERROR_STOP=1
Get-Content .\src\database\migrations\002_promotion_decisions.sql -Raw | docker compose exec -T postgres psql -U joseph -d mlops_db -v ON_ERROR_STOP=1
```

`docker-compose.yml` ejecuta `schema.sql` al inicializar un volumen nuevo,
y las migraciones 001–003 al crear un volumen nuevo. Los volúmenes existentes
requieren aplicar las migraciones explícitamente. Las promociones aprobadas
también se registran en `deployments` dentro de la misma transacción.

## Validación del caso existente (sin entrenamiento nuevo)

`models/model_selection.json` y `models/model_comparison.json` reportan F1
`0.6031746031746031` para la regresión logística, idéntico al modelo activo
`v1.0`; se espera que se cree `v1.1` como `descartada`.

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -q
.\venv\Scripts\python.exe -m src.database.persist_results
```

Verificar luego `model_versions`, `model_metrics`, `promotion_decisions` y
que `/predict` continúe respondiendo con `model_version=v1.0`.

**Limitaciones:** Los archivos no participan en transacciones SQL. La API
usa la versión activa de PostgreSQL; la numeración/alias de MLflow sigue
independiente y debe coordinarse cuando se implemente una política de alias
única. No ejecutar dos pipelines completos a la vez: comparten archivos
intermedios (`churn_model_candidate.joblib`, JSON y modelos de entrenamiento).
