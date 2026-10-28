package com.olimpos.gym.ui.theme

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ListAlt
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.automirrored.outlined.ShowChart
import androidx.compose.material.icons.outlined.AccessibilityNew
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Calculate
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.CreditCard
import androidx.compose.material.icons.outlined.EmojiEvents
import androidx.compose.material.icons.outlined.FitnessCenter
import androidx.compose.material.icons.outlined.Group
import androidx.compose.material.icons.outlined.Groups
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Leaderboard
import androidx.compose.material.icons.outlined.LocalFireDepartment
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.MilitaryTech
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Restaurant
import androidx.compose.material.icons.outlined.RestaurantMenu
import androidx.compose.material.icons.outlined.ShoppingBag
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material.icons.outlined.Security
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material.icons.outlined.SupervisorAccount
import androidx.compose.ui.graphics.vector.ImageVector

/** Íconos de línea en vez de emojis, como el menú del sistema de empleados.
 *  Las pantallas siguen pasando el emoji de siempre (así no hubo que tocar
 *  cada llamada); acá se traduce al ícono equivalente. Si un emoji no está
 *  en la tabla, se dibuja el emoji tal cual. */
val ICONO_DE_EMOJI: Map<String, ImageVector> = mapOf(
    "🏛️" to Icons.Outlined.Home,
    "🏋️" to Icons.Outlined.FitnessCenter,
    "⚔️" to Icons.Outlined.EmojiEvents,
    "🥗" to Icons.Outlined.Restaurant,
    "🛍️" to Icons.Outlined.ShoppingBag,
    "👤" to Icons.Outlined.Person,
    "🗺️" to Icons.Outlined.Map,
    "💳" to Icons.Outlined.CreditCard,
    "🔐" to Icons.Outlined.Security,
    "🔒" to Icons.Outlined.Lock,
    "📈" to Icons.AutoMirrored.Outlined.ShowChart,
    "🤝" to Icons.Outlined.Group,
    "👥" to Icons.Outlined.Groups,
    "📅" to Icons.Outlined.CalendarMonth,
    "⚙️" to Icons.Outlined.Settings,
    "ℹ️" to Icons.Outlined.Info,
    "🚪" to Icons.AutoMirrored.Outlined.Logout,
    "🐕" to Icons.Outlined.AutoAwesome,
    "💪" to Icons.Outlined.AccessibilityNew,
    "🧮" to Icons.Outlined.Calculate,
    "🎖️" to Icons.Outlined.MilitaryTech,
    "📋" to Icons.AutoMirrored.Outlined.ListAlt,
    "📊" to Icons.Outlined.Leaderboard,
    "🧑‍🏫" to Icons.Outlined.SupervisorAccount,
    "🔥" to Icons.Outlined.LocalFireDepartment,
    "🍽️" to Icons.Outlined.RestaurantMenu,
    "🕐" to Icons.Outlined.Schedule
)
