// Rutas de entrenamiento y actividad en el club: rutinas, catálogo de
// ejercicios, clases, ingresos, lockers, compañeros y fotos de progreso.

import { claveSemana, Contexto, Db, entero, ErrorApi, Fila, idNumerico, MINUTOS_EN_EL_CLUB, MS, numero, Ruta, texto } from "./util.js";

// ───────────── catálogo de ejercicios (Galería) ─────────────

const catalogoEjercicios: Ruta = {
  metodo: "GET", patron: /^\/v1\/ejercicios$/,
  async manejador(c) {
    const [ejs, etq, puntos, etqPunto] = await Promise.all([
      c.db.query("SELECT id_ejercicio, nombre, descripcion FROM ejercicios WHERE estado = 'publicado' ORDER BY id_ejercicio"),
      c.db.query("SELECT id_ejercicio, etiqueta FROM ejercicioetiquetas ORDER BY id_ejercicio, orden"),
      c.db.query("SELECT id_ejercicio, punto_id, zona, nombre, descripcion FROM ejerciciopuntos ORDER BY id_ejercicio, orden"),
      c.db.query("SELECT id_ejercicio, punto_id, etiqueta FROM puntoetiquetas ORDER BY id_ejercicio, punto_id, orden"),
    ]);
    const tagsDe = new Map<number, string[]>();
    for (const e of etq.rows) tagsDe.set(e.id_ejercicio, [...(tagsDe.get(e.id_ejercicio) ?? []), e.etiqueta]);
    const tagsPunto = new Map<string, string[]>();
    for (const e of etqPunto.rows) {
      const k = `${e.id_ejercicio}/${e.punto_id}`;
      tagsPunto.set(k, [...(tagsPunto.get(k) ?? []), e.etiqueta]);
    }
    const puntosDe = new Map<number, Fila[]>();
    for (const p of puntos.rows) {
      puntosDe.set(p.id_ejercicio, [...(puntosDe.get(p.id_ejercicio) ?? []), {
        id: p.punto_id, zona: p.zona, nombre: p.nombre, descripcion: p.descripcion,
        tags: tagsPunto.get(`${p.id_ejercicio}/${p.punto_id}`) ?? [],
      }]);
    }
    return {
      ejercicios: ejs.rows.map((e) => ({
        id: String(e.id_ejercicio), nombre: e.nombre, descripcion: e.descripcion ?? "",
        tags: tagsDe.get(e.id_ejercicio) ?? [], puntos: puntosDe.get(e.id_ejercicio) ?? [],
      })),
    };
  },
};

// ───────────── rutinas (las del entrenador y las que arma el socio) ─────────────

async function rutinasDe(db: Db, idSocio: number): Promise<Fila[]> {
  const rutinas = await db.query(
    `SELECT cod_rutina, nombre, creada_por, origen, activa FROM rutinas WHERE id_socio = $1 ORDER BY cod_rutina`, [idSocio]);
  if (!rutinas.rows.length) return [];
  const ejercicios = await db.query(
    `SELECT cod_rutina, id_ejercicio, nombre, series, peso, es_peso_corporal FROM rutinaejercicio
     WHERE cod_rutina = ANY($1::int[]) ORDER BY cod_rutina, orden`, [rutinas.rows.map((r) => r.cod_rutina)]);
  const de = new Map<number, Fila[]>();
  for (const e of ejercicios.rows) {
    de.set(e.cod_rutina, [...(de.get(e.cod_rutina) ?? []), {
      nombre: e.nombre, series_objetivo: e.series ?? 3, peso_base_kg: Number(e.peso ?? 0),
      es_peso_corporal: e.es_peso_corporal, ejercicio_id: e.id_ejercicio === null ? null : String(e.id_ejercicio),
    }]);
  }
  return rutinas.rows.map((r) => ({
    id: String(r.cod_rutina), nombre: r.nombre, creada_por: r.creada_por ?? "", origen: r.origen, activa: r.activa,
    ejercicios: de.get(r.cod_rutina) ?? [],
  }));
}

/** Valida y normaliza los ejercicios que manda la app al armar una rutina propia. */
async function ejerciciosDeBody(db: Db, v: unknown): Promise<Fila[]> {
  if (!Array.isArray(v) || v.length < 1) throw new ErrorApi(400, "Agregá al menos un ejercicio.");
  if (v.length > 60) throw new ErrorApi(400, "Una rutina no puede tener más de 60 ejercicios.");
  const idsPedidos = v.map((e) => (e?.ejercicio_id ? String(e.ejercicio_id) : null)).filter((x): x is string => !!x && /^[0-9]+$/.test(x));
  const existentes = new Set<string>();
  if (idsPedidos.length) {
    const r = await db.query("SELECT id_ejercicio FROM ejercicios WHERE id_ejercicio = ANY($1::int[])", [idsPedidos.map(Number)]);
    for (const f of r.rows) existentes.add(String(f.id_ejercicio));
  }
  return v.map((e) => ({
    nombre: texto(e?.nombre, "nombre del ejercicio", 255),
    series: entero(e?.series_objetivo ?? 3, "series", 1, 30),
    peso: numero(e?.peso_base_kg ?? 0, "peso", 0, 1000),
    corporal: !!e?.es_peso_corporal,
    // si el id ya no existe en el catálogo, queda como ejercicio escrito a mano
    ejercicioId: e?.ejercicio_id && existentes.has(String(e.ejercicio_id)) ? Number(e.ejercicio_id) : null,
  }));
}

async function guardarEjerciciosRutina(db: Db, cod: number, ejercicios: Fila[]) {
  for (let i = 0; i < ejercicios.length; i++) {
    const e = ejercicios[i];
    await db.query(
      `INSERT INTO rutinaejercicio (cod_rutina, id_ejercicio, orden, nombre, series, peso, es_peso_corporal)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`, [cod, e.ejercicioId, i, e.nombre, e.series, e.peso, e.corporal]);
  }
}

async function rutinaPropia(db: Db, idSocio: number, idTexto: string, soloSocio: boolean): Promise<Fila> {
  const r = await db.query("SELECT cod_rutina, origen FROM rutinas WHERE cod_rutina = $1 AND id_socio = $2", [idNumerico(idTexto), idSocio]);
  if (!r.rows.length) throw new ErrorApi(404, "Esa rutina no existe.");
  if (soloSocio && r.rows[0].origen !== "socio") throw new ErrorApi(403, "Las rutinas armadas por tu entrenador no se pueden modificar desde la app.");
  return r.rows[0];
}

const listarRutinas: Ruta = {
  metodo: "GET", patron: /^\/v1\/rutinas$/,
  async manejador(c) { return { rutinas: await rutinasDe(c.db, c.idSocio) }; },
};

const crearRutina: Ruta = {
  metodo: "POST", patron: /^\/v1\/rutinas$/,
  async manejador(c) {
    const nombre = texto(c.body.nombre, "nombre", 255);
    return c.db.tx(async (db) => {
      const ejercicios = await ejerciciosDeBody(db, c.body.ejercicios);
      // La primera rutina que tiene el socio queda activa sola; si ya seguía
      // otra, no se le cambia sin que él lo elija.
      const previas = await db.query("SELECT 1 FROM rutinas WHERE id_socio = $1 LIMIT 1", [c.idSocio]);
      const r = await db.query(
        `INSERT INTO rutinas (id_socio, nombre, creada_por, origen, activa) VALUES ($1, $2, 'Vos mismo', 'socio', $3) RETURNING cod_rutina`,
        [c.idSocio, nombre, previas.rows.length === 0]);
      await guardarEjerciciosRutina(db, r.rows[0].cod_rutina, ejercicios);
      return { id: String(r.rows[0].cod_rutina) };
    });
  },
};

const editarRutina: Ruta = {
  metodo: "PUT", patron: /^\/v1\/rutinas\/([0-9]+)$/,
  async manejador(c) {
    const nombre = texto(c.body.nombre, "nombre", 255);
    return c.db.tx(async (db) => {
      const rutina = await rutinaPropia(db, c.idSocio, c.params[0], true);
      const ejercicios = await ejerciciosDeBody(db, c.body.ejercicios);
      await db.query("UPDATE rutinas SET nombre = $1, fecha_actualizacion = now() WHERE cod_rutina = $2", [nombre, rutina.cod_rutina]);
      await db.query("DELETE FROM rutinaejercicio WHERE cod_rutina = $1", [rutina.cod_rutina]);
      await guardarEjerciciosRutina(db, rutina.cod_rutina, ejercicios);
      return { ok: true };
    });
  },
};

const borrarRutina: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/rutinas\/([0-9]+)$/,
  async manejador(c) {
    const rutina = await rutinaPropia(c.db, c.idSocio, c.params[0], true);
    await c.db.query("DELETE FROM rutinas WHERE cod_rutina = $1", [rutina.cod_rutina]);
    return { ok: true };
  },
};

const activarRutina: Ruta = {
  metodo: "POST", patron: /^\/v1\/rutinas\/([0-9]+)\/activar$/,
  async manejador(c) {
    return c.db.tx(async (db) => {
      const rutina = await rutinaPropia(db, c.idSocio, c.params[0], false);
      await db.query("UPDATE rutinas SET activa = FALSE WHERE id_socio = $1 AND activa", [c.idSocio]);
      await db.query("UPDATE rutinas SET activa = TRUE WHERE cod_rutina = $1", [rutina.cod_rutina]);
      return { ok: true };
    });
  },
};

// ───────────── clases y reservas (el cupo lo hace cumplir la base) ─────────────

const listarClases: Ruta = {
  metodo: "GET", patron: /^\/v1\/clases$/,
  async manejador(c) {
    const semana = claveSemana(c.ahora);
    const [clases, mias] = await Promise.all([
      c.db.query(
        `SELECT c.codigo, c.capacidad,
           (SELECT count(*)::int FROM reservasclase r WHERE r.id_clase = c.id_clase AND r.semana = $1 AND r.estado = 'confirmada') AS reservados
         FROM clases c WHERE c.estado = 'activa' AND c.codigo IS NOT NULL ORDER BY c.id_clase`, [semana]),
      c.db.query(
        `SELECT c.codigo, ${MS("r.fecha_reserva")} AS ts FROM reservasclase r JOIN clases c USING (id_clase)
         WHERE r.id_socio = $1 AND r.semana = $2 AND r.estado = 'confirmada'`, [c.idSocio, semana]),
    ]);
    return {
      semana,
      clases: clases.rows.map((f) => ({ id: f.codigo, cupo: f.capacidad, reservados: f.reservados })),
      mis_reservas: mias.rows.map((f) => ({ clase_id: f.codigo, timestamp: f.ts })),
    };
  },
};

const reservarClase: Ruta = {
  metodo: "POST", patron: /^\/v1\/clases\/([a-z0-9-]{1,50})\/reservar$/,
  async manejador(c) {
    const semana = claveSemana(c.ahora);
    return c.db.tx(async (db) => {
      // FOR UPDATE: dos socios que reservan a la vez la última plaza se ponen
      // en fila — el segundo ve la clase llena en vez de pasarse del cupo.
      const cl = await db.query("SELECT id_clase, capacidad FROM clases WHERE codigo = $1 AND estado = 'activa' FOR UPDATE", [c.params[0]]);
      if (!cl.rows.length) throw new ErrorApi(404, "Esa clase no existe.");
      const { id_clase, capacidad } = cl.rows[0];
      const ya = await db.query(
        "SELECT 1 FROM reservasclase WHERE id_clase = $1 AND id_socio = $2 AND semana = $3 AND estado = 'confirmada'", [id_clase, c.idSocio, semana]);
      if (ya.rows.length) return { resultado: "YA_RESERVADA" };
      const n = await db.query(
        "SELECT count(*)::int AS n FROM reservasclase WHERE id_clase = $1 AND semana = $2 AND estado = 'confirmada'", [id_clase, semana]);
      if (n.rows[0].n >= capacidad) return { resultado: "CLASE_LLENA" };
      await db.query("INSERT INTO reservasclase (id_clase, id_socio, semana, estado) VALUES ($1, $2, $3, 'confirmada')", [id_clase, c.idSocio, semana]);
      return { resultado: "OK" };
    });
  },
};

const cancelarClase: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/clases\/([a-z0-9-]{1,50})\/reserva$/,
  async manejador(c) {
    await c.db.query(
      `UPDATE reservasclase SET estado = 'cancelada' WHERE id_socio = $1 AND semana = $2 AND estado = 'confirmada'
         AND id_clase = (SELECT id_clase FROM clases WHERE codigo = $3)`, [c.idSocio, claveSemana(c.ahora), c.params[0]]);
    return { ok: true };
  },
};

// ───────────── ingresos al gimnasio ─────────────

const listarIngresos: Ruta = {
  metodo: "GET", patron: /^\/v1\/ingresos$/,
  async manejador(c) {
    const r = await c.db.query(`SELECT ${MS("fecha")} AS ts, metodo FROM accesos WHERE id_socio = $1 ORDER BY fecha`, [c.idSocio]);
    return { ingresos: r.rows.map((f) => ({ timestamp: f.ts, metodo: f.metodo })) };
  },
};

// ── QR de entrada ──
// Recepción muestra en la PC del mostrador un QR que cambia cada 30 segundos
// (Aplicaciones/olimpos_gym/qr_ingreso_repo.py): "OLIMPOS-INGRESO:<ventana>:<código>",
// con código = primeros 16 hex de HMAC-SHA256(clave, ventana). La clave está
// en configuracionsistema ("qr_ingreso"); acá se rehace la misma cuenta. Se
// aceptan unas pocas ventanas de diferencia por si el reloj de la PC y el de
// Cloudflare no coinciden exacto.
const VENTANA_QR_SEGUNDOS = 30;
const VENTANAS_TOLERADAS = 4;   // ±2 minutos

async function hmacHex(claveHex: string, mensaje: string): Promise<string> {
  const bytes = new Uint8Array(claveHex.match(/../g)!.map((h) => parseInt(h, 16)));
  const clave = await crypto.subtle.importKey("raw", bytes, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const firma = new Uint8Array(await crypto.subtle.sign("HMAC", clave, new TextEncoder().encode(mensaje)));
  return Array.from(firma, (b) => b.toString(16).padStart(2, "0")).join("");
}

async function qrValido(db: Db, contenido: unknown, ahora: Date): Promise<boolean> {
  const m = /^OLIMPOS-INGRESO:([0-9]{1,12}):([0-9a-f]{16})$/.exec(typeof contenido === "string" ? contenido.trim() : "");
  if (!m) return false;
  const ventana = Number(m[1]);
  if (Math.abs(ventana - Math.floor(ahora.getTime() / 1000 / VENTANA_QR_SEGUNDOS)) > VENTANAS_TOLERADAS) return false;
  const r = await db.query("SELECT valor->>'secreto' AS secreto FROM configuracionsistema WHERE clave = 'qr_ingreso'");
  const secreto = r.rows[0]?.secreto;
  if (!secreto || !/^[0-9a-f]{64}$/.test(secreto)) return false;
  return (await hmacHex(secreto, String(ventana))).slice(0, 16) === m[2];
}

// Lo llama la app después de escanear el QR de la recepción: así el ingreso
// lo confirma el club, no el propio socio. Si ya había entrado hace menos de
// MINUTOS_EN_EL_CLUB no se agrega otra fila (escanear dos veces es una sola
// entrada y no infla la ocupación ni los logros).
const registrarIngreso: Ruta = {
  metodo: "POST", patron: /^\/v1\/ingresos$/,
  async manejador(c) {
    if (!c.body.qr) throw new ErrorApi(400, "Escaneá el QR de la recepción para registrar tu entrada.");
    if (!(await qrValido(c.db, c.body.qr, c.ahora))) {
      throw new ErrorApi(400, "Ese QR no es válido o ya venció. Escaneá el que está en la pantalla de la recepción.");
    }
    const r = await c.db.query(
      `INSERT INTO accesos (id_socio, metodo, resultado)
       SELECT $1::int, 'qr', 'permitido'
       WHERE NOT EXISTS (SELECT 1 FROM accesos WHERE id_socio = $1::int AND resultado = 'permitido'
                         AND fecha > now() - make_interval(mins => $2::int))
       RETURNING id_acceso`, [c.idSocio, MINUTOS_EN_EL_CLUB]);
    const desde = await c.db.query(
      `SELECT ${MS("max(fecha)")} AS ts FROM accesos WHERE id_socio = $1 AND resultado = 'permitido'`, [c.idSocio]);
    return { ok: true, nuevo: r.rows.length > 0, desde: desde.rows[0]?.ts ?? null };
  },
};

// ───────────── lockers ─────────────

const listarLockers: Ruta = {
  metodo: "GET", patron: /^\/v1\/lockers$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT l.numero, s.firebase_uid FROM reservaslocker rl JOIN lockers l USING (id_locker)
       JOIN socios s ON s.id_socio = rl.id_socio WHERE rl.estado = 'activa'`);
    return { lockers: r.rows.map((f) => ({ numero: Number(f.numero), socio_id: f.firebase_uid })) };
  },
};

const reservarLocker: Ruta = {
  metodo: "POST", patron: /^\/v1\/lockers\/reservar$/,
  async manejador(c) {
    const numero = String(entero(c.body.numero, "numero", 1, 9999));
    return c.db.tx(async (db) => {
      const l = await db.query("SELECT id_locker FROM lockers WHERE numero = $1", [numero]);
      if (!l.rows.length) throw new ErrorApi(404, "Ese locker no existe.");
      await db.query("UPDATE reservaslocker SET estado = 'liberada', fecha_fin = now() WHERE id_socio = $1 AND estado = 'activa'", [c.idSocio]);
      try {
        await db.query("INSERT INTO reservaslocker (id_locker, id_socio, estado) VALUES ($1, $2, 'activa')", [l.rows[0].id_locker, c.idSocio]);
      } catch (e: any) {
        // El índice único de la base impide que dos socios tengan el mismo locker.
        // Al lanzar, se deshace TODA la transacción: el socio conserva el locker que ya tenía.
        if (e?.code === "23505") throw new ErrorApi(409, "Ese locker ya lo tiene otro socio.");
        throw e;
      }
      return { ok: true };
    });
  },
};

const liberarLocker: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/lockers\/mio$/,
  async manejador(c) {
    await c.db.query("UPDATE reservaslocker SET estado = 'liberada', fecha_fin = now() WHERE id_socio = $1 AND estado = 'activa'", [c.idSocio]);
    return { ok: true };
  },
};

// ───────────── compañeros de entrenamiento ─────────────

const listarCompaneros: Ruta = {
  metodo: "GET", patron: /^\/v1\/companeros$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT s.firebase_uid, trim(s.nombre || ' ' || s.apellido) AS nombre FROM companeros k
       JOIN socios s ON s.id_socio = k.id_companero WHERE k.id_socio = $1 ORDER BY k.fecha_agregado`, [c.idSocio]);
    return { companeros: r.rows.map((f) => ({ socio_id: f.firebase_uid, nombre: f.nombre })) };
  },
};

const agregarCompanero: Ruta = {
  metodo: "POST", patron: /^\/v1\/companeros$/,
  async manejador(c) {
    const uid = texto(c.body.companero_id, "companero_id", 128);
    const r = await c.db.query(
      `INSERT INTO companeros (id_socio, id_companero) SELECT $1, id_socio FROM socios WHERE firebase_uid = $2 AND id_socio <> $1
       ON CONFLICT DO NOTHING`, [c.idSocio, uid]);
    if (r.rowCount === 0) {
      const existe = await c.db.query("SELECT 1 FROM socios WHERE firebase_uid = $1 AND id_socio <> $2", [uid, c.idSocio]);
      if (!existe.rows.length) throw new ErrorApi(404, "Ese socio no existe.");
    }
    return { ok: true };
  },
};

const quitarCompanero: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/companeros\/([A-Za-z0-9_-]{1,128})$/,
  async manejador(c) {
    await c.db.query(
      "DELETE FROM companeros WHERE id_socio = $1 AND id_companero = (SELECT id_socio FROM socios WHERE firebase_uid = $2)", [c.idSocio, c.params[0]]);
    return { ok: true };
  },
};

const diasConCompaneros: Ruta = {
  metodo: "GET", patron: /^\/v1\/companeros\/dias-juntos$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT count(*)::int AS dias FROM (
         SELECT DISTINCT (fecha AT TIME ZONE 'UTC')::date AS d FROM marcaspersonales WHERE id_socio = $1 AND estado <> 'rechazada'
         INTERSECT
         SELECT DISTINCT (fecha AT TIME ZONE 'UTC')::date FROM marcaspersonales WHERE estado <> 'rechazada'
           AND id_socio IN (SELECT id_companero FROM companeros WHERE id_socio = $1)
       ) x`, [c.idSocio]);
    return { dias: r.rows[0].dias };
  },
};

// ───────────── fotos de progreso ─────────────

const listarFotosProgreso: Ruta = {
  metodo: "GET", patron: /^\/v1\/fotos-progreso$/,
  async manejador(c) {
    const r = await c.db.query(`SELECT id_foto, imagen, ${MS("fecha")} AS ts FROM fotosprogreso WHERE id_socio = $1 ORDER BY fecha`, [c.idSocio]);
    return { fotos: r.rows.map((f) => ({ id: String(f.id_foto), imagen: f.imagen, timestamp: f.ts })) };
  },
};

const subirFotoProgreso: Ruta = {
  metodo: "POST", patron: /^\/v1\/fotos-progreso$/,
  async manejador(c) {
    const imagen = texto(c.body.imagen, "imagen", 1_000_000);
    if (!/^[A-Za-z0-9+/=\r\n]+$/.test(imagen.slice(0, 2000))) throw new ErrorApi(400, "La imagen no está en el formato esperado.");
    const r = await c.db.query("INSERT INTO fotosprogreso (id_socio, imagen) VALUES ($1, $2) RETURNING id_foto", [c.idSocio, imagen]);
    return { id: String(r.rows[0].id_foto) };
  },
};

const borrarFotoProgreso: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/fotos-progreso\/([0-9]+)$/,
  async manejador(c) {
    await c.db.query("DELETE FROM fotosprogreso WHERE id_foto = $1 AND id_socio = $2", [idNumerico(c.params[0]), c.idSocio]);
    return { ok: true };
  },
};

export const rutasEntrenamiento: Ruta[] = [
  catalogoEjercicios, listarRutinas, crearRutina, editarRutina, borrarRutina, activarRutina,
  listarClases, reservarClase, cancelarClase, listarIngresos, registrarIngreso,
  listarLockers, reservarLocker, liberarLocker,
  diasConCompaneros, listarCompaneros, agregarCompanero, quitarCompanero,
  listarFotosProgreso, subirFotoProgreso, borrarFotoProgreso,
];

export type { Contexto };
export { qrValido };
