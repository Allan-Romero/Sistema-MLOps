# S5-A2 — Tiempos del ciclo manual frente al automatizado

Issue #115. Medición del 7 y 8 de noviembre de 2026, en la misma máquina,
sobre el caso de uso de churn y con los cuatro servicios levantados.

Es el resultado cuantitativo central del trabajo: cuánto cuesta recorrer el
ciclo de vida del modelo a mano y cuánto a través de la plataforma.

## Resultado

| Actividad | Manual | Automatizado | Reducción |
|---|---:|---:|---:|
| Preprocesamiento | 407,63 s | 0,31 s | 99,92 % |
| Entrenamiento | 303,23 s | 2,22 s | 99,27 % |
| Evaluación comparativa | 253,90 s | 0,20 s | 99,92 % |
| Registro de la versión | 165,80 s | 47,36 s | 71,44 % |
| Promoción a producción | 223,19 s | 1,97 s | 99,12 % |
| Detección de drift | 362,67 s | 1,59 s | 99,56 % |
| **Ciclo completo** | **1716,42 s** | **53,65 s** | **96,87 %** |

El ciclo completo pasa de **28 min 36 s** a **53,65 s**: la plataforma lo
recorre **32 veces más rápido**.

Figura 21 del documento: `docs/figuras/sprint5/figura-21-tiempos-comparacion.png`.

### Dónde está y dónde no está la ganancia

El registro de la versión es la única actividad donde la automatización no
arrasa: 71 % de reducción frente a más del 99 % en las demás. La razón es que
ahí el tiempo no es humano sino de máquina —inicializar el cliente de MLflow,
subir los artefactos y escribir la transacción en PostgreSQL— y eso cuesta lo
mismo lo haga quien lo haga. Es también la actividad que domina el ciclo
automatizado: 47 de sus 54 segundos.

En el resto, lo que se elimina es tiempo de persona: escribir el código,
teclear las consultas, copiar archivos y revisar resultados en pantalla.

## Repeticiones y variabilidad

| Escenario | Repeticiones | Variabilidad |
|---|---|---|
| Automatizado | 3 por actividad | Se reporta promedio, mínimo y máximo |
| Manual | 1 por actividad | No hay varianza que reportar |

Dispersión del escenario automatizado:

| Actividad | Promedio | Mín | Máx |
|---|---:|---:|---:|
| Preprocesamiento | 0,31 s | 0,22 s | 0,47 s |
| Entrenamiento | 2,22 s | 1,87 s | 2,92 s |
| Evaluación comparativa | 0,20 s | 0,17 s | 0,24 s |
| Registro de la versión | 47,36 s | 35,35 s | 67,47 s |
| Promoción a producción | 1,97 s | 0,09 s | 5,70 s |
| Detección de drift | 1,59 s | 0,77 s | 2,76 s |

Dos actividades concentran la dispersión y conviene explicarla:

- **Registro de la versión**: la primera repetición tardó 67,47 s y las
  siguientes 39,25 s y 35,35 s. La diferencia es la inicialización del
  cliente de MLflow y la carga de artefactos en el servidor de tracking.
- **Promoción a producción**: 5,70 s la primera y menos de una décima las
  siguientes. La primera petición carga el modelo en memoria; después ya
  está cacheado.

Una sola repetición del escenario manual es la limitación principal de esta
medición. Repetirlo exige rehacer el trabajo completo a mano, y la segunda
pasada ya no sería comparable porque el operador conoce el procedimiento.

## Procedimiento

### Escenario automatizado

```powershell
python -m src.benchmark.medir_tiempos 3
python -m src.benchmark.graficar_tiempos
```

Cada actividad se ejecuta a través de las mismas funciones que invoca el
pipeline y se mide con `time.perf_counter()` alrededor de la llamada,
incluyendo su escritura en disco, en MLflow y en PostgreSQL.

La promoción merece una aclaración, porque cambió en el Sprint 4. Antes era
copiar un archivo y reiniciar la API; hoy el pipeline decide y escribe el
cambio de versión dentro de la misma transacción del registro, y el cargador
de la API consulta `model_versions` en cada petición. Lo que se mide, por
tanto, es el tiempo hasta que la API atiende con la versión activa, sin
reinicio ni intervención.

### Escenario manual

Una persona ejecuta las seis actividades a mano, con el protocolo de
`docs/evidencias/sprint5/protocolo_manual.md` delante y cronometrando cada
una con `scripts/cronometro_manual.py`.

Qué incluye el tiempo medido:

- Escribir el código de preprocesamiento, entrenamiento y evaluación en una
  consola de Python, sin importar nada de `src/`.
- Escribir a mano los `INSERT` y los `SELECT` de comprobación en `psql`.
- Copiar el artefacto del modelo y cambiar los estados de versión.
- Extraer los datos de producción, calcular el PSI de las tres variables e
  insertar las alertas.
- Los reintentos y los errores de tecleo, que no se descuentan.

Qué no incluye, y por eso el número es una **cota inferior** del costo real:

- El tiempo de diseñar la solución: el operador tenía el procedimiento
  escrito delante.
- El tiempo de depurar errores de concepto.
- La lectura de documentación o la búsqueda de la sintaxis correcta.

Quien se enfrente a estas actividades sin el procedimiento delante tardará
más, de modo que la reducción real de la plataforma es al menos la reportada.

## Trazabilidad

| Archivo | Contenido |
|---|---|
| `evidencias/sprint5/tiempos_ciclo.csv` | Tabla consolidada de ambos escenarios |
| `evidencias/sprint5/tiempos_manual_medicion.csv` | Cada actividad manual con su marca de tiempo |
| `evidencias/sprint5/protocolo_manual.md` | El paso a paso que siguió el operador |
| `figuras/sprint5/figura-21-tiempos-comparacion.png` | Gráfico comparativo |

## Salvedades de esta medición

**Las actividades 1 y 2 provienen de una primera pasada cuyos intervalos se
solapan.** En esa pasada el operador adelantó trabajo de una actividad
mientras el cronómetro corría en la anterior: los artefactos del
entrenamiento aparecen en disco antes de que se cerrara el preprocesamiento.
La suma de ambas, 710,86 s, sí corresponde al trabajo de preprocesar y
entrenar; el reparto entre las dos es aproximado. Las actividades 3 a 6 se
midieron una por una, sin solapamiento.

**Un hallazgo del escenario manual que vale la pena reportar.** Al ejecutar
la promoción a mano, el paso que degrada la versión activa se ejecutó antes
que el que activa la nueva, y como el registro de la versión había fallado,
el sistema quedó **sin ninguna versión activa**: la API respondió 404 a
`/predict` hasta que se corrigió a mano. La promoción automática del Sprint 4
hace las dos cosas en una sola transacción, de modo que ese estado
intermedio no existe. Es un argumento de confiabilidad que la medición de
tiempos, por sí sola, no captura.

**La medición es de un operador y una máquina.** No se afirma que estos
tiempos sean representativos de otro equipo ni de otro hardware.
