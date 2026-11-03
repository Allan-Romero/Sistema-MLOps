# Sprint 4 - A7: Tiempos del ciclo manual frente al automatizado

## Objetivo

Obtener la evidencia cuantitativa del aporte de la plataforma: cuánto tarda
cada actividad del ciclo de vida del modelo ejecutada a mano y cuánto a
través del sistema.

## Qué está medido y qué falta medir

| Escenario | Estado | Quién lo mide |
|---|---|---|
| Automatizado | Medido | `python -m src.benchmark.medir_tiempos` |
| Manual | Pendiente | Una persona, con cronómetro, siguiendo el protocolo de este documento |

El escenario automatizado se cronometra solo: el módulo ejecuta cada
actividad a través de las mismas funciones que invoca el pipeline y mide el
tiempo de reloj de cada repetición.

El escenario manual **no puede automatizarse sin dejar de ser manual**. Su
duración es tiempo humano: escribir la consulta, copiar el archivo, mirar el
resultado y decidir. Por eso este documento entrega el protocolo y la tabla
queda con esa columna vacía hasta que se cronometre. Una cifra estimada
presentada como medida es justo lo que el issue advierte no hacer.

## Procedimiento del escenario automatizado

```powershell
python -m src.benchmark.medir_tiempos 3     # 3 repeticiones por actividad
python -m src.benchmark.graficar_tiempos
```

Condiciones de la medición:

- Las seis actividades se ejecutan en el orden del ciclo: preprocesamiento,
  entrenamiento, evaluación comparativa, registro de la versión, promoción a
  producción y detección de drift.
- Cada actividad se mide con `time.perf_counter()` alrededor de la llamada
  real, incluyendo su escritura en disco, en MLflow y en PostgreSQL.
- La promoción incluye copiar el candidato, reiniciar el contenedor de la API
  y esperar a que `/health` vuelva a responder: el tiempo hasta que el modelo
  nuevo está efectivamente sirviendo.
- Se registran promedio, mínimo y máximo de las repeticiones.
- Los servicios deben estar levantados (`docker compose up -d`), porque el
  registro de versiones y la detección de drift escriben en la base.

Resultados en `reports/tiempos_ciclo.csv`.

## Resultados medidos del escenario automatizado

Medición del 31 de octubre de 2026, 3 repeticiones por actividad, sobre el
caso de uso de churn con los cuatro servicios levantados:

| Actividad | Repeticiones | Promedio (s) | Mín (s) | Máx (s) |
|---|---|---|---|---|
| Preprocesamiento | 3 | 0.37 | 0.21 | 0.60 |
| Entrenamiento | 3 | 1.68 | 1.41 | 1.86 |
| Evaluación comparativa | 3 | 0.20 | 0.17 | 0.24 |
| Registro de la versión | 3 | 50.70 | 31.30 | 87.78 |
| Promoción a producción | 3 | 7.52 | 5.77 | 10.16 |
| Detección de drift | 3 | 1.24 | 0.84 | 1.73 |
| **Ciclo completo** | | **61.71** | | |

Dos observaciones sobre la dispersión:

- El registro de la versión domina el ciclo y es la actividad más variable.
  La primera repetición tardó 87.78 s y las siguientes 31.30 s y 33.02 s: la
  diferencia corresponde a la inicialización del cliente de MLflow y a la
  carga de los artefactos del modelo en el servidor de tracking.
- La promoción incluye el reinicio del contenedor de la API y la espera
  hasta que `/health` responde, que es lo que explica sus 7.52 s.

## Protocolo del escenario manual

Se cronometra a mano, con la plataforma detenida en lo que respecta a
automatización: cada paso se hace como se haría sin el pipeline. Se
recomiendan tres repeticiones por actividad y anotar el promedio.

| Actividad | Qué se hace a mano | Cuándo arranca y para el cronómetro |
|---|---|---|
| Preprocesamiento | Abrir el dataset, limpiar `TotalCharges`, codificar las variables y guardar los conjuntos | Desde abrir el archivo hasta tener los CSV de train y test escritos |
| Entrenamiento | Ajustar cada algoritmo y guardar los dos modelos | Desde escribir el ajuste hasta tener los `.joblib` en disco |
| Evaluación comparativa | Calcular las métricas de ambos, compararlas y decidir cuál pasa | Desde la primera métrica hasta la decisión tomada |
| Registro de la versión | Anotar la versión y sus métricas en la base, escribiendo el INSERT a mano | Desde abrir el cliente de PostgreSQL hasta confirmar el registro |
| Promoción a producción | Copiar el modelo elegido al nombre del modelo activo y reiniciar el servicio | Desde la copia hasta comprobar que la API responde con el modelo nuevo |
| Detección de drift | Extraer los datos de producción, calcular el PSI de cada variable y registrar las alertas | Desde la consulta de extracción hasta las alertas escritas |

Reglas para que la comparación sea honesta:

1. Ejecutar realmente cada paso, sin saltarse la escritura de consultas ni la
   revisión de resultados.
2. No descontar los errores de tecleo ni los reintentos: forman parte del
   costo real del trabajo manual.
3. Usar la misma máquina y el mismo dataset que en el escenario automatizado.
4. Anotar el número de repeticiones junto con el promedio.

Los tiempos obtenidos se escriben en la columna `manual_s` de
`reports/tiempos_ciclo.csv`, una fila por actividad, y se vuelve a ejecutar
`python -m src.benchmark.graficar_tiempos` para regenerar el gráfico con las
dos series.

## Gráfico comparativo

`reports/tiempos_comparacion.png`, generado por
`src.benchmark.graficar_tiempos`. Mientras falten los tiempos manuales el
gráfico dibuja solo la serie automatizada y lo advierte en el subtítulo, de
modo que no pueda confundirse con la comparación completa.

## Alcance

La medición cubre el ciclo tal como existe hoy. Dos actividades cambiarán
cuando se cierren las tareas de las que dependen:

- La promoción a producción se mide sobre el procedimiento manual vigente
  (copiar el archivo y reiniciar la API). Cuando S4-J2 implemente la
  promoción automática, el escenario automatizado deberá volver a medirse.
- El ciclo completo de extremo a extremo depende de S4-I2.
