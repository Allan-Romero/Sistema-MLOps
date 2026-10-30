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
    algoritmo VARCHAR(50),
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

-- Tabla de versiones de modelos generadas por el pipeline
CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    version VARCHAR(20) NOT NULL,
    algoritmo VARCHAR(50),
    metrica_principal VARCHAR(20),
    valor_metrica FLOAT,
    estado VARCHAR(20) DEFAULT 'historica',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de despliegues: bitácora de los cambios de versión en producción
-- (se usará a partir del Sprint 4)
CREATE TABLE IF NOT EXISTS deployments (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    version_origen VARCHAR(20),
    version_destino VARCHAR(20) NOT NULL,
    tipo_operacion VARCHAR(20) NOT NULL
        CHECK (tipo_operacion IN ('promocion', 'rollback')),
    motivo TEXT,
    metrica_principal VARCHAR(20),
    valor_metrica_origen FLOAT,
    valor_metrica_destino FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de experimentos A/B: configuración de cada comparación entre versiones
-- (la consulta la API para repartir el tráfico)
CREATE TABLE IF NOT EXISTS experiments (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    version_a VARCHAR(20) NOT NULL,
    version_b VARCHAR(20) NOT NULL,
    porcentaje_trafico_b INTEGER NOT NULL DEFAULT 50
        CHECK (porcentaje_trafico_b BETWEEN 0 AND 100),
    estado VARCHAR(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'finalizado', 'cancelado')),
    version_ganadora VARCHAR(20),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- Garantiza que exista a lo sumo un experimento activo por caso de uso
CREATE UNIQUE INDEX IF NOT EXISTS idx_experiments_activo
    ON experiments (caso_uso)
    WHERE estado = 'activo';
