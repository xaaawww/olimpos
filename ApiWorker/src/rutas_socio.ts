// Rutas del socio como persona: su ficha, datos físicos, marcas (Arena) y
// la Escalera del Olimpo (clasificación).

import {
  Contexto, Db, entero, ErrorApi, fechaLegible, Fila, idNumerico, MS, numero, OBJETIVOS, Ruta, texto,
} from "./util.js";

const SEXOS = ["MASCULINO", "FEMENINO", "PREFIERO_NO_DECIRLO"];
const NIVELES = ["Principiante", "Intermedio", "Avanzado"];

// ───────────── datos físicos ─────────────
// Se reparten en varias tablas (socios, perfilapp, progresopeso, objetivos,
// salud, perfilappsecciones) pero a la app le llegan como UN solo objeto, con
// los mismos nombres de campo de siempre.

const SQL_DATOS_FISICOS = `
  SELECT s.id_socio, s.firebase_uid, s.sexo, s.nivel_experiencia AS experiencia,
         p.edad, p.oculto_clasificacion, p.vio_plano, p.vistas_bodygraph,
         (SELECT pp.peso FROM progresopeso pp WHERE pp.id_socio = s.id_socio
            ORDER BY pp.fecha DESC, pp.id_progreso_peso DESC LIMIT 1) AS peso_kg,
         (SELECT o.tipo FROM objetivos o WHERE o.id_socio = s.id_socio AND o.estado = 'activo') AS objetivo,
         (SELECT sa.observaciones FROM salud sa WHERE sa.id_socio = s.id_socio AND sa.observaciones IS NOT NULL
            ORDER BY sa.fecha DESC, sa.id_salud DESC LIMIT 1) AS condicion_medica
  FROM socios s LEFT JOIN perfilapp p USING (id_socio)`;

function datosFisicosJson(f: Fila, incluirPrivados: boolean): Fila {
  return {
    peso_kg: f.peso_kg === null ? null : Number(f.peso_kg),
    edad: f.edad ?? 0,
    sexo: f.sexo ?? "PREFIERO_NO_DECIRLO",
    experiencia: f.experiencia ?? "",
    condicion_medica: incluirPrivados ? f.condicion_medica ?? "" : "",
    oculto_clasificacion: f.oculto_clasificacion ?? false,
    vio_plano: f.vio_plano ?? false,
    vistas_bodygraph: f.vistas_bodygraph ?? 0,
    objetivo: f.objetivo ?? null,
  };
}

async function asegurarPerfilApp(db: Db, idSocio: number) {
  await db.query("INSERT INTO perfilapp (id_socio, debe_cambiar_password) VALUES ($1, FALSE) ON CONFLICT (id_socio) DO NOTHING", [idSocio]);
}

async function fijarObjetivo(db: Db, idSocio: number, objetivo: string) {
  await db.query("UPDATE objetivos SET estado = 'historico' WHERE id_socio = $1 AND estado = 'activo' AND tipo <> $2", [idSocio, objetivo]);
  await db.query(
    `INSERT INTO objetivos (id_socio, tipo, prioridad, estado)
     SELECT $1::int, $2::text, 'principal', 'activo' WHERE NOT EXISTS
       (SELECT 1 FROM objetivos WHERE id_socio = $1 AND estado = 'activo')`,
    [idSocio, objetivo],
  );
}

const verYo: Ruta = {
  metodo: "GET", patron: /^\/v1\/yo$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT trim(s.nombre || ' ' || s.apellido) AS nombre, s.email, COALESCE(p.debe_cambiar_password, FALSE) AS debe
       FROM socios s LEFT JOIN perfilapp p USING (id_socio) WHERE s.id_socio = $1`, [c.idSocio]);
    const f = r.rows[0];
    return { nombre: f.nombre, email: f.email, debe_cambiar_password: f.debe };
  },
};

const passwordCambiada: Ruta = {
  metodo: "POST", patron: /^\/v1\/yo\/password-cambiada$/,
  async manejador(c) {
    await c.db.query(
      `INSERT INTO perfilapp (id_socio, debe_cambiar_password) VALUES ($1, FALSE)
       ON CONFLICT (id_socio) DO UPDATE SET debe_cambiar_password = FALSE`, [c.idSocio]);
    return { ok: true };
  },
};

const leerDatosFisicos: Ruta = {
  metodo: "GET", patron: /^\/v1\/datos-fisicos$/,
  async manejador(c) {
    const r = await c.db.query(`${SQL_DATOS_FISICOS} WHERE s.id_socio = $1`, [c.idSocio]);
    const f = r.rows[0];
    if (!f || f.peso_kg === null) return { existe: false };
    const secciones = await c.db.query("SELECT seccion FROM perfilappsecciones WHERE id_socio = $1", [c.idSocio]);
    return { existe: true, ...datosFisicosJson(f, true), secciones_arena_visitadas: secciones.rows.map((s) => s.seccion) };
  },
};

const guardarDatosFisicos: Ruta = {
  metodo: "PUT", patron: /^\/v1\/datos-fisicos$/,
  async manejador(c) {
    const b = c.body;
    const peso = numero(b.peso_kg, "peso_kg", 20, 400);
    const edad = entero(b.edad, "edad", 1, 120);
    if (!SEXOS.includes(b.sexo)) throw new ErrorApi(400, '"sexo" inválido.');
    const experiencia = b.experiencia ? texto(b.experiencia, "experiencia", 30) : null;
    if (experiencia && !NIVELES.includes(experiencia)) throw new ErrorApi(400, '"experiencia" inválida.');
    const condicion = texto(b.condicion_medica ?? "", "condicion_medica", 500, { vacio: true });
    const objetivo = b.objetivo ? String(b.objetivo) : null;
    if (objetivo && !(OBJETIVOS as readonly string[]).includes(objetivo)) throw new ErrorApi(400, '"objetivo" inválido.');
    const secciones: string[] = Array.isArray(b.secciones_arena_visitadas)
      ? [...new Set<string>(b.secciones_arena_visitadas.map((s: unknown) => texto(s, "seccion", 100)))].slice(0, 50)
      : [];

    await c.db.tx(async (db) => {
      await db.query("UPDATE socios SET sexo = $1, nivel_experiencia = $2 WHERE id_socio = $3", [b.sexo, experiencia, c.idSocio]);
      await db.query(
        `INSERT INTO perfilapp (id_socio, edad, debe_cambiar_password, oculto_clasificacion, vio_plano, vistas_bodygraph, fecha_actualizacion)
         VALUES ($1, $2, FALSE, $3, $4, $5, now())
         ON CONFLICT (id_socio) DO UPDATE SET edad = EXCLUDED.edad, oculto_clasificacion = EXCLUDED.oculto_clasificacion,
           vio_plano = EXCLUDED.vio_plano, vistas_bodygraph = EXCLUDED.vistas_bodygraph, fecha_actualizacion = now()`,
        [c.idSocio, edad, !!b.oculto_clasificacion, !!b.vio_plano, Math.max(0, Number(b.vistas_bodygraph) || 0)],
      );
      // El peso es un historial: solo se agrega una fila si cambió.
      await db.query(
        `INSERT INTO progresopeso (id_socio, fecha, peso)
         SELECT $1::int, CURRENT_DATE, $2::numeric WHERE COALESCE((SELECT pp.peso FROM progresopeso pp WHERE pp.id_socio = $1
           ORDER BY pp.fecha DESC, pp.id_progreso_peso DESC LIMIT 1), -1) <> $2::numeric`, [c.idSocio, peso]);
      if (objetivo) await fijarObjetivo(db, c.idSocio, objetivo);
      await db.query(
        `INSERT INTO salud (id_socio, fecha, observaciones)
         SELECT $1::int, now(), $2::text WHERE COALESCE((SELECT sa.observaciones FROM salud sa WHERE sa.id_socio = $1 AND sa.observaciones IS NOT NULL
           ORDER BY sa.fecha DESC, sa.id_salud DESC LIMIT 1), '') <> $2::text`, [c.idSocio, condicion]);
      for (const s of secciones) {
        await db.query("INSERT INTO perfilappsecciones (id_socio, seccion) VALUES ($1, $2) ON CONFLICT DO NOTHING", [c.idSocio, s]);
      }
    });
    return { ok: true };
  },
};

const actualizarDatosFisicos: Ruta = {
  metodo: "POST", patron: /^\/v1\/datos-fisicos\/parcial$/,
  async manejador(c) {
    const b = c.body;
    await c.db.tx(async (db) => {
      await asegurarPerfilApp(db, c.idSocio);
      if (b.objetivo !== undefined) {
        if (!(OBJETIVOS as readonly string[]).includes(b.objetivo)) throw new ErrorApi(400, '"objetivo" inválido.');
        await fijarObjetivo(db, c.idSocio, b.objetivo);
      }
      if (typeof b.oculto_clasificacion === "boolean") {
        await db.query("UPDATE perfilapp SET oculto_clasificacion = $1 WHERE id_socio = $2", [b.oculto_clasificacion, c.idSocio]);
      }
      if (b.vio_plano === true) await db.query("UPDATE perfilapp SET vio_plano = TRUE WHERE id_socio = $1", [c.idSocio]);
      if (b.incrementar_vista_bodygraph === true) {
        await db.query("UPDATE perfilapp SET vistas_bodygraph = vistas_bodygraph + 1 WHERE id_socio = $1", [c.idSocio]);
      }
      if (b.seccion_arena !== undefined) {
        await db.query("INSERT INTO perfilappsecciones (id_socio, seccion) VALUES ($1, $2) ON CONFLICT DO NOTHING",
          [c.idSocio, texto(b.seccion_arena, "seccion_arena", 100)]);
      }
    });
    return { ok: true };
  },
};

// ───────────── marcas personales (Arena) ─────────────

const SQL_MARCAS = `
  SELECT mp.id_marca, s.firebase_uid, trim(s.nombre || ' ' || s.apellido) AS socio_nombre, e.nombre AS ejercicio,
         mp.peso, mp.repeticiones, ${MS("mp.fecha")} AS ts, mp.estado
  FROM marcaspersonales mp JOIN socios s USING (id_socio)
  JOIN ejerciciosmarca em USING (id_ejercicio_marca) JOIN ejercicios e ON e.id_ejercicio = em.id_ejercicio
  WHERE mp.estado <> 'rechazada'`;

function marcaJson(f: Fila): Fila {
  return {
    id: String(f.id_marca), socio_id: f.firebase_uid, socio_nombre: f.socio_nombre, ejercicio: f.ejercicio,
    peso: Number(f.peso), repeticiones: f.repeticiones, fecha: fechaLegible(f.ts), timestamp: f.ts,
    verificado: f.estado === "verificada",
  };
}

const misMarcas: Ruta = {
  metodo: "GET", patron: /^\/v1\/marcas$/,
  async manejador(c) {
    const r = await c.db.query(`${SQL_MARCAS} AND mp.id_socio = $1 ORDER BY mp.fecha DESC`, [c.idSocio]);
    return { marcas: r.rows.map(marcaJson) };
  },
};

const nuevaMarca: Ruta = {
  metodo: "POST", patron: /^\/v1\/marcas$/,
  async manejador(c) {
    const ejercicio = texto(c.body.ejercicio, "ejercicio", 100);
    const peso = numero(c.body.peso, "peso", 0, 1000);
    const reps = entero(c.body.repeticiones, "repeticiones", 1, 1000);
    // La fecha la manda el celular; si está muy lejos de la real se usa la del servidor.
    let ts = Number(c.body.timestamp);
    if (!Number.isFinite(ts) || Math.abs(ts - c.ahora.getTime()) > 7 * 86_400_000) ts = c.ahora.getTime();
    const r = await c.db.query(
      `INSERT INTO marcaspersonales (id_socio, id_ejercicio_marca, peso, repeticiones, uno_rm_estimado, peso_corporal, fecha, estado)
       SELECT $1, em.id_ejercicio_marca, $3::numeric, $4::int, round($3::numeric * (1 + $4::numeric / 30), 2),
              (SELECT pp.peso FROM progresopeso pp WHERE pp.id_socio = $1 ORDER BY pp.fecha DESC, pp.id_progreso_peso DESC LIMIT 1),
              to_timestamp($5::float8 / 1000.0), 'pendiente'
       FROM ejerciciosmarca em JOIN ejercicios e ON e.id_ejercicio = em.id_ejercicio WHERE e.nombre = $2
       RETURNING id_marca`,
      [c.idSocio, ejercicio, peso, reps, ts]);
    if (!r.rows.length) throw new ErrorApi(400, `"${ejercicio}" no es un ejercicio de la Calculadora.`);
    return { id: String(r.rows[0].id_marca) };
  },
};

const borrarMarca: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/marcas\/([0-9]+)$/,
  async manejador(c) {
    const r = await c.db.query("DELETE FROM marcaspersonales WHERE id_marca = $1 AND id_socio = $2", [idNumerico(c.params[0]), c.idSocio]);
    if (!r.rowCount) throw new ErrorApi(404, "Esa marca no existe.");
    return { ok: true };
  },
};

// ───────────── Escalera del Olimpo ─────────────
// Todo lo que hace falta para armar el ranking de TODOS los socios en una sola
// llamada. Datos sensibles (condición médica) nunca salen de acá.

const clasificacion: Ruta = {
  metodo: "GET", patron: /^\/v1\/clasificacion$/,
  async manejador(c) {
    const [marcas, socios, datos] = await Promise.all([
      c.db.query(`${SQL_MARCAS} AND s.estado = 'activo' ORDER BY mp.fecha DESC`),
      c.db.query(`SELECT firebase_uid, ${MS("fecha_registro")} AS creado_ms FROM socios WHERE estado = 'activo' AND firebase_uid IS NOT NULL`),
      c.db.query(`${SQL_DATOS_FISICOS} WHERE s.estado = 'activo' AND s.firebase_uid IS NOT NULL`),
    ]);
    const datosPorUid: Record<string, Fila> = {};
    for (const f of datos.rows) if (f.peso_kg !== null) datosPorUid[f.firebase_uid] = datosFisicosJson(f, false);
    return {
      marcas: marcas.rows.map(marcaJson),
      socios: Object.fromEntries(socios.rows.map((s) => [s.firebase_uid, s.creado_ms])),
      datos_fisicos: datosPorUid,
    };
  },
};

// ───────────── series de entrenamiento ─────────────

const misSeries: Ruta = {
  metodo: "GET", patron: /^\/v1\/series$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT id_serie, ejercicio, peso, repeticiones, es_peso_corporal, ${MS("fecha")} AS ts
       FROM seriesentrenamiento WHERE id_socio = $1 ORDER BY fecha`, [c.idSocio]);
    return {
      series: r.rows.map((f) => ({
        id: String(f.id_serie), ejercicio: f.ejercicio, peso: Number(f.peso ?? 0), repeticiones: f.repeticiones,
        timestamp: f.ts, es_peso_corporal: f.es_peso_corporal,
      })),
    };
  },
};

const nuevaSerie: Ruta = {
  metodo: "POST", patron: /^\/v1\/series$/,
  async manejador(c) {
    const ejercicio = texto(c.body.ejercicio, "ejercicio", 255);
    const peso = numero(c.body.peso, "peso", 0, 1000);
    const reps = entero(c.body.repeticiones, "repeticiones", 1, 1000);
    let ts = Number(c.body.timestamp);
    if (!Number.isFinite(ts) || Math.abs(ts - c.ahora.getTime()) > 86_400_000) ts = c.ahora.getTime();
    await c.db.query(
      `INSERT INTO seriesentrenamiento (id_socio, ejercicio, numero_serie, peso, repeticiones, es_peso_corporal, fecha)
       VALUES ($1, $2::text,
         1 + (SELECT count(*) FROM seriesentrenamiento WHERE id_socio = $1 AND ejercicio = $2::text
              AND fecha::date = to_timestamp($6::float8 / 1000.0)::date),
         $3, $4, $5, to_timestamp($6::float8 / 1000.0))`,
      [c.idSocio, ejercicio, peso, reps, !!c.body.es_peso_corporal, ts]);
    return { ok: true };
  },
};

export const rutasSocio: Ruta[] = [
  verYo, passwordCambiada, leerDatosFisicos, guardarDatosFisicos, actualizarDatosFisicos,
  misMarcas, nuevaMarca, borrarMarca, clasificacion, misSeries, nuevaSerie,
];

export type { Contexto };
