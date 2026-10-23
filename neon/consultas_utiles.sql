-- =====================================================================
--  OLIMPOS — Consultas útiles para el SQL Editor de Neon
-- =====================================================================
--  Cómo usarlas: console.neon.tech → el proyecto → "SQL Editor" (menú de
--  la izquierda) → pegar UNA consulta → "Run".
--  Todas son de solo lectura (SELECT): no cambian nada en la base.
--  Las fechas se muestran en hora de Argentina.
-- =====================================================================


-- 1) SOCIOS con su plan y si están al día --------------------------------
SELECT s.id_socio, s.nombre || ' ' || s.apellido AS socio, s.email, s.estado,
       m.nombre AS plan, sm.fecha_vencimiento AS vence,
       CASE WHEN sm.id_socio IS NULL THEN 'Sin plan'
            WHEN sm.fecha_vencimiento < current_date THEN 'VENCIDO'
            ELSE 'Al día' END AS situacion
FROM socios s
LEFT JOIN sociomembresia sm ON sm.id_socio = s.id_socio AND sm.estado = 'activa'
LEFT JOIN membresias m ON m.id_membresia = sm.id_membresia
ORDER BY situacion DESC, socio;


-- 2) MEMBRESÍAS que vencen en los próximos 7 días (o ya vencieron) -------
SELECT s.nombre || ' ' || s.apellido AS socio, s.telefono, m.nombre AS plan,
       sm.fecha_vencimiento AS vence, sm.fecha_vencimiento - current_date AS dias
FROM sociomembresia sm
JOIN socios s USING (id_socio) JOIN membresias m USING (id_membresia)
WHERE sm.estado = 'activa' AND sm.fecha_vencimiento <= current_date + 7
ORDER BY sm.fecha_vencimiento;


-- 3) PAGOS del mes actual (y el total) -----------------------------------
SELECT (p.fecha_pago AT TIME ZONE 'America/Argentina/Buenos_Aires')::date AS fecha,
       s.nombre || ' ' || s.apellido AS socio, m.nombre AS plan, p.monto,
       mp.tipo AS medio, p.estado
FROM pagos p
JOIN socios s USING (id_socio) JOIN membresias m USING (id_membresia)
JOIN mediospago mp USING (id_medio_pago)
WHERE date_trunc('month', p.fecha_pago AT TIME ZONE 'America/Argentina/Buenos_Aires')
      = date_trunc('month', now() AT TIME ZONE 'America/Argentina/Buenos_Aires')
ORDER BY p.fecha_pago DESC;

SELECT COALESCE(sum(monto), 0) AS total_cobrado_este_mes
FROM pagos
WHERE estado = 'Aprobado'
  AND date_trunc('month', fecha_pago AT TIME ZONE 'America/Argentina/Buenos_Aires')
      = date_trunc('month', now() AT TIME ZONE 'America/Argentina/Buenos_Aires');


-- 4) INGRESOS por mes (últimos 12 meses) ---------------------------------
SELECT to_char(date_trunc('month', fecha_pago AT TIME ZONE 'America/Argentina/Buenos_Aires'), 'YYYY-MM') AS mes,
       count(*) AS pagos, sum(monto) AS total
FROM pagos
WHERE estado = 'Aprobado' AND fecha_pago > now() - interval '12 months'
GROUP BY 1 ORDER BY 1;


-- 5) PLANES y precios (lo que cobra Mercado Pago) ------------------------
SELECT nombre, precio, duracion_dias, incluye_argos, estado FROM membresias ORDER BY precio;


-- 6) ENTRADAS al club de hoy (carnet de la app) --------------------------
SELECT (a.fecha AT TIME ZONE 'America/Argentina/Buenos_Aires')::time(0) AS hora,
       s.nombre || ' ' || s.apellido AS socio, a.metodo, a.resultado
FROM accesos a JOIN socios s USING (id_socio)
WHERE (a.fecha AT TIME ZONE 'America/Argentina/Buenos_Aires')::date
      = (now() AT TIME ZONE 'America/Argentina/Buenos_Aires')::date
ORDER BY a.fecha DESC;


-- 7) ENTRENAMIENTOS: series por socio en los últimos 30 días -------------
SELECT s.nombre || ' ' || s.apellido AS socio, count(*) AS series,
       count(DISTINCT se.fecha::date) AS dias,
       max(se.fecha AT TIME ZONE 'America/Argentina/Buenos_Aires')::date AS ultimo
FROM seriesentrenamiento se JOIN socios s USING (id_socio)
WHERE se.fecha > now() - interval '30 days'
GROUP BY socio ORDER BY series DESC;


-- 8) MARCAS personales por verificar (las de la Arena) -------------------
SELECT s.nombre || ' ' || s.apellido AS socio, e.nombre AS ejercicio,
       mp.peso, mp.repeticiones, mp.fecha::date, mp.estado
FROM marcaspersonales mp
JOIN socios s USING (id_socio)
JOIN ejerciciosmarca em ON em.id_ejercicio_marca = mp.id_ejercicio_marca
JOIN ejercicios e ON e.id_ejercicio = em.id_ejercicio
WHERE mp.estado NOT IN ('verificada', 'rechazada')
ORDER BY mp.fecha DESC;


-- 9) SOCIOS sin rutina o sin dieta vigente -------------------------------
SELECT s.nombre || ' ' || s.apellido AS socio,
       EXISTS (SELECT 1 FROM rutinas r WHERE r.id_socio = s.id_socio AND r.estado = 'vigente') AS tiene_rutina,
       EXISTS (SELECT 1 FROM dietas d WHERE d.id_socio = s.id_socio AND d.estado = 'vigente') AS tiene_dieta
FROM socios s WHERE s.estado = 'activo' ORDER BY socio;


-- 10) EMPLEADOS y su rol --------------------------------------------------
SELECT e.usuario, e.nombre || ' ' || e.apellido AS empleado, r.descripcion AS rol, e.estado
FROM empleados e JOIN rol r ON r.id_rol = e.rol ORDER BY r.id_rol;


-- 11) SEGURIDAD: ingresos fallidos al sistema de empleados (7 días) -----
SELECT (i.fecha AT TIME ZONE 'America/Argentina/Buenos_Aires')::timestamp(0) AS cuando,
       e.usuario, i.motivo, i.dispositivo
FROM intentosacceso i LEFT JOIN empleados e ON e.id_empleado = i.id_empleado
WHERE i.resultado = 'fallido' AND i.fecha > now() - interval '7 days'
ORDER BY i.fecha DESC;


-- 12) ARGOS: mensajes usados por día -------------------------------------
SELECT fecha, sum(mensajes_enviados) AS mensajes FROM argoscupodiario
GROUP BY fecha ORDER BY fecha DESC LIMIT 30;


-- 13) MENSAJES de la página web sin responder ----------------------------
SELECT fecha::date, nombre, email, telefono, mensaje FROM contactosweb
WHERE estado = 'nuevo' ORDER BY fecha DESC;


-- 14) CONFIGURACIÓN del sistema de empleados (por usuario y del club) ---
SELECT clave, valor, fecha_actualizacion FROM configuracionsistema ORDER BY clave;


-- 15) Cuántas filas tiene cada tabla (para ver qué se está usando) ------
SELECT relname AS tabla, n_live_tup AS filas
FROM pg_stat_user_tables ORDER BY n_live_tup DESC;
