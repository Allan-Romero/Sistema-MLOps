-- Compatible con el esquema de Allan: solo agrega columnas si faltan.
-- No altera ni crea etiquetas reales; estas deben provenir de datos verificables.
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS etiqueta_real INTEGER;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS etiqueta_registrada_at TIMESTAMP;
