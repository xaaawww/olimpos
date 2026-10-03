// Rutas del club: tablón de avisos, ocupación, membresía y pagos, Argos
// (asistente de IA) y el formulario de contacto de la página web.

import { ErrorApi, fechaLocalISO, MS, Ruta, texto } from "./util.js";

const tablon: Ruta = {
  metodo: "GET", patron: /^\/v1\/tablon$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT id_publicacion, titulo, mensaje, categoria, fijado, autor, ${MS("fecha_creacion")} AS creado_ms
       FROM tablonpublicaciones WHERE publicado ORDER BY fijado DESC, fecha_creacion DESC`);
    return {
      publicaciones: r.rows.map((f) => ({
        id: String(f.id_publicacion), titulo: f.titulo, mensaje: f.mensaje, categoria: f.categoria,
        fijado: f.fijado, creado_ms: f.creado_ms, autor: f.autor,
      })),
    };
  },
};

const ocupacion: Ruta = {
  metodo: "GET", patron: /^\/v1\/ocupacion$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT cantidad_personas, capacidad_maxima, ${MS("fecha")} AS ts FROM aforo ORDER BY fecha DESC, id_aforo DESC LIMIT 1`);
    const f = r.rows[0];
    return f ? { personas: f.cantidad_personas, capacidad_maxima: f.capacidad_maxima, actualizado_ms: f.ts } : { existe: false };
  },
};

const membresia: Ruta = {
  metodo: "GET", patron: /^\/v1\/membresia$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT m.nombre AS plan, m.incluye_argos, ${MS("sm.fecha_inicio::timestamp")} AS inicio_ms
       FROM sociomembresia sm JOIN membresias m USING (id_membresia) WHERE sm.id_socio = $1 AND sm.estado = 'activa'`, [c.idSocio]);
    const f = r.rows[0];
    return f ? { existe: true, plan: f.plan, fecha_inicio_ms: f.inicio_ms, incluye_argos: f.incluye_argos } : { existe: false };
  },
};

const pagos: Ruta = {
  metodo: "GET", patron: /^\/v1\/pagos$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT m.nombre AS plan, p.monto, p.estado, ${MS("p.fecha_pago")} AS ts
       FROM pagos p JOIN membresias m USING (id_membresia) WHERE p.id_socio = $1 ORDER BY p.fecha_pago DESC`, [c.idSocio]);
    return { pagos: r.rows.map((f) => ({ plan: f.plan, monto: Math.round(Number(f.monto)), estado: f.estado, fecha_ms: f.ts })) };
  },
};

// ───────────── Argos ─────────────

const MAXIMO_DIARIO_ARGOS = 300;

const baseArgos: Ruta = {
  metodo: "GET", patron: /^\/v1\/argos\/base-conocimiento$/,
  async manejador(c) {
    const r = await c.db.query("SELECT contenido FROM argosbaseconocimiento WHERE estado = 'activa'");
    return { texto: r.rows[0]?.contenido ?? "" };
  },
};

/** Lo llama el Worker de Argos con el token del socio ANTES de gastar plata en
 *  Anthropic: comprueba que el plan incluya Argos y que no se haya agotado el
 *  tope diario, y anota el uso. El tope es del club entero (suma de todos). */
const consumirArgos: Ruta = {
  metodo: "POST", patron: /^\/v1\/argos\/consumir$/,
  async manejador(c) {
    return c.db.tx(async (db) => {
      const plan = await db.query(
        `SELECT m.incluye_argos FROM sociomembresia sm JOIN membresias m USING (id_membresia)
         WHERE sm.id_socio = $1 AND sm.estado = 'activa'`, [c.idSocio]);
      if (!plan.rows[0]?.incluye_argos) {
        throw new ErrorApi(403, "Argos es parte de los planes Oro y Platino. Pedile a recepción que te active uno.");
      }
      const hoy = fechaLocalISO(c.ahora);
      const total = await db.query("SELECT COALESCE(sum(mensajes_enviados), 0)::int AS n FROM argoscupodiario WHERE fecha = $1", [hoy]);
      if (total.rows[0].n >= MAXIMO_DIARIO_ARGOS) {
        throw new ErrorApi(429, "Argos llegó al máximo de mensajes de hoy. Probá de nuevo mañana.");
      }
      await db.query(
        `INSERT INTO argoscupodiario (id_socio, fecha, mensajes_enviados, limite_diario) VALUES ($1, $2, 1, $3)
         ON CONFLICT (id_socio, fecha) WHERE id_socio IS NOT NULL DO UPDATE SET mensajes_enviados = argoscupodiario.mensajes_enviados + 1`,
        [c.idSocio, hoy, MAXIMO_DIARIO_ARGOS]);
      return { ok: true, restantes: MAXIMO_DIARIO_ARGOS - total.rows[0].n - 1 };
    });
  },
};

// ───────────── contacto de la página web (pública, sin login) ─────────────

const contactoWeb: Ruta = {
  metodo: "POST", patron: /^\/v1\/contacto$/, publica: true,
  async manejador(c) {
    const nombre = texto(c.body.nombre, "nombre", 100);
    const contacto = texto(c.body.contacto, "contacto", 150);
    const mensaje = texto(c.body.mensaje, "mensaje", 999);
    const esEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contacto);
    await c.db.query(
      "INSERT INTO contactosweb (nombre, email, telefono, mensaje) VALUES ($1, $2, $3, $4)",
      [nombre, esEmail ? contacto : null, esEmail ? null : contacto, mensaje]);
    return { ok: true };
  },
};

export const rutasClub: Ruta[] = [tablon, ocupacion, membresia, pagos, baseArgos, consumirArgos, contactoWeb];
