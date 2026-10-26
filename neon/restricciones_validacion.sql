-- OLIMPOS GYM — Restricciones extra de validación (2026-10)
--
-- El sistema de empleados ya valida todo antes de guardar (ver
-- Aplicaciones/olimpos_gym/validaciones.py). Esto es una segunda capa en la
-- base: frena datos inválidos aunque entren por otro lado (la app móvil, la
-- API o un script). Probado contra los datos actuales: todos cumplen.
--
-- Se aplica una sola vez (en el SQL Editor de Neon, o con psql). Es seguro
-- volver a correrlo: borra y recrea cada restricción con su nombre.

BEGIN;

-- Email y usuario únicos sin importar mayúsculas ("Ana@Gmail.com" = "ana@gmail.com")
CREATE UNIQUE INDEX IF NOT EXISTS uq_socios_email_lower ON socios (lower(email));
CREATE UNIQUE INDEX IF NOT EXISTS uq_empleados_email_lower ON empleados (lower(email));
CREATE UNIQUE INDEX IF NOT EXISTS uq_empleados_usuario_lower ON empleados (lower(usuario));

-- DNI argentino: 7 u 8 números (antes aceptaba de 6 a 10)
ALTER TABLE socios DROP CONSTRAINT IF EXISTS ck_socios_dni;
ALTER TABLE socios DROP CONSTRAINT IF EXISTS socios_dni_check;
ALTER TABLE socios ADD CONSTRAINT socios_dni_check CHECK (dni IS NULL OR dni ~ '^[0-9]{7,8}$');
ALTER TABLE empleados DROP CONSTRAINT IF EXISTS ck_empleados_dni;
ALTER TABLE empleados DROP CONSTRAINT IF EXISTS empleados_dni_check;
ALTER TABLE empleados ADD CONSTRAINT empleados_dni_check CHECK (dni IS NULL OR dni ~ '^[0-9]{7,8}$');

-- Montos y duraciones con sentido
ALTER TABLE membresias DROP CONSTRAINT IF EXISTS membresias_precio_duracion_check;
ALTER TABLE membresias ADD CONSTRAINT membresias_precio_duracion_check
    CHECK (precio > 0 AND duracion_dias BETWEEN 1 AND 3650);
ALTER TABLE pagos DROP CONSTRAINT IF EXISTS pagos_monto_check;
ALTER TABLE pagos ADD CONSTRAINT pagos_monto_check CHECK (monto > 0);
ALTER TABLE liquidacionessueldo DROP CONSTRAINT IF EXISTS liquidacionessueldo_monto_check;
ALTER TABLE liquidacionessueldo ADD CONSTRAINT liquidacionessueldo_monto_check CHECK (monto > 0);

COMMIT;
