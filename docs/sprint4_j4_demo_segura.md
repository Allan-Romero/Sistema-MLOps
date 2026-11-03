# S4-J4 — Evidencia de rollback sin tocar la base productiva

Esta demostración **no modifica** `mlops_db`: crea una base de datos PostgreSQL nueva con nombre aleatorio `mlops_j4_demo_*`, inserta una promoción y etiquetas **enteramente sintéticas**, provoca un A/B desfavorable, ejecuta el rollback transaccional y elimina la base de pruebas.

## Requisitos

- Docker Compose/PostgreSQL encendidos y usuario PostgreSQL con permiso `CREATEDB` (con la instalación local de `POSTGRES_USER=joseph` como superusuario, se cumple).
- Las versiones `models/churn_model_v1.0.joblib` y `models/churn_model_v1.2.joblib` deben existir.
- Dependencias locales del proyecto instaladas (incluyendo `fastapi`, `psycopg2-binary`, `xgboost`, `joblib`, `pandas`, `httpx`).
- Ejecutar desde la raíz del repositorio, con `.env` apuntando a `mlops_db`.

```powershell
.\venv\Scripts\python.exe scripts\demo_rollback_j4.py --run
```

## Qué comprueba

1. `model_versions` antes: `v1.2` activa, `v1.0` histórica.
2. Se genera un experimento finalizado y 30 observaciones sintéticas por modelo, F1 control = 1.0 y F1 candidata = 0.0. Los resultados son **artificiales** y no son métricas reales de los modelos.
3. `rollback_auto` detecta el resultado A/B desfavorable.
4. El servicio confirma una operación transaccional y la registra en `deployments`.
5. `model_versions` después: `v1.2` descartada, `v1.0` activa.
6. `/model-version` cambia de `v1.2` a `v1.0`, y `/predict` usa `v1.0` **en la misma instancia ASGI** sin reiniciar la aplicación. La instancia probada es TestClient apuntando solo a la base aislada; el servicio real en el puerto 8000 no se altera.
7. Se elimina la base de pruebas. Un informe JSON reproducible queda en `reports/s4_j4_rollback_demo.json`.

## Advertencias

- No usar etiquetas sintéticas en producción ni considerar este ensayo una validación del F1 real del candidato.
- No confundir ejecutar el evaluador con programarlo. Para operación desatendida, el equipo debe invocar `python -m src.monitoring.rollback_auto --caso-uso churn --aplicar` desde un job autorizado **después** de registrar etiquetas verificadas. No activar dicho job hasta que exista el flujo de etiquetas y se decidan permisos, frecuencia y supervisión.
- La base aislada se elimina incluso si falla la prueba, siempre que PostgreSQL esté accesible. Si la limpieza falla por caída del servidor, puede quedar una base llamada `mlops_j4_demo_*` que debe revisarse antes de eliminar manualmente.
