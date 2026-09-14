package com.olimpos.gym.data

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch

/**
 * Caché en memoria (dura lo que dura el proceso de la app) de todo lo que
 * antes cada pantalla pedía por su cuenta a Firebase: marcas, platos,
 * ejercicios y el ranking de socios. Antes, Bodygraph/Dieta/Galería
 * arrancaban mostrando su catálogo de ejemplo local y un instante después
 * lo reemplazaban por lo real — el "salto" que se veía al entrar. Acá se
 * dispara una sola vez (ver [precargar], llamado desde MainActivity apenas
 * se entra a la app) para que, cuando el socio realmente abre esas
 * pantallas, los datos ya estén listos y no haya cambio visible.
 *
 * `null` = todavía no llegó nada de Firebase (usar el catálogo de ejemplo
 * como respaldo); lista vacía o con datos = ya se sabe la respuesta real.
 */
object DatosRemotos {
    var marcas by mutableStateOf<List<MarcaPersonal>?>(null); private set
    var platos by mutableStateOf<List<Plato>?>(null); private set
    var ejercicios by mutableStateOf<List<EjercicioCatalogo>?>(null); private set
    var rangosSocios by mutableStateOf<List<SocioRango>?>(null); private set
    var datosFisicosPropios by mutableStateOf<DatosFisicos?>(null); private set
    var seriesEntrenamiento by mutableStateOf<List<SerieEntrenamiento>?>(null); private set
    /** `null` = todavía no se sabe (recién arrancando) O ya se sabe que no
     *  hay ninguna asignada — misma ambigüedad que [datosFisicosPropios],
     *  aceptable porque [precargar] ya corrió antes de que el socio llegue
     *  a abrir Entrenar (ver MainActivity). */
    var rutinaAsignada by mutableStateOf<RutinaDelDia?>(null); private set
    var ingresos by mutableStateOf<List<IngresoRegistro>?>(null); private set
    var reservasClase by mutableStateOf<List<ReservaClase>?>(null); private set
    /** uid del ocupante -> número de locker, de TODOS los socios (hace
     *  falta para saber qué lockers están libres/ocupados por otro). */
    var lockersOcupados by mutableStateOf<Map<Int, String>?>(null); private set
    var perfilNutricional by mutableStateOf<PerfilNutricional?>(null); private set
    /** `null` = todavía no le asignaron ninguna membresía. */
    var membresia by mutableStateOf<MembresiaAsignada?>(null); private set
    var platosProbados by mutableStateOf<Set<String>?>(null); private set
    var registrosAgua by mutableStateOf<List<Long>?>(null); private set
    var fotosProgreso by mutableStateOf<List<FotoProgreso>?>(null); private set
    /** Se pone en `true` recién cuando TODAS las cargas de [precargar]
     *  terminaron — lo usa ObservadorDeLogros para saber cuándo es seguro
     *  tomar la "foto" inicial de qué logros ya estaban desbloqueados, sin
     *  confundir datos que todavía están llegando con logros recién
     *  conseguidos (ver LogroToast.kt). */
    var listo by mutableStateOf(false); private set

    private var yaPrecargado = false

    suspend fun precargar() {
        if (yaPrecargado) return
        yaPrecargado = true
        coroutineScope {
            launch { marcas = cargarMarcasDesdeFirebase() }
            launch { platos = cargarPlatosDesdeFirebase() }
            launch { ejercicios = cargarEjerciciosDesdeFirebase() }
            launch { datosFisicosPropios = cargarDatosFisicosPropios() }
            launch { rangosSocios = cargarRangosDeSocios() }
            launch { seriesEntrenamiento = cargarSeriesDesdeFirebase() }
            launch { rutinaAsignada = cargarRutinaAsignada() }
            launch { ingresos = cargarIngresosDesdeFirebase() }
            launch { reservasClase = cargarReservasClaseDesdeFirebase() }
            launch { lockersOcupados = cargarLockersDesdeFirebase() }
            launch { perfilNutricional = cargarPerfilNutricionalDesdeFirebase() }
            launch { membresia = cargarMembresiaDesdeFirebase() }
            launch { platosProbados = cargarPlatosProbadosDesdeFirebase() }
            launch { registrosAgua = cargarRegistrosAguaDesdeFirebase() }
            launch { fotosProgreso = cargarFotosProgresoDesdeFirebase() }
        }
        listo = true
    }

    /** Se llama al subir o borrar una foto de progreso. */
    suspend fun recargarFotosProgreso() {
        fotosProgreso = cargarFotosProgresoDesdeFirebase()
    }

    /** Botón manual en Membresía, por si un empleado la asignó/cambió
     *  mientras el socio ya tenía la app abierta. */
    suspend fun recargarMembresia() {
        membresia = cargarMembresiaDesdeFirebase()
    }

    /** Se llama al marcar un plato como probado, en Dieta. */
    suspend fun recargarPlatosProbados() {
        platosProbados = cargarPlatosProbadosDesdeFirebase()
    }

    /** Se llama al registrar el consumo de agua de hoy, en Nutrición. */
    suspend fun recargarRegistrosAgua() {
        registrosAgua = cargarRegistrosAguaDesdeFirebase()
    }

    /** Se llama al tocar "Marcar mi ingreso de hoy" en Accesos. */
    suspend fun recargarIngresos() {
        ingresos = cargarIngresosDesdeFirebase()
    }

    /** Se llama al tocar "Reservar" en una clase de Inicio. */
    suspend fun recargarReservasClase() {
        reservasClase = cargarReservasClaseDesdeFirebase()
    }

    /** Se llama al reservar/liberar un locker en Mis lockers. */
    suspend fun recargarLockers() {
        lockersOcupados = cargarLockersDesdeFirebase()
    }

    /** Se llama al guardar las preferencias nutricionales. */
    suspend fun recargarPerfilNutricional() {
        perfilNutricional = cargarPerfilNutricionalDesdeFirebase()
    }

    /** Se llama después de registrar una serie nueva en Entrenar, para que
     *  "kg movidos este mes" y el Ghost Mode no se queden con la foto vieja. */
    suspend fun recargarSeriesEntrenamiento() {
        seriesEntrenamiento = cargarSeriesDesdeFirebase()
    }

    /** Botón manual en Entrenar, por si el entrenador asignó o cambió la
     *  rutina mientras el socio ya tenía la app abierta. */
    suspend fun recargarRutinaAsignada() {
        rutinaAsignada = cargarRutinaAsignada()
    }

    /** Se llama después de cargar una marca nueva (ver [MarcasScreen]), para
     *  que Bodygraph y Clasificación no se queden con la foto vieja hasta
     *  el próximo reinicio de la app. */
    suspend fun recargarMarcas() {
        marcas = cargarMarcasDesdeFirebase()
    }

    suspend fun recargarRangosSocios() {
        rangosSocios = cargarRangosDeSocios()
    }

    /** Se llama apenas termina el onboarding (ver MainActivity), para que
     *  el peso recién cargado ya esté disponible sin reiniciar la app. */
    suspend fun recargarDatosFisicosPropios() {
        datosFisicosPropios = cargarDatosFisicosPropios()
    }
}
