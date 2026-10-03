// OLIMPOS — Worker de Pagos (Mercado Pago, modo prueba)
//
// La app móvil NUNCA tiene el Access Token de Mercado Pago — igual que con
// la clave de Anthropic en ArgosWorker, un secreto adentro de un APK
// instalado no es un secreto. La app le pide a ESTE Worker "quiero pagar el
// plan Oro" (con su propio token de Firebase Auth), el Worker arma el cobro
// en Mercado Pago con el precio que él mismo conoce —el de la tabla
// "membresias" de la base de datos, nunca el que mande la app— y devuelve el
// link de pago (Checkout Pro).
//
// Cuando el pago se aprueba, Mercado Pago le avisa a este mismo Worker
// (webhook). Ahí, y SOLO ahí, se activa la membresía en la base de datos —
// nunca se confía en que la app "avise" que pagó, porque eso se podría
// simular sin pagar nada. El webhook tampoco confía en lo que dice el aviso
// en sí (alguien podría mandar uno falso): vuelve a preguntarle a la API de
// Mercado Pago, con el propio Access Token, si ESE pago está realmente
// aprobado, antes de tocar la base.
//
// El pago y el cambio de membresía se guardan en UNA transacción (o se
// aplican los dos o ninguno), y son idempotentes: si Mercado Pago reintenta
// el mismo aviso, el segundo intento no duplica nada.

import { Pool, neon } from "@neondatabase/serverless";
import { importX509, jwtVerify, decodeProtectedHeader } from "jose";

export interface Env {
  MP_ACCESS_TOKEN: string;
  FIREBASE_PROJECT_ID: string;
  /** Cadena de conexión de Neon (secreto). */
  DATABASE_URL: string;
}

const CERTS_URL =
  "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com";

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS_HEADERS },
  });
}

/** Verifica un ID token de Firebase Auth contra el proyecto de OlimpΩs.
 *  Devuelve el uid y el email del socio logueado — el email hace falta para
 *  armar la preferencia de pago (ver [crearPreferencia]): Mercado Pago
 *  necesita un "payer.email" para completar el checkout de invitado con
 *  tarjeta, si no, el pago se cae en el último paso. */
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

/** Precio vigente de un plan, de la tabla "membresias" (única fuente de verdad:
 *  la misma que usa la app y el sistema de empleados). `null` si no existe. */
async function precioDelPlan(env: Env, plan: string): Promise<number | null> {
  const sql = neon(env.DATABASE_URL);
  const filas = (await sql.query("SELECT precio FROM membresias WHERE nombre = $1 AND estado = 'activa'", [plan])) as { precio: string }[];
  return filas.length ? Math.round(Number(filas[0].precio)) : null;
}

/** Registra un pago aprobado y activa la membresía, todo en una transacción.
 *  Idempotente: el id de pago de Mercado Pago es único en "pagos" (columna
 *  numero_comprobante), así que un reintento del webhook no hace nada. */
async function registrarPagoYActivarMembresia(env: Env, pagoId: string, uid: string, plan: string, monto: number): Promise<void> {
  const pool = new Pool({ connectionString: env.DATABASE_URL });
  const cliente = await pool.connect();
  try {
    await cliente.query("BEGIN");
    const yaRegistrado = await cliente.query("SELECT 1 FROM pagos WHERE numero_comprobante = $1", [pagoId]);
    if (yaRegistrado.rows.length) {
      await cliente.query("ROLLBACK");
      return;
    }
    const socio = await cliente.query("SELECT id_socio FROM socios WHERE firebase_uid = $1", [uid]);
    const membresia = await cliente.query("SELECT id_membresia, duracion_dias FROM membresias WHERE nombre = $1", [plan]);
    const planPago = await cliente.query("SELECT id_plan_pago FROM planespago WHERE nombre = 'Pago único'");
    if (!socio.rows.length || !membresia.rows.length || !planPago.rows.length) {
      await cliente.query("ROLLBACK");
      throw new Error(`No se pudo registrar el pago ${pagoId}: socio, plan o forma de pago inexistente.`);
    }
    const idSocio = socio.rows[0].id_socio;
    const { id_membresia, duracion_dias } = membresia.rows[0];

    await cliente.query(
      `INSERT INTO mediospago (id_socio, tipo, proveedor, estado) VALUES ($1, 'Mercado Pago', 'Mercado Pago', 'activo')
       ON CONFLICT (id_socio, tipo, proveedor) DO NOTHING`, [idSocio]);
    const medio = await cliente.query("SELECT id_medio_pago FROM mediospago WHERE id_socio = $1 AND tipo = 'Mercado Pago' AND proveedor = 'Mercado Pago'", [idSocio]);

    // Una sola membresía activa por socio: la anterior queda como 'cancelada' (historial).
    await cliente.query(
      `UPDATE sociomembresia SET estado = 'cancelada', fecha_cancelacion = (now() AT TIME ZONE 'America/Argentina/Buenos_Aires')::date
       WHERE id_socio = $1 AND estado = 'activa'`, [idSocio]);
    await cliente.query(
      `INSERT INTO sociomembresia (id_socio, id_membresia, fecha_inicio, fecha_vencimiento, estado, asignado_por)
       VALUES ($1, $2, (now() AT TIME ZONE 'America/Argentina/Buenos_Aires')::date,
               (now() AT TIME ZONE 'America/Argentina/Buenos_Aires')::date + $3::int, 'activa', 'Mercado Pago (pago del socio)')`,
      [idSocio, id_membresia, duracion_dias]);
    await cliente.query(
      `INSERT INTO pagos (id_socio, id_membresia, id_plan_pago, id_medio_pago, monto, fecha_pago, fecha_vencimiento, numero_comprobante, estado)
       VALUES ($1, $2, $3, $4, $5, now(), (now() AT TIME ZONE 'America/Argentina/Buenos_Aires')::date + $6::int, $7, 'Aprobado')`,
      [idSocio, id_membresia, planPago.rows[0].id_plan_pago, medio.rows[0].id_medio_pago, monto, duracion_dias, pagoId]);
    await cliente.query("COMMIT");
  } catch (e) {
    await cliente.query("ROLLBACK").catch(() => {});
    throw e;
  } finally {
    cliente.release();
    await pool.end();
  }
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
  let precio: number | null;
  try {
    precio = await precioDelPlan(env, plan);
  } catch {
    return json({ error: "No se pudo consultar el precio del plan. Probá de nuevo en un momento." }, 502);
  }
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
 *  estado real de ESE pago antes de tocar la base. */
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
    if (!uid || !plan) return new Response("ok", { status: 200 });
    const precio = await precioDelPlan(env, plan);
    if (!precio) return new Response("ok", { status: 200 });

    await registrarPagoYActivarMembresia(env, String(pagoId), uid, plan, pago.transaction_amount ?? precio);
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
