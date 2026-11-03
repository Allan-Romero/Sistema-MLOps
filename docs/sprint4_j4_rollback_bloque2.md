# S4-J4 — Bloque 2. Observaciones reales y disparador de rollback

## Funcionalidad

- `rollback_observations.py` calcula F1 a partir de `predictions.prediction` y `predictions.etiqueta_real`, nunca del entrenamiento.
- Si `etiqueta_real` no existe, no hay promoción auditada o faltan observaciones, el sistema **no ejecuta rollback**.
- A/B: se requieren al menos 30 observaciones etiquetadas por versión dentro del intervalo de un experimento cerrado reciente. Solo se revierte si la candidata B está activa, es la versión de una promoción auditada desde A y su F1 está al menos 0.01 por debajo del control A.
- Drift: exige una alerta `alto` no revisada posterior a la promoción en los últimos 7 días, al menos 30 observaciones etiquetadas tanto de la versión activa como de la anterior, F1 actual < 0.55 y F1 anterior >= 0.55.
- La revisión es **solo lectura por defecto**. `--aplicar` delega en `ejecutar_rollback`, que hace los cambios y la auditoría en una única transacción.

## Uso

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_rollback_auto.py -v
.\venv\Scripts\python.exe -m pytest tests/ -q
```

Después de aplicar la migración de columnas, cuando haya datos reales etiquetados y una promoción reversible:

```powershell
# inspección sin cambios en PostgreSQL
.\venv\Scripts\python.exe -m src.monitoring.rollback_auto --caso-uso churn

# SOLO en un entorno de prueba controlado o scheduler autorizado:
# .\venv\Scripts\python.exe -m src.monitoring.rollback_auto --caso-uso churn --aplicar
```

En un despliegue continuo, programar el último comando tras el proceso que registra etiquetas verificadas (p. ej. un job de Windows Task Scheduler o cron). La ejecución aislada del script **no** crea programación automática por sí sola. No activar `--aplicar` en la base local mientras `v1.0` deba permanecer activa.

## Dependencias

La migración `003_real_labels_for_rollback.sql` es aditiva y compatible con la del PR de Allan. **La mera existencia de las columnas no proporciona etiquetas verdaderas**: registrar resultados reales requiere el flujo de etiquetado que está implementando el equipo. No imputar ni inventar etiquetas para demostrar eficacia.

## Validación pendiente

- Demostración de promoción + rollback en DB aislada, leyendo antes/después `model_versions`, `deployments`, `/model-version`.
- Integración del job de monitoreo con un scheduler o el pipeline de recepción de etiquetas reales.
- Evitar conflictos con el PR de Allan antes de subir la rama.
