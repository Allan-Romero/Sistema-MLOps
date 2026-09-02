-- Esquema de la base de datos: Plataforma MLOps
-- Ejecutar con: docker exec -i mlops_postgres psql -U mlops_user -d mlops_db < src/database/schema.sql

-- Tabla de predicciones realizadas por la API
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    input_data JSONB NOT NULL,
    prediction INTEGER NOT NULL,
    probability FLOAT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de métricas históricas del modelo
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    accuracy FLOAT,
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    roc_auc FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de alertas de drift (se usará a partir del Sprint 3)
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    variable_afectada VARCHAR(50) NOT NULL,
    nivel_drift VARCHAR(20),
    descripcion TEXT,
    revisada BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);