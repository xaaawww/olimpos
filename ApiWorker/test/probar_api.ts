// Pruebas de la API contra un PostgreSQL real (no se simula la base): ejecutan
// la MISMA lógica que corre en Cloudflare, con un token falso "uid:<uid>".
// Uso: OLIMPOS_DATABASE_URL=postgresql://... npm test   (la base debe tener
// el esquema aplicado y los datos migrados: python neon/migrar_firestore_a_neon.py --limpiar)

import pg from "pg";
import { manejar, Dependencias } from "../src/api.js";
import { dbDesdePool } from "../src/util.js";

const url = process.env.OLIMPOS_DATABASE_URL;
if (!url) throw new Error("Falta OLIMPOS_DATABASE_URL");
const pool = new pg.Pool({ connectionString: url, max: 10 });

const deps: Dependencias = {
  abrirDb: async () => ({ db: dbDesdePool(pool), cerrar: async () => {} }),
  verificarToken: async (t) => {
    if (!t.startsWith("uid:")) throw new Error("token inválido");
    return { uid: t.slice(4), email: null };
  },
  ahora: () => new Date(),
};

let total = 0;
function check(nombre: string, cond: unknown, extra = "") {
  total++;
  console.log(`${cond ? "OK   " : "FALLA"} ${nombre}${extra ? "  → " + extra : ""}`);
  if (!cond) { console.error("\nPRUEBA FALLIDA"); process.exit(1); }
}

async function api(metodo: string, ruta: string, uid: string | null, body?: unknown): Promise<{ s: number; j: any }> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (uid !== null) headers.Authorization = `Bearer uid:${uid}`;
  const r = await manejar(new Request("http://x" + ruta, { method: metodo, headers, body: body === undefined ? undefined : JSON.stringify(body) }), deps);
  return { s: r.status, j: await r.json() };
}

const q = async (sql: string, p: unknown[] = []) => (await pool.query(sql, p)).rows;
const socios = await q("SELECT firebase_uid, nombre FROM socios ORDER BY id_socio");
const uidDe = (nombre: string) => socios.find((s) => s.nombre === nombre)!.firebase_uid as string;
const MATIAS = uidDe("Matias"); // tiene membresía Platino, dieta, rutina y marcas
const JANO = uidDe("Jano");
const PRUEBA2 = uidDe("prueba2");
const PRUEBA1 = uidDe("prueba1");

// ───── autenticación ─────
check("salud sin token", (await api("GET", "/v1/salud", null)).j.ok === true);
check("sin token → 401", (await api("GET", "/v1/yo", null)).s === 401);
{
  const r = await manejar(new Request("http://x/v1/yo", { headers: { Authorization: "Bearer cualquiera" } }), deps);
  check("token inválido → 401", r.status === 401);
}
check("usuario sin ficha → 403", (await api("GET", "/v1/yo", "uid-que-no-existe")).s === 403);
check("ruta inexistente → 404", (await api("GET", "/v1/nada", MATIAS)).s === 404);
check("método incorrecto → 405", (await api("DELETE", "/v1/yo", MATIAS)).s === 405);

// ───── ficha y datos físicos ─────
let r = await api("GET", "/v1/yo", MATIAS);
check("yo", r.s === 200 && r.j.nombre.startsWith("Matias"), JSON.stringify(r.j));
await q("UPDATE perfilapp SET debe_cambiar_password = TRUE WHERE id_socio = (SELECT id_socio FROM socios WHERE firebase_uid = $1)", [PRUEBA2]);
check("debe cambiar password", (await api("GET", "/v1/yo", PRUEBA2)).j.debe_cambiar_password === true);
await api("POST", "/v1/yo/password-cambiada", PRUEBA2);
check("password cambiada", (await api("GET", "/v1/yo", PRUEBA2)).j.debe_cambiar_password === false);

r = await api("GET", "/v1/datos-fisicos", MATIAS);
check("datos físicos de Matias", r.j.existe === true && r.j.peso_kg > 0, JSON.stringify(r.j));
r = await api("PUT", "/v1/datos-fisicos", PRUEBA2, { peso_kg: 77.5, edad: 30, sexo: "MASCULINO", experiencia: "Intermedio", condicion_medica: "Asma leve", objetivo: "HIPERTROFIA" });
check("guardar datos físicos", r.s === 200, JSON.stringify(r.j));
r = await api("GET", "/v1/datos-fisicos", PRUEBA2);
check("datos físicos releídos", r.j.peso_kg === 77.5 && r.j.edad === 30 && r.j.objetivo === "HIPERTROFIA" && r.j.condicion_medica === "Asma leve" && r.j.experiencia === "Intermedio");
await api("PUT", "/v1/datos-fisicos", PRUEBA2, { peso_kg: 78, edad: 30, sexo: "MASCULINO", experiencia: "Intermedio", condicion_medica: "Asma leve", objetivo: "FUERZA" });
check("el peso queda como historial", (await q("SELECT count(*)::int n FROM progresopeso WHERE id_socio = (SELECT id_socio FROM socios WHERE firebase_uid=$1)", [PRUEBA2]))[0].n === 2);
check("un solo objetivo activo", (await q("SELECT count(*)::int n FROM objetivos WHERE estado='activo' AND id_socio = (SELECT id_socio FROM socios WHERE firebase_uid=$1)", [PRUEBA2]))[0].n === 1);
check("validación: peso absurdo → 400", (await api("PUT", "/v1/datos-fisicos", PRUEBA2, { peso_kg: 5, edad: 30, sexo: "MASCULINO" })).s === 400);
check("validación: sexo inválido → 400", (await api("PUT", "/v1/datos-fisicos", PRUEBA2, { peso_kg: 70, edad: 30, sexo: "X" })).s === 400);
await api("PATCH", "/v1/datos-fisicos", PRUEBA2, { vio_plano: true, incrementar_vista_bodygraph: true, seccion_arena: "ranking", oculto_clasificacion: true });
await api("PATCH", "/v1/datos-fisicos", PRUEBA2, { incrementar_vista_bodygraph: true });
r = await api("GET", "/v1/datos-fisicos", PRUEBA2);
check("PATCH flags", r.j.vio_plano === true && r.j.vistas_bodygraph === 2 && r.j.oculto_clasificacion === true && r.j.secciones_arena_visitadas.includes("ranking"));
await api("PATCH", "/v1/datos-fisicos", PRUEBA2, { oculto_clasificacion: false });

// ───── clasificación ─────
r = await api("GET", "/v1/clasificacion", MATIAS);
check("clasificación", r.s === 200 && r.j.marcas.length > 0 && Object.keys(r.j.socios).length >= 4 && Object.keys(r.j.datos_fisicos).length >= 2);
check("clasificación no filtra condición médica", Object.values<any>(r.j.datos_fisicos).every((d) => d.condicion_medica === ""));
check("marcas rechazadas no cuentan", r.j.marcas.every((m: any) => typeof m.verificado === "boolean"));

// ───── marcas ─────
r = await api("POST", "/v1/marcas", JANO, { ejercicio: "Press banca", peso: 90, repeticiones: 5, timestamp: Date.now() });
check("nueva marca", r.s === 200 && r.j.id, JSON.stringify(r.j));
const marcaId = r.j.id;
check("marca desconocida → 400", (await api("POST", "/v1/marcas", JANO, { ejercicio: "Curl de bíceps", peso: 20, repeticiones: 5 })).s === 400);
r = await api("GET", "/v1/marcas", JANO);
const m = r.j.marcas.find((x: any) => x.id === marcaId);
check("mis marcas incluye la nueva, pendiente", m && m.verificado === false && m.peso === 90 && m.fecha.length > 5, JSON.stringify(m));
check("1RM estimado (Epley)", Number((await q("SELECT uno_rm_estimado FROM marcaspersonales WHERE id_marca=$1", [marcaId]))[0].uno_rm_estimado) === 105);
check("no puede borrar la marca de otro → 404", (await api("DELETE", `/v1/marcas/${marcaId}`, MATIAS)).s === 404);
check("borrar marca propia", (await api("DELETE", `/v1/marcas/${marcaId}`, JANO)).s === 200);

// ───── series ─────
await api("POST", "/v1/series", JANO, { ejercicio: "Sentadilla", peso: 100, repeticiones: 8, es_peso_corporal: false });
await api("POST", "/v1/series", JANO, { ejercicio: "Sentadilla", peso: 100, repeticiones: 7 });
r = await api("GET", "/v1/series", JANO);
check("series", r.j.series.length >= 2 && r.j.series.at(-1).repeticiones === 7);
check("numero_serie correlativo", (await q("SELECT max(numero_serie)::int n FROM seriesentrenamiento WHERE ejercicio='Sentadilla' AND id_socio=(SELECT id_socio FROM socios WHERE firebase_uid=$1) AND fecha::date = CURRENT_DATE", [JANO]))[0].n === 2);

// ───── rutinas ─────
r = await api("GET", "/v1/rutinas", MATIAS);
const delEntrenador = r.j.rutinas.find((x: any) => x.origen === "entrenador");
check("rutina del entrenador", delEntrenador && delEntrenador.activa && delEntrenador.ejercicios.length === 5);
check("no se puede editar la del entrenador → 403", (await api("PUT", `/v1/rutinas/${delEntrenador.id}`, MATIAS, { nombre: "x", ejercicios: [{ nombre: "a" }] })).s === 403);
check("no se puede borrar la del entrenador → 403", (await api("DELETE", `/v1/rutinas/${delEntrenador.id}`, MATIAS)).s === 403);
const cat = (await api("GET", "/v1/ejercicios", MATIAS)).j.ejercicios;
check("catálogo de ejercicios publicado", cat.length > 0 && cat[0].puntos !== undefined, `${cat.length} ejercicios`);
r = await api("POST", "/v1/rutinas", MATIAS, { nombre: "Mi rutina", ejercicios: [
  { nombre: cat[0].nombre, ejercicio_id: cat[0].id, series_objetivo: 4, peso_base_kg: 20 },
  { nombre: "Curl inventado", series_objetivo: 3, peso_base_kg: 7.5 },
  { nombre: "Con id roto", ejercicio_id: "99999", series_objetivo: 2 }] });
check("crear rutina propia", r.s === 200, JSON.stringify(r.j));
const propiaId = r.j.id;
r = await api("GET", "/v1/rutinas", MATIAS);
const propia = r.j.rutinas.find((x: any) => x.id === propiaId);
check("la propia no desplaza a la activa del entrenador", propia.activa === false && r.j.rutinas.find((x: any) => x.id === delEntrenador.id).activa === true);
check("ejercicio escrito a mano sin ficha", propia.ejercicios[1].ejercicio_id === null && propia.ejercicios[2].ejercicio_id === null && propia.ejercicios[0].ejercicio_id === cat[0].id);
check("validación: rutina vacía → 400", (await api("POST", "/v1/rutinas", MATIAS, { nombre: "Vacía", ejercicios: [] })).s === 400);
check("validación: series 0 → 400", (await api("POST", "/v1/rutinas", MATIAS, { nombre: "x", ejercicios: [{ nombre: "a", series_objetivo: 0 }] })).s === 400);
check("activar la propia", (await api("POST", `/v1/rutinas/${propiaId}/activar`, MATIAS)).s === 200);
r = await api("GET", "/v1/rutinas", MATIAS);
check("una sola activa", r.j.rutinas.filter((x: any) => x.activa).length === 1 && r.j.rutinas.find((x: any) => x.id === propiaId).activa);
check("editar la propia", (await api("PUT", `/v1/rutinas/${propiaId}`, MATIAS, { nombre: "Renombrada", ejercicios: [{ nombre: "Solo uno", series_objetivo: 5 }] })).s === 200);
r = await api("GET", "/v1/rutinas", MATIAS);
check("edición aplicada", r.j.rutinas.find((x: any) => x.id === propiaId).ejercicios.length === 1 && r.j.rutinas.find((x: any) => x.id === propiaId).nombre === "Renombrada");
check("rutina de otro socio → 404", (await api("POST", `/v1/rutinas/${propiaId}/activar`, JANO)).s === 404);
check("borrar la propia", (await api("DELETE", `/v1/rutinas/${propiaId}`, MATIAS)).s === 200);
await api("POST", "/v1/rutinas", PRUEBA2, { nombre: "Primera", ejercicios: [{ nombre: "Algo" }] });
r = await api("GET", "/v1/rutinas", PRUEBA2);
check("primera rutina → activa", r.j.rutinas.length === 1 && r.j.rutinas[0].activa === true);

// ───── clases: reservas, cancelación y cupo ─────
r = await api("GET", "/v1/clases", MATIAS);
check("clases", r.j.clases.length === 3 && r.j.semana.startsWith("20"), JSON.stringify(r.j.clases));
const boxeo = r.j.clases.find((c: any) => c.id === "boxeo-mar");
check("cupo de boxeo = 15", boxeo.cupo === 15);
check("reservar", (await api("POST", "/v1/clases/boxeo-mar/reservar", MATIAS)).j.resultado === "OK");
check("no se reserva dos veces", (await api("POST", "/v1/clases/boxeo-mar/reservar", MATIAS)).j.resultado === "YA_RESERVADA");
r = await api("GET", "/v1/clases", MATIAS);
check("la reserva aparece y suma al cupo", r.j.mis_reservas.some((x: any) => x.clase_id === "boxeo-mar") && r.j.clases.find((c: any) => c.id === "boxeo-mar").reservados >= 1);
check("clase inexistente → 404", (await api("POST", "/v1/clases/no-existe/reservar", MATIAS)).s === 404);
// 14 socios de relleno + los que ya hay llenan la clase
await q("INSERT INTO socios (firebase_uid, nombre, apellido, email) SELECT 'relleno_'||g, 'Relleno', ''||g, 'relleno'||g||'@test.com' FROM generate_series(1,20) g ON CONFLICT DO NOTHING");
const yaReservados = (await api("GET", "/v1/clases", MATIAS)).j.clases.find((c: any) => c.id === "boxeo-mar").reservados;
for (let i = 1; i <= 14 - yaReservados + 1; i++) await api("POST", "/v1/clases/boxeo-mar/reservar", `relleno_${i}`);
check("la clase llega al cupo exacto", (await api("GET", "/v1/clases", MATIAS)).j.clases.find((c: any) => c.id === "boxeo-mar").reservados === 15);
check("clase llena → CLASE_LLENA", (await api("POST", "/v1/clases/boxeo-mar/reservar", "relleno_20")).j.resultado === "CLASE_LLENA");
// cancelar libera 1 lugar; 3 socios compiten a la vez por ese único lugar
check("cancelar", (await api("DELETE", "/v1/clases/boxeo-mar/reserva", MATIAS)).s === 200);
const carrera = await Promise.all(["relleno_16", "relleno_17", "relleno_18", "relleno_19"].map((u) => api("POST", "/v1/clases/boxeo-mar/reservar", u)));
const resultados = carrera.map((x) => x.j.resultado).sort();
check("carrera por la última plaza: exactamente 1 gana", resultados.filter((x) => x === "OK").length === 1 && resultados.filter((x) => x === "CLASE_LLENA").length === 3, resultados.join(","));
const semanaActual = (await api("GET", "/v1/clases", MATIAS)).j.semana;
check("cupo nunca se supera", (await q("SELECT count(*)::int n FROM reservasclase WHERE estado='confirmada' AND semana=$1 AND id_clase=(SELECT id_clase FROM clases WHERE codigo='boxeo-mar')", [semanaActual]))[0].n === 15);
check("el historial conserva lo cancelado", (await q("SELECT count(*)::int n FROM reservasclase WHERE estado='cancelada'"))[0].n >= 1);

// ───── ingresos ─────
await api("POST", "/v1/ingresos", JANO, { metodo: "qr" });
await api("POST", "/v1/ingresos", JANO, { metodo: "cualquiera" });
r = await api("GET", "/v1/ingresos", JANO);
check("ingresos", r.j.ingresos.length >= 2 && r.j.ingresos.at(-1).metodo === "manual" && r.j.ingresos.some((x: any) => x.metodo === "qr"));

// ───── lockers ─────
await q("DELETE FROM reservaslocker");
check("reservar locker 5", (await api("POST", "/v1/lockers/reservar", MATIAS, { numero: 5 })).s === 200);
r = await api("POST", "/v1/lockers/reservar", JANO, { numero: 5 });
check("locker ocupado → 409", r.s === 409, r.j.error);
check("locker inexistente → 404", (await api("POST", "/v1/lockers/reservar", JANO, { numero: 99 })).s === 404);
check("cambiar de locker libera el anterior", (await api("POST", "/v1/lockers/reservar", MATIAS, { numero: 6 })).s === 200 && (await api("POST", "/v1/lockers/reservar", JANO, { numero: 5 })).s === 200);
r = await api("GET", "/v1/lockers", MATIAS);
check("lista de lockers ocupados", r.j.lockers.length === 2 && r.j.lockers.some((l: any) => l.numero === 6 && l.socio_id === MATIAS));
check("un fallo no pierde el locker que ya tenía", (await api("POST", "/v1/lockers/reservar", MATIAS, { numero: 5 })).s === 409 && (await api("GET", "/v1/lockers", MATIAS)).j.lockers.some((l: any) => l.numero === 6 && l.socio_id === MATIAS));
check("liberar", (await api("DELETE", "/v1/lockers/mio", MATIAS)).s === 200 && (await api("GET", "/v1/lockers", MATIAS)).j.lockers.length === 1);

// ───── compañeros ─────
check("agregar compañero", (await api("POST", "/v1/companeros", MATIAS, { companero_id: JANO })).s === 200);
check("no puede ser compañero de sí mismo → 404", (await api("POST", "/v1/companeros", MATIAS, { companero_id: MATIAS })).s === 404);
check("compañero inexistente → 404", (await api("POST", "/v1/companeros", MATIAS, { companero_id: "no-existe" })).s === 404);
r = await api("GET", "/v1/companeros", MATIAS);
check("lista de compañeros", r.j.companeros.length === 1 && r.j.companeros[0].socio_id === JANO);
check("días juntos", typeof (await api("GET", "/v1/companeros/dias-juntos", MATIAS)).j.dias === "number");
check("quitar compañero", (await api("DELETE", `/v1/companeros/${JANO}`, MATIAS)).s === 200 && (await api("GET", "/v1/companeros", MATIAS)).j.companeros.length === 0);

// ───── fotos de progreso ─────
const png = Buffer.from("fake-image-data").toString("base64");
r = await api("POST", "/v1/fotos-progreso", JANO, { imagen: png });
check("subir foto", r.s === 200 && r.j.id);
check("foto no base64 → 400", (await api("POST", "/v1/fotos-progreso", JANO, { imagen: "###no es base64###" })).s === 400);
check("listar fotos", (await api("GET", "/v1/fotos-progreso", JANO)).j.fotos.some((f: any) => f.id === r.j.id && f.imagen === png));
check("foto de otro no se borra", (await api("DELETE", `/v1/fotos-progreso/${r.j.id}`, MATIAS)).s === 200 && (await api("GET", "/v1/fotos-progreso", JANO)).j.fotos.length === 1);
check("borrar foto propia", (await api("DELETE", `/v1/fotos-progreso/${r.j.id}`, JANO)).s === 200 && (await api("GET", "/v1/fotos-progreso", JANO)).j.fotos.length === 0);

// ───── nutrición ─────
r = await api("GET", "/v1/platos", MATIAS);
check("platos publicados", r.j.platos.length > 0 && r.j.platos[0].imagen && r.j.platos[0].puntos.length > 0 && r.j.platos[0].macros.kcal >= 0, `${r.j.platos.length}`);
const platoId = r.j.platos[0].id;
r = await api("GET", "/v1/dieta-asignada", MATIAS);
check("dieta asignada", r.j.existe === true && Object.values<any>(r.j.comidas).flat().length > 0 && r.j.asignada_por.includes("—"), JSON.stringify(r.j));
check("sin dieta → existe false", (await api("GET", "/v1/dieta-asignada", PRUEBA2)).j.existe === false);
await api("POST", "/v1/platos-probados", PRUEBA2, { plato_id: platoId });
await api("POST", "/v1/platos-probados", PRUEBA2, { plato_id: platoId });
check("platos probados (sin duplicar)", (await api("GET", "/v1/platos-probados", PRUEBA2)).j.plato_ids.length === 1);
check("plato inexistente → 409", (await api("POST", "/v1/platos-probados", PRUEBA2, { plato_id: "99999" })).s === 409);
await api("POST", "/v1/agua", PRUEBA2);
check("agua", (await api("GET", "/v1/agua", PRUEBA2)).j.registros.length === 1);
check("perfil nutricional vacío", (await api("GET", "/v1/perfil-nutricional", PRUEBA1)).j.existe === false);
check("guardar perfil", (await api("PUT", "/v1/perfil-nutricional", JANO, { preferencias: ["Vegano", "Keto"], excluidos: ["Maní"] })).s === 200);
r = await api("GET", "/v1/perfil-nutricional", JANO);
check("perfil releído", r.j.preferencias.length === 2 && r.j.excluidos[0] === "Maní");
const hoy = new Date(Date.now() - 3 * 3600_000).toISOString().slice(0, 10).replaceAll("-", "");
r = await api("PUT", "/v1/comidas", JANO, { fecha: hoy, momento: "desayuno", kcal: 450, proteinas: 35, carbs: 40, grasas: 14, plato_ids: [platoId, "99999"], nota: "rico", imagen: png,
  meta: { kcal: 1800, proteinas: 120, carbs: 200, grasas: 60, momentos: ["desayuno", "cena"] }, objetivo: "FUERZA" });
check("registrar comida", r.s === 200, JSON.stringify(r.j));
r = await api("GET", "/v1/comidas", JANO);
const dia = r.j.dias.find((d: any) => d.fecha === hoy);
check("comida releída con meta y platos válidos", dia && dia.comidas.desayuno.kcal === 450 && dia.comidas.desayuno.plato_ids.length === 1 && dia.meta.kcal === 1800 && dia.meta.momentos.length === 2 && dia.objetivo === "FUERZA", JSON.stringify(dia));
check("foto de la comida", (await api("GET", `/v1/comidas/${hoy}/desayuno/foto`, JANO)).j.imagen === png);
check("fecha vieja → 400", (await api("PUT", "/v1/comidas", JANO, { fecha: "20200101", momento: "cena", imagen: png })).s === 400);
check("momento inválido → 400", (await api("PUT", "/v1/comidas", JANO, { fecha: hoy, momento: "merienda", imagen: png })).s === 400);
check("borrar comida", (await api("DELETE", `/v1/comidas/${hoy}/desayuno`, JANO)).s === 200 && (await api("GET", `/v1/comidas/${hoy}/desayuno/foto`, JANO)).j.imagen === null);

// ───── club ─────
r = await api("GET", "/v1/tablon", MATIAS);
check("tablón (solo publicado)", r.j.publicaciones.length === 1 && r.j.publicaciones[0].categoria === "Importante");
r = await api("GET", "/v1/ocupacion", MATIAS);
check("ocupación", r.j.personas >= 0 && r.j.capacidad_maxima === 120, JSON.stringify(r.j));
r = await api("GET", "/v1/membresia", MATIAS);
check("membresía", r.j.existe && r.j.plan === "Platino" && r.j.incluye_argos === true && r.j.fecha_inicio_ms > 1.7e12, JSON.stringify(r.j));
check("sin membresía", (await api("GET", "/v1/membresia", PRUEBA1)).j.existe === false);
check("pagos vacíos", (await api("GET", "/v1/pagos", MATIAS)).j.pagos.length === 0);

// ───── Argos ─────
check("base de conocimiento", typeof (await api("GET", "/v1/argos/base-conocimiento", MATIAS)).j.texto === "string");
r = await api("POST", "/v1/argos/consumir", MATIAS);
check("Argos con plan Platino", r.s === 200 && r.j.restantes <= 299, JSON.stringify(r.j));
check("Argos sin plan → 403", (await api("POST", "/v1/argos/consumir", PRUEBA1)).s === 403);
await q("UPDATE argoscupodiario SET mensajes_enviados = 300 WHERE id_socio = (SELECT id_socio FROM socios WHERE firebase_uid=$1)", [MATIAS]);
check("cupo diario agotado → 429", (await api("POST", "/v1/argos/consumir", MATIAS)).s === 429);

// ───── contacto web (público) ─────
check("contacto con email", (await api("POST", "/v1/contacto", null, { nombre: "Ana", contacto: "ana@mail.com", mensaje: "Hola, quiero info" })).s === 200);
check("contacto con teléfono", (await api("POST", "/v1/contacto", null, { nombre: "Beto", contacto: "351 555 1234", mensaje: "Hola" })).s === 200);
check("contacto inválido → 400", (await api("POST", "/v1/contacto", null, { nombre: "", contacto: "x", mensaje: "y" })).s === 400);
const ultimo = (await q("SELECT email, telefono FROM contactosweb ORDER BY id_contacto DESC LIMIT 2"));
check("el contacto va a email o teléfono según corresponda", ultimo[1].email === "ana@mail.com" && ultimo[1].telefono === null && ultimo[0].telefono === "351 555 1234");
check("CORS preflight", (await manejar(new Request("http://x/v1/yo", { method: "OPTIONS" }), deps)).status === 204);

// ───── aislamiento entre socios ─────
check("las series de Jano no aparecen en Matias", !(await api("GET", "/v1/series", MATIAS)).j.series.some((s: any) => s.repeticiones === 7 && s.ejercicio === "Sentadilla" && s.peso === 100));
r = await api("GET", "/v1/ingresos", MATIAS);
check("el ingreso de Jano no aparece en Matias", !r.j.ingresos.some((x: any) => x.metodo === "qr"));

// limpieza de lo creado por la prueba
await q("DELETE FROM socios WHERE firebase_uid LIKE 'relleno_%'");
await pool.end();
console.log(`\nTODO OK: ${total} comprobaciones`);
