# S5-J4 — Suite de pruebas, cobertura y alcance declarado

Issue relacionada: #113. Fecha de preparación: 5 de noviembre de 2026.

## Qué se verifica

La suite `tests/` ejecuta pruebas unitarias, contratos de artefactos reales
pequeños y solicitudes HTTP en proceso mediante FastAPI TestClient. Las
conexiones SQL se sustituyen por dobles controlados en estas pruebas. Pasar
la suite no significa haber probado una base PostgreSQL real ni haber
completado una validación científica con datasets externos.

El job `delivery` es la verificación complementaria: construye las tres
imágenes, levanta cuatro servicios y ejecuta `scripts/e2e_deployment.py`
con HTTP y PostgreSQL reales. El escenario usa datos sintéticos identificados
como tales. Después `scripts/check_dashboard.py` renderiza el dashboard para
churn y fraude con consultas a esa base. Sus logs y JSON se conservan como
artefactos separados del reporte de cobertura de la suite.

## Componentes críticos y protecciones

| Componente | Evidencia en tests | Invariante comprobada |
|---|---|---|
| Promoción y persistencia | `test_promotion_policy.py`, `test_model_promotion*.py`, `test_promotion_audit.py`, `test_persist_results.py` | La mejora mínima es 0,01 absoluto de F1; versión, métricas, decisión e historial se confirman juntos; un fallo revierte BD y retira el artefacto nuevo. |
| A/B y API | `test_ab_routing.py`, `test_ab_models.py`, `test_ab_api.py`, `test_fraud_api.py` | Reparto configurable; no servir modelos descartados; la pareja histórica/activa debe estar auditada; fallo de consulta no se oculta. |
| Rollback | `test_rollback_service.py`, `test_rollback_auto.py`, `test_rollback_job.py` | No revertir sin autorización, muestras o promoción previa; verificar el destino; no escribir un éxito si falla la bitácora; cancelar si cambió la activa. |
| Cierre A/B | `test_experiment_service.py` | Cierre y elección atómicos; al menos 30 etiquetas por versión; no cerrar si la activa cambió. |
| Contrato del ensayo | `test_e2e_model_contract.py` | Los artefactos serializados del ensayo aceptan los payloads reales de cada endpoint, incluidas las 30 columnas de fraude. |
| Fallos añadidos en S5 | `test_sprint5_critical_failures.py` | Archivo de retorno ausente impide cambiar versiones o cerrar experimento; fallo de `deployments` revierte promoción; fallo de apertura cierra conexión; porcentajes inválidos no conectan. |

Se añadieron once casos parametrizados de fallo de operación, no un duplicado
del camino favorable. No se cambia código de producción para mejorar una cifra
de cobertura.

## Ejecutar y generar reportes

Desde la raíz del repositorio, con las dependencias de desarrollo instaladas
según el manual de reproducción:

```powershell
python -m pytest -ra --junitxml=reports/sprint5/junit.xml --cov --cov-report=term-missing --cov-report=html --cov-report=xml --cov-report=json
python scripts/resumir_pruebas.py --salida docs/evidencias/sprint5/pruebas_resumen.json
```

`.coveragerc` mide líneas **y ramas** de todo `src/`, incluidos módulos no
ejecutados; no excluye módulos difíciles para aumentar el porcentaje. El
denominador no incluye tests, dashboard ni scripts auxiliares. Estos últimos
tienen comprobaciones separadas de ejecución; el porcentaje de `src/` no
representa cobertura de todo el producto.

Abrir `reports/sprint5/htmlcov/index.html` para inspeccionar líneas y ramas
faltantes. `coverage.xml` sirve para herramientas de CI; `coverage.json`
permite reproducir el resumen; `junit.xml` declara fallos, errores y omisiones.
Los reportes grandes están ignorados por Git. El resumen pequeño versionable
incluye versiones de entorno y hashes de archivos Python del árbol probado.
No contiene secretos ni rutas absolutas del computador.

No se impone un umbral de aceptación retrospectivo. La cobertura localiza
zonas sin ejercitar; no prueba ausencia de defectos, corrección de SQL real,
resistencia a concurrencia ni calidad estadística de modelos.

## Omisiones y pruebas históricas

La descripción de #113 menciona `skipif` por artefactos no versionados. La
auditoría de la versión base `f245128` no encontró `skip`, `skipif`, `xfail`
ni `importorskip` en los archivos de `tests/`. Se conserva este hecho como
hallazgo de versión, no se fabrica una lista de pruebas omitidas.

El número definitivo se obtiene del JUnit de cada ejecución, no de una
búsqueda textual. `scripts/resumir_pruebas.py` registra tanto las omisiones
observadas como las marcas estáticas; si aparecen en futuras versiones se
deben revisar y justificar con su motivo. Las nuevas pruebas generan sus
artefactos pequeños en `tmp_path`, por lo que no necesitan modelos del usuario.

## Estado de evidencia y entorno

El resumen final de la ejecución local queda en
`docs/evidencias/sprint5/pruebas_resumen.json`. Consultar allí el conteo,
porcentajes y versiones efectivamente utilizados; no inferirlos de corridas
anteriores del Sprint 4. Una instalación local con Python 3.14 no sustituye
la ejecución objetivo de Linux/Python 3.11 en Actions.

Durante la preparación, el entorno restringido de un subagente bloqueó la
creación del socket local que usa `asyncio` dentro de TestClient. Ese bloqueo
se diagnosticó por el stack en `socket._fallback_socketpair`; no se contó como
prueba aprobada ni se atribuyó a PostgreSQL. La ejecución final debe realizarse
con acceso a sockets locales y quedar registrada en el resumen.

El workflow conserva `pruebas-cobertura-<sha>` aunque falle la suite. Un
workflow anterior del Sprint 4 no demuestra el estado del Sprint 5: después
de publicar esta rama, confirmar `tests` y `delivery` sobre su commit y
descargar ambos artefactos. Hasta observar esa ejecución, CI del Sprint 5
permanece pendiente y la issue no se declara cerrada.
