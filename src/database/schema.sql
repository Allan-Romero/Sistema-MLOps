CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    input_data JSONB NOT NULL,
    prediction INTEGER NOT NULL,
    probability FLOAT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    variable_afectada VARCHAR(50) NOT NULL,
    nivel_drift VARCHAR(20),
    descripcion TEXT,
    revisada BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);