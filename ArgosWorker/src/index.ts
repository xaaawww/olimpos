// OLIMPOS — Worker de Argos (proxy para la app móvil)
//
// La app móvil NUNCA tiene la clave de Anthropic — no hay forma de ocultar
// un secreto adentro de un APK instalado. En cambio, llama a este Worker
// (con su propio token de Firebase Auth de socio logueado), y este Worker
// —que sí puede guardar secretos, corre en Cloudflare, no en el celular de
// nadie— es quien realmente llama a Anthropic.
//
// El plan de membresía (Argos es de pago: planes Oro y Platino) y el cupo
// diario de mensajes viven en la base de datos (Neon), y los maneja la API
// del club: este Worker le pide permiso con el MISMO token del socio
// (POST /v1/argos/consumir) antes de gastar plata en Anthropic. Así no
// necesita ninguna credencial de base de datos, y el chequeo sigue estando
// del lado del servidor (el de la app se puede saltear modificando el APK).
// El texto real de la conversación (pregunta + historial + contexto propio
// del socio + base de conocimiento) lo arma y manda la app móvil.

export interface Env {
  ANTHROPIC_API_KEY: string;
  /** URL de la API del club (Worker "api-olimpos"). */
  API_URL: string;
}

const MODELO = "claude-haiku-4-5-20251001";
const MAX_TOKENS_RESPUESTA = 600;
const MAX_HISTORIAL_MENSAJES = 20;

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

/** Le pide permiso a la API del club: verifica el token, que el plan incluya
 *  Argos y que no se haya agotado el tope diario, y anota el uso. Devuelve
 *  `null` si todo está bien, o la respuesta de error lista para devolver. */
async function pedirPermiso(env: Env, token: string): Promise<{ restantes: number } | Response> {
  let resp: Response;
  try {
    resp = await fetch(`${env.API_URL}/v1/argos/consumir`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "content-type": "application/json" },
      body: "{}",
    });
  } catch {
    return json({ error: "No se pudo verificar tu plan de membresía. Probá de nuevo en un momento." }, 502);
  }
  const datos = (await resp.json().catch(() => ({}))) as { error?: string; restantes?: number };
  if (resp.ok) return { restantes: datos.restantes ?? 0 };
  if (resp.status === 401 || resp.status === 403 || resp.status === 429) {
    return json({ error: datos.error ?? "No tenés permiso para usar Argos.", ...(resp.status === 403 ? { codigo: "plan_requerido" } : {}) }, resp.status);
  }
  return json({ error: "No se pudo verificar tu plan de membresía. Probá de nuevo en un momento." }, 502);
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

    // Beneficio de pago con tope diario: sin plan que lo incluya, o con el
    // tope agotado, no se llama a Anthropic. Si no se puede verificar, se
    // rechaza — nunca se deja pasar "por las dudas".
    const permiso = await pedirPermiso(env, token);
    if (permiso instanceof Response) return permiso;

    try {
      const respuesta = await preguntarClaude(env, mensaje, historial, contextoSocio, baseConocimiento);
      return json({ respuesta, restantes: permiso.restantes });
    } catch (ex) {
      return json({ error: ex instanceof Error ? ex.message : "Error inesperado" }, 502);
    }
  },
};
