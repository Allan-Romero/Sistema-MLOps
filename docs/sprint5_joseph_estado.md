# Sprint 5 de Joseph — estado de entrega y revisión

Fecha: 5 de noviembre de 2026. Base: `develop` en `f245128`.
Rama de trabajo: `feature/sprint5-joseph`.

## Mesa de especialistas

| Rol | Responsabilidad y revisión |
|---|---|
| Líder técnico | Alcance #110–#113, comparación real, integración, revisión cruzada y evidencias finales. |
| Arquitectura | Documentación fiel al código y cuatro figuras de topología, datos, training y rollback. |
| DevOps y reproducción | Manifiestos comunes, manual, verificador y revisión independiente del comparador de modelos. |
| Calidad | Casos de fallo críticos, reporte de cobertura, auditoría de omisiones y workflow de evidencias. |

El trabajo se realizó en un worktree separado. No se alteraron datos,
credenciales, modelos activos ni el documento académico oficial. El refactor
de factorías de modelos conserva los hiperparámetros productivos.

## Criterios por issue

| Issue | Entregado | Pendiente para cierre formal |
|---|---|---|
| #110 S5-J1 | Script de comparación real sin mutaciones; tabla de ambos algoritmos/dos casos; warning capturado y explicado; selección y métricas justificadas; texto académico propuesto. | Revisión de los autores, incorporación al documento oficial y conformidad académica. No se presupone aprobación del asesor. |
| #111 S5-J2 | Arquitectura, flujos y cuatro diagramas actualizados; estados y umbrales descritos desde código. | Revisión cruzada e incorporación de figuras al documento, con numeración institucional. |
| #112 S5-J3 | Manual desde clonación, perfiles de dependencias con fuente única de versiones, verificador de reproducción. | Ensayo limpio completo con Python 3.11, Docker, inferencia y evidencia de los nuevos manifiestos. La instalación local Python 3.14 se informa por separado. |
| #113 S5-J4 | Once casos adicionales, suite local, cobertura global y crítica, omisiones auditadas, reportes y artefactos en CI. | Ejecución del commit de Sprint 5 en GitHub Actions y revisión cruzada del PR. |

Los resultados exactos y versiones están en `docs/evidencias/sprint5/`.
La cobertura mide todo `src/`, incluidos módulos nunca ejecutados, y no
incluye dashboard, scripts ni tests en el denominador. Los ensayos HTTP en
proceso no sustituyen el job `delivery` con PostgreSQL y contenedores reales.

## Dependencias y límites que se mantienen

### Validación local registrada

- Instalación desde cero en venv Windows/Python 3.14.5, con las versiones
  declaradas por el proyecto; `pip check` sin conflictos y 22 versiones
  directas verificadas.
- Dos algoritmos entrenados sobre los CSV reales de churn y fraude, con
  hashes de datos y fuentes y advertencias conservadas. La tabla final usa
  scikit-learn 1.9.1 y XGBoost 3.2.0, no el entorno previo del usuario.
- Suite: 177 aprobadas, cero errores/fallos/omisiones, una advertencia de
  deprecación de Starlette/httpx. Cobertura combinada de líneas y ramas de
  todo `src/`: 41,06 %. Las tablas por componente están en el resumen JSON.
- La configuración Compose CI es válida. El motor Docker no estaba
  disponible desde este entorno, por lo que las nuevas imágenes y la
  validación Python 3.11 quedan pendientes del workflow de este commit.

### Límites de integración

- El PR #108 está fusionado a `develop`, seguido del PR #109. La issue #105
  figura cerrada en GitHub; al iniciar este trabajo `main` seguía en `1380cf2`,
  por detrás de `develop`. El cierre de la issue no prueba por sí solo la
  integración en `main` ni la aprobación académica de los objetivos.
- Se mantienen los cinco objetivos específicos de la tesis 2026 como
  referencia provisional, sin modificarlos ni asumir aprobación formal.
- Este paquete cubre Joseph (#110–#113). No da por terminadas las tareas
  de Allan (#114–#118) ni las integradoras del Sprint 5 (#119–#122).
- Ninguna issue se cierra automáticamente y no se fusiona a `main` desde
  esta rama. Aplicar el DoD y la revisión del otro integrante.

## Orden de continuación

1. Publicar la rama y abrir PR a `develop`, relacionando #110–#113 sin cierre
   automático.
2. Comprobar `tests` y `delivery` sobre el nuevo commit; descargar cobertura
   y logs. El verde del Sprint 4 no valida estos cambios de dependencias.
3. Seguir el manual en un entorno limpio, conservar hashes de datasets y
   resultados de inferencia. Registrar cualquier paso que obligue a improvisar.
4. Revisar con Allan los entregables y con el asesor el texto académico.
5. Integrar por PR y cerrar solo los criterios realmente comprobados.
