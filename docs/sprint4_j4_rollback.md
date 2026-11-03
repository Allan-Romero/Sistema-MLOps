# S4-J4 — Política y operación de rollback

## Alcance de este primer bloque

- La decisión `evaluar_ab` requiere **≥30 predicciones con etiqueta real por grupo**; la candidata debe ser la versión actualmente activa y presentar un F1 inferior al control por al menos **0,01 puntos**. Si el control continúa activo, **no se ejecuta rollback**; tampoco se puede inferir desempeño real a partir de métricas de entrenamiento.
- La decisión `evaluar_drift` requiere simultáneamente una alerta de nivel **alto** (correspondiente en el Sprint 3 a PSI ≥0,25), **≥30 predicciones etiquetadas** para estimar F1 y **F1 observado <0,55**. La versión anterior debe tener F1 conocido ≥0,55. Estos valores son umbrales de operación iniciales, no pruebas de significancia estadística.
- `ejecutar_rollback` ejecuta toda la reversión en una **única transacción**: bloquea por caso de uso igual que S4-J2; comprueba la versión activa; obtiene la predecesora desde `promotion_decisions` con resultado `promovida`; verifica su estado `historica` y que exista su artefacto; marca la degradada `descartada`; reactiva la histórica; cancela el experimento activo si lo hubiera; y escribe la bitácora `deployments`.
- La API puede reconocer el nuevo estado sin reinicio gracias a la carga dinámica de S4-J1. El servicio de rollback **no se ejecuta al importar**, ni produce cambios mediante las pruebas mockeadas.

## Dependencias y tareas pendientes antes de declarar J4 completa

1. `deployments` y `experiments` deben existir en cada entorno: están definidas en el PR S4-A1 de Allan. En la base local ya se crearon manualmente, pero se debe integrar `schema.sql` cuando se fusione ese PR.
2. Conectar la política a métricas **observadas** a partir de `predictions.etiqueta_real`, que incorpora S4-A2, y obtener una muestra suficiente por experimento o ventana de monitoreo. Si no existen etiquetas, **no se debe ejecutar rollback automáticamente**.
3. Integrar el evaluador con el cierre del experimento A/B y el ciclo de monitoreo de drift, de forma que el disparador automatizado pueda invocar `ejecutar_rollback` tras comprobar las condiciones. Añadir pruebas de integración del flujo completo.
4. Validar un rollback deliberado **en un entorno aislado** con una promoción previa real y auditable, comprobando `model_versions`, `deployments` y `/model-version` antes y después. **No alterar `v1.0` de la base actual para crear evidencia artificial**.
5. Conservar registro de todas las ejecuciones y vigilar las condiciones reales de despliegue. No afirmar que el proceso es autónomo sin integrar un disparador operativo programado.

### Contexto actual

En la base local `v1.0` continúa activa y `v1.2` sigue como candidata de un experimento ya terminado. Como la candidata nunca se promovió, no existe una promoción para revertir. Es correcto que este bloque no ejecute ninguna reversión sobre la base actual.
