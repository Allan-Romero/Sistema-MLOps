# Sprint 3 - J2: Simulacion de Data Drift

## Objetivo
Generar datos simulados para validar el sistema de monitoreo de drift.

## Conjunto de referencia
Archivo: data/reference/churn_reference.csv

- Registros: 5634
- Variables: 45

## Escenario 1: Control
Archivo: data/simulated/churn_control.csv

Se utiliza una copia exacta del baseline, sin modificar las variables.

Resultado esperado: ausencia de drift.

## Escenario 2: Drift
Archivo: data/simulated/churn_drift.csv

Modificaciones realizadas:

- MonthlyCharges: incremento de 30 unidades.
- tenure: incremento de 18 meses, limitado a 72 meses.
- Las otras 43 variables permanecen sin cambios.

Registros modificados:
- MonthlyCharges: 5634
- tenure: 5342

Resultado esperado: deteccion de cambios en las distribuciones
de las variables alteradas.

## Reproducibilidad

Ejecutar desde la raiz del proyecto:

python -m src.monitoring.simulate_data

El script genera los dos escenarios a partir del baseline
utilizando transformaciones deterministas.

## Validacion

Se verifico la generacion de ambos archivos CSV.
La deteccion efectiva de drift se validara durante
la integracion con Evidently AI.
