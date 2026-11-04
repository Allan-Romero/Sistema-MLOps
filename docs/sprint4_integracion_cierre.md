# Sprint 4: integración, validación y cierre

Fecha: 2026-11-03. Issues relacionadas: #103, #104 y #105.

## Alcance de la entrega (#103)

El job `delivery`, dependiente de `tests`, construye las tres imágenes y
levanta cuatro servicios con `docker-compose.ci.yml`. Cada servicio debe
superar su healthcheck. Se repite en pushes y PR, incluido el push de merge
a `main`. No publica imágenes ni instala servicios en infraestructura externa.
Usa credenciales efímeras, una red aislada y un volumen exclusivo de modelos.

Los scripts SQL 001–003 se aplican al crear bases nuevas. Una base existente
requiere migración explícita, sin eliminar sus datos.

## Validación funcional integrada (#104)

Desde una copia limpia, en PowerShell, con Docker funcionando:

```powershell
$env:COMPOSE_FILE = 'docker-compose.ci.yml'
$env:COMPOSE_PROJECT_NAME = 'mlops-validacion-s4'
$env:CI_DB_PASSWORD = [guid]::NewGuid().ToString('N')
docker compose build
docker compose up --wait --wait-timeout 240
docker compose exec -T api python scripts/e2e_deployment.py
docker compose exec -T dashboard python scripts/check_dashboard.py
docker compose logs --no-color
docker compose down --volumes
```

El último comando elimina solo el entorno de validación indicado arriba.
No usarlo sobre el Compose de desarrollo que contiene datos de trabajo.

La prueba requiere una base vacía `mlops_ci` y la marca
`MLOPS_E2E_ISOLATED=1`; rechaza bases ya pobladas. Entrena modelos pequeños,
registra versiones usando el servicio de promoción y abre un A/B pospromoción.
Genera solicitudes HTTP reales, registra la etiqueta sintética conocida y
cierra el experimento usando F1 observado con al menos 80 muestras por versión.
Comprueba que la siguiente solicitud sirve la ganadora sin reiniciar la API,
además de la versión activa, el experimento y la bitácora SQL.

Se recorren mejora y degradación controlada para churn y fraude. La degradación
se introduce invirtiendo la relación entre entradas y etiquetas antes de
enviar tráfico, sin editar predicciones almacenadas. Todo se ejecuta en una
base de prueba aislada; no representa degradación real en producción.

El JSON y los logs del workflow se guardan como artefactos de Actions.
Este ensayo verifica integración funcional con datos sintéticos. No sustituye
el protocolo científico, el entrenamiento completo con Telco/Credit Card,
la comparación manual/automática de #102 ni las capturas del dashboard.

### Evidencia adicional necesaria para cerrar #104

- [ ] Workflow `tests` y `delivery` aprobado sobre el commit del PR.
- [ ] Capturas del dashboard al abrir A/B, durante el tráfico y después del
  cierre, seleccionando ambos casos. Comprobar ganadora e historial.
- [ ] Ejecución con los modelos y datasets reales del proyecto, con etiquetas
  provenientes de conjuntos reservados y particiones reproducibles.
- [ ] Registrar el escenario adverso como estrés controlado, sin atribuirlo
  a degradación observada en usuarios reales.
- [ ] Revisión cruzada por el otro integrante conforme al DoD.

## Matriz provisional de objetivos 2026 (#105)

El usuario confirmó el 2026-11-03 que la versión vigente contiene cinco
objetivos. Se usan provisionalmente; falta confirmar aprobación del asesor.
La referencia a cuatro objetivos en la issue corresponde a una versión anterior.
No se modifica la formulación ni se cierra #105 hasta esa confirmación.

| Objetivo específico del documento 2026 | Evidencia técnica identificada | Verificación pendiente |
|---|---|---|
| Identificar el estado del arte sobre automatización MLOps para modelos de clasificación | `docs/tech_stack.md`, `docs/architecture.md` y documento académico | Estos archivos respaldan decisiones técnicas; falta revisar el capítulo académico y sus fuentes. No demuestran por sí solos una revisión del estado del arte. |
| Diseñar un pipeline automatizado para entrenar, validar y desplegar modelos scikit-learn y XGBoost | `src/training/run_pipeline.py`, `fraud_pipeline.py`, `model_registry.py`, `.github/workflows/ci.yml`, `docker/*.Dockerfile` | Ejecución verde y artefactos del workflow; validación con modelos/datos reales. |
| Implementar un módulo de detección y monitoreo de data drift | `src/monitoring/detect_drift.py`, `reference_data.py`, `src/database/crud.py` | Evidencia reproducible de control/drift y alertas para ambos casos. |
| Construir un dashboard de métricas en tiempo real con alertas automáticas | `dashboard/app.py`, consultas de métricas, alertas, A/B y despliegues en `crud.py` | Capturas y verificación de actualización. El dashboard requiere recarga; no afirmar actualización continua automática sin probarla. |
| Validar la plataforma en casos de uso reales (fraude y churn) | `data/raw/churn.csv`, `src/training/fraud_pipeline.py`, `src/api/fraud.py`, `scripts/e2e_deployment.py` | La prueba sintética no demuestra este objetivo; faltan ensayos completos con Telco/Credit Card y resultados trazables. |

## Checklist honesto de cierre (#105)

- [x] PR #106 y #107 integrados a `develop` al punto de partida `2c11aa8`.
- [x] README actualizado con carga dinámica, A/B, rollback y ambos casos.
- [x] Matriz provisional de cinco objetivos y sus brechas documentada.
- [ ] Cambios de integración revisados por el otro integrante.
- [ ] #103 verificada en Actions con evidencia guardada.
- [ ] #104 verificada y evidencia visual/datasets reales completada.
- [ ] Revisión de todas las tareas pendientes de Sprint 4 y del DoD.
- [ ] Confirmación del asesor sobre los cinco objetivos.
- [ ] PR `develop` → `main` revisado, comprobado y fusionado.
- [ ] Cierre de #105 autorizado después de la confirmación anterior.

No marcar los pendientes como cumplidos por existir código o pasar pruebas unitarias.

## Referencias de configuración

- [Dependencias entre jobs de GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs): `delivery` requiere que `tests` termine correctamente.
- [Docker Compose up](https://docs.docker.com/reference/cli/docker/compose/up/): `--wait` espera el arranque y los healthchecks, con tiempo máximo explícito.
