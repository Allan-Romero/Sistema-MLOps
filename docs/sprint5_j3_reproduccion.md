# S5-J3 — Manual de despliegue y reproducción

Fecha: 5 de noviembre de 2026. Relacionado con la issue #112.
Audiencia: una persona que no participó en el desarrollo.

## 1. Alcance y versión

La plataforma ejecuta PostgreSQL, MLflow, FastAPI y Streamlit en Docker
Compose. El entrenamiento y la generación de tráfico se ejecutan desde Python
en el equipo anfitrión. La entrega de CI construye imágenes y verifica el
arranque en un entorno efímero; no despliega a infraestructura externa.

Este manual describe el Sprint 5 basado en `develop` (`f245128`). Las
instrucciones nuevas de dependencias requieren la revisión que contiene este
manual, no el `main` anterior. Para revisar el PR, usar
`feature/sprint5-joseph`; tras su fusión, usar el commit aprobado de `develop`.
Registrar siempre `git rev-parse HEAD`: una rama por sí sola no identifica
una ejecución reproducible. Ver [arquitectura](sprint5_j2_arquitectura.md).

La reproducción funcional sintética y la validación académica con datasets
públicos son ensayos distintos. No atribuir resultados del primer ensayo a
Telco ni Credit Card. No copiar modelos ni `.env` de otra persona para hacer
pasar una instalación nueva.

## 2. Requisitos previos

- Git, Python **3.11** de 64 bits con `venv` y `pip` y Docker Desktop con
  motor Linux y Docker Compose v2. Mantener la misma versión Python que CI y
  los Dockerfiles. Las pruebas en 3.14 no sustituyen la prueba en 3.11.
- Conexión a Internet para paquetes/imágenes y acceso a los datasets.
- Puertos 5432, 5000, 8000 y 8501 libres para el entorno habitual.
- Recursos suficientes para cuatro contenedores y el entrenamiento del
  dataset de fraude (284.807 filas). No se ha fijado un mínimo empírico de RAM.

Comprobar antes de continuar:

```powershell
git --version
py -3.11 --version
docker version
docker compose version
```

`docker version` debe mostrar cliente **y servidor**. Si falta el servidor,
abrir Docker Desktop y esperar a que arranque el motor. En Linux/macOS,
sustituir `py -3.11` por el ejecutable `python3.11` y usar
`.venv/bin/python` en lugar de `.venv\Scripts\python.exe`.

## 3. Obtener una copia limpia

Crear una carpeta de trabajo nueva, distinta del repositorio ya utilizado:

```powershell
git clone https://github.com/Allan-Romero/Sistema-MLOps.git Sistema-MLOps-reproduccion
cd Sistema-MLOps-reproduccion
git switch feature/sprint5-joseph
git rev-parse HEAD
git status --short
```

La rama debe existir remotamente antes de seguir el manual del PR. Una vez
fusionado, sustituir el `switch` por `git switch develop` y registrar el SHA.
Para una reproducción histórica, usar `git switch --detach <SHA_aprobado>`.
El árbol debe estar limpio antes de instalar. No usar `git reset --hard` para
limpiar una carpeta con trabajo sin guardar.

## 4. Dependencias: una única fuente de versiones

`requirements/constraints.txt` contiene las versiones de dependencias
**directas**; se preservan las versiones de ejecución ya utilizadas por el
proyecto. Los manifiestos por rol declaran nombres y consumen esas constraints:

| Archivo | Uso |
|---|---|
| `requirements/common.txt` | Datos, sklearn, serialización y PostgreSQL |
| `docker/requirements-api.txt` | API y carga de modelos |
| `docker/requirements-dashboard.txt` | Streamlit y monitoreo |
| `docker/requirements-mlflow.txt` | Servidor MLflow |
| `requirements/training.txt` | Entrenamiento y utilidades del anfitrión |
| `requirements/dev.txt` | pytest, cobertura y cliente HTTP de pruebas |
| `requirements.txt` | Agrega todos los roles para desarrollo local y CI |

Los Dockerfiles copian `requirements/` y su manifiesto `docker/` conservando
la relación de rutas. Una versión se cambia en constraints, no en tres
requirements distintos. Se eliminó el `pip freeze` de Windows y `pywin32`
como declaración de instalación. No se eliminó el uso legítimo de
dependencias transitivas: ahora las selecciona el resolutor de pip.

Este esquema **no es un lock completo con hashes**: las transitivas pueden
variar. Para cada ensayo se conserva el reporte de instalación y `pip freeze`
como evidencia de lo instalado; freeze no vuelve a ser la fuente del producto.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
New-Item -ItemType Directory -Force reports/reproduccion | Out-Null
.\.venv\Scripts\python.exe -m pip install --report reports/reproduccion/instalacion.json -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze > reports/reproduccion/entorno-instalado.txt
.\.venv\Scripts\python.exe scripts/verificar_reproduccion.py > reports/reproduccion/manifiestos-y-versiones.json
```

Continuar solo si los comandos terminan con código cero y `pip check` informa
que no hay dependencias rotas. No desactivar el resolutor ni utilizar
`--no-deps` para ocultar incompatibilidades. Los informes generados no deben
contener URLs privadas con credenciales antes de compartirse.

## 5. Configurar variables y carpetas

Solo en esta copia nueva:

```powershell
Copy-Item .env.example .env
New-Item -ItemType Directory -Force models,reports,mlartifacts,data/raw | Out-Null
New-Item -ItemType File -Path mlflow.db -ErrorAction SilentlyContinue | Out-Null
```

Editar `.env` con usuario, contraseña **propia** y nombre de base:
`POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`. No usar literalmente los
marcadores `tu_usuario`/`tu_password_seguro`, ni publicar ese archivo. No
sobrescribir el `.env` de una instalación existente. El archivo `mlflow.db`
debe ser un archivo, no un directorio; una SQLite vacía se inicializa al arrancar.

Desde el anfitrión se usa `localhost:5432`; dentro de Compose, el host es
`postgres`. La API recibe este último automáticamente. Las direcciones de
MLflow son `http://127.0.0.1:5000` desde el anfitrión y `http://mlflow:5000`
dentro de la red de contenedores.

## 6. Construir, iniciar y comprobar servicios

El arranque de los procesos puede continuar después de `up -d`. Esperar
hasta dos minutos y repetir la comprobación HTTP si aparece un fallo inicial,
antes de diagnosticarlo como avería. El Compose habitual no tiene healthcheck
para dashboard; el entorno CI sí espera el de cada servicio.

```powershell
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml ps
.\.venv\Scripts\python.exe scripts/verificar_reproduccion.py --servicios
.\.venv\Scripts\python.exe -m src.database.test_connection
```

| Servicio | Verificación |
|---|---|
| PostgreSQL | `test_connection` completa sin error; `pg_isready` del contenedor responde |
| API | `http://localhost:8000/health`, Swagger en `/docs` |
| Dashboard | `http://localhost:8501`, salud en `/_stcore/health` |
| MLflow | `http://localhost:5000`, salud en `/health` |

`/health` con `model_loaded=false` **no demuestra un fallo**: la carga es
diferida. Tampoco demuestra inferencia correcta: eso se comprueba después
de entrenar y registrar una versión activa. El dashboard puede mostrar
advertencias de que todavía no existen métricas ni predicciones.

## 7. Esquema y migraciones

Un volumen PostgreSQL nuevo aplica `schema.sql` y las migraciones 001–003 en
orden mediante los scripts de inicialización. El volumen conserva los datos
entre reinicios. Modificar SQL o reconstruir imágenes **no migra un volumen
ya existente**.

Para una base existente, detener escritores, respaldar la base y aplicar los
archivos sin borrar datos. En PowerShell, usando las variables del contenedor:

```powershell
Get-Content src/database/schema.sql -Raw | docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content src/database/migrations/001_unique_active_model.sql -Raw | docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content src/database/migrations/002_promotion_decisions.sql -Raw | docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content src/database/migrations/003_real_labels_for_rollback.sql -Raw | docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Revisar el código de salida de **cada** comando. La migración 001 rechaza
varias versiones activas del mismo caso; investigar la inconsistencia antes
de continuar. `promotion_decisions` es una séptima tabla de auditoría
introducida por migración, además de las seis del esquema base.

## 8. Preparar datasets verificables

- Churn: `data/raw/churn.csv`, variable objetivo `Churn`, valores `Yes`/`No`.
  El repositorio incluye el dataset Telco; comprobar el nombre que requiere
  `src/training/preprocess.py`, no renombrar columnas arbitrariamente.
- Fraude: obtener Credit Card Fraud Detection de su fuente pública y guardar
  como `data/raw/creditcard.csv`. Debe contener `Time`, `V1`–`V28`, `Amount`
  y `Class`; no basta un CSV con el mismo nombre. El entrenamiento valida
  esquema, clases, números finitos y nulos.
- Fuente de fraude: [ULB en Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).
  Fuente Telco: [IBM](https://github.com/IBM/telco-customer-churn-on-icp4d).
  Respetar las condiciones de acceso de cada fuente. No incluir claves de
  Kaggle ni subir el CSV grande al repositorio.

Registrar huellas para el informe de ejecución:

```powershell
Get-FileHash data/raw/churn.csv -Algorithm SHA256
Get-FileHash data/raw/creditcard.csv -Algorithm SHA256
```

## 9. Entrenar y registrar ambos casos

Con los servicios disponibles y desde la raíz de esta copia:

```powershell
.\.venv\Scripts\python.exe -m src.training.pipeline_multicaso --caso-uso churn
.\.venv\Scripts\python.exe -m src.training.pipeline_multicaso --caso-uso fraude
.\.venv\Scripts\python.exe -m src.training.pipeline_multicaso --caso-uso fraude --registrar
```

Para churn, ejecutar el pipeline también registra experimentos en MLflow y
persistencia/promoción en PostgreSQL. Para fraude son **dos pasos**:
entrenar crea artefacto y reporte; `--registrar` registra el resultado ya
generado, no vuelve a entrenar. No ejecutar pipelines simultáneamente porque
comparten archivos intermedios. Conservar stdout, warnings y reportes de cada
ejecución; no ocultar `ConvergenceWarning` ni cambiar métricas a mano.

La política compara F1 con la activa y exige mejora absoluta de al menos
0,01. La primera versión se activa; una posterior que no mejora queda
descartada. Es correcto que repetir un entrenamiento no cambie la activa.
Las versiones y los artefactos son registrados por el servicio: no copiar
`*_candidate.joblib` encima del modelo activo ni editar estados por SQL para
forzar una promoción. El criterio operativo F1 no es prueba de significancia.

Verificar versiones y predicciones reales:

```powershell
Invoke-RestMethod http://localhost:8000/model-version
Invoke-RestMethod http://localhost:8000/model-version/fraude
```

En Swagger ejecutar `/predict` con una fila Telco sin `Churn` ni `customerID`,
y `/predict-fraud` con las 30 características sin `Class`. Deben devolver
HTTP 200, `prediction_id` y la versión; confirmar el registro en el dashboard
tras recargar. La salida de MLflow refleja el flujo de churn; el adaptador de
fraude registra su informe/artefacto y PostgreSQL, no asumir que registra la
misma información en MLflow sin comprobar el código.

## 10. Prueba funcional de entrega en entorno limpio y aislado

Esta prueba no requiere descargar datasets ni cargar credenciales del usuario.
Usa PostgreSQL nuevo, modelos sintéticos y nombres de proyecto exclusivos,
sin puertos públicos. Ejecutar en una sesión PowerShell nueva:

```powershell
$proyectoPrueba = "mlops-repro-" + [guid]::NewGuid().ToString('N').Substring(0,8)
$env:CI_DB_PASSWORD = [guid]::NewGuid().ToString('N')
docker compose -f docker-compose.ci.yml -p $proyectoPrueba build
docker compose -f docker-compose.ci.yml -p $proyectoPrueba up --wait --wait-timeout 240
docker compose -f docker-compose.ci.yml -p $proyectoPrueba exec -T api python scripts/e2e_deployment.py
docker compose -f docker-compose.ci.yml -p $proyectoPrueba exec -T dashboard python scripts/check_dashboard.py
docker compose -f docker-compose.ci.yml -p $proyectoPrueba ps
```

Guardar los JSON y el estado de servicios. El primero debe incluir mejora y
degradación para churn y fraude; el segundo, ambos dashboards sin excepción.
La prueba E2E requiere base inicialmente vacía y se ejecuta una sola vez por
entorno; para repetir usar otro proyecto nuevo. Luego de guardar evidencias:

```powershell
docker compose -f docker-compose.ci.yml -p $proyectoPrueba down --volumes
Remove-Item Env:CI_DB_PASSWORD
```

El borrado anterior solo corresponde al proyecto aleatorio de prueba. No
usar `down --volumes` en el entorno habitual con información a conservar.

## 11. Pruebas y evidencia de reproducción

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Para la cobertura y omisiones, seguir el informe S5-J4 de la misma revisión.
Un resultado verde de pruebas unitarias no sustituye la instalación limpia,
la reproducción Docker ni las predicciones con datasets reales.

Por ejecución guardar: SHA del código, fecha, SO, versión Python/Docker,
hash de datasets, reporte pip, `pip check`, `pip freeze`, stdout del pipeline,
pruebas, JSON E2E, captura de los servicios y enlaces de Actions. No registrar
contraseñas ni `.env`. Revisar logs antes de adjuntarlos.

### Registro de verificación de esta revisión

- Instalación en una **venv vacía** de Windows/Python 3.14.5 ejecutada por
  el líder con `pip install --report ... -r requirements.txt`: terminó
  correctamente. `pip check` no encontró dependencias rotas y el verificador
  confirmó las 22 versiones directas. Ver
  [entorno](evidencias/sprint5/reproduccion_entorno.json),
  [pip check](evidencias/sprint5/pip-check.txt) y
  [freeze de esa ejecución](evidencias/sprint5/entorno-instalado.txt).
  Algunas bibliotecas instalan dependencias transitivas condicionales de
  Windows; estas no se declaran como requisito del producto para Linux.
- En esa venv pasaron 177 pruebas, cero omisiones. Esto prueba instalación
  y ejecución local en 3.14; **no sustituye** un arranque limpio en Python
  3.11/Docker ni valida por sí solo la inferencia de un modelo productivo.

- Comprobación estática de manifiestos: ejecutada con
  `scripts/verificar_reproduccion.py --solo-manifiestos`, Windows/Python 3.14.5,
  5/11/2026; 22 dependencias directas con versión central y sin errores.
- Docker local del agente: el motor no estaba disponible; **no se afirma**
  reproducción limpia con contenedores de esta revisión a partir de esa comprobación.
- Instalación limpia en Python 3.11 y ensayo completo: requieren registro
  del líder/CI de esta revisión antes de marcar el criterio como cumplido.
- El Sprint 4 tiene evidencia anterior de E2E aprobado; no sustituye verificar
  las imágenes de Sprint 5 que ahora consumen manifiestos reorganizados.

## 12. Diagnóstico de fallos frecuentes

| Síntoma | Comprobación y acción |
|---|---|
| Docker no muestra servidor | Abrir motor Linux de Docker Desktop; no es fallo PostgreSQL. |
| Puerto ocupado o nombre `mlops_*` en uso | Revisar el stack ya levantado. No iniciar dos copias del Compose habitual; usar CI aislado para ensayos paralelos. |
| API 503 consultando PostgreSQL | Comprobar contenedor, credenciales propias y host `postgres` dentro/`localhost` fuera. |
| Falta `promotion_decisions` | Aplicar migraciones sobre el volumen existente; reconstruir no las aplica. |
| No existe versión activa/artefacto | Ejecutar entrenamiento/registro y revisar rutas; salud HTTP no demuestra que exista un modelo. |
| MLflow no conecta | Comprobar puerto 5000 y `MLFLOW_TRACKING_URI` según host/contenedor. |
| `mlflow.db` es directorio | Detener MLflow y corregir el montaje en copia nueva; no borrar una base con historial. |
| El candidato no se activa | Revisar F1, delta mínimo y auditoría; no forzar la versión por SQL. |
| Dataset de fraude ausente | Descargar `creditcard.csv` y validar columnas; no usar datos sintéticos como sustituto académico. |
| Dashboard no cambia tras editar módulos `src` | `docker compose restart dashboard`; después recargar navegador. |
| Dependencias incompatibles | Usar Python 3.11, venv nueva y constraints de esta misma revisión; guardar error del resolutor. |

Detener normalmente con `docker compose stop` o `docker compose down`, sin
`--volumes`; conservar PostgreSQL, modelos y artefactos. No declarar tareas
cerradas hasta revisión cruzada y evidencia exigida por el DoD.

## Referencias de implementación

- [pip: constraints](https://pip.pypa.io/en/stable/user_guide/#constraints-files):
  una constraint restringe versiones, no instala por sí sola un paquete.
- [Dockerfile COPY](https://docs.docker.com/reference/dockerfile/#copy): los
  manifiestos compartidos deben estar en el contexto y copiarse a la imagen.
