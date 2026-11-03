
BEGIN;

-- Comprobar que no existan varios modelos activos.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM model_versions
        WHERE estado = 'activa'
        GROUP BY caso_uso
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Existen varias versiones activas para un caso de uso.';
    END IF;
END
$$;

-- Permitir solo un modelo activo por caso de uso.
CREATE UNIQUE INDEX IF NOT EXISTS
    uq_model_versions_active_caso
ON model_versions (caso_uso)
WHERE estado = 'activa';

COMMIT;
