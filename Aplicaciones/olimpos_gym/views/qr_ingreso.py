import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import threading
import time
from datetime import datetime

import flet as ft
from theme import *
from components import section_card, page_header, action_button
import qr_ingreso_repo as repo
import ocupacion_repo


class QrIngresoView:
    """El QR que se deja abierto en el mostrador: el socio lo escanea con la
    app y queda registrado que está adentro. Cambia solo cada 30 segundos."""

    def __init__(self, page: ft.Page, rol: str):
        self.page = page
        self.rol = rol
        self._vivo = True
        self._ventana = None
        self.imagen = ft.Image(src=b"", width=340, height=340, fit=ft.BoxFit.CONTAIN, gapless_playback=True)
        self.cuenta = ft.Text("", size=12.5, color=TEXT_MUTED)
        self.barra = ft.ProgressBar(value=1, width=340, color=GOLD, bgcolor=GRAY_LIGHT, border_radius=4)
        self.adentro_titulo = ft.Text("", size=15, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins")
        self.adentro_lista = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, height=360)
        self.mensaje = ft.Text("", size=12.5)
        self.root = ft.Column(spacing=18)

    # ── pantalla ──
    def build(self) -> ft.Column:
        acciones = [action_button("Pantalla completa", "gold", lambda e: self._pantalla_completa())]
        if self.rol == "dueno":
            acciones.append(action_button("Cambiar clave del QR", "outline", lambda e: self._confirmar_cambio()))
        qr = section_card(ft.Column([
            ft.Text("Escaneá para registrar tu entrada", size=17, weight=ft.FontWeight.W_600, color=DARK,
                    font_family="Poppins", text_align=ft.TextAlign.CENTER),
            ft.Text("Abrí la app OlimpΩs → Inicio → «Escanear QR de entrada»", size=12.5, color=TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER),
            ft.Container(self.imagen, padding=8, border_radius=12, bgcolor=WHITE),
            self.barra,
            self.cuenta,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), padding=28)
        adentro = section_card(ft.Column([
            self.adentro_titulo,
            ft.Text(f"Socios que escanearon en los últimos {ocupacion_repo.MINUTOS_EN_EL_CLUB} minutos",
                    size=12, color=TEXT_MUTED),
            ft.Divider(height=14, color=GRAY_LIGHT),
            self.adentro_lista,
        ], spacing=4), padding=22)
        self.root.controls = [
            page_header("QR de entrada", "Dejalo abierto en el mostrador: cambia solo cada "
                        f"{repo.VENTANA_SEGUNDOS} segundos, así una foto no sirve para entrar desde afuera.", acciones),
            self.mensaje,
            ft.Row([ft.Container(qr, width=430), ft.Container(adentro, expand=True)],
                   vertical_alignment=ft.CrossAxisAlignment.START, spacing=18),
        ]
        self.root.data = {"al_salir": self.detener}
        self._refrescar_qr()
        self._refrescar_adentro()
        self.page.run_thread(self._bucle)
        return self.root

    def detener(self):
        self._vivo = False

    def _bucle(self):
        vueltas = 0
        while self._vivo:
            time.sleep(1)
            vueltas += 1
            try:
                self._refrescar_qr()
                if vueltas % 15 == 0:
                    self._refrescar_adentro()
                self.page.update()
            except Exception:
                pass   # sin conexión por un momento: lo intenta en el próximo segundo

    def _refrescar_qr(self):
        try:
            v = repo.ventana_actual()
            if v != self._ventana:
                self.imagen.src = repo.imagen_png(repo.contenido(v))
                self._ventana = v
                self.mensaje.value = ""
            quedan = repo.segundos_restantes()
            self.barra.value = quedan / repo.VENTANA_SEGUNDOS
            self.cuenta.value = f"Se renueva en {quedan} s"
        except Exception as ex:
            self.mensaje.value, self.mensaje.color = f"No se pudo generar el QR: {ex}", RED

    def _refrescar_adentro(self):
        try:
            filas = ocupacion_repo.entradas_recientes()
        except Exception as ex:
            self.adentro_titulo.value = "Adentro ahora"
            self.adentro_lista.controls = [ft.Text(f"No se pudo cargar: {ex}", size=12, color=RED)]
            return
        self.adentro_titulo.value = f"Adentro ahora · {len(filas)} de {ocupacion_repo.capacidad()}"
        if not filas:
            self.adentro_lista.controls = [ft.Text("Todavía nadie escaneó el QR en este rato.", size=12.5, color=TEXT_MUTED)]
            return
        self.adentro_lista.controls = [
            ft.Container(ft.Row([
                ft.Text(f["nombre"], size=13, color=DARK, expand=True),
                ft.Text("entró " + datetime.fromtimestamp(f["entrada_ms"] / 1000).strftime("%H:%M"),
                        size=12, color=TEXT_MUTED),
            ]), padding=ft.padding.symmetric(vertical=8),
                border=ft.border.only(bottom=ft.border.BorderSide(1, GRAY_LIGHT)))
            for f in filas
        ]

    # ── acciones ──
    def _pantalla_completa(self):
        grande = ft.Image(src=self.imagen.src, width=560, height=560, fit=ft.BoxFit.CONTAIN, gapless_playback=True)
        abierto = {"si": True}

        def seguir():
            ultima = self._ventana
            while abierto["si"] and self._vivo:
                time.sleep(1)
                if self._ventana != ultima:
                    ultima, grande.src = self._ventana, self.imagen.src
                    try:
                        grande.update()
                    except Exception:
                        return

        def cerrar(e):
            abierto["si"] = False
            self.page.pop_dialog()

        self.page.show_dialog(ft.AlertDialog(
            modal=True, bgcolor=WHITE,
            content=ft.Column([
                ft.Text("Escaneá con la app OlimpΩs", size=20, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins"),
                grande,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, spacing=12),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        ))
        self.page.run_thread(seguir)

    def _confirmar_cambio(self):
        def cambiar(e):
            self.page.pop_dialog()
            try:
                repo.cambiar_clave()
                self._ventana = None
                self._refrescar_qr()
                self.mensaje.value, self.mensaje.color = "Listo: los QR anteriores ya no sirven.", GREEN
            except Exception as ex:
                self.mensaje.value, self.mensaje.color = f"No se pudo cambiar: {ex}", RED
            self.page.update()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Cambiar la clave del QR?", weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text("Los QR que se hayan mostrado o fotografiado hasta ahora dejan de servir. "
                            "Usalo si creés que alguien copió el QR.", width=380),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.FilledButton("Cambiar clave", on_click=cambiar, style=ft.ButtonStyle(bgcolor=GOLD, color=DARK))],
            actions_alignment=ft.MainAxisAlignment.END,
        ))


def build_qr_ingreso(page: ft.Page, rol: str) -> ft.Column:
    return QrIngresoView(page, rol).build()
