// Punto de entrada del Worker: conecta la lógica de la API (api.ts) con Neon
// (PostgreSQL serverless) y con la verificación del token de Firebase.

import { Pool } from "@neondatabase/serverless";
import { importX509, jwtVerify, decodeProtectedHeader } from "jose";
import { Dependencias, Env, manejar } from "./api.js";
import { dbDesdePool } from "./util.js";

const CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com";

/** Verifica un ID token de Firebase Auth contra el proyecto de OlimpΩs.
 *  Lanza si la firma, el emisor, la audiencia o la expiración no cierran. */
async function verificarTokenFirebase(token: string, projectId: string) {
  const { kid } = decodeProtectedHeader(token);
  if (!kid) throw new Error("Token sin 'kid'");
  const resp = await fetch(CERTS_URL, { cf: { cacheTtl: 3600, cacheEverything: true } } as RequestInit);
  if (!resp.ok) throw new Error("No se pudieron obtener las claves públicas de Google");
  const certs = (await resp.json()) as Record<string, string>;
  const cert = certs[kid];
  if (!cert) throw new Error("No hay una clave pública que matchee este token");
  const clave = await importX509(cert, "RS256");
  const { payload } = await jwtVerify(token, clave, {
    issuer: `https://securetoken.google.com/${projectId}`,
    audience: projectId,
  });
  if (!payload.sub) throw new Error("Token sin 'sub' (uid)");
  return { uid: payload.sub, email: typeof payload.email === "string" ? payload.email : null };
}

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const deps: Dependencias = {
      async abrirDb() {
        const pool = new Pool({ connectionString: env.DATABASE_URL });
        return { db: dbDesdePool(pool), cerrar: () => pool.end() };
      },
      verificarToken: (token) => verificarTokenFirebase(token, env.FIREBASE_PROJECT_ID),
      ahora: () => new Date(),
    };
    return manejar(req, deps);
  },
};
