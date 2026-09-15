// OLIMPOS — Worker de Argos (proxy para la app móvil)
//
// La app móvil NUNCA tiene la clave de Anthropic — no hay forma de ocultar
// un secreto adentro de un APK instalado. En cambio, llama a este Worker
// (con su propio token de Firebase Auth de socio logueado), y este Worker
// —que sí puede guardar secretos, corre en Cloudflare, no en el celular de
// nadie— es quien realmente llama a Anthropic.
//
// Verifica el token de Firebase (prueba que quien llama es un socio real y
// logueado) y lleva el cupo diario de mensajes en Workers KV (gratis, sin
// necesitar el plan pago de Firebase que ya se descartó para Storage/
// Cloud Functions). El texto real de la conversación (pregunta + historial
// + contexto propio del socio + base de conocimiento) lo arma y manda la
// app móvil — este Worker no lee Firestore por su cuenta, así se evita
// necesitar una cuenta de servicio acá también.

import { importX509, jwtVerify, decodeProtectedHeader } from "jose";

export interface Env {
  ANTHROPIC_API_KEY: string;
  FIREBASE_PROJECT_ID: string;
  ARGOS_KV: KVNamespace;
}

const MODELO = "claude-haiku-4-5-20251001";
const MAX_TOKENS_RESPUESTA = 600;
const MAXIMO_DIARIO = 300;
const MAX_HISTORIAL_MENSAJES = 20;

const CERTS_URL =
  "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com";

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const INSTRUCCIONES_BASE =
  "Sos Argos, el asistente de IA del gimnasio OlimpΩs. Respondés ÚNICAMENTE " +
  "preguntas relacionadas con OlimpΩs: horarios, membresías y precios, " +
  "clases, máquinas y el plano del club, el catálogo de comidas/dietas, tu " +
  "propio progreso/membresía si te lo preguntan, y consejos generales de " +
  "entrenamiento y hábitos saludables. Si te preguntan algo que no tiene " +
  "nada que ver con el gimnasio, respondé amablemente que solo podés ayudar " +
  "con temas de OlimpΩs. Nunca inventes datos: si no tenés la información, " +
  "decilo con honestidad en vez de adivinar. Respuestas breves y claras, en " +
  "español rioplatense, sin markdown pesado (nada de tablas). No des " +
  "consejos médicos, legales o financieros específicos — para eso, sugerí " +
  "consultar a un profesional.";

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS_HEADERS },
  });
}

/** Verifica un ID token de Firebase Auth contra el proyecto de OlimpΩs.
 *  Lanza si la firma, el emisor, la audiencia o la expiración no cierran. */
async function verificarTokenFirebase(token: string, projectId: string): Promise<string> {
  const { kid } = decodeProtectedHeader(token);
  if (!kid) throw new Error("Token sin 'kid'");

  const certsResp = await fetch(CERTS_URL);
  if (!certsResp.ok) throw new Error("No se pudieron obtener las claves públicas de Google");
  const certs = (await certsResp.json()) as Record<string, string>;
  const cert = certs[kid];
  if (!cert) throw new Error("No hay una clave pública que matchee este token");

  const clavePublica = await importX509(cert, "RS256");
  const { payload } = await jwtVerify(token, clavePublica, {
    issuer: `https://securetoken.google.com/${projectId}`,
    audience: projectId,
  });
  if (!payload.sub) throw new Error("Token sin 'sub' (uid)");
  return payload.sub;
}

/** Cupo diario en Workers KV — no es un conteo perfectamente atómico (KV no
 *  da transacciones), así que bajo mucha concurrencia podría dejar pasar
 *  algún mensaje de más, pero para el volumen de un gimnasio alcanza de
 *  sobra: la idea es no gastar de más "sin darse cuenta", no una barrera
 *  de seguridad dura. */
async function consumirCupoDiario(env: Env): Promise<{ ok: boolean; restantes: number }> {
  const hoy = new Date().toISOString().slice(0, 10);
  const clave = `argos_count_${hoy}`;
  const actualStr = await env.ARGOS_KV.get(clave);
  const actual = actualStr ? parseInt(actualStr, 10) : 0;
  if (actual >= MAXIMO_DIARIO) {
    return { ok: false, restantes: 0 };
  }
  await env.ARGOS_KV.put(clave, String(actual + 1), { expirationTtl: 60 * 60 * 30 });
  return { ok: true, restantes: MAXIMO_DIARIO - (actual + 1) };
}

interface MensajeHistorial {
  rol: "user" | "assistant";
  texto: string;
}

async function preguntarClaude(
  env: Env,
  mensaje: string,
  historial: MensajeHistorial[],
  contextoSocio: string,
  baseConocimiento: string
): Promise<string> {
  let system = INSTRUCCIONES_BASE;
  if (baseConocimiento.trim()) {
    system += `\n\nInformación real de OlimpΩs para basar tus respuestas:\n${baseConocimiento}`;
  }
  if (contextoSocio.trim()) {
    system += `\n\nDatos propios de ESTE socio (nunca reveles datos de otro socio, no los tenés igual):\n${contextoSocio}`;
  }

  const messages = [
    ...historial.slice(-MAX_HISTORIAL_MENSAJES).map((h) => ({
      role: h.rol === "assistant" ? "assistant" : "user",
      content: h.texto,
    })),
    { role: "user", content: mensaje },
  ];

  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: MODELO,
      max_tokens: MAX_TOKENS_RESPUESTA,
      system,
      messages,
    }),
  });

  if (!resp.ok) {
    const detalle = await resp.text();
    throw new Error(`Anthropic devolvió ${resp.status}: ${detalle.slice(0, 300)}`);
  }
  const datos = (await resp.json()) as { content?: { type: string; text?: string }[] };
  const texto = (datos.content ?? [])
    .filter((b) => b.type === "text")
    .map((b) => b.text ?? "")
    .join("")
    .trim();
  return texto || "No obtuve una respuesta — probá de nuevo.";
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    if (request.method !== "POST") {
      return json({ error: "Método no soportado" }, 405);
    }

    const authHeader = request.headers.get("Authorization") || "";
    const token = authHeader.replace(/^Bearer\s+/i, "").trim();
    if (!token) return json({ error: "Falta iniciar sesión" }, 401);

    try {
      await verificarTokenFirebase(token, env.FIREBASE_PROJECT_ID);
    } catch (ex) {
      return json({ error: "Sesión inválida o vencida" }, 401);
    }

    let body: {
      mensaje?: string;
      historial?: MensajeHistorial[];
      contexto_socio?: string;
      base_conocimiento?: string;
    };
    try {
      body = await request.json();
    } catch {
      return json({ error: "Cuerpo de la solicitud inválido" }, 400);
    }

    const mensaje = (body.mensaje || "").trim();
    if (!mensaje) return json({ error: "Escribí una pregunta primero." }, 400);
    if (mensaje.length > 2000) return json({ error: "La pregunta es demasiado larga." }, 400);

    const historial = Array.isArray(body.historial) ? body.historial : [];
    const contextoSocio = (body.contexto_socio || "").slice(0, 4000);
    const baseConocimiento = (body.base_conocimiento || "").slice(0, 6000);

    const cupo = await consumirCupoDiario(env);
    if (!cupo.ok) {
      return json(
        { error: `Se llegó al máximo de ${MAXIMO_DIARIO} mensajes de Argos hoy. Probá de nuevo mañana.` },
        429
      );
    }

    try {
      const respuesta = await preguntarClaude(env, mensaje, historial, contextoSocio, baseConocimiento);
      return json({ respuesta, restantes: cupo.restantes });
    } catch (ex) {
      return json({ error: ex instanceof Error ? ex.message : "Error inesperado" }, 502);
    }
  },
};
