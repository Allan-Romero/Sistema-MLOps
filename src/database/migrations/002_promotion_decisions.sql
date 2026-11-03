
BEGIN;

-- Historial completo de decisiones de promoción S4-J2.
CREATE TABLE IF NOT EXISTS promotion_decisions (
    id BIGSERIAL PRIMARY KEY,
    caso_uso VARCHAR(20) NOT NULL,
    version_candidata VARCHAR(20) NOT NULL,
    version_anterior VARCHAR(20),
    algoritmo VARCHAR(50) NOT NULL,

    f1_candidato DOUBLE PRECISION NOT NULL
        CHECK (f1_candidato BETWEEN 0 AND 1),
    f1_activo DOUBLE PRECISION
        CHECK (f1_activo BETWEEN 0 AND 1),

    mejora DOUBLE PRECISION,
    umbral DOUBLE PRECISION NOT NULL
        CHECK (umbral > 0 AND umbral <= 1),

    resultado VARCHAR(20) NOT NULL
        CHECK (resultado IN ('promovida', 'descartada')),

    motivo TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (caso_uso, version_candidata)
);

COMMIT;
