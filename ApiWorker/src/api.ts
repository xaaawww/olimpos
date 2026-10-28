// OLIMPOS — API para la app móvil (Cloudflare Worker + Neon / PostgreSQL)
//
// La app móvil NO puede hablar directo con la base de datos (dentro de un APK
// no se puede esconder una contraseña de base). Habla con este Worker, que:
//   1. verifica el token de Firebase Authentication del socio (el LOGIN sigue
//      en Firebase: acá solo se comprueba la firma del token),
//   2. busca al socio en la tabla "socios" por su firebase_uid, y
//   3. ejecuta SOLO las consultas de esta lista, siempre acotadas a ese socio.
// Esta capa reemplaza a las "firestore.rules": cada ruta decide qué puede ver
// y tocar el socio. Las restricciones de la base (claves foráneas, únicos,
// checks) son la segunda barrera.

import { aLocal, Contexto, Db, ErrorApi, Ruta } from "./util.js";
import { rutasSocio } from "./rutas_socio.js";
import { rutasEntrenamiento } from "./rutas_entrenamiento.js";
import { rutasNutricion } from "./rutas_nutricion.js";
import { rutasClub } from "./rutas_club.js";
import { rutasTienda } from "./rutas_tienda.js";

export interface Env {
  DATABASE_URL: string;
  FIREBASE_PROJECT_ID: string;
}

export interface Dependencias {
  /** Abre acceso a la base para UNA petición; `cerrar` libera la conexión. */
  abrirDb(): Promise<{ db: Db; cerrar(): Promise<void> }>;
  /** Verifica el ID token de Firebase y devuelve quién es. Lanza si es inválido. */
  verificarToken(token: string): Promise<{ uid: string; email: string | null }>;
  ahora(): Date;
}

const CORS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Max-Age": "86400",
};

const RUTAS: Ruta[] = [...rutasSocio, ...rutasEntrenamiento, ...rutasNutricion, ...rutasClub, ...rutasTienda];

function responder(data: unknown, estado = 200): Response {
  return new Response(JSON.stringify(data), {
    status: estado,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS },
  });
}

/** Mensaje legible para errores de la base que el usuario puede causar. */
function traducirErrorDb(e: any): ErrorApi | null {
  switch (e?.code) {
    case "23505": return new ErrorApi(409, "Ya existe un registro igual.");
    case "23503": return new ErrorApi(409, "Ese dato depende de otro que no existe.");
    case "23514": return new ErrorApi(400, "Alguno de los valores no es válido.");
    case "22001": return new ErrorApi(400, "Alguno de los textos es demasiado largo.");
    default: return null;
  }
}

export async function manejar(req: Request, deps: Dependencias): Promise<Response> {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });

  const url = new URL(req.url);
  if (url.pathname === "/" || url.pathname === "/v1/salud") return responder({ ok: true, servicio: "api-olimpos" });

  const encontrada = RUTAS.find((r) => r.metodo === req.method && r.patron.test(url.pathname));
  if (!encontrada) {
    const existePath = RUTAS.some((r) => r.patron.test(url.pathname));
    return responder({ error: existePath ? "Método no permitido." : "Ruta inexistente." }, existePath ? 405 : 404);
  }

  let cierre: (() => Promise<void>) | null = null;
  try {
    let body: any = {};
    if (req.method !== "GET" && req.method !== "DELETE") {
      const crudo = await req.text();
      if (crudo.length > 2_500_000) throw new ErrorApi(413, "El pedido es demasiado grande.");
      try {
        body = crudo ? JSON.parse(crudo) : {};
      } catch {
        throw new ErrorApi(400, "El cuerpo no es un JSON válido.");
      }
    }

    let uid = "";
    let email: string | null = null;
    if (!encontrada.publica) {
      const auth = req.headers.get("Authorization") ?? "";
      const token = auth.startsWith("Bearer ") ? auth.slice(7).trim() : "";
      if (!token) throw new ErrorApi(401, "Falta iniciar sesión.");
      try {
        ({ uid, email } = await deps.verificarToken(token));
      } catch {
        throw new ErrorApi(401, "Tu sesión no es válida — volvé a iniciar sesión.");
      }
    }

    const abierta = await deps.abrirDb();
    cierre = abierta.cerrar;
    const db = abierta.db;

    let idSocio = 0;
    if (!encontrada.publica) {
      const r = await db.query("SELECT id_socio, estado FROM socios WHERE firebase_uid = $1", [uid]);
      if (!r.rows.length) throw new ErrorApi(403, "Tu cuenta todavía no está dada de alta en el gimnasio.");
      if (r.rows[0].estado !== "activo") throw new ErrorApi(403, "Tu acceso está desactivado. Consultá en recepción.");
      idSocio = r.rows[0].id_socio;
    }

    const m = encontrada.patron.exec(url.pathname)!;
    const ctx: Contexto = { db, uid, email, idSocio, req, url, params: m.slice(1), body, ahora: deps.ahora() };
    const resultado = await encontrada.manejador(ctx);
    return resultado instanceof Response ? resultado : responder(resultado ?? { ok: true });
  } catch (e: any) {
    const err = e instanceof ErrorApi ? e : traducirErrorDb(e);
    if (err) return responder({ error: err.message }, err.estado);
    console.error("Error inesperado:", e?.message ?? e);
    return responder({ error: "Algo salió mal de nuestro lado. Probá de nuevo en un momento." }, 500);
  } finally {
    if (cierre) await cierre().catch(() => {});
  }
}

export { aLocal };
