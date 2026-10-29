# Imagen de la API de predicciones (FastAPI + Uvicorn)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependencias de Python (capa cacheada: solo se reinstala si cambia el archivo)
COPY docker/requirements-api.txt ./requirements-api.txt
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r requirements-api.txt

# Código de la aplicación
COPY src/ ./src/

# Usuario sin privilegios para ejecutar el servicio
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# El modelo se monta desde ./models y se carga en la primera predicción
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
