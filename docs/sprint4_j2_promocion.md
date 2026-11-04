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

Antes de las migraciones, dejar una sola versión activa por caso de uso. La
migración 001 se detiene a propósito si encuentra más de una, y las bases
creadas antes del Sprint 4 pueden tener varias, porque el `persist_results`
anterior insertaba una fila `activa` en cada ejecución del pipeline:

```sql
UPDATE model_versions SET estado = 'historica'
WHERE estado = 'activa' AND id NOT IN (
    SELECT DISTINCT ON (caso_uso) id FROM model_versions
    WHERE estado = 'activa' ORDER BY caso_uso, created_at DESC, id DESC);
```

En PowerShell, desde la raíz del proyecto, con PostgreSQL activo:

```powershell
Get-Content .\src\database\migrations\001_unique_active_model.sql -Raw | docker compose exec -T postgres psql -U joseph -d mlops_db -v ON_ERROR_STOP=1
Get-Content .\src\database\migrations\002_promotion_decisions.sql -Raw | docker compose exec -T postgres psql -U joseph -d mlops_db -v ON_ERROR_STOP=1
```

Falta un paso más, y sin él la API deja de responder: el artefacto de la
versión activa debe llamarse como exige la convención nueva,
`models/<caso_uso>_model_<version>.joblib`. Un modelo promovido a mano antes
del Sprint 4 se llama `churn_model_v1.joblib`, y con la versión activa `v1.0`
el endpoint responde 503 con «No existe el artefacto de la versión v1.0».

```powershell
Copy-Item models\churn_model_v1.joblib models\churn_model_v1.0.joblib
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
