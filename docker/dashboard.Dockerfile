# Imagen del dashboard de monitoreo (Streamlit)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependencias de Python (capa cacheada: solo se reinstala si cambia el archivo)
COPY docker/requirements-dashboard.txt ./requirements-dashboard.txt
RUN pip install --no-cache-dir --retries 10 --timeout 120 -r requirements-dashboard.txt

# Código de la aplicación
COPY src/ ./src/
COPY dashboard/ ./dashboard/

# Usuario sin privilegios para ejecutar el servicio
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
