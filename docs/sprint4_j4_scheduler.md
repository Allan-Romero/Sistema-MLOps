# S4-J4 — Ejecución desatendida del evaluador

El rollback automático usa la política de `src.monitoring.rollback_auto` y una tarea programada del sistema operativo. El job nuevo no altera la lógica de decisión ni el servicio transaccional.

## Evaluar manualmente (solo lectura)

```powershell
.\venv\Scripts\python.exe -m src.monitoring.rollback_job --caso-uso churn
```

Los resultados se agregan a `reports/s4_j4_monitoring.jsonl`. Si no existe promoción reversible o no hay etiquetas reales, no hay rollback.

## Configurar tarea programada en Windows

Previsualizar configuración, sin crear nada:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\configurar_rollback_j4.ps1
```

Crear tarea diaria de **solo consulta**, a las 03:00, en el equipo local (debe estar encendido y con acceso a PostgreSQL):

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\configurar_rollback_j4.ps1 -Registrar
```

Para activar el rollback **real** en un despliegue autorizado con etiquetas verificadas, existe un segundo modo que requiere dos parámetros explícitos:

```powershell
# NO ejecutar en esta demostración de Sprint 4.
# powershell.exe -ExecutionPolicy Bypass -File .\scripts\configurar_rollback_j4.ps1 -Modo aplicar -Registrar -ConfirmarAplicacion
```

El script reusa el nombre de tarea `Sistema-MLOps-S4-J4`, de modo que el segundo modo reemplaza al primero. La tarea llama a Python con `--aplicar`; no toma decisiones por sí sola: solo si la política encuentra evidencia suficiente y una promoción auditable, ejecuta la reversión transaccional.

Comprobar la tarea:

```powershell
Get-ScheduledTask -TaskName 'Sistema-MLOps-S4-J4'
```

Desinstalar:

```powershell
Unregister-ScheduledTask -TaskName 'Sistema-MLOps-S4-J4' -Confirm:$false
```

## Precauciones

- No se ha activado ningún scheduler al copiar estos archivos: el usuario debe registrarlo explícitamente.
- Antes de usar el modo `aplicar` con usuarios reales, validar que las etiquetas reales correspondan a eventos observados y que el pipeline de etiquetado sea confiable.
- Como tarea de Windows, solo puede ejecutarse si ese equipo está disponible; para un despliegue servidor, usar cron, un orquestador o un job del pipeline que invoque el mismo módulo.
- El archivo JSONL es un registro operativo generado localmente, no una evidencia de precisión estadística del modelo. La auditoría de reversiones efectivas queda en `deployments`.
