package com.olimpos.gym.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.olimpos.gym.data.DatosRemotos
import com.olimpos.gym.data.EstadoLocker
import com.olimpos.gym.data.Locker
import com.olimpos.gym.data.LOCKERS_EJEMPLO
import com.olimpos.gym.data.liberarLockerEnFirebase
import com.olimpos.gym.data.reservarLockerEnFirebase
import com.olimpos.gym.data.socioActualId
import com.olimpos.gym.ui.theme.Olimpos
import kotlinx.coroutines.launch

@Composable
fun LockersScreen(onVolver: () -> Unit) {
    var aviso by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    // Los números/zonas de los lockers son el layout físico real del
    // vestidor (fijo); quién tiene reservado cada uno sale de Firestore —
    // antes ese "ocupado" era un estado inventado sin ningún socio detrás.
    val ocupantes = DatosRemotos.lockersOcupados ?: emptyMap()
    val miId = socioActualId()
    val lockers = LOCKERS_EJEMPLO.map { l ->
        val ocupante = ocupantes[l.numero]
        l.copy(
            estado = when {
                ocupante == miId -> EstadoLocker.RESERVADO_POR_MI
                ocupante != null -> EstadoLocker.OCUPADO
                else -> EstadoLocker.LIBRE
            }
        )
    }
    val miLocker = lockers.firstOrNull { it.estado == EstadoLocker.RESERVADO_POR_MI }

    Column(Modifier.fillMaxSize()) {
        EncabezadoVolver("Mis lockers", "Reservá y abrí tu locker", onVolver)

        Column(Modifier.padding(horizontal = 20.dp, vertical = 6.dp)) {
            if (miLocker != null) {
                TarjetaOro(Modifier.fillMaxWidth()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        IconoCuadrado("🔒")
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text("Locker Nº ${miLocker.numero}", fontWeight = FontWeight.ExtraBold, fontSize = 14.sp, color = Olimpos.Cream)
                            Text(miLocker.zona, fontSize = 11.5.sp, color = Olimpos.Muted)
                        }
                    }
                    Spacer(Modifier.height(10.dp))
                    BotonPrincipal("Abrir locker") { aviso = "Locker Nº ${miLocker.numero} abierto ✓" }
                    Spacer(Modifier.height(8.dp))
                    BotonSecundario("Liberar este locker") {
                        scope.launch {
                            liberarLockerEnFirebase()
                            DatosRemotos.recargarLockers()
                        }
                        aviso = "Locker Nº ${miLocker.numero} liberado"
                    }
                }
                aviso?.let {
                    Spacer(Modifier.height(10.dp))
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(14.dp))
                            .background(Olimpos.GoldSoft)
                            .border(1.dp, Olimpos.Gold.copy(alpha = 0.35f), RoundedCornerShape(14.dp))
                            .padding(13.dp)
                    ) {
                        Text(it, fontSize = 12.5.sp, fontWeight = FontWeight.Bold, color = Olimpos.GoldLight)
                    }
                }
            }
            SeccionLabel("Disponibilidad")
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                Leyenda(Olimpos.Green, "Libre")
                Leyenda(Olimpos.Muted, "Ocupado")
                Leyenda(Olimpos.Gold, "Tu locker")
            }
        }

        LazyVerticalGrid(
            columns = GridCells.Fixed(4),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(20.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            items(lockers, key = { it.numero }) { l ->
                CasillaLocker(l) {
                    if (l.estado == EstadoLocker.LIBRE) {
                        scope.launch {
                            reservarLockerEnFirebase(l.numero)
                            DatosRemotos.recargarLockers()
                        }
                        aviso = "Locker Nº ${l.numero} reservado ✓"
                    }
                }
            }
        }
    }
}

@Composable
private fun Leyenda(color: androidx.compose.ui.graphics.Color, texto: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        androidx.compose.foundation.layout.Box(
            Modifier.size(10.dp).clip(RoundedCornerShape(4.dp)).background(color)
        )
        Spacer(Modifier.width(6.dp))
        Text(texto, fontSize = 11.sp, color = Olimpos.Muted)
    }
}

@Composable
private fun CasillaLocker(locker: Locker, onClick: () -> Unit) {
    val color = when (locker.estado) {
        EstadoLocker.LIBRE -> Olimpos.Green
        EstadoLocker.OCUPADO -> Olimpos.Muted
        EstadoLocker.RESERVADO_POR_MI -> Olimpos.Gold
    }
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(Olimpos.Card)
            .border(1.5.dp, color, RoundedCornerShape(14.dp))
            .clickable(enabled = locker.estado != EstadoLocker.OCUPADO, onClick = onClick)
            .padding(vertical = 14.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("🔒", fontSize = 18.sp)
        Text("${locker.numero}", fontWeight = FontWeight.Black, fontSize = 13.sp, color = Olimpos.Cream)
    }
}
