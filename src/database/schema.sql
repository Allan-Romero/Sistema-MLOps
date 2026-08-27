CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    input_data JSONB NOT NULL,
    prediction INTEGER NOT NULL,
    probability FLOAT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);