// Tipos y utilidades compartidas por todas las rutas de la API.

export type Fila = Record<string, any>;

/** Acceso a la base: una consulta suelta o una transacción (todo o nada). */
export interface Db {
  query(texto: string, params?: unknown[]): Promise<{ rows: Fila[]; rowCount: number | null }>;
  tx<T>(fn: (db: Db) => Promise<T>): Promise<T>;
}

export interface Contexto {
  db: Db;
  /** UID de Firebase Authentication del socio que llama. */
  uid: string;
  email: string | null;
  /** id_socio (clave primaria de la tabla "socios"). */
  idSocio: number;
  req: Request;
  url: URL;
  /** Grupos capturados por la expresión regular de la ruta. */
  params: string[];
  /** Cuerpo JSON ya leído ({} si no hay). */
  body: any;
  ahora: Date;
}

export type Manejador = (c: Contexto) => Promise<unknown>;

export interface Ruta {
  metodo: "GET" | "POST" | "PUT" | "DELETE";
  patron: RegExp;
  manejador: Manejador;
  /** true = no pide token (por ejemplo el formulario de contacto de la web). */
  publica?: boolean;
}

/** Error con código HTTP y un mensaje que se le muestra tal cual al usuario. */
export class ErrorApi extends Error {
  constructor(public estado: number, mensaje: string) {
    super(mensaje);
  }
}

export const MS_DIA = 86_400_000;
// Argentina no tiene horario de verano: UTC-3 todo el año.
const OFFSET_LOCAL_MS = -3 * 3_600_000;

/** Fecha "de pared" en Argentina como Date en UTC (para sacar día/semana). */
export function aLocal(d: Date): Date {
  return new Date(d.getTime() + OFFSET_LOCAL_MS);
}

/** "2026-W40": semana ISO 8601 (lunes a domingo) de la hora local argentina. */
export function claveSemana(d: Date): string {
  const t = aLocal(d);
  const dia = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - dia);
  const inicio = Date.UTC(t.getUTCFullYear(), 0, 1);
  const semana = Math.ceil(((t.getTime() - inicio) / MS_DIA + 1) / 7);
  return `${t.getUTCFullYear()}-W${semana}`;
}

/** "2026-10-02" del día local argentino. */
export function fechaLocalISO(d: Date): string {
  return aLocal(d).toISOString().slice(0, 10);
}

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

/** "13 sep 2026" a partir de milisegundos. */
export function fechaLegible(ms: number): string {
  const t = aLocal(new Date(ms));
  return `${t.getUTCDate()} ${MESES[t.getUTCMonth()]} ${t.getUTCFullYear()}`;
}

/** Fragmento SQL: milisegundos desde 1970 (número, no texto) de una columna de fecha. */
export function MS(columna: string): string {
  return `floor(extract(epoch from ${columna}) * 1000)::float8`;
}

// ───────────── validación del cuerpo ─────────────

export function texto(v: unknown, campo: string, max: number, opciones: { vacio?: boolean } = {}): string {
  if (typeof v !== "string") throw new ErrorApi(400, `Falta "${campo}".`);
  const t = v.trim();
  if (!t && !opciones.vacio) throw new ErrorApi(400, `"${campo}" no puede estar vacío.`);
  if (t.length > max) throw new ErrorApi(400, `"${campo}" es demasiado largo (máximo ${max} caracteres).`);
  return t;
}

export function numero(v: unknown, campo: string, min: number, max: number): number {
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n) || n < min || n > max) throw new ErrorApi(400, `"${campo}" tiene que ser un número entre ${min} y ${max}.`);
  return n;
}

export function entero(v: unknown, campo: string, min: number, max: number): number {
  const n = numero(v, campo, min, max);
  if (!Number.isInteger(n)) throw new ErrorApi(400, `"${campo}" tiene que ser un número entero.`);
  return n;
}

export function idNumerico(v: string, campo = "id"): number {
  if (!/^[0-9]{1,9}$/.test(v)) throw new ErrorApi(400, `"${campo}" inválido.`);
  return Number(v);
}

export function listaTextos(v: unknown, campo: string, maxItems: number, maxLargo: number): string[] {
  if (v === undefined || v === null) return [];
  if (!Array.isArray(v)) throw new ErrorApi(400, `"${campo}" tiene que ser una lista.`);
  if (v.length > maxItems) throw new ErrorApi(400, `"${campo}" tiene demasiados elementos (máximo ${maxItems}).`);
  return [...new Set(v.map((x) => texto(x, campo, maxLargo)))];
}

export const MOMENTOS = ["desayuno", "almuerzo", "cena"] as const;
export type Momento = (typeof MOMENTOS)[number];
export const OBJETIVOS = ["FUERZA", "HIPERTROFIA", "SALUD"] as const;

/** Adapta cualquier "pool" compatible con node-postgres (Neon o pg) a la interfaz Db. */
export function dbDesdePool(pool: { query: Function; connect: Function }): Db {
  return {
    query: (texto, params) => pool.query(texto, params as any[]),
    async tx(fn) {
      const cliente = await pool.connect();
      const dbTx: Db = {
        query: (texto, params) => cliente.query(texto, params as any[]),
        tx: () => { throw new Error("No se anidan transacciones."); },
      };
      try {
        await cliente.query("BEGIN");
        const r = await fn(dbTx);
        await cliente.query("COMMIT");
        return r;
      } catch (e) {
        await cliente.query("ROLLBACK").catch(() => {});
        throw e;
      } finally {
        cliente.release();
      }
    },
  };
}

