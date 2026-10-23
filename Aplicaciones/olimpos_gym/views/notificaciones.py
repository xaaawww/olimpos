# OLIMPOS GYM — Notificaciones (cada empleado ve las de su rol)
#
# Los avisos salen de notificaciones_repo, calculados con los datos reales.
# Arriba, filtros (Todas / Sin leer / por tipo); cada aviso tiene "Ver" (lleva
# a la sección donde se resuelve, si el rol la tiene) y marcar leído/no leído.
# Lo leído se guarda por empleado, así que cada uno tiene su propia bandeja.

import os
import sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
import empleados_credenciales
import notificaciones_repo as repo

COLORES = {
    "rojo": ("#FEE2E2", "#DC2626"), "naranja": ("#FFEDD5", "#C2410C"), "verde": ("#DCFCE7", "#15803D"),
    "azul": ("#DBEAFE", "#1D4ED8"), "acento": (GOLD_BG2, GOLD_DARK),
}


def hace(fecha: datetime | None) -> str:
    if not fecha:
        return ""
    seg = (datetime.now(timezone.utc) - fecha).total_seconds()
    if seg < 0:
        return "ahora"
    if seg < 60:
        return "recién"
    if seg < 3600:
        return f"hace {int(seg // 60)} min"
    if seg < 86400:
        return f"hace {int(seg // 3600)} h"
    dias = int(seg // 86400)
    if dias == 1:
        return "ayer"
    if dias < 30:
        return f"hace {dias} días"
    return fecha.astimezone().strftime("%d/%m/%Y")


class NotificacionesView:
    def __init__(self, page: ft.Page, rol: str, navegar=None, on_cambio=None):
        self.page = page
        self.rol = rol
        self.navegar = navegar            # navegar(seccion) del menú
        self.on_cambio = on_cambio        # para actualizar el contador del menú
        self.id_empleado = empleados_credenciales.id_empleado_actual()
        self.filtro = "sin_leer"
        self.avisos: list[dict] = []
        self.error = None
        self.root = ft.Column(spacing=0, expand=True)
        self._montado = False
        self._cargar()

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _cargar(self):
        try:
            self.avisos = repo.avisos_de(self.rol, self.id_empleado)
            self.error = None
        except Exception as ex:
            self.avisos, self.error = [], str(ex)
        if self.filtro == "sin_leer" and not any(not a["leido"] for a in self.avisos):
            self.filtro = "todas"

    def _render(self):
        self.root.controls = [self._pantalla()]
        if self._montado:
            self.root.update()
        if self.on_cambio:
            self.on_cambio(sum(1 for a in self.avisos if not a["leido"]))

    # ── pantalla ──
    def _pantalla(self) -> ft.Column:
        pendientes = [a for a in self.avisos if not a["leido"]]
        rol_label = (empleados_credenciales.actual() or {}).get("rol_label") or self.rol
        marcar_todas = ft.Container(
            ft.Row([ft.Icon(ft.Icons.DONE_ALL, size=18, color=DARK),
                    ft.Text("Marcar todas como leídas", size=13.5, weight=ft.FontWeight.W_500, color=DARK)],
                   spacing=8, tight=True),
            bgcolor=GOLD if pendientes else "#F1F0EA", border_radius=12,
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            on_click=self._marcar_todas if pendientes else None, ink=bool(pendientes),
            opacity=1 if pendientes else 0.6,
        )
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Sistema", size=13, color=TEXT_MUTED),
                ft.Text("Notificaciones", size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.15)),
                ft.Text(f"Avisos para tu rol ({rol_label}), calculados en el momento con los datos del club.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            ft.IconButton(ft.Icons.REFRESH, tooltip="Buscar avisos nuevos", on_click=self._refrescar),
            marcar_todas,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        controles = [cabecera]
        if self.error:
            controles.append(ft.Container(ft.Text(f"⚠️ No se pudieron leer los avisos: {self.error}", size=12, color=RED),
                                          bgcolor=BADGE_RED_BG, border_radius=10, padding=12))
        controles += [self._filtros(pendientes), self._lista()]
        return ft.Column(controles, spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)

    def _filtros(self, pendientes) -> ft.Container:
        por_tipo = {}
        for a in self.avisos:
            por_tipo[a["tipo"]] = por_tipo.get(a["tipo"], 0) + 1
        opciones = [("todas", f"Todas ({len(self.avisos)})"), ("sin_leer", f"Sin leer ({len(pendientes)})")]
        opciones += [(t, f"{repo.TIPOS[t]['nombre']} ({n})") for t, n in por_tipo.items()]

        def pill(clave, texto):
            activo = clave == self.filtro
            return ft.Container(
                ft.Text(texto, size=13, weight=ft.FontWeight.W_500 if activo else ft.FontWeight.W_400, color=DARK),
                bgcolor=GOLD if activo else "#F4F2EB", border_radius=22,
                padding=ft.padding.symmetric(horizontal=18, vertical=9),
                on_click=lambda e, c=clave: self._cambiar_filtro(c), ink=True,
            )
        return ft.Container(ft.Row([pill(c, t) for c, t in opciones], spacing=8, wrap=True, run_spacing=8),
                            bgcolor=WHITE, border_radius=18, border=ft.border.all(1, GRAY_LIGHT), padding=8)

    def _visibles(self) -> list[dict]:
        if self.filtro == "todas":
            return self.avisos
        if self.filtro == "sin_leer":
            return [a for a in self.avisos if not a["leido"]]
        return [a for a in self.avisos if a["tipo"] == self.filtro]

    def _lista(self) -> ft.Container:
        visibles = self._visibles()
        if not visibles:
            vacio = ft.Column([
                ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=44, color=GRAY),
                ft.Text("No tenés avisos sin leer" if self.filtro == "sin_leer" else "No hay avisos acá",
                        size=15, weight=ft.FontWeight.W_500, color=DARK),
                ft.Text("Cuando pase algo que te toque (según tu rol), aparece en esta lista.", size=12.5, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
            return ft.Container(vacio, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16,
                                padding=40, alignment=ft.Alignment.CENTER)
        filas = [self._fila(a, i == 0) for i, a in enumerate(visibles)]
        return ft.Container(ft.Column(filas, spacing=0), bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT),
                            border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def _fila(self, a: dict, primera: bool) -> ft.Container:
        info = repo.TIPOS[a["tipo"]]
        fondo, color = COLORES.get(info["color"], COLORES["azul"])
        secciones = {i["s"] for i in ROLES.get(self.rol, {}).get("nav", []) if "s" in i}
        acciones = []
        if info["seccion"] and info["seccion"] in secciones and self.navegar:
            acciones.append(ft.Container(
                ft.Text("Ver", size=12.5, weight=ft.FontWeight.W_500, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border_radius=10, padding=ft.padding.symmetric(horizontal=14, vertical=7),
                on_click=lambda e, av=a: self._ver(av), ink=True, tooltip="Ir a la sección donde se resuelve",
            ))
        acciones.append(ft.IconButton(
            ft.Icons.MARK_EMAIL_UNREAD_OUTLINED if a["leido"] else ft.Icons.DONE,
            icon_size=19, icon_color=TEXT_MUTED,
            tooltip="Marcar como no leída" if a["leido"] else "Marcar como leída",
            on_click=lambda e, av=a: self._alternar(av),
        ))
        punto = ft.Container(width=8, height=8, border_radius=4, bgcolor=GOLD if not a["leido"] else ft.Colors.TRANSPARENT)
        return ft.Container(
            ft.Row([
                punto,
                ft.Container(ft.Icon(getattr(ft.Icons, info["icono"], ft.Icons.NOTIFICATIONS_NONE), size=20, color=color),
                             width=42, height=42, border_radius=21, bgcolor=fondo, alignment=ft.Alignment.CENTER),
                ft.Column([
                    ft.Text(a["titulo"], size=14, weight=ft.FontWeight.W_400 if a["leido"] else ft.FontWeight.W_500,
                            color=TEXT_MUTED if a["leido"] else DARK, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(a["detalle"], size=12.5, color=TEXT_MUTED, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row([ft.Text(info["nombre"], size=11, weight=ft.FontWeight.W_500, color=color),
                            ft.Text("·", size=11, color=TEXT_MUTED),
                            ft.Text(hace(a["fecha"]), size=11, color=TEXT_MUTED)], spacing=6),
                ], spacing=2, expand=True),
                ft.Row(acciones, spacing=4),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            bgcolor=None if a["leido"] else GOLD_BG,
            border=None if primera else ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
        )

    # ── acciones ──
    def _cambiar_filtro(self, clave: str):
        self.filtro = clave
        self._render()

    def _alternar(self, a: dict):
        try:
            if a["leido"]:
                repo.marcar_no_leida(self.id_empleado, a)
            else:
                repo.marcar_leidas(self.id_empleado, [a])
            a["leido"] = not a["leido"]
        except Exception as ex:
            self.error = str(ex)
        self._render()

    def _marcar_todas(self, e=None):
        pendientes = [a for a in self.avisos if not a["leido"]]
        try:
            repo.marcar_leidas(self.id_empleado, pendientes)
            for a in pendientes:
                a["leido"] = True
        except Exception as ex:
            self.error = str(ex)
        self._render()

    def _ver(self, a: dict):
        if not a["leido"]:
            try:
                repo.marcar_leidas(self.id_empleado, [a])
                a["leido"] = True
            except Exception:
                pass
        self.navegar(repo.TIPOS[a["tipo"]]["seccion"])

    def _refrescar(self, e=None):
        self._cargar()
        self._render()


def build_notificaciones(page: ft.Page, rol: str, navegar=None, on_cambio=None) -> ft.Column:
    return NotificacionesView(page, rol, navegar, on_cambio).build()
