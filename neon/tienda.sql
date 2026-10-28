-- OLIMPOS GYM — Tienda (suplementos, accesorios, ropa…)
--
-- El dueño carga los productos desde el sistema de empleados (sección Tienda).
-- El socio arma un pedido en la app; queda reservado (descuenta el stock) y lo
-- paga y retira en la recepción, donde se marca como entregado. Si se cancela,
-- el stock vuelve.
--
-- Solo crea tablas nuevas: no toca ninguna de las que ya existen. Es seguro
-- volver a correrlo.

BEGIN;

CREATE TABLE IF NOT EXISTS productos (
    id_producto          SERIAL PRIMARY KEY,
    nombre               VARCHAR(80)  NOT NULL,
    descripcion          VARCHAR(1000),
    precio               NUMERIC(12,2) NOT NULL CHECK (precio > 0 AND precio <= 10000000),
    stock                INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0 AND stock <= 100000),
    imagen               TEXT,                         -- JPEG en Base64 (como platos.imagen)
    publicado            BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_actualizacion  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_productos_nombre_lower ON productos (lower(nombre));

CREATE TABLE IF NOT EXISTS productoetiquetas (
    id_producto  INTEGER NOT NULL REFERENCES productos (id_producto) ON DELETE CASCADE,
    etiqueta     VARCHAR(30) NOT NULL,
    orden        SMALLINT NOT NULL DEFAULT 0,
    PRIMARY KEY (id_producto, etiqueta)
);

CREATE TABLE IF NOT EXISTS pedidostienda (
    id_pedido            SERIAL PRIMARY KEY,
    id_socio             INTEGER NOT NULL REFERENCES socios (id_socio) ON DELETE CASCADE,
    estado               VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                         CHECK (estado IN ('pendiente', 'entregado', 'cancelado')),
    total                NUMERIC(12,2) NOT NULL CHECK (total > 0),
    fecha                TIMESTAMPTZ NOT NULL DEFAULT now(),
    fecha_cierre         TIMESTAMPTZ,                  -- cuando se entregó o se canceló
    id_empleado_cierre   INTEGER REFERENCES empleados (id_empleado)
);
CREATE INDEX IF NOT EXISTS ix_pedidostienda_socio ON pedidostienda (id_socio, fecha DESC);

-- Nombre y precio se copian al hacer el pedido: si después cambia el precio,
-- el pedido sigue diciendo lo que se cobró.
CREATE TABLE IF NOT EXISTS pedidotiendaitems (
    id_pedido        INTEGER NOT NULL REFERENCES pedidostienda (id_pedido) ON DELETE CASCADE,
    id_producto      INTEGER NOT NULL REFERENCES productos (id_producto) ON DELETE RESTRICT,
    nombre           VARCHAR(80) NOT NULL,
    precio_unitario  NUMERIC(12,2) NOT NULL CHECK (precio_unitario > 0),
    cantidad         SMALLINT NOT NULL CHECK (cantidad BETWEEN 1 AND 20),
    PRIMARY KEY (id_pedido, id_producto)
);

-- SKU (código interno) y costo de compra (para el valor del stock y el margen).
ALTER TABLE productos ADD COLUMN IF NOT EXISTS sku VARCHAR(30);
ALTER TABLE productos ADD COLUMN IF NOT EXISTS costo NUMERIC(12,2) CHECK (costo IS NULL OR (costo >= 0 AND costo <= 10000000));
CREATE UNIQUE INDEX IF NOT EXISTS uq_productos_sku_upper ON productos (upper(sku)) WHERE sku IS NOT NULL;

COMMIT;
