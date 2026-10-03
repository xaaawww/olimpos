// Rutas de nutrición: catálogo de platos, dieta asignada, comidas que el socio
// registra (con foto), platos probados, agua y preferencias alimentarias.

import {
  Contexto, Db, entero, ErrorApi, Fila, idNumerico, listaTextos, MOMENTOS, Momento, MS, OBJETIVOS, Ruta, texto, fechaLocalISO,
} from "./util.js";

// ───────────── catálogo de platos publicados ─────────────

const catalogoPlatos: Ruta = {
  metodo: "GET", patron: /^\/v1\/platos$/,
  async manejador(c) {
    const [platos, etq, ing, ingEtq, ingBen] = await Promise.all([
      c.db.query(
        `SELECT id_plato, nombre, descripcion, imagen, crop_x, crop_y, kcal, proteinas, carbs, grasas
         FROM platos WHERE estado = 'publicado' ORDER BY id_plato`),
      c.db.query("SELECT id_plato, etiqueta FROM platoetiquetas ORDER BY id_plato, orden"),
      c.db.query("SELECT id_plato, ingrediente_id, nombre, categoria, aporte, kcal_texto, x, y FROM platoingredientes ORDER BY id_plato, orden"),
      c.db.query("SELECT id_plato, ingrediente_id, etiqueta FROM ingredienteetiquetas ORDER BY id_plato, ingrediente_id, orden"),
      c.db.query("SELECT id_plato, ingrediente_id, beneficio FROM ingredientebeneficios ORDER BY id_plato, ingrediente_id, orden"),
    ]);
    const agrupar = (filas: Fila[], clave: (f: Fila) => string, valor: (f: Fila) => string) => {
      const m = new Map<string, string[]>();
      for (const f of filas) m.set(clave(f), [...(m.get(clave(f)) ?? []), valor(f)]);
      return m;
    };
    const tags = agrupar(etq.rows, (f) => String(f.id_plato), (f) => f.etiqueta);
    const tagsIng = agrupar(ingEtq.rows, (f) => `${f.id_plato}/${f.ingrediente_id}`, (f) => f.etiqueta);
    const benIng = agrupar(ingBen.rows, (f) => `${f.id_plato}/${f.ingrediente_id}`, (f) => f.beneficio);
    const puntos = new Map<number, Fila[]>();
    for (const i of ing.rows) {
      const k = `${i.id_plato}/${i.ingrediente_id}`;
      puntos.set(i.id_plato, [...(puntos.get(i.id_plato) ?? []), {
        id: i.ingrediente_id, x: i.x, y: i.y, nombre: i.nombre, categoria: i.categoria, kcal: i.kcal_texto,
        tags: tagsIng.get(k) ?? [], aporte: i.aporte, beneficios: benIng.get(k) ?? [],
      }]);
    }
    return {
      platos: platos.rows.map((p) => ({
        id: String(p.id_plato), nombre: p.nombre, descripcion: p.descripcion ?? "", imagen: p.imagen,
        crop_x: p.crop_x ?? 0, crop_y: p.crop_y ?? 0, tags: tags.get(String(p.id_plato)) ?? [], asignada: false,
        macros: { kcal: p.kcal ?? 0, proteinas: p.proteinas ?? 0, carbs: p.carbs ?? 0, grasas: p.grasas ?? 0 },
        puntos: puntos.get(p.id_plato) ?? [],
      })),
    };
  },
};

// ───────────── dieta asignada por el nutricionista ─────────────

const dietaAsignada: Ruta = {
  metodo: "GET", patron: /^\/v1\/dieta-asignada$/,
  async manejador(c) {
    const r = await c.db.query(
      `SELECT pp.momento, pp.id_plato, trim(e.nombre || ' ' || e.apellido) || ' — ' || ro.descripcion AS asignada_por
       FROM dietas d JOIN planalimentario pa USING (cod_dieta) JOIN planplato pp USING (id_plan_alimentario)
       JOIN empleados e ON e.id_empleado = d.id_empleado JOIN rol ro ON ro.id_rol = e.rol
       WHERE d.id_socio = $1 AND d.estado = 'vigente' AND pa.estado = 'vigente'
       ORDER BY pp.momento, pp.orden`, [c.idSocio]);
    if (!r.rows.length) return { existe: false };
    const comidas: Record<string, string[]> = { desayuno: [], almuerzo: [], cena: [] };
    for (const f of r.rows) comidas[f.momento].push(String(f.id_plato));
    return { existe: true, comidas, asignada_por: r.rows[0].asignada_por };
  },
};

// ───────────── platos probados ─────────────

const listarProbados: Ruta = {
  metodo: "GET", patron: /^\/v1\/platos-probados$/,
  async manejador(c) {
    const r = await c.db.query("SELECT id_plato FROM platosprobados WHERE id_socio = $1", [c.idSocio]);
    return { plato_ids: r.rows.map((f) => String(f.id_plato)) };
  },
};

const marcarProbado: Ruta = {
  metodo: "POST", patron: /^\/v1\/platos-probados$/,
  async manejador(c) {
    const id = idNumerico(String(c.body.plato_id ?? ""), "plato_id");
    await c.db.query("INSERT INTO platosprobados (id_socio, id_plato) VALUES ($1, $2) ON CONFLICT DO NOTHING", [c.idSocio, id]);
    return { ok: true };
  },
};

// ───────────── agua ─────────────

const listarAgua: Ruta = {
  metodo: "GET", patron: /^\/v1\/agua$/,
  async manejador(c) {
    const r = await c.db.query(`SELECT ${MS("fecha")} AS ts FROM registroagua WHERE id_socio = $1 ORDER BY fecha`, [c.idSocio]);
    return { registros: r.rows.map((f) => f.ts) };
  },
};

const registrarAgua: Ruta = {
  metodo: "POST", patron: /^\/v1\/agua$/,
  async manejador(c) {
    await c.db.query("INSERT INTO registroagua (id_socio) VALUES ($1)", [c.idSocio]);
    return { ok: true };
  },
};

// ───────────── preferencias alimentarias ─────────────

const leerPerfil: Ruta = {
  metodo: "GET", patron: /^\/v1\/perfil-nutricional$/,
  async manejador(c) {
    const [p, e] = await Promise.all([
      c.db.query("SELECT tipo FROM preferenciasalimentarias WHERE id_socio = $1 ORDER BY id_preferencia", [c.idSocio]),
      c.db.query("SELECT alimento FROM alimentosexcluidos WHERE id_socio = $1 ORDER BY id_exclusion", [c.idSocio]),
    ]);
    if (!p.rows.length && !e.rows.length) return { existe: false };
    return { existe: true, preferencias: p.rows.map((f) => f.tipo), excluidos: e.rows.map((f) => f.alimento) };
  },
};

const guardarPerfil: Ruta = {
  metodo: "PUT", patron: /^\/v1\/perfil-nutricional$/,
  async manejador(c) {
    const preferencias = listaTextos(c.body.preferencias, "preferencias", 30, 100);
    const excluidos = listaTextos(c.body.excluidos, "excluidos", 60, 100);
    await c.db.tx(async (db) => {
      await db.query("DELETE FROM preferenciasalimentarias WHERE id_socio = $1", [c.idSocio]);
      await db.query("DELETE FROM alimentosexcluidos WHERE id_socio = $1", [c.idSocio]);
      for (const t of preferencias) await db.query("INSERT INTO preferenciasalimentarias (id_socio, tipo) VALUES ($1, $2)", [c.idSocio, t]);
      for (const a of excluidos) await db.query("INSERT INTO alimentosexcluidos (id_socio, alimento) VALUES ($1, $2)", [c.idSocio, a]);
    });
    return { ok: true };
  },
};

// ───────────── comidas registradas (con foto) ─────────────
// Forma de cada día igual a la de siempre para la app:
//   { fecha: "20261002", objetivo, comidas: { desayuno: { kcal, proteinas, carbs,
//     grasas, plato_ids, nota, hora_ms } }, meta: { kcal, ..., momentos: [...] } }

const fechaClave = (iso: string) => iso.replaceAll("-", "");

const listarComidas: Ruta = {
  metodo: "GET", patron: /^\/v1\/comidas$/,
  async manejador(c) {
    const [dias, comidas, platos, momentos] = await Promise.all([
      c.db.query(`SELECT fecha::text AS fecha, objetivo, meta_kcal, meta_proteinas, meta_carbs, meta_grasas FROM comidasdia WHERE id_socio = $1`, [c.idSocio]),
      c.db.query(`SELECT fecha::text AS fecha, momento, kcal, proteinas, carbs, grasas, nota, ${MS("hora")} AS hora_ms FROM comidasregistradas WHERE id_socio = $1`, [c.idSocio]),
      c.db.query("SELECT fecha::text AS fecha, momento, id_plato FROM comidaregistradaplatos WHERE id_socio = $1", [c.idSocio]),
      c.db.query("SELECT fecha::text AS fecha, momento FROM comidasdiametamomentos WHERE id_socio = $1", [c.idSocio]),
    ]);
    const salida = new Map<string, Fila>();
    for (const d of dias.rows) {
      salida.set(d.fecha, {
        fecha: fechaClave(d.fecha), objetivo: d.objetivo, comidas: {},
        ...(d.meta_kcal !== null ? { meta: { kcal: d.meta_kcal, proteinas: d.meta_proteinas, carbs: d.meta_carbs, grasas: d.meta_grasas, momentos: [] as string[] } } : {}),
      });
    }
    for (const f of comidas.rows) {
      salida.get(f.fecha)!.comidas[f.momento] = {
        kcal: f.kcal, proteinas: f.proteinas, carbs: f.carbs, grasas: f.grasas, nota: f.nota, hora_ms: f.hora_ms, plato_ids: [],
      };
    }
    for (const f of platos.rows) salida.get(f.fecha)?.comidas[f.momento]?.plato_ids.push(String(f.id_plato));
    for (const f of momentos.rows) salida.get(f.fecha)?.meta?.momentos.push(f.momento);
    return { dias: [...salida.values()] };
  },
};

function fechaDeBody(c: Contexto): string {
  const v = String(c.body.fecha ?? "");
  if (!/^[0-9]{8}$/.test(v)) throw new ErrorApi(400, '"fecha" tiene que ser aaaammdd.');
  const iso = `${v.slice(0, 4)}-${v.slice(4, 6)}-${v.slice(6, 8)}`;
  const dif = Math.abs(Date.parse(iso) - Date.parse(fechaLocalISO(c.ahora))) / 86_400_000;
  if (!(dif <= 2)) throw new ErrorApi(400, "Solo se pueden registrar comidas de hoy.");
  return iso;
}

const registrarComida: Ruta = {
  metodo: "PUT", patron: /^\/v1\/comidas$/,
  async manejador(c) {
    const b = c.body;
    const momento = b.momento as Momento;
    if (!MOMENTOS.includes(momento)) throw new ErrorApi(400, '"momento" inválido.');
    const fecha = fechaDeBody(c);
    const macros = ["kcal", "proteinas", "carbs", "grasas"].map((k) => entero(b[k] ?? 0, k, 0, 20000));
    const nota = texto(b.nota ?? "", "nota", 500, { vacio: true });
    const imagen = texto(b.imagen, "imagen", 1_000_000);
    const objetivo = b.objetivo && (OBJETIVOS as readonly string[]).includes(b.objetivo) ? b.objetivo : null;
    const platoIds = [...new Set<string>((Array.isArray(b.plato_ids) ? b.plato_ids : []).map((x: unknown) => String(x)).filter((x: string) => /^[0-9]+$/.test(x)))];
    const meta = b.meta && typeof b.meta === "object" ? b.meta : null;

    await c.db.tx(async (db) => {
      if (meta) {
        await db.query(
          `INSERT INTO comidasdia (id_socio, fecha, objetivo, meta_kcal, meta_proteinas, meta_carbs, meta_grasas)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (id_socio, fecha) DO UPDATE SET objetivo = COALESCE(EXCLUDED.objetivo, comidasdia.objetivo),
             meta_kcal = EXCLUDED.meta_kcal, meta_proteinas = EXCLUDED.meta_proteinas, meta_carbs = EXCLUDED.meta_carbs,
             meta_grasas = EXCLUDED.meta_grasas, fecha_actualizacion = now()`,
          [c.idSocio, fecha, objetivo, ...["kcal", "proteinas", "carbs", "grasas"].map((k) => entero(meta[k] ?? 0, `meta.${k}`, 0, 20000))]);
        await db.query("DELETE FROM comidasdiametamomentos WHERE id_socio = $1 AND fecha = $2", [c.idSocio, fecha]);
        for (const m of new Set<string>(Array.isArray(meta.momentos) ? meta.momentos : [])) {
          if ((MOMENTOS as readonly string[]).includes(m)) {
            await db.query("INSERT INTO comidasdiametamomentos (id_socio, fecha, momento) VALUES ($1, $2, $3)", [c.idSocio, fecha, m]);
          }
        }
      } else {
        await db.query(
          `INSERT INTO comidasdia (id_socio, fecha, objetivo) VALUES ($1, $2, $3)
           ON CONFLICT (id_socio, fecha) DO UPDATE SET objetivo = COALESCE(EXCLUDED.objetivo, comidasdia.objetivo), fecha_actualizacion = now()`,
          [c.idSocio, fecha, objetivo]);
      }
      await db.query(
        `INSERT INTO comidasregistradas (id_socio, fecha, momento, hora, kcal, proteinas, carbs, grasas, nota)
         VALUES ($1, $2, $3, now(), $4, $5, $6, $7, $8)
         ON CONFLICT (id_socio, fecha, momento) DO UPDATE SET hora = now(), kcal = EXCLUDED.kcal, proteinas = EXCLUDED.proteinas,
           carbs = EXCLUDED.carbs, grasas = EXCLUDED.grasas, nota = EXCLUDED.nota`,
        [c.idSocio, fecha, momento, ...macros, nota]);
      await db.query("DELETE FROM comidaregistradaplatos WHERE id_socio = $1 AND fecha = $2 AND momento = $3", [c.idSocio, fecha, momento]);
      for (const p of platoIds) {
        await db.query(
          `INSERT INTO comidaregistradaplatos (id_socio, fecha, momento, id_plato) SELECT $1, $2, $3, id_plato FROM platos WHERE id_plato = $4`,
          [c.idSocio, fecha, momento, Number(p)]);
      }
      await db.query(
        `INSERT INTO fotoscomidas (id_socio, fecha, momento, imagen) VALUES ($1, $2, $3, $4)
         ON CONFLICT (id_socio, fecha, momento) DO UPDATE SET imagen = EXCLUDED.imagen, fecha_foto = now()`,
        [c.idSocio, fecha, momento, imagen]);
    });
    return { ok: true };
  },
};

const borrarComida: Ruta = {
  metodo: "DELETE", patron: /^\/v1\/comidas\/([0-9]{8})\/(desayuno|almuerzo|cena)$/,
  async manejador(c) {
    const [f, momento] = c.params;
    const fecha = `${f.slice(0, 4)}-${f.slice(4, 6)}-${f.slice(6, 8)}`;
    await c.db.tx(async (db) => {
      await db.query("DELETE FROM comidasregistradas WHERE id_socio = $1 AND fecha = $2 AND momento = $3", [c.idSocio, fecha, momento]);
      await db.query("DELETE FROM fotoscomidas WHERE id_socio = $1 AND fecha = $2 AND momento = $3", [c.idSocio, fecha, momento]);
    });
    return { ok: true };
  },
};

const fotoComida: Ruta = {
  metodo: "GET", patron: /^\/v1\/comidas\/([0-9]{8})\/(desayuno|almuerzo|cena)\/foto$/,
  async manejador(c) {
    const [f, momento] = c.params;
    const fecha = `${f.slice(0, 4)}-${f.slice(4, 6)}-${f.slice(6, 8)}`;
    const r = await c.db.query("SELECT imagen FROM fotoscomidas WHERE id_socio = $1 AND fecha = $2 AND momento = $3", [c.idSocio, fecha, momento]);
    return { imagen: r.rows[0]?.imagen ?? null };
  },
};

export const rutasNutricion: Ruta[] = [
  catalogoPlatos, dietaAsignada, listarProbados, marcarProbado, listarAgua, registrarAgua,
  leerPerfil, guardarPerfil, listarComidas, registrarComida, borrarComida, fotoComida,
];

export type { Db };
