# Diccionario de datos - OlimpOS Gym

Base de datos relacional PostgreSQL (Neon). 114 tablas, 114 claves primarias, 136 claves foráneas.

Leyenda: **PK** clave primaria · **FK** clave foránea (con su regla de borrado) · **UK** clave única · **NN** no admite nulos.

## Personas y roles

### socios

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** |
| dni | character varying |  |
| nombre | character varying | NN |
| apellido | character varying | NN |
| fecha_nacimiento | date |  |
| sexo | character varying |  |
| rol | int | **FK** → rol.id_rol (borrado: NO ACTION) · NN · por defecto `1` |
| direccion | character varying |  |
| telefono | character varying |  |
| email | character varying | NN |
| contraseña | character varying |  |
| estado | character varying | NN · por defecto `'activo'::character varying` |
| fecha_registro | timestamptz | NN · por defecto `now()` |
| nivel_experiencia | character varying |  |
| disponibilidad_horaria | character varying |  |
| firebase_uid | character varying |  |

Reglas adicionales: `CHECK (((dni IS NULL) OR ((dni)::text ~ '^[0-9]{7,8}$'::text)))`; `CHECK (((nivel_experiencia IS NULL) OR ((nivel_experiencia)::text = ANY ((ARRAY['Principiante'::character varying, 'Intermedio'::character varying, 'Avanzado'::character varying])::text[]))))`; `CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'inactivo'::character varying])::text[])))`; `CHECK (((sexo IS NULL) OR ((sexo)::text = ANY ((ARRAY['MASCULINO'::character varying, 'FEMENINO'::character varying, 'PREFIERO_NO_DECIRLO'::character varying])::text[]))))`; índice: `public.socios USING btree (email)`; índice: `public.socios USING btree (dni)`; índice: `public.socios USING btree (lower((email)::text))`; índice: `public.socios USING btree (firebase_uid)`

### empleados

| Columna | Tipo | Restricciones |
|---|---|---|
| id_empleado | int | **PK** |
| dni | character varying |  |
| nombre | character varying | NN |
| apellido | character varying | NN |
| rol | int | **FK** → rol.id_rol (borrado: NO ACTION) · NN |
| email | character varying | NN |
| contraseña | character varying | NN |
| direccion | character varying |  |
| telefono | character varying |  |
| estado | character varying | NN · por defecto `'activo'::character varying` |
| fecha_ingreso | timestamptz | NN · por defecto `now()` |
| usuario | character varying |  |
| sueldo | numeric |  |
| turno | character varying |  |
| especialidad | character varying |  |
| fecha_baja | date |  |
| motivo_baja | character varying |  |

Reglas adicionales: `CHECK (((dni IS NULL) OR ((dni)::text ~ '^[0-9]{7,8}$'::text)))`; `CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'inactivo'::character varying])::text[])))`; `CHECK (((sueldo IS NULL) OR (sueldo >= (0)::numeric)))`; índice: `public.empleados USING btree (lower((usuario)::text))`; índice: `public.empleados USING btree (lower((email)::text))`; índice: `public.empleados USING btree (usuario)`; índice: `public.empleados USING btree (email)`; índice: `public.empleados USING btree (dni)`

### entrenadores

| Columna | Tipo | Restricciones |
|---|---|---|
| id_empleado | int | **PK** · **FK** → empleados.id_empleado (borrado: CASCADE) |
| especialidad | character varying |  |
| descripcion | character varying |  |
| experiencia | character varying |  |
| disponibilidad | character varying |  |
| estado | character varying | NN |

### profesionales

| Columna | Tipo | Restricciones |
|---|---|---|
| id_profesional | int | **PK** |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: CASCADE) · NN |
| especialidad | character varying |  |
| descripcion | character varying |  |
| disponibilidad | character varying |  |
| estado | character varying | NN |

### rol

| Columna | Tipo | Restricciones |
|---|---|---|
| id_rol | int | **PK** |
| nombre | character varying | **UK** · NN |
| descripcion | character varying |  |

Reglas adicionales: índice: `public.rol USING btree (nombre)`

### perfilapp

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** · **FK** → socios.id_socio (borrado: CASCADE) |
| edad | smallint |  |
| debe_cambiar_password | bool | NN · por defecto `true` |
| oculto_clasificacion | bool | NN · por defecto `false` |
| vio_plano | bool | NN · por defecto `false` |
| vistas_bodygraph | int | NN · por defecto `0` |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |

Reglas adicionales: `CHECK ((vistas_bodygraph >= 0))`; `CHECK (((edad >= 1) AND (edad <= 120)))`

### perfilappsecciones

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → perfilapp.id_socio (borrado: CASCADE) |
| seccion | character varying | **PK** (compuesta) |

## Seguridad y accesos de usuarios

### permisos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_permiso | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |

### rolpermiso

| Columna | Tipo | Restricciones |
|---|---|---|
| id_rol | int | **PK** (compuesta) · **FK** → rol.id_rol (borrado: CASCADE) |
| id_permiso | int | **PK** (compuesta) · **FK** → permisos.id_permiso (borrado: CASCADE) |

### usuariopermiso

| Columna | Tipo | Restricciones |
|---|---|---|
| id_usuario | int | **PK** (compuesta) |
| tipo_usuario | character varying | **PK** (compuesta) |
| id_permiso | numeric | **PK** (compuesta) |
| estado | character varying | NN |

Reglas adicionales: `CHECK (((tipo_usuario)::text = ANY ((ARRAY['socio'::character varying, 'empleado'::character varying])::text[])))`

### sesiones

| Columna | Tipo | Restricciones |
|---|---|---|
| id_sesion | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha_inicio | timestamptz | NN |
| fecha_fin | timestamptz |  |
| dispositivo | character varying |  |
| ip | character varying |  |
| estado | character varying | NN |

### intentosacceso

| Columna | Tipo | Restricciones |
|---|---|---|
| id_intento | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| fecha | timestamptz | NN |
| tipo_usuario | character varying | NN |
| resultado | character varying | NN |
| motivo | character varying |  |
| dispositivo | character varying |  |

### dispositivos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_dispositivo | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| tipo_dispositivo | character varying | NN |
| nombre_dispositivo | character varying |  |
| identificador | character varying | NN |
| fecha_vinculacion | timestamptz | NN |
| estado | character varying | NN |

### politicasseguridad

| Columna | Tipo | Restricciones |
|---|---|---|
| id_politica | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| valor | character varying |  |
| estado | character varying | NN |
| fecha_actualizacion | timestamptz | NN |

### recuperacioncontraseña

| Columna | Tipo | Restricciones |
|---|---|---|
| id_recuperacion | int | **PK** |
| id_socio | int |  |
| id_empleado | int |  |
| token | character varying | NN |
| fecha_solicitud | timestamptz | NN |
| fecha_expiracion | timestamptz | NN |
| estado | character varying | NN |

### historialaccesos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_historial | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| fecha | timestamptz | NN |
| accion | character varying | NN |
| descripcion | character varying |  |
| dispositivo | character varying |  |

### historialactividadusuarios

| Columna | Tipo | Restricciones |
|---|---|---|
| id_actividad | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| fecha | timestamptz | NN |
| accion | character varying | NN |
| descripcion | character varying |  |
| tipo_usuario | character varying | NN |

## Membresías y pagos

### membresias

| Columna | Tipo | Restricciones |
|---|---|---|
| id_membresia | int | **PK** |
| nombre | character varying | **UK** · NN |
| descripcion | character varying |  |
| precio | numeric | NN |
| duracion_dias | int | NN |
| beneficios | character varying |  |
| estado | character varying | NN · por defecto `'activa'::character varying` |
| incluye_argos | bool | NN · por defecto `false` |
| destacado | bool | NN · por defecto `false` |

Reglas adicionales: `CHECK (((precio > (0)::numeric) AND ((duracion_dias >= 1) AND (duracion_dias <= 3650))))`; `CHECK (((precio > (0)::numeric) AND (duracion_dias > 0)))`; índice: `public.membresias USING btree (nombre)`

### sociomembresia

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio_membresia | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_membresia | int | **FK** → membresias.id_membresia (borrado: NO ACTION) · NN |
| fecha_inicio | date | NN |
| fecha_vencimiento | date | NN |
| estado | character varying | NN · por defecto `'activa'::character varying` |
| fecha_cancelacion | date |  |
| asignado_por | character varying |  |

Reglas adicionales: índice: `public.sociomembresia USING btree (id_socio) WHERE ((estado)::text = 'activa'::text)`

### planespago

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plan_pago | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| cantidad_cuotas | int | NN |
| frecuencia | character varying | NN |
| recargo | numeric |  |
| estado | character varying | NN |

### mediospago

| Columna | Tipo | Restricciones |
|---|---|---|
| id_medio_pago | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| tipo | character varying | NN |
| proveedor | character varying |  |
| numero_referencia | character varying |  |
| titular | character varying |  |
| vencimiento | date |  |
| estado | character varying | NN |

Reglas adicionales: índice: `public.mediospago USING btree (id_socio, tipo, proveedor)`

### pagos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_pago | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: RESTRICT) · NN |
| id_membresia | int | **FK** → membresias.id_membresia (borrado: NO ACTION) · NN |
| id_plan_pago | int | **FK** → planespago.id_plan_pago (borrado: NO ACTION) · NN |
| id_medio_pago | int | **FK** → mediospago.id_medio_pago (borrado: NO ACTION) · NN |
| monto | numeric | NN |
| fecha_pago | timestamptz | NN · por defecto `now()` |
| fecha_vencimiento | date |  |
| numero_comprobante | character varying | **UK** |
| estado | character varying | NN |

Reglas adicionales: `CHECK ((monto > (0)::numeric))`; `CHECK ((monto > (0)::numeric))`; índice: `public.pagos USING btree (numero_comprobante)`

### cuotas

| Columna | Tipo | Restricciones |
|---|---|---|
| cod_cuota | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: RESTRICT) · NN |
| id_membresia | int | **FK** → membresias.id_membresia (borrado: NO ACTION) · NN |
| numero_cuota | int | NN |
| monto | numeric | NN |
| fecha_emision | date | NN |
| fecha_vencimiento | date | NN |
| fecha_pago | date |  |
| estado | character varying | NN |

### promociones

| Columna | Tipo | Restricciones |
|---|---|---|
| id_promocion | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| descuento | numeric |  |
| fecha_inicio | date | NN |
| fecha_fin | date | NN |
| condiciones | character varying |  |
| estado | character varying | NN |

### membresiapromocion

| Columna | Tipo | Restricciones |
|---|---|---|
| id_membresia | int | **PK** (compuesta) · **FK** → membresias.id_membresia (borrado: CASCADE) |
| id_promocion | int | **PK** (compuesta) · **FK** → promociones.id_promocion (borrado: CASCADE) |

## Clases e instalaciones

### clases

| Columna | Tipo | Restricciones |
|---|---|---|
| id_clase | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| disciplina | character varying |  |
| capacidad | int | NN |
| nivel | character varying |  |
| estado | character varying | NN · por defecto `'activa'::character varying` |
| codigo | character varying | **UK** |
| lugar | character varying |  |
| dia | character varying |  |
| hora | time |  |

Reglas adicionales: `CHECK ((capacidad > 0))`; índice: `public.clases USING btree (codigo)`

### clasehorario

| Columna | Tipo | Restricciones |
|---|---|---|
| id_clase_horario | int | **PK** |
| id_clase | int | **FK** → clases.id_clase (borrado: CASCADE) · NN |
| id_horario | int | **FK** → horarios.id_horario (borrado: NO ACTION) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |

### horarios

| Columna | Tipo | Restricciones |
|---|---|---|
| id_horario | int | **PK** |
| dia_semana | character varying | NN |
| hora_inicio | time | NN |
| hora_fin | time | NN |
| tipo | character varying | NN |
| estado | character varying | NN |

### disciplinas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_disciplina | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| estado | character varying | NN |

### reservasclase

| Columna | Tipo | Restricciones |
|---|---|---|
| id_reserva | int | **PK** |
| id_clase | int | **FK** → clases.id_clase (borrado: NO ACTION) · NN |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha_reserva | timestamptz | NN · por defecto `now()` |
| estado | character varying | NN · por defecto `'confirmada'::character varying` |
| semana | character varying | NN |

Reglas adicionales: `CHECK (((semana)::text ~ '^[0-9]{4}-W[0-9]{1,2}$'::text))`; `CHECK (((estado)::text = ANY ((ARRAY['confirmada'::character varying, 'cancelada'::character varying])::text[])))`; índice: `public.reservasclase USING btree (id_socio, id_clase, semana) WHERE ((estado)::text = 'con`; índice: `public.reservasclase USING btree (id_clase, semana) WHERE ((estado)::text = 'confirmada'::`

### instalaciones

| Columna | Tipo | Restricciones |
|---|---|---|
| id_instalacion | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| ubicacion | character varying |  |
| capacidad | int |  |
| estado | character varying | NN |

### ubicaciongimnasio

| Columna | Tipo | Restricciones |
|---|---|---|
| id_ubicacion | int | **PK** |
| nombre | character varying | NN |
| direccion | character varying | NN |
| ciudad | character varying | NN |
| provincia | character varying | NN |
| codigo_postal | character varying |  |
| telefono | character varying |  |
| email | character varying |  |
| horarios | character varying |  |

### turnos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_turno | int | **PK** |
| fecha | timestamptz | NN |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| tipo | character varying | NN |
| estado | character varying | NN |

### visitas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_visita | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha_solicitud | timestamptz | NN |
| fecha_visita | timestamptz |  |
| motivo | character varying |  |
| estado | character varying | NN |

### maquinas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_maquina | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| ubicacion | character varying |  |
| tipo | character varying |  |
| estado | character varying | NN |

### usomaquinas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_uso | int | **PK** |
| id_maquina | int | **FK** → maquinas.id_maquina (borrado: NO ACTION) · NN |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha_inicio | timestamptz | NN |
| fecha_fin | timestamptz |  |
| estado | character varying | NN |

## Entrenamiento

### rutinas

| Columna | Tipo | Restricciones |
|---|---|---|
| cod_rutina | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| nombre | character varying | NN |
| descripcion | character varying |  |
| fecha_creacion | timestamptz | NN · por defecto `now()` |
| fecha_actualizacion | timestamptz | por defecto `now()` |
| estado | character varying | NN · por defecto `'vigente'::character varying` |
| origen | character varying | NN · por defecto `'entrenador'::character varying` |
| activa | bool | NN · por defecto `false` |
| creada_por | character varying |  |

Reglas adicionales: `CHECK (((origen)::text = ANY ((ARRAY['entrenador'::character varying, 'socio'::character varying])::text[])))`; `CHECK ((((origen)::text = 'socio'::text) OR (id_empleado IS NOT NULL)))`; índice: `public.rutinas USING btree (id_socio) WHERE activa`; índice: `public.rutinas USING btree (id_socio) WHERE ((origen)::text = 'entrenador'::text)`

### rutinaejercicio

| Columna | Tipo | Restricciones |
|---|---|---|
| id_rutina_ejercicio | int | **PK** |
| cod_rutina | int | **FK** → rutinas.cod_rutina (borrado: CASCADE) · NN |
| id_ejercicio | int | **FK** → ejercicios.id_ejercicio (borrado: SET NULL) |
| orden | int | NN |
| series | int |  |
| repeticiones | int |  |
| peso | numeric |  |
| descanso | int |  |
| observaciones | character varying |  |
| nombre | character varying | NN |
| es_peso_corporal | bool | NN · por defecto `false` |

Reglas adicionales: `CHECK (((series IS NULL) OR (series > 0)))`; índice: `public.rutinaejercicio USING btree (cod_rutina, orden)`

### ejercicios

| Columna | Tipo | Restricciones |
|---|---|---|
| id_ejercicio | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| tecnica | text |  |
| musculos_trabajados | character varying |  |
| series | int |  |
| repeticiones | character varying |  |
| tiempo_descanso | int |  |
| dificultad | character varying |  |
| alternativas | character varying |  |
| estado | character varying | NN · por defecto `'borrador'::character varying` |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |
| consejo | text |  |
| tipo | character varying |  |
| aparato | character varying |  |

Reglas adicionales: `CHECK (((estado)::text = ANY ((ARRAY['publicado'::character varying, 'borrador'::character varying, 'competencia'::character varying])::text[])))`

### ejerciciopuntos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_ejercicio | int | **PK** (compuesta) · **FK** → ejercicios.id_ejercicio (borrado: CASCADE) |
| punto_id | character varying | **PK** (compuesta) |
| zona | character varying | **FK** → zonasmusculares.zona (borrado: NO ACTION) · NN |
| nombre | character varying | NN |
| descripcion | character varying | NN · por defecto `''::character varying` |
| orden | smallint | NN · por defecto `0` |

### ejercicioetiquetas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_ejercicio | int | **PK** (compuesta) · **FK** → ejercicios.id_ejercicio (borrado: CASCADE) |
| etiqueta | character varying | **PK** (compuesta) |
| orden | smallint | NN · por defecto `0` |

### puntoetiquetas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_ejercicio | int | **PK** (compuesta) · **FK** → ejerciciopuntos.id_ejercicio (borrado: CASCADE) |
| punto_id | character varying | **PK** (compuesta) · **FK** → ejerciciopuntos.punto_id (borrado: CASCADE) |
| etiqueta | character varying | **PK** (compuesta) |
| orden | smallint | NN · por defecto `0` |

### zonasmusculares

| Columna | Tipo | Restricciones |
|---|---|---|
| zona | character varying | **PK** |
| etiqueta | character varying | NN |
| emoji | character varying | NN |

### sesionesentrenamiento

| Columna | Tipo | Restricciones |
|---|---|---|
| id_sesion_entrenamiento | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| fecha | timestamptz | NN |
| hora_inicio | time | NN |
| hora_fin | time |  |
| estado | character varying | NN |

### solicitudesrutina

| Columna | Tipo | Restricciones |
|---|---|---|
| id_solicitud | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| fecha_solicitud | timestamptz | NN |
| descripcion | character varying |  |
| estado | character varying | NN |
| respuesta | character varying |  |

### historialentrenamientos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_historial | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_ejercicio | int | **FK** → ejercicios.id_ejercicio (borrado: NO ACTION) · NN |
| fecha | timestamptz | NN |
| peso | numeric |  |
| series | int |  |
| repeticiones | int |  |
| observaciones | character varying |  |

### progresofuerza

| Columna | Tipo | Restricciones |
|---|---|---|
| id_progreso | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_ejercicio | int | **FK** → ejercicios.id_ejercicio (borrado: NO ACTION) · NN |
| fecha | timestamptz | NN |
| peso_maximo | numeric |  |
| repeticiones | int |  |

### progresopeso

| Columna | Tipo | Restricciones |
|---|---|---|
| id_progreso_peso | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | date | NN |
| peso | numeric | NN |

### seriesentrenamiento

| Columna | Tipo | Restricciones |
|---|---|---|
| id_serie | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_rutina_ejercicio | int | **FK** → rutinaejercicio.id_rutina_ejercicio (borrado: SET NULL) |
| numero_serie | int | NN |
| peso | numeric |  |
| repeticiones | int | NN |
| fecha | timestamptz | NN · por defecto `now()` |
| ejercicio | character varying | NN |
| es_peso_corporal | bool | NN · por defecto `false` |

Reglas adicionales: `CHECK (((repeticiones > 0) AND ((peso IS NULL) OR (peso >= (0)::numeric))))`; índice: `public.seriesentrenamiento USING btree (id_socio, fecha DESC)`

## Arena (rangos y marcas)

### gruposmusculares

| Columna | Tipo | Restricciones |
|---|---|---|
| id_grupo_muscular | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |

### rangos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_rango | int | **PK** |
| nombre | character varying | NN |
| orden | int | NN |
| descripcion | character varying |  |

### ejerciciosmarca

| Columna | Tipo | Restricciones |
|---|---|---|
| id_ejercicio_marca | int | **PK** |
| id_ejercicio | int | **FK** → ejercicios.id_ejercicio (borrado: CASCADE) · **UK** · NN |
| id_grupo_muscular | int | **FK** → gruposmusculares.id_grupo_muscular (borrado: NO ACTION) · NN |
| estado | character varying | NN · por defecto `'activo'::character varying` |
| beginner_m | numeric | NN |
| dios_m | numeric | NN |
| beginner_f | numeric | NN |
| dios_f | numeric | NN |
| es_peso_corporal | bool | NN · por defecto `false` |

Reglas adicionales: índice: `public.ejerciciosmarca USING btree (id_ejercicio)`

### marcaspersonales

| Columna | Tipo | Restricciones |
|---|---|---|
| id_marca | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_ejercicio_marca | int | **FK** → ejerciciosmarca.id_ejercicio_marca (borrado: NO ACTION) · NN |
| peso | numeric | NN |
| repeticiones | int | NN |
| uno_rm_estimado | numeric |  |
| peso_corporal | numeric |  |
| fecha | timestamptz | NN · por defecto `now()` |
| estado | character varying | NN · por defecto `'pendiente'::character varying` |
| id_empleado_verificador | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| fecha_verificacion | timestamptz |  |
| verificado_por | character varying |  |

Reglas adicionales: `CHECK (((estado)::text = ANY ((ARRAY['pendiente'::character varying, 'verificada'::character varying, 'rechazada'::character varying])::text[])))`; `CHECK (((peso >= (0)::numeric) AND (repeticiones > 0)))`; índice: `public.marcaspersonales USING btree (id_socio, fecha DESC)`

### rangossocio

| Columna | Tipo | Restricciones |
|---|---|---|
| id_rango_socio | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_grupo_muscular | int | **FK** → gruposmusculares.id_grupo_muscular (borrado: NO ACTION) · NN |
| id_rango | int | **FK** → rangos.id_rango (borrado: NO ACTION) · NN |
| fecha_actualizacion | timestamptz | NN |

### logros

| Columna | Tipo | Restricciones |
|---|---|---|
| id_logro | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| categoria | character varying |  |
| secreto | bool | NN |
| estado | character varying | NN |

### logrossocio

| Columna | Tipo | Restricciones |
|---|---|---|
| id_logro_socio | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_logro | int | **FK** → logros.id_logro (borrado: NO ACTION) · NN |
| fecha_obtencion | timestamptz | NN |

### nivelesescalera

| Columna | Tipo | Restricciones |
|---|---|---|
| id_nivel | int | **PK** |
| numero | int | NN |
| nombre | character varying | NN |
| puntos_requeridos | int | NN |

### progresoarena

| Columna | Tipo | Restricciones |
|---|---|---|
| id_progreso_arena | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · **UK** · NN |
| id_nivel | int | **FK** → nivelesescalera.id_nivel (borrado: NO ACTION) · NN |
| puntos_totales | int | NN |
| fecha_actualizacion | timestamptz | NN |

Reglas adicionales: índice: `public.progresoarena USING btree (id_socio)`

### companeros

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → socios.id_socio (borrado: CASCADE) |
| id_companero | int | **PK** (compuesta) · **FK** → socios.id_socio (borrado: CASCADE) |
| fecha_agregado | timestamptz | NN · por defecto `now()` |

Reglas adicionales: `CHECK ((id_socio <> id_companero))`

## Nutrición

### dietas

| Columna | Tipo | Restricciones |
|---|---|---|
| cod_dieta | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| nombre | character varying | NN |
| objetivo | character varying |  |
| fecha_creacion | timestamptz | NN · por defecto `now()` |
| fecha_actualizacion | timestamptz | por defecto `now()` |
| estado | character varying | NN · por defecto `'vigente'::character varying` |

Reglas adicionales: índice: `public.dietas USING btree (id_socio) WHERE ((estado)::text = 'vigente'::text)`

### planalimentario

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plan_alimentario | int | **PK** |
| cod_dieta | int | **FK** → dietas.cod_dieta (borrado: CASCADE) · NN |
| nombre | character varying | NN |
| descripcion | character varying |  |
| fecha_inicio | date | NN |
| fecha_fin | date |  |
| estado | character varying | NN |

### planalimento

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plan_alimento | int | **PK** |
| id_plan_alimentario | int | **FK** → planalimentario.id_plan_alimentario (borrado: CASCADE) · NN |
| id_alimento | int | **FK** → alimentos.id_alimento (borrado: NO ACTION) · NN |
| cantidad | numeric | NN |
| unidad | character varying | NN |
| momento | character varying |  |

### planplato

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plan_plato | int | **PK** |
| id_plan_alimentario | int | **FK** → planalimentario.id_plan_alimentario (borrado: CASCADE) · NN |
| id_plato | int | **FK** → platos.id_plato (borrado: NO ACTION) · NN |
| momento | character varying |  |
| orden | smallint | NN · por defecto `0` |

Reglas adicionales: `CHECK (((momento)::text = ANY ((ARRAY['desayuno'::character varying, 'almuerzo'::character varying, 'cena'::character varying])::text[])))`; índice: `public.planplato USING btree (id_plan_alimentario, momento, id_plato)`

### alimentos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_alimento | int | **PK** |
| nombre | character varying | NN |
| categoria | character varying |  |
| calorias | numeric |  |
| proteinas | numeric |  |
| carbohidratos | numeric |  |
| grasas | numeric |  |

### platos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plato | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| imagen | text |  |
| imagen_generada_ia | bool | NN · por defecto `false` |
| estado | character varying | NN · por defecto `'borrador'::character varying` |
| kcal | int |  |
| proteinas | int |  |
| carbs | int |  |
| grasas | int |  |
| crop_x | real |  |
| crop_y | real |  |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |

Reglas adicionales: `CHECK ((proteinas >= 0))`; `CHECK ((carbs >= 0))`; `CHECK ((kcal >= 0))`; `CHECK (((estado)::text = ANY ((ARRAY['publicado'::character varying, 'borrador'::character varying])::text[])))`; `CHECK ((grasas >= 0))`

### platoingredientes

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plato | int | **PK** (compuesta) · **FK** → platos.id_plato (borrado: CASCADE) |
| ingrediente_id | character varying | **PK** (compuesta) |
| nombre | character varying | NN |
| categoria | character varying | NN |
| aporte | character varying | NN · por defecto `''::character varying` |
| kcal_texto | character varying | NN · por defecto `''::character varying` |
| x | real |  |
| y | real |  |
| orden | smallint | NN · por defecto `0` |

Reglas adicionales: `CHECK (((categoria)::text = ANY ((ARRAY['Proteína'::character varying, 'Verdura'::character varying, 'Fruta'::character varying, 'Carbohidrato'::character varying, 'Grasa saludable'::character varying, 'Cereal integral'::character varying])::text[])))`

### platoetiquetas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plato | int | **PK** (compuesta) · **FK** → platos.id_plato (borrado: CASCADE) |
| etiqueta | character varying | **PK** (compuesta) |
| orden | smallint | NN · por defecto `0` |

### ingredienteetiquetas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plato | int | **PK** (compuesta) · **FK** → platoingredientes.id_plato (borrado: CASCADE) |
| ingrediente_id | character varying | **PK** (compuesta) · **FK** → platoingredientes.ingrediente_id (borrado: CASCADE) |
| etiqueta | character varying | **PK** (compuesta) |
| orden | smallint | NN · por defecto `0` |

### ingredientebeneficios

| Columna | Tipo | Restricciones |
|---|---|---|
| id_plato | int | **PK** (compuesta) · **FK** → platoingredientes.id_plato (borrado: CASCADE) |
| ingrediente_id | character varying | **PK** (compuesta) · **FK** → platoingredientes.ingrediente_id (borrado: CASCADE) |
| beneficio | character varying | **PK** (compuesta) |
| orden | smallint | NN · por defecto `0` |

### platosprobados

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → socios.id_socio (borrado: CASCADE) |
| id_plato | int | **PK** (compuesta) · **FK** → platos.id_plato (borrado: CASCADE) |
| fecha_probado | timestamptz | NN · por defecto `now()` |

### comidasdia

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → socios.id_socio (borrado: CASCADE) |
| fecha | date | **PK** (compuesta) |
| objetivo | character varying |  |
| meta_kcal | int |  |
| meta_proteinas | int |  |
| meta_carbs | int |  |
| meta_grasas | int |  |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |

Reglas adicionales: `CHECK ((meta_kcal >= 0))`; `CHECK (((objetivo)::text = ANY ((ARRAY['FUERZA'::character varying, 'HIPERTROFIA'::character varying, 'SALUD'::character varying])::text[])))`; `CHECK ((meta_grasas >= 0))`; `CHECK ((meta_carbs >= 0))`; `CHECK ((meta_proteinas >= 0))`

### comidasregistradas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → comidasdia.id_socio (borrado: CASCADE) |
| fecha | date | **PK** (compuesta) · **FK** → comidasdia.fecha (borrado: CASCADE) |
| momento | character varying | **PK** (compuesta) |
| hora | timestamptz | NN |
| kcal | int | NN · por defecto `0` |
| proteinas | int | NN · por defecto `0` |
| carbs | int | NN · por defecto `0` |
| grasas | int | NN · por defecto `0` |
| nota | character varying | NN · por defecto `''::character varying` |

Reglas adicionales: `CHECK ((proteinas >= 0))`; `CHECK (((momento)::text = ANY ((ARRAY['desayuno'::character varying, 'almuerzo'::character varying, 'cena'::character varying])::text[])))`; `CHECK ((kcal >= 0))`; `CHECK ((grasas >= 0))`; `CHECK ((carbs >= 0))`

### comidaregistradaplatos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → comidasregistradas.id_socio (borrado: CASCADE) |
| fecha | date | **PK** (compuesta) · **FK** → comidasregistradas.fecha (borrado: CASCADE) |
| momento | character varying | **PK** (compuesta) · **FK** → comidasregistradas.momento (borrado: CASCADE) |
| id_plato | int | **PK** (compuesta) · **FK** → platos.id_plato (borrado: RESTRICT) |

### fotoscomidas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → socios.id_socio (borrado: CASCADE) |
| fecha | date | **PK** (compuesta) |
| momento | character varying | **PK** (compuesta) |
| imagen | text | NN |
| fecha_foto | timestamptz | NN · por defecto `now()` |

Reglas adicionales: `CHECK (((momento)::text = ANY ((ARRAY['desayuno'::character varying, 'almuerzo'::character varying, 'cena'::character varying])::text[])))`

### historialalimentario

| Columna | Tipo | Restricciones |
|---|---|---|
| id_historial_alimentario | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_alimento | int | **FK** → alimentos.id_alimento (borrado: NO ACTION) · NN |
| fecha | timestamptz | NN |
| cantidad | numeric |  |
| observaciones | character varying |  |

### preferenciasalimentarias

| Columna | Tipo | Restricciones |
|---|---|---|
| id_preferencia | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| tipo | character varying | NN |
| descripcion | character varying |  |

Reglas adicionales: índice: `public.preferenciasalimentarias USING btree (id_socio, tipo)`

### restriccionesalimentarias

| Columna | Tipo | Restricciones |
|---|---|---|
| id_restriccion | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| tipo | character varying | NN |
| descripcion | character varying |  |

### alimentosexcluidos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_exclusion | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| alimento | character varying | NN |
| motivo | character varying |  |

Reglas adicionales: índice: `public.alimentosexcluidos USING btree (id_socio, alimento)`

### evaluacionesnutricionales

| Columna | Tipo | Restricciones |
|---|---|---|
| id_evaluacion | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| fecha | timestamptz | NN |
| peso | numeric |  |
| altura | numeric |  |
| imc | numeric |  |
| observaciones | character varying |  |
| recomendaciones | character varying |  |

### recomendacionesnutricionales

| Columna | Tipo | Restricciones |
|---|---|---|
| id_recomendacion | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| fecha | timestamptz | NN |
| recomendacion | character varying | NN |

### solicitudesnutricionales

| Columna | Tipo | Restricciones |
|---|---|---|
| id_solicitud_nutricional | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| fecha | timestamptz | NN |
| tipo | character varying | NN |
| descripcion | character varying |  |
| estado | character varying | NN |
| respuesta | character varying |  |

### registroagua

| Columna | Tipo | Restricciones |
|---|---|---|
| id_registro_agua | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | timestamptz | NN · por defecto `now()` |
| cantidad_ml | int | NN · por defecto `250` |

Reglas adicionales: `CHECK ((cantidad_ml > 0))`; índice: `public.registroagua USING btree (id_socio, fecha DESC)`

## Salud y progreso

### salud

| Columna | Tipo | Restricciones |
|---|---|---|
| id_salud | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | timestamptz | NN |
| peso | numeric |  |
| altura | numeric |  |
| imc | numeric |  |
| porcentaje_grasa | numeric |  |
| observaciones | character varying |  |

### cuestionarios

| Columna | Tipo | Restricciones |
|---|---|---|
| id_cuestionario | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | timestamptz | NN |
| tipo | character varying | NN |
| estado | character varying | NN |

### objetivos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_objetivo | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| tipo | character varying | NN |
| descripcion | character varying |  |
| prioridad | character varying |  |
| fecha_registro | timestamptz | NN · por defecto `now()` |
| estado | character varying | NN · por defecto `'activo'::character varying` |

Reglas adicionales: `CHECK (((tipo)::text = ANY ((ARRAY['FUERZA'::character varying, 'HIPERTROFIA'::character varying, 'SALUD'::character varying])::text[])))`; índice: `public.objetivos USING btree (id_socio) WHERE ((estado)::text = 'activo'::text)`

### fotosprogreso

| Columna | Tipo | Restricciones |
|---|---|---|
| id_foto | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | timestamptz | NN · por defecto `now()` |
| imagen | text | NN |
| observaciones | character varying |  |

Reglas adicionales: índice: `public.fotosprogreso USING btree (id_socio, fecha DESC)`

## Lockers, accesos y aforo

### lockers

| Columna | Tipo | Restricciones |
|---|---|---|
| id_locker | int | **PK** |
| numero | character varying | **UK** · NN |
| ubicacion | character varying |  |
| tipo | character varying |  |
| estado | character varying | NN · por defecto `'disponible'::character varying` |

Reglas adicionales: índice: `public.lockers USING btree (numero)`

### reservaslocker

| Columna | Tipo | Restricciones |
|---|---|---|
| id_reserva_locker | int | **PK** |
| id_locker | int | **FK** → lockers.id_locker (borrado: NO ACTION) · NN |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha_inicio | timestamptz | NN · por defecto `now()` |
| fecha_fin | timestamptz |  |
| estado | character varying | NN · por defecto `'activa'::character varying` |

Reglas adicionales: índice: `public.reservaslocker USING btree (id_locker) WHERE ((estado)::text = 'activa'::text)`; índice: `public.reservaslocker USING btree (id_socio) WHERE ((estado)::text = 'activa'::text)`

### aperturaslocker

| Columna | Tipo | Restricciones |
|---|---|---|
| id_apertura | int | **PK** |
| id_locker | int | **FK** → lockers.id_locker (borrado: NO ACTION) · NN |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | timestamptz | NN |
| metodo_acceso | character varying | NN |
| resultado | character varying | NN |

### accesos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_acceso | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | timestamptz | NN · por defecto `now()` |
| metodo | character varying | NN |
| resultado | character varying | NN · por defecto `'permitido'::character varying` |
| dispositivo | character varying |  |

Reglas adicionales: `CHECK (((metodo)::text = ANY ((ARRAY['qr'::character varying, 'biometrico'::character varying, 'manual'::character varying])::text[])))`; índice: `public.accesos USING btree (id_socio, fecha DESC)`

### codigosacceso

| Columna | Tipo | Restricciones |
|---|---|---|
| id_codigo | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| codigo | character varying | NN |
| fecha_generacion | timestamptz | NN |
| fecha_expiracion | timestamptz |  |
| estado | character varying | NN |

### codigosqr

| Columna | Tipo | Restricciones |
|---|---|---|
| id_qr | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| codigo | character varying | NN |
| fecha_generacion | timestamptz | NN |
| fecha_expiracion | timestamptz |  |
| estado | character varying | NN |

### datosbiometricos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_biometrico | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| tipo | character varying | NN |
| identificador | character varying | NN |
| fecha_registro | timestamptz | NN |
| estado | character varying | NN |

### relojesdeportivos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_reloj | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| marca | character varying |  |
| modelo | character varying |  |
| identificador | character varying | NN |
| fecha_vinculacion | timestamptz | NN |
| estado | character varying | NN |

### aforo

| Columna | Tipo | Restricciones |
|---|---|---|
| id_aforo | int | **PK** |
| fecha | timestamptz | NN · por defecto `now()` |
| cantidad_personas | int | NN |
| capacidad_maxima | int | NN |
| estado | character varying | NN · por defecto `'vigente'::character varying` |

Reglas adicionales: `CHECK (((cantidad_personas >= 0) AND (capacidad_maxima > 0)))`

### incidenciasacceso

| Columna | Tipo | Restricciones |
|---|---|---|
| id_incidencia | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| fecha | timestamptz | NN |
| descripcion | character varying | NN |
| tipo | character varying | NN |
| estado | character varying | NN |
| resolucion | character varying |  |

## Comunicación y web

### consultas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_consulta | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| tipo | character varying | NN |
| descripcion | character varying | NN |
| fecha | timestamptz | NN |
| estado | character varying | NN |
| respuesta | character varying |  |

### notificaciones

| Columna | Tipo | Restricciones |
|---|---|---|
| id_notificacion | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| tipo | character varying | NN |
| mensaje | character varying | NN |
| fecha | timestamptz | NN |
| estado | character varying | NN |
| clave | character varying |  |

Reglas adicionales: índice: `public.notificaciones USING btree (id_empleado, clave)`

### solicitudescontacto

| Columna | Tipo | Restricciones |
|---|---|---|
| id_solicitud | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| tipo | character varying | NN |
| mensaje | character varying |  |
| fecha | timestamptz | NN |
| estado | character varying | NN |

### tablonpublicaciones

| Columna | Tipo | Restricciones |
|---|---|---|
| id_publicacion | int | **PK** |
| titulo | character varying | NN |
| mensaje | text | NN |
| categoria | character varying | NN |
| autor | character varying | NN |
| fijado | bool | NN · por defecto `false` |
| publicado | bool | NN · por defecto `false` |
| fecha_creacion | timestamptz | NN · por defecto `now()` |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |

Reglas adicionales: `CHECK (((categoria)::text = ANY ((ARRAY['Aviso'::character varying, 'Evento'::character varying, 'Promoción'::character varying, 'Importante'::character varying])::text[])))`

### contactosweb

| Columna | Tipo | Restricciones |
|---|---|---|
| id_contacto | int | **PK** |
| nombre | character varying | NN |
| email | character varying |  |
| telefono | character varying |  |
| mensaje | text | NN |
| fecha | timestamptz | NN · por defecto `now()` |
| estado | character varying | NN · por defecto `'nuevo'::character varying` |

Reglas adicionales: `CHECK (((email IS NOT NULL) OR (telefono IS NOT NULL)))`; `CHECK (((char_length((nombre)::text) <= 100) AND (char_length(mensaje) < 1000)))`

## Argos (asistente de IA)

### argosbaseconocimiento

| Columna | Tipo | Restricciones |
|---|---|---|
| id_conocimiento | int | **PK** |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| titulo | character varying | NN |
| contenido | text | NN |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |
| estado | character varying | NN · por defecto `'activa'::character varying` |

Reglas adicionales: índice: `public.argosbaseconocimiento USING btree ((true)) WHERE ((estado)::text = 'activa'::text)`

### argosconversaciones

| Columna | Tipo | Restricciones |
|---|---|---|
| id_conversacion | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| origen | character varying | NN |
| fecha_inicio | timestamptz | NN |

### argosmensajes

| Columna | Tipo | Restricciones |
|---|---|---|
| id_mensaje | int | **PK** |
| id_conversacion | int | **FK** → argosconversaciones.id_conversacion (borrado: CASCADE) · NN |
| emisor | character varying | NN |
| contenido | text | NN |
| fecha | timestamptz | NN |

### argoscupodiario

| Columna | Tipo | Restricciones |
|---|---|---|
| id_cupo | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |
| fecha | date | NN |
| mensajes_enviados | int | NN |
| limite_diario | int | NN |

Reglas adicionales: `CHECK ((num_nonnulls(id_socio, id_empleado) = 1))`; índice: `public.argoscupodiario USING btree (id_empleado, fecha) WHERE (id_empleado IS NOT NULL)`; índice: `public.argoscupodiario USING btree (id_socio, fecha) WHERE (id_socio IS NOT NULL)`

### consumoimagenesia

| Columna | Tipo | Restricciones |
|---|---|---|
| fecha | date | **PK** |
| cantidad | int | NN · por defecto `0` |

Reglas adicionales: `CHECK ((cantidad >= 0))`

## Tienda

### productos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_producto | int | **PK** |
| nombre | character varying | NN |
| descripcion | character varying |  |
| precio | numeric | NN |
| stock | int | NN · por defecto `0` |
| imagen | text |  |
| publicado | bool | NN · por defecto `false` |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |

Reglas adicionales: `CHECK (((precio > (0)::numeric) AND (precio <= (10000000)::numeric)))`; `CHECK (((stock >= 0) AND (stock <= 100000)))`; índice: `public.productos USING btree (lower((nombre)::text))`

### productoetiquetas

| Columna | Tipo | Restricciones |
|---|---|---|
| id_producto | int | **PK** (compuesta) · **FK** → productos.id_producto (borrado: CASCADE) |
| etiqueta | character varying | **PK** (compuesta) |
| orden | smallint | NN · por defecto `0` |

### pedidostienda

| Columna | Tipo | Restricciones |
|---|---|---|
| id_pedido | int | **PK** |
| id_socio | int | **FK** → socios.id_socio (borrado: CASCADE) · NN |
| estado | character varying | NN · por defecto `'pendiente'::character varying` |
| total | numeric | NN |
| fecha | timestamptz | NN · por defecto `now()` |
| fecha_cierre | timestamptz |  |
| id_empleado_cierre | int | **FK** → empleados.id_empleado (borrado: NO ACTION) |

Reglas adicionales: `CHECK (((estado)::text = ANY ((ARRAY['pendiente'::character varying, 'entregado'::character varying, 'cancelado'::character varying])::text[])))`; `CHECK ((total > (0)::numeric))`; índice: `public.pedidostienda USING btree (id_socio, fecha DESC)`

### pedidotiendaitems

| Columna | Tipo | Restricciones |
|---|---|---|
| id_pedido | int | **PK** (compuesta) · **FK** → pedidostienda.id_pedido (borrado: CASCADE) |
| id_producto | int | **PK** (compuesta) · **FK** → productos.id_producto (borrado: RESTRICT) |
| nombre | character varying | NN |
| precio_unitario | numeric | NN |
| cantidad | smallint | NN |

Reglas adicionales: `CHECK (((cantidad >= 1) AND (cantidad <= 20)))`; `CHECK ((precio_unitario > (0)::numeric))`

## Otras

### comidasdiametamomentos

| Columna | Tipo | Restricciones |
|---|---|---|
| id_socio | int | **PK** (compuesta) · **FK** → comidasdia.id_socio (borrado: CASCADE) |
| fecha | date | **PK** (compuesta) · **FK** → comidasdia.fecha (borrado: CASCADE) |
| momento | character varying | **PK** (compuesta) |

Reglas adicionales: `CHECK (((momento)::text = ANY ((ARRAY['desayuno'::character varying, 'almuerzo'::character varying, 'cena'::character varying])::text[])))`

### configuracionsistema

| Columna | Tipo | Restricciones |
|---|---|---|
| clave | character varying | **PK** |
| valor | jsonb | NN |
| fecha_actualizacion | timestamptz | NN · por defecto `now()` |

### historialsueldo

| Columna | Tipo | Restricciones |
|---|---|---|
| id_historial | int | **PK** |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| sueldo_anterior | numeric |  |
| sueldo_nuevo | numeric | NN |
| fecha | timestamptz | NN · por defecto `now()` |
| registrado_por | character varying |  |

### liquidacionessueldo

| Columna | Tipo | Restricciones |
|---|---|---|
| id_liquidacion | int | **PK** |
| id_empleado | int | **FK** → empleados.id_empleado (borrado: NO ACTION) · NN |
| periodo | date | NN |
| concepto | character varying | NN · por defecto `'Sueldo'::character varying` |
| monto | numeric | NN |
| medio | character varying | NN |
| fecha_pago | timestamptz | NN · por defecto `now()` |
| nota | character varying |  |
| registrado_por | character varying |  |
| estado | character varying | NN · por defecto `'pagado'::character varying` |

Reglas adicionales: `CHECK (((estado)::text = ANY ((ARRAY['pagado'::character varying, 'anulado'::character varying])::text[])))`; `CHECK (((concepto)::text = ANY ((ARRAY['Sueldo'::character varying, 'Adelanto'::character varying, 'Bono'::character varying])::text[])))`; `CHECK ((monto > (0)::numeric))`; índice: `public.liquidacionessueldo USING btree (id_empleado, periodo) WHERE (((concepto)::text = '`
