# OLIMPOS GYM — Configuración
#
# Cada empleado ajusta SU sistema (se guarda en Neon con su id, así lo sigue
# a cualquier computadora):
#   Apariencia         color de acento, fondo, menú lateral compacto
#   Inicio y sesión    sección al entrar, recordar usuario, confirmar salida
#   Notificaciones     contador en el menú, qué avisos ver, anticipación
# Y el dueño, además, los datos del club (nombre, capacidad, cuándo avisar
# que está lleno, cuántos días un socio cuenta como nuevo).
# Todo se guarda al tocarlo; lo visual rearma la pantalla en el momento.

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
import empleados_credenciales
import configuracion_repo as cfg
import notificaciones_repo

DESCRIPCION_AVISO = {
    "membresia_vencida": "Socios con la membresía vencida que todavía no renovaron.",
    "membresia_por_vencer": "Membresías que vencen dentro de los días que elijas abajo.",
    "sin_membresia": "Socios activos que no tienen ningún plan asignado.",
    "socio_nuevo": "Cada socio que se registra en la app.",
    "pago_recibido": "Pagos de cuotas de los últimos 7 días.",
    "contacto_web": "Mensajes nuevos del formulario de la página web.",
    "marca_pendiente": "Marcas personales que los socios cargaron y esperan verificación.",
    "sin_rutina": "Socios activos sin una rutina vigente.",
    "sin_dieta": "Socios activos sin una dieta vigente.",
    "peso_registrado": "Cuando un socio registra su peso (con la diferencia con el anterior).",
    "ocupacion_alta": "Cuando el club llega al porcentaje de ocupación configurado.",
    "acceso_denegado": "Entradas al club que fueron rechazadas en los últimos 2 días.",
    "intentos_fallidos": "Intentos de entrar al sistema con usuario o contraseña incorrectos.",
    "mi_cuenta": "Si alguien escribió mal TU contraseña en los últimos 7 días.",
}


class ConfiguracionView:
    def __init__(self, page: ft.Page, rol: str, shell=None):
        self.page = page
        self.rol = rol
        self.shell = shell
        self.actual = empleados_credenciales.actual() or {}
        self.id_empleado = self.actual.get("id_empleado")
        self.es_dueno = rol == "dueno"
        self.grupos = [
            ("apariencia", ft.Icons.PALETTE_OUTLINED, "Apariencia", "Colores, fondo y menú"),
            ("inicio", ft.Icons.LOGIN, "Inicio y sesión", "Cómo entra y sale tu usuario"),
            ("avisos", ft.Icons.NOTIFICATIONS_NONE, "Notificaciones", "Qué avisos ver y cómo"),
        ] + ([("club", ft.Icons.STOREFRONT_OUTLINED, "Club", "Datos del gimnasio")] if self.es_dueno else [])
        # al rearmar la pantalla (cambio de colores) vuelve al mismo grupo
        guardado = getattr(cfg, "_grupo_configuracion", "apariencia")
        self.grupo = guardado if guardado in [g[0] for g in self.grupos] else "apariencia"
        self.mensaje = ft.Text("", size=12.5, weight=ft.FontWeight.W_500, color=GREEN)
        self.root = ft.Column(spacing=0, expand=True)
        self._montado = False

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls = [self._pantalla()]
        if self._montado:
            self.root.update()

    def _ok(self, texto: str = "✓ Guardado", color: str = GREEN):
        self.mensaje.value, self.mensaje.color = texto, color
        try:
            if self.mensaje.page:
                self.mensaje.update()
        except RuntimeError:
            pass

    # ── pantalla ──
    def _pantalla(self) -> ft.Column:
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Sistema", size=13, color=TEXT_MUTED),
                ft.Text("Configuración", size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.15)),
                ft.Text("Ajustá el sistema a tu gusto. Cada cambio se guarda solo y es solo para tu usuario"
                        + (", salvo los datos del club." if self.es_dueno else "."), size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            self.mensaje,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        menu = ft.Container(
            ft.Column([self._item_menu(*g) for g in self.grupos] + [
                ft.Container(height=6),
                ft.Divider(height=1, color=GRAY_LIGHT),
                ft.Container(
                    ft.Row([ft.Icon(ft.Icons.RESTART_ALT, size=18, color=RED),
                            ft.Text("Restablecer mis preferencias", size=12.5, color=RED)], spacing=10),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10), border_radius=10, ink=True,
                    on_click=self._confirmar_restablecer,
                ),
            ], spacing=4),
            width=260, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18, padding=10,
        )
        contenido = {"apariencia": self._apariencia, "inicio": self._inicio, "avisos": self._avisos,
                     "club": self._club}[self.grupo]()
        panel = ft.Container(contenido, expand=True, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT),
                             border_radius=18, padding=ft.padding.symmetric(horizontal=26, vertical=22))
        # sin scroll propio: el área de contenido del menú ya desplaza (y así queda arriba, no centrado)
        return ft.Column([cabecera, ft.Row([menu, panel], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)],
                         spacing=22)

    def _item_menu(self, clave, icono, titulo, sub) -> ft.Container:
        activo = clave == self.grupo
        return ft.Container(
            ft.Row([
                ft.Container(ft.Icon(icono, size=19, color=GOLD_DARK if activo else NAV_ICONO), width=36, height=36,
                             border_radius=10, bgcolor=WHITE if activo else "#F4F2EB", alignment=ft.Alignment.CENTER),
                ft.Column([ft.Text(titulo, size=13.5, weight=ft.FontWeight.W_500, color=DARK),
                           ft.Text(sub, size=11.5, color=TEXT_MUTED)], spacing=0, expand=True),
            ], spacing=12),
            bgcolor=NAV_ACTIVO_BG if activo else None, border_radius=12,
            padding=ft.padding.symmetric(horizontal=10, vertical=8), ink=True,
            on_click=lambda e: self._cambiar_grupo(clave),
        )

    def _cambiar_grupo(self, clave: str):
        self.grupo = cfg._grupo_configuracion = clave
        self._ok("")
        self._render()

    # ── piezas comunes ──
    def _titulo(self, texto: str, sub: str) -> ft.Column:
        return ft.Column([ft.Text(texto, size=18, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins"),
                          ft.Text(sub, size=12.5, color=TEXT_MUTED)], spacing=2)

    def _fila(self, icono, titulo: str, descripcion: str, control: ft.Control | None = None,
              debajo: ft.Control | None = None) -> ft.Container:
        fila = ft.Row([
            ft.Container(ft.Icon(icono, size=19, color=GOLD_DARK), width=38, height=38, border_radius=19,
                         bgcolor=GOLD_BG2, alignment=ft.Alignment.CENTER),
            ft.Column([ft.Text(titulo, size=14, weight=ft.FontWeight.W_500, color=DARK),
                       ft.Text(descripcion, size=12, color=TEXT_MUTED)], spacing=1, expand=True),
        ] + ([control] if control else []), spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        partes = [fila] + ([ft.Container(debajo, padding=ft.padding.only(left=52, top=10))] if debajo else [])
        return ft.Container(ft.Column(partes, spacing=0), padding=ft.padding.symmetric(vertical=14),
                            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)))

    def _switch(self, valor: bool, al_cambiar) -> ft.Switch:
        return ft.Switch(value=bool(valor), active_color=GOLD, on_change=lambda e: al_cambiar(e.control.value))

    def _opciones(self, valores: list, actual, al_elegir, formato=str) -> ft.Row:
        def chip(v):
            activo = v == actual
            return ft.Container(
                ft.Text(formato(v), size=12.5, weight=ft.FontWeight.W_500 if activo else ft.FontWeight.W_400,
                        color=DARK),
                bgcolor=GOLD if activo else "#F4F2EB", border_radius=18,
                padding=ft.padding.symmetric(horizontal=14, vertical=7), ink=True,
                on_click=lambda e: al_elegir(v),
            )
        return ft.Row([chip(v) for v in valores], spacing=6, wrap=True, run_spacing=6)

    def _guardar_pref(self, clave: str, valor, recargar: bool = False, render: bool = False):
        try:
            cfg.guardar_preferencia(self.id_empleado, clave, valor)
        except Exception as ex:
            self._ok(f"No se pudo guardar: {ex}", RED)
            return False
        if recargar and self.shell:
            self.shell.recargar("configuracion")   # rearma todo con la apariencia nueva
            return True
        if render:
            self._render()
        self._ok()
        return True

    # ── Apariencia ──
    def _apariencia(self) -> ft.Column:
        prefs = cfg.preferencias()

        def muestra(clave):
            nombre, principal, *_ = PALETAS[clave]
            activo = prefs["acento"] == clave
            return ft.Column([
                ft.Container(
                    ft.Icon(ft.Icons.CHECK, size=18, color=WHITE) if activo else None,
                    width=40, height=40, border_radius=20, bgcolor=principal, alignment=ft.Alignment.CENTER,
                    border=ft.border.all(3, WHITE), shadow=ft.BoxShadow(blur_radius=0, spread_radius=2,
                                                                       color=principal if activo else GRAY_LIGHT),
                    on_click=lambda e: self._guardar_pref("acento", clave, recargar=True), tooltip=nombre,
                ),
                ft.Text(nombre, size=11.5, color=DARK if activo else TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        def fondo(clave):
            nombre, contenido, menu = FONDOS[clave]
            activo = prefs["fondo"] == clave
            vista = ft.Row([
                ft.Container(width=26, bgcolor=menu, border=ft.border.only(right=ft.BorderSide(1, GRAY_LIGHT))),
                ft.Container(ft.Column([ft.Container(height=6, width=40, bgcolor=GRAY_LIGHT, border_radius=3),
                                        ft.Container(height=22, bgcolor=WHITE, border_radius=4,
                                                     border=ft.border.all(1, GRAY_LIGHT))], spacing=5),
                             bgcolor=contenido, expand=True, padding=8),
            ], spacing=0)
            return ft.Column([
                ft.Container(vista, width=118, height=64, border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                             border=ft.border.all(2.5 if activo else 1, GOLD if activo else GRAY_LIGHT),
                             on_click=lambda e: self._guardar_pref("fondo", clave, recargar=True), ink=True),
                ft.Text(nombre, size=11.5, color=DARK if activo else TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        return ft.Column([
            self._titulo("Apariencia", "Elegí cómo se ve el sistema. Se aplica en el momento."),
            ft.Container(height=6),
            self._fila(ft.Icons.COLOR_LENS_OUTLINED, "Color de acento",
                       "Botones, sección elegida del menú, filtros y resaltados.",
                       debajo=ft.Row([muestra(c) for c in PALETAS], spacing=18)),
            self._fila(ft.Icons.WALLPAPER, "Fondo", "El color detrás de las tarjetas y del menú lateral.",
                       debajo=ft.Row([fondo(c) for c in FONDOS], spacing=14)),
            self._fila(ft.Icons.VIEW_SIDEBAR_OUTLINED, "Menú lateral compacto",
                       "Muestra solo los íconos y deja más lugar para el contenido (el nombre aparece al pasar el mouse).",
                       self._switch(prefs["menu_compacto"],
                                    lambda v: self._guardar_pref("menu_compacto", v, recargar=True))),
        ], spacing=0)

    # ── Inicio y sesión ──
    def _inicio(self) -> ft.Column:
        prefs = cfg.preferencias()
        secciones = [(i["s"], i["l"]) for i in ROLES.get(self.rol, {}).get("nav", []) if "s" in i]
        selector = ft.Dropdown(
            value=prefs["seccion_inicio"] if prefs["seccion_inicio"] in dict(secciones) else "dashboard",
            width=230, dense=True, border_radius=10, border_color=GRAY_LIGHT, text_size=13,
            options=[ft.DropdownOption(key=s, text=l) for s, l in secciones],
            on_select=lambda e: self._guardar_pref("seccion_inicio", e.control.value),
        )

        def recordar(v):
            if self._guardar_pref("recordar_usuario", v):
                cfg.recordar_usuario(self.actual.get("usuario") if v else None)

        return ft.Column([
            self._titulo("Inicio y sesión", "Qué pasa cuando entrás y salís del sistema."),
            ft.Container(height=6),
            self._fila(ft.Icons.HOME_OUTLINED, "Sección al iniciar sesión",
                       "La pantalla que se abre apenas entrás.", selector),
            self._fila(ft.Icons.PERSON_PIN_OUTLINED, "Recordar mi usuario en esta computadora",
                       f"El login aparece con \"{self.actual.get('usuario', '')}\" ya escrito (la contraseña nunca se guarda).",
                       self._switch(prefs["recordar_usuario"], recordar)),
            self._fila(ft.Icons.LOGOUT, "Preguntar antes de cerrar sesión",
                       "Evita salir sin querer al tocar \"Cerrar sesión\".",
                       self._switch(prefs["confirmar_salida"], lambda v: self._guardar_pref("confirmar_salida", v))),
        ], spacing=0)

    # ── Notificaciones ──
    def _avisos(self) -> ft.Column:
        prefs = cfg.preferencias()
        apagados = set(prefs.get("avisos_apagados") or [])
        tipos = notificaciones_repo.tipos_de_rol(self.rol)

        def contador(v):
            if self._guardar_pref("contador_menu", v) and self.shell:
                self.shell.mostrar_contador(0)
                if v:
                    self.shell.actualizar_contador()

        def alternar_tipo(tipo, encendido):
            nuevos = sorted((apagados - {tipo}) if encendido else (apagados | {tipo}))
            if self._guardar_pref("avisos_apagados", nuevos, render=True) and self.shell:
                self.shell.actualizar_contador()

        filas_tipos = []
        for t in tipos:
            info = notificaciones_repo.TIPOS[t]
            filas_tipos.append(ft.Container(ft.Row([
                ft.Icon(getattr(ft.Icons, info["icono"], ft.Icons.NOTIFICATIONS_NONE), size=18, color=NAV_ICONO),
                ft.Column([ft.Text(info["nombre"], size=13, weight=ft.FontWeight.W_500, color=DARK),
                           ft.Text(DESCRIPCION_AVISO.get(t, ""), size=11.5, color=TEXT_MUTED)], spacing=0, expand=True),
                self._switch(t not in apagados, lambda v, t=t: alternar_tipo(t, v)),
            ], spacing=12), padding=ft.padding.symmetric(vertical=6)))

        controles = [
            self._titulo("Notificaciones", "Solo aparecen los avisos que corresponden a tu rol."),
            ft.Container(height=6),
            self._fila(ft.Icons.MARK_UNREAD_CHAT_ALT_OUTLINED, "Contador en el menú",
                       "El número rojo de avisos sin leer al lado de \"Notificaciones\".",
                       self._switch(prefs["contador_menu"], contador)),
        ]
        if "membresia_por_vencer" in tipos:
            controles.append(self._fila(
                ft.Icons.EVENT_OUTLINED, "Avisar vencimientos con anticipación",
                "Cuántos días antes de que venza una membresía querés el aviso.",
                debajo=self._opciones([3, 5, 7, 10, 15], int(prefs["dias_aviso_vencimiento"]),
                                      lambda v: self._guardar_pref("dias_aviso_vencimiento", v, render=True),
                                      lambda v: f"{v} días")))
        controles.append(self._fila(ft.Icons.TUNE, "Qué avisos querés ver",
                                    f"{len(tipos) - len(apagados & set(tipos))} de {len(tipos)} encendidos.",
                                    debajo=ft.Column(filas_tipos, spacing=0)))
        return ft.Column(controles, spacing=0)

    # ── Club (solo dueño) ──
    def _club(self) -> ft.Column:
        club = cfg.club()

        def guardar_club(clave, valor, recargar=False):
            try:
                cfg.guardar_club(clave, valor)
            except Exception as ex:
                self._ok(f"No se pudo guardar: {ex}", RED)
                return
            if recargar and self.shell:
                self.shell.recargar("configuracion")
                return
            self._render()
            self._ok()

        nombre = ft.TextField(value=club["nombre"], width=230, dense=True, border_radius=10, border_color=GRAY_LIGHT,
                              text_size=13, max_length=40, counter=ft.Text(""))
        capacidad = ft.TextField(value=str(club["capacidad_maxima"]), width=90, dense=True, border_radius=10,
                                 border_color=GRAY_LIGHT, text_size=13, keyboard_type=ft.KeyboardType.NUMBER,
                                 suffix="pers.")

        def guardar_nombre(e=None):
            texto = (nombre.value or "").strip()
            if not texto:
                self._ok("Escribí el nombre del gimnasio.", RED)
                return
            guardar_club("nombre", texto[:40], recargar=True)

        def guardar_capacidad(e=None):
            try:
                n = int((capacidad.value or "").strip())
                if not 1 <= n <= 5000:
                    raise ValueError
            except ValueError:
                self._ok("La capacidad tiene que ser un número entre 1 y 5000.", RED)
                return
            guardar_club("capacidad_maxima", n)

        def boton(on_click):
            return ft.Container(ft.Text("Guardar", size=12.5, weight=ft.FontWeight.W_500, color=DARK), bgcolor=GOLD,
                                border_radius=10, padding=ft.padding.symmetric(horizontal=14, vertical=9),
                                on_click=on_click, ink=True)

        nombre.on_submit = guardar_nombre
        capacidad.on_submit = guardar_capacidad
        return ft.Column([
            self._titulo("Club", "Datos del gimnasio. Los ve todo el personal."),
            ft.Container(height=6),
            self._fila(ft.Icons.STOREFRONT_OUTLINED, "Nombre del gimnasio",
                       "Aparece en el menú lateral y en el título de la ventana.",
                       ft.Row([nombre, boton(guardar_nombre)], spacing=8)),
            self._fila(ft.Icons.GROUPS_OUTLINED, "Capacidad máxima",
                       "Cuántas personas entran a la vez. Se usa en la ocupación en vivo del Dashboard.",
                       ft.Row([capacidad, boton(guardar_capacidad)], spacing=8)),
            self._fila(ft.Icons.WARNING_AMBER_ROUNDED, "Avisar que el club está lleno",
                       "Desde qué porcentaje de ocupación avisa a dueño, seguridad y recepción.",
                       debajo=self._opciones([60, 70, 80, 90, 100], int(club["porcentaje_lleno"]),
                                             lambda v: guardar_club("porcentaje_lleno", v), lambda v: f"{v}%")),
            self._fila(ft.Icons.PERSON_ADD_ALT, "Socio nuevo durante",
                       "Cuántos días después de registrarse un socio figura como \"nuevo\" (en Socios y en los avisos).",
                       debajo=self._opciones([7, 14, 30, 60], int(club["dias_socio_nuevo"]),
                                             lambda v: guardar_club("dias_socio_nuevo", v), lambda v: f"{v} días")),
        ], spacing=0)

    # ── restablecer ──
    def _confirmar_restablecer(self, e=None):
        def si(ev):
            self.page.pop_dialog()
            try:
                cfg.restablecer_preferencias(self.id_empleado)
                cfg.recordar_usuario(self.actual.get("usuario"))
            except Exception as ex:
                self._ok(f"No se pudo restablecer: {ex}", RED)
                return
            if self.shell:
                self.shell.recargar("configuracion")

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Restablecer tus preferencias?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text("Vuelven los colores, el menú y los avisos de siempre. Los datos del club no cambian.",
                            size=13, color=TEXT_MUTED),
            actions=[ft.TextButton("Cancelar", on_click=lambda ev: self.page.pop_dialog()),
                     ft.TextButton("Restablecer", on_click=si, style=ft.ButtonStyle(color=RED))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))


def build_configuracion(page: ft.Page, rol: str = "dueno", shell=None) -> ft.Column:
    return ConfiguracionView(page, rol, shell).build()
