// OLIMPOS — Worker de Pagos (Mercado Pago, modo prueba)
//
// La app móvil NUNCA tiene el Access Token de Mercado Pago — igual que con
// la clave de Anthropic en ArgosWorker, un secreto adentro de un APK
// instalado no es un secreto. La app le pide a ESTE Worker "quiero pagar el
// plan Oro" (con su propio token de Firebase Auth), el Worker arma el cobro
// en Mercado Pago con el precio que él mismo conoce —nunca el que mande la
// app— y devuelve el link de pago (Checkout Pro).
//
// Cuando el pago se aprueba, Mercado Pago le avisa a este mismo Worker
// (webhook). Ahí, y SOLO ahí, se activa la membresía en Firestore — nunca
// se confía en que la app "avise" que pagó, porque eso se podría simular
// sin pagar nada. El webhook tampoco confía en lo que dice el aviso en sí
// (alguien podría mandar uno falso): vuelve a preguntarle a la API de
// Mercado Pago, con el propio Access Token, si ESE pago está realmente
// aprobado, antes de tocar Firestore.
//
// Para escribir en Firestore hace falta la cuenta de servicio de Firebase
// (mismas credenciales que ya usa el sistema de empleados en Python) —acá
// no hay Admin SDK, así que se pide un access token de Google a mano
// (JWT firmado con la clave privada de la cuenta de servicio, intercambiado
// por un token en oauth2.googleapis.com). Es el mismo mecanismo que usan
// las Admin SDK de Firebase por dentro, hecho a mano con Web Crypto.

import { importPKCS8, SignJWT, importX509, jwtVerify, decodeProtectedHeader } from "jose";

export interface Env {
  MP_ACCESS_TOKEN: string;
  FIREBASE_PROJECT_ID: string;
  FIREBASE_SA_EMAIL: string;
  FIREBASE_SA_PRIVATE_KEY: string;
}

const CERTS_URL =
  "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com";

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// Mismos 3 planes y precios que PLANES_MEMBRESIA en la app móvil (SocioData.kt)
// y que PLANES en el sistema de empleados (membresias_repo.py). El precio
// vive ACÁ, del lado del servidor, para que nadie pueda pagar un plan Platino
// al precio de uno Bronce con una app modificada.
const PRECIOS: Record<string, number> = {
  Bronce: 18000,
  Oro: 28000,
  Platino: 42000,
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS_HEADERS },
  });
}

/** Verifica un ID token de Firebase Auth contra el proyecto de OlimpΩs —
 *  mismo mecanismo que ArgosWorker/src/index.ts (ver ese archivo para más
 *  detalle). Devuelve el uid y el email del socio logueado — el email hace
 *  falta para armar la preferencia de pago (ver [crearPreferencia]):
 *  Mercado Pago necesita un "payer.email" para completar el checkout de
 *  invitado con tarjeta, si no, el pago se cae en el último paso. */
async function verificarTokenFirebase(
  token: string,
  projectId: string
): Promise<{ uid: string; email: string | null }> {
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
  return { uid: payload.sub, email: typeof payload.email === "string" ? payload.email : null };
}

/** Access token de Google (OAuth2) para la cuenta de servicio de Firebase,
 *  vía el flujo "JWT bearer" — el mismo que usa por dentro cualquier Admin
 *  SDK. Alcance "datastore": lectura/escritura de Firestore, nada más
 *  (no hace falta "cloud-platform" completo para esto). */
async function tokenDeServicioGoogle(env: Env): Promise<string> {
  const clavePrivada = await importPKCS8(env.FIREBASE_SA_PRIVATE_KEY, "RS256");
  const ahora = Math.floor(Date.now() / 1000);
  const jwt = await new SignJWT({ scope: "https://www.googleapis.com/auth/datastore" })
    .setProtectedHeader({ alg: "RS256" })
    .setIssuer(env.FIREBASE_SA_EMAIL)
    .setSubject(env.FIREBASE_SA_EMAIL)
    .setAudience("https://oauth2.googleapis.com/token")
    .setIssuedAt(ahora)
    .setExpirationTime(ahora + 3600)
    .sign(clavePrivada);

  const resp = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: jwt,
    }),
  });
  const datos = (await resp.json()) as { access_token?: string; error?: string };
  if (!resp.ok || !datos.access_token) {
    throw new Error("No se pudo autenticar con Google: " + JSON.stringify(datos));
  }
  return datos.access_token;
}

/** Reemplaza por completo el documento "membresias/{uid}" — misma forma que
 *  usa asignar_membresia() en membresias_repo.py, así la app y el sistema
 *  de empleados leen exactamente lo mismo sin importar quién la activó. */
async function activarMembresia(env: Env, accessToken: string, uid: string, plan: string): Promise<void> {
  const url =
    `https://firestore.googleapis.com/v1/projects/${env.FIREBASE_PROJECT_ID}/databases/(default)/documents/membresias/${encodeURIComponent(uid)}`;
  const resp = await fetch(url, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${accessToken}`, "content-type": "application/json" },
    body: JSON.stringify({
      fields: {
        socio_id: { stringValue: uid },
        plan: { stringValue: plan },
        fecha_inicio_ms: { integerValue: String(Date.now()) },
        asignado_por: { stringValue: "Mercado Pago (pago del socio)" },
      },
    }),
  });
  if (!resp.ok) throw new Error(`Firestore (membresias) devolvió ${resp.status}: ${await resp.text()}`);
}

/** Un documento por pago aprobado, id = el propio id de pago de Mercado
 *  Pago — así, si MP reintenta el mismo webhook (puede pasar), esto
 *  simplemente sobreescribe el mismo documento en vez de duplicarlo. */
async function registrarPago(
  env: Env,
  accessToken: string,
  pagoId: string,
  uid: string,
  plan: string,
  monto: number
): Promise<void> {
  const url =
    `https://firestore.googleapis.com/v1/projects/${env.FIREBASE_PROJECT_ID}/databases/(default)/documents/pagos_socios/${encodeURIComponent(pagoId)}`;
  const resp = await fetch(url, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${accessToken}`, "content-type": "application/json" },
    body: JSON.stringify({
      fields: {
        socio_id: { stringValue: uid },
        plan: { stringValue: plan },
        monto: { integerValue: String(monto) },
        estado: { stringValue: "Aprobado" },
        fecha_ms: { integerValue: String(Date.now()) },
        mp_payment_id: { stringValue: pagoId },
      },
    }),
  });
  if (!resp.ok) throw new Error(`Firestore (pagos_socios) devolvió ${resp.status}: ${await resp.text()}`);
}

/** POST /crear-preferencia — arma un cobro de Mercado Pago (Checkout Pro)
 *  para el plan pedido y devuelve el link de pago. Requiere sesión de
 *  socio (mismo Authorization: Bearer <idToken> que usa Argos). */
async function crearPreferencia(request: Request, env: Env): Promise<Response> {
  const authHeader = request.headers.get("Authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "").trim();
  if (!token) return json({ error: "Falta iniciar sesión" }, 401);

  let uid: string;
  let email: string | null;
  try {
    ({ uid, email } = await verificarTokenFirebase(token, env.FIREBASE_PROJECT_ID));
  } catch {
    return json({ error: "Sesión inválida o vencida" }, 401);
  }

  let body: { plan?: string };
  try {
    body = await request.json();
  } catch {
    return json({ error: "Cuerpo de la solicitud inválido" }, 400);
  }
  const plan = body.plan || "";
  const precio = PRECIOS[plan];
  if (!precio) return json({ error: "Plan inválido" }, 400);

  const origen = new URL(request.url).origin;
  const mpResp = await fetch("https://api.mercadopago.com/checkout/preferences", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.MP_ACCESS_TOKEN}`, "content-type": "application/json" },
    body: JSON.stringify({
      items: [
        {
          title: `Membresía OlimpΩs — Plan ${plan}`,
          quantity: 1,
          unit_price: precio,
          currency_id: "ARS",
        },
      ],
      // "uid|plan" en vez de dos campos separados: es lo único que hace
      // falta para que el webhook sepa a quién activarle qué, y Mercado
      // Pago devuelve este mismo string tal cual en el pago.
      external_reference: `${uid}|${plan}`,
      payer: email ? { email } : undefined,
      back_urls: {
        success: "https://olimpos-18320.web.app/pago-exitoso.html",
        failure: "https://olimpos-18320.web.app/pago-fallido.html",
        pending: "https://olimpos-18320.web.app/pago-pendiente.html",
      },
      auto_return: "approved",
      notification_url: `${origen}/webhook`,
    }),
  });

  const datos = (await mpResp.json()) as {
    init_point?: string;
    sandbox_init_point?: string;
    message?: string;
  };
  if (!mpResp.ok) {
    return json({ error: "Mercado Pago rechazó la solicitud: " + (datos.message || mpResp.status) }, 502);
  }

  // Con credenciales de prueba, Mercado Pago puede devolver cualquiera de
  // los dos según la cuenta — se prioriza sandbox_init_point si vino.
  const checkoutUrl = datos.sandbox_init_point || datos.init_point;
  if (!checkoutUrl) return json({ error: "Mercado Pago no devolvió un link de pago" }, 502);

  return json({ checkout_url: checkoutUrl });
}

/** POST /webhook — lo llama Mercado Pago, no la app. Nunca confía en lo que
 *  diga el aviso: vuelve a preguntarle a la API de Mercado Pago por el
 *  estado real de ESE pago antes de tocar Firestore. */
async function manejarWebhook(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const tipo = url.searchParams.get("type") || url.searchParams.get("topic") || "";
  const pagoId = url.searchParams.get("data.id") || url.searchParams.get("id") || "";

  // Cualquier otro tipo de evento (o uno sin id) se ignora con 200 — si se
  // devolviera un error, Mercado Pago seguiría reintentando algo que nunca
  // vamos a poder procesar.
  if (tipo !== "payment" || !pagoId) return new Response("ok", { status: 200 });

  try {
    const pagoResp = await fetch(`https://api.mercadopago.com/v1/payments/${pagoId}`, {
      headers: { Authorization: `Bearer ${env.MP_ACCESS_TOKEN}` },
    });
    if (!pagoResp.ok) return new Response("ok", { status: 200 });
    const pago = (await pagoResp.json()) as {
      status?: string;
      external_reference?: string;
      transaction_amount?: number;
    };

    if (pago.status !== "approved") return new Response("ok", { status: 200 });

    const [uid, plan] = (pago.external_reference || "").split("|");
    if (!uid || !plan || !PRECIOS[plan]) return new Response("ok", { status: 200 });

    const accessToken = await tokenDeServicioGoogle(env);
    await activarMembresia(env, accessToken, uid, plan);
    await registrarPago(env, accessToken, String(pagoId), uid, plan, pago.transaction_amount ?? PRECIOS[plan]);

    return new Response("ok", { status: 200 });
  } catch (ex) {
    // 200 igual: un error de nuestro lado no debería hacer que Mercado Pago
    // reintente indefinidamente un webhook que quizás nunca va a poder
    // procesar (por ejemplo, un pago de otra integración vieja).
    console.error("Error procesando webhook de pago:", ex);
    return new Response("ok", { status: 200 });
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const path = new URL(request.url).pathname;
    if (request.method === "POST" && path === "/crear-preferencia") {
      return crearPreferencia(request, env);
    }
    if (request.method === "POST" && path === "/webhook") {
      return manejarWebhook(request, env);
    }
    return json({ error: "No encontrado" }, 404);
  },
};
