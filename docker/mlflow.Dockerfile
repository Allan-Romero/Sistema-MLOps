# Imagen del servidor de tracking de MLflow
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY docker/requirements-mlflow.txt ./requirements-mlflow.txt
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r requirements-mlflow.txt

# Backend de metadatos y destino de artefactos (se montan desde el host)
ENV MLFLOW_BACKEND_STORE_URI=sqlite:////app/mlflow.db \
    MLFLOW_ARTIFACTS_DESTINATION=/app/mlartifacts

EXPOSE 5000

# Forma shell para que se expandan las variables de entorno anteriores
CMD mlflow server \
      --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
      --artifacts-destination "$MLFLOW_ARTIFACTS_DESTINATION" \
      --host 0.0.0.0 \
      --port 5000 \
      --workers 1
