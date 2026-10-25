# OLIMPOS GYM — Cámaras (Dueño / Seguridad)
#
# Grilla con la imagen en vivo de cada cámara, que se vuelve a pedir sola cada
# N segundos (en un hilo aparte, para no trabar la pantalla). Cada cámara
# muestra si está en línea, sin señal o sin conexión y a qué hora llegó la
# última imagen. Tocar una la agranda; desde ahí se puede guardar una captura
# (queda en Imágenes\OlimpOS - Cámaras). Las cámaras se agregan, editan y
# quitan desde acá (ver camaras_repo.py). El hilo se corta solo al salir.

import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
import camaras_repo as repo

INTERVALOS = {10: "Cada 10 s", 30: "Cada 30 s", 60: "Cada 1 min"}
ESTADOS = {
    "ok": ("En línea", "#DCFCE7", "#15803D"),
    "sin_senal": ("Sin señal", "#FEF3C7", "#B45309"),
    "error": ("Sin conexión", "#FEE2E2", "#B91C1C"),
    "cargando": ("Conectando…", "#F1F0EA", "#6B6656"),
}


class CamarasView:
    def __init__(self, page: ft.Page, rol: str = "dueno"):
        self.page = page
        self.rol = rol
        self.intervalo = 30
        self.pausado = False
        self.error = None
        self.estado: dict[str, dict] = {}        # id -> último resultado de capturar()
        self.tarjetas: dict[str, dict] = {}      # id -> controles a actualizar
        self.ampliada = None                     # (id, imagen, texto) de la cámara agrandada
        self.mensaje = ft.Text("", size=12.5, weight=ft.FontWeight.W_500)
        self.texto_resumen = ft.Text("", size=12.5, color=TEXT_MUTED)
        self.root = ft.Column(spacing=0)
        self._vivo = True
        self._despertar = threading.Event()
        self._cargar_lista()

    def build(self) -> ft.Column:
        self._render()
        # el menú llama a "al_salir" cuando se cambia de sección o se cierra sesión
        self.root.data = {"al_salir": self.detener}
        # con run_thread el hilo puede actualizar la pantalla (con un Thread común Flet no redibuja)
        if self.page is not None:
            self.page.run_thread(self._bucle)
        else:
            threading.Thread(target=self._bucle, daemon=True).start()
        return self.root

    def detener(self):
        self._vivo = False
        self._despertar.set()

    def _cargar_lista(self):
        try:
            self.camaras = repo.listar()
            self.error = None
        except Exception as ex:
            self.camaras, self.error = [], str(ex)

    # ── hilo que refresca las imágenes ──
    def _bucle(self):
        time.sleep(0.5)
        while self._vivo:
            if not self.pausado:
                self._refrescar_todas()
            self._despertar.wait(self.intervalo)
            self._despertar.clear()

    def _refrescar_todas(self):
        camaras = list(self.camaras)
        if not camaras:
            return
        with ThreadPoolExecutor(min(8, len(camaras))) as ex:
            for camara, res in zip(camaras, ex.map(repo.capturar, camaras)):
                if not self._vivo:
                    return
                self.estado[camara["id"]] = res
                self._pintar(camara["id"])
        self._pintar_resumen()

    def _pintar(self, id_camara: str):
        t, res = self.tarjetas.get(id_camara), self.estado.get(id_camara)
        if not t or not res:
            return
        etiqueta, fondo, color = ESTADOS[res["estado"]]
        if res["imagen"]:
            t["imagen"].src = res["imagen"]
            t["imagen"].visible = True
            t["vacio"].visible = False
        else:
            t["imagen"].visible = False
            t["vacio"].visible = True
            t["vacio"].content.controls[1].value = res["detalle"]
        t["estado"].content.controls[0].bgcolor = color
        t["estado"].content.controls[1].value = etiqueta
        t["estado"].bgcolor = fondo
        t["estado"].content.controls[1].color = color
        t["hora"].value = f"Última imagen {res['hora']:%H:%M:%S}" if res["imagen"] else res["detalle"]
        try:
            t["caja"].update()
        except Exception:
            pass
        if self.ampliada and self.ampliada[0] == id_camara and res["imagen"]:
            self.ampliada[1].src = res["imagen"]
            self.ampliada[2].value = f"{etiqueta} · última imagen {res['hora']:%H:%M:%S}"
            try:
                self.ampliada[1].update()
                self.ampliada[2].update()
            except Exception:
                pass

    def _pintar_resumen(self):
        en_linea = sum(1 for r in self.estado.values() if r["estado"] == "ok")
        problemas = sum(1 for r in self.estado.values() if r["estado"] != "ok")
        self.texto_resumen.value = (f"{en_linea} en línea · {problemas} con problemas · "
                                    f"actualizado {time.strftime('%H:%M:%S')}")
        try:
            self.texto_resumen.update()
        except Exception:
            pass

    # ── pantalla ──
    def _render(self):
        self.root.controls = [self._pantalla()]
        try:
            if self.root.page:
                self.root.update()
        except RuntimeError:
            pass

    def _pantalla(self) -> ft.Column:
        agregar = ft.Container(
            ft.Row([ft.Icon(ft.Icons.ADD, size=18, color=DARK),
                    ft.Text("Agregar cámara", size=14, weight=ft.FontWeight.W_500, color=DARK)], spacing=8, tight=True),
            bgcolor=GOLD, border_radius=12, padding=ft.padding.symmetric(horizontal=20, vertical=12),
            on_click=lambda e: self._dialogo_camara(), ink=True)
        intervalo = ft.Dropdown(value=str(self.intervalo), width=150, dense=True, border_radius=12, border_color=GRAY_LIGHT,
                                bgcolor=WHITE, text_size=13,
                                options=[ft.DropdownOption(key=str(k), text=v) for k, v in INTERVALOS.items()],
                                on_select=self._cambiar_intervalo)
        pausa = ft.IconButton(ft.Icons.PLAY_ARROW if self.pausado else ft.Icons.PAUSE,
                              tooltip="Reanudar" if self.pausado else "Pausar la actualización",
                              on_click=self._alternar_pausa)
        ahora = ft.IconButton(ft.Icons.REFRESH, tooltip="Actualizar ahora", on_click=lambda e: self._despertar.set())
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Seguridad", size=13, color=TEXT_MUTED),
                ft.Text("Cámaras", size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.15)),
                ft.Text("Imagen en vivo de cada cámara, actualizada sola.", size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            intervalo, pausa, ahora, agregar,
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.END)
        controles = [cabecera]
        if any(c.get("prueba") for c in self.camaras):
            controles.append(ft.Container(ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color="#1D4ED8"),
                ft.Text("Estas son cámaras de PRUEBA: tráfico en vivo de Los Ángeles, públicas y gratuitas (Caltrans, "
                        "se actualizan cada ~2 minutos). Cuando el gimnasio tenga cámaras IP, agregalas con su "
                        "dirección de captura (snapshot JPG) y quitá las de prueba.", size=12, color="#1E3A8A",
                        expand=True),
                ft.TextButton("Quitar las de prueba", on_click=lambda e: self._confirmar_quitar_pruebas()),
            ], spacing=10), bgcolor="#EFF6FF", border=ft.border.all(1, "#BFDBFE"), border_radius=12, padding=12))
        if self.error:
            controles.append(ft.Text(f"⚠️ No se pudo leer la lista de cámaras: {self.error}", color=RED))
        if self.mensaje.value:
            controles.append(self.mensaje)
        controles.append(ft.Row([ft.Text(f"{len(self.camaras)} cámaras", size=13, weight=ft.FontWeight.W_500,
                                         color=DARK), self.texto_resumen], spacing=12))
        if self.camaras:
            self.tarjetas = {}
            controles.append(ft.ResponsiveRow([self._tarjeta(c) for c in self.camaras], spacing=16, run_spacing=16))
        else:
            controles.append(ft.Container(ft.Column([
                ft.Icon(ft.Icons.VIDEOCAM_OFF_OUTLINED, size=40, color=GRAY),
                ft.Text("No hay cámaras cargadas.", size=14, weight=ft.FontWeight.W_500, color=DARK),
                ft.TextButton("Volver a poner las cámaras de prueba", on_click=lambda e: self._restaurar_pruebas()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=40, alignment=ft.Alignment.CENTER,
                bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16))
        return ft.Column(controles, spacing=16)

    def _tarjeta(self, c: dict) -> ft.Container:
        imagen = ft.Image(src="L21.png", fit=ft.BoxFit.COVER, expand=True, visible=False, gapless_playback=True)
        vacio = ft.Container(ft.Column([ft.ProgressRing(width=22, height=22, stroke_width=2.5, color=GOLD),
                                        ft.Text("Conectando…", size=11.5, color="#C8C4B4")],
                                       horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                             alignment=ft.Alignment.CENTER, expand=True)
        estado = ft.Container(ft.Row([ft.Container(width=7, height=7, border_radius=4, bgcolor="#6B6656"),
                                      ft.Text("Conectando…", size=11, weight=ft.FontWeight.W_500, color="#6B6656")],
                                     spacing=6, tight=True),
                              bgcolor="#F1F0EA", border_radius=10, padding=ft.padding.symmetric(horizontal=8, vertical=3))
        hora = ft.Text("", size=11, color=TEXT_MUTED)
        menu = ft.PopupMenuButton(icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Opciones", items=[
            ft.PopupMenuItem(content=ft.Text("🔍  Agrandar"), on_click=lambda e, x=c: self._ampliar(x)),
            ft.PopupMenuItem(content=ft.Text("📸  Guardar captura"), on_click=lambda e, x=c: self._capturar(x)),
            ft.PopupMenuItem(content=ft.Text("✏️  Editar"), on_click=lambda e, x=c: self._dialogo_camara(x)),
            ft.PopupMenuItem(content=ft.Text("🗑️  Quitar", color=RED), on_click=lambda e, x=c: self._confirmar_quitar(x)),
        ])
        visor = ft.Container(ft.Stack([vacio, imagen], expand=True, fit=ft.StackFit.EXPAND), height=210, bgcolor="#1C1A12",
                             border_radius=ft.border_radius.only(top_left=16, top_right=16),
                             clip_behavior=ft.ClipBehavior.ANTI_ALIAS, on_click=lambda e, x=c: self._ampliar(x),
                             tooltip="Tocá para agrandar")
        caja = ft.Container(ft.Column([
            visor,
            ft.Container(ft.Row([
                ft.Column([ft.Text(c["nombre"], size=13.5, weight=ft.FontWeight.W_600, color=DARK, max_lines=1,
                                   overflow=ft.TextOverflow.ELLIPSIS),
                           ft.Text(c.get("ubicacion") or c["url"], size=11.5, color=TEXT_MUTED, max_lines=1,
                                   overflow=ft.TextOverflow.ELLIPSIS),
                           ft.Row([estado, hora], spacing=8)], spacing=3, expand=True),
                menu,
            ], vertical_alignment=ft.CrossAxisAlignment.START), padding=ft.padding.only(left=14, right=4, top=10, bottom=12)),
        ], spacing=0), bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16,
            col={"xs": 12, "md": 6, "xl": 4})
        self.tarjetas[c["id"]] = {"caja": caja, "imagen": imagen, "vacio": vacio, "estado": estado, "hora": hora}
        if c["id"] in self.estado:
            self._pintar_sin_actualizar(c["id"])
        return caja

    def _pintar_sin_actualizar(self, id_camara):
        """Al rearmar la pantalla, mostrar enseguida la última imagen que ya había."""
        t, res = self.tarjetas[id_camara], self.estado[id_camara]
        etiqueta, fondo, color = ESTADOS[res["estado"]]
        if res["imagen"]:
            t["imagen"].src, t["imagen"].visible, t["vacio"].visible = res["imagen"], True, False
        t["estado"].bgcolor = fondo
        t["estado"].content.controls[0].bgcolor = color
        t["estado"].content.controls[1].value, t["estado"].content.controls[1].color = etiqueta, color
        t["hora"].value = f"Última imagen {res['hora']:%H:%M:%S}" if res["imagen"] else res["detalle"]

    # ── controles ──
    def _cambiar_intervalo(self, e):
        self.intervalo = int(e.control.value)
        self._despertar.set()

    def _alternar_pausa(self, e):
        self.pausado = not self.pausado
        self._render()
        if not self.pausado:
            self._despertar.set()

    def _avisar(self, texto, color=GREEN):
        self.mensaje.value, self.mensaje.color = texto, color

    def _recargar(self):
        self._cargar_lista()
        self.estado = {k: v for k, v in self.estado.items() if any(c["id"] == k for c in self.camaras)}
        self._render()
        self._despertar.set()

    # ── agrandar y capturar ──
    def _ampliar(self, c: dict):
        res = self.estado.get(c["id"])
        imagen = ft.Image(src=res["imagen"] if res and res["imagen"] else "L21.png", fit=ft.BoxFit.CONTAIN,
                          width=720, height=460, gapless_playback=True)
        texto = ft.Text(f"{ESTADOS[res['estado']][0]} · última imagen {res['hora']:%H:%M:%S}" if res else "Conectando…",
                        size=12, color=TEXT_MUTED)
        self.ampliada = (c["id"], imagen, texto)

        def cerrar(e):
            self.ampliada = None
            self.page.pop_dialog()
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Column([ft.Text(c["nombre"], weight=ft.FontWeight.W_600, font_family="Poppins"),
                             ft.Text(c.get("ubicacion") or c["url"], size=12, color=TEXT_MUTED)], spacing=2),
            content=ft.Column([ft.Container(imagen, bgcolor="#1C1A12", border_radius=12,
                                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS), texto], tight=True, spacing=8),
            actions=[ft.TextButton("Guardar captura", icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
                                   on_click=lambda e: self._capturar(c, en_dialogo=True)),
                     ft.TextButton("Cerrar", on_click=cerrar)],
            on_dismiss=lambda e: setattr(self, "ampliada", None)))

    def _capturar(self, c: dict, en_dialogo: bool = False):
        res = self.estado.get(c["id"])
        if not res or not res["imagen"]:
            self._avisar(f"{c['nombre']}: todavía no hay imagen para guardar.", RED)
        else:
            try:
                ruta = repo.guardar_captura(c, res["imagen"])
                self._avisar(f"📸 Captura guardada en {ruta}")
            except Exception as ex:
                self._avisar(f"No se pudo guardar la captura: {ex}", RED)
        if en_dialogo and self.ampliada:
            self.ampliada[2].value = self.mensaje.value
            try:
                self.ampliada[2].update()
            except Exception:
                pass
        else:
            self._render()

    # ── agregar / editar / quitar ──
    def _dialogo_camara(self, c: dict | None = None):
        nombre = ft.TextField(label="Nombre *", value=c["nombre"] if c else "", hint_text="Ej.: Entrada principal",
                              dense=True, border_radius=10, text_size=13)
        ubicacion = ft.TextField(label="Ubicación", value=c.get("ubicacion", "") if c else "",
                                 hint_text="Ej.: Planta baja, sobre recepción", dense=True, border_radius=10, text_size=13)
        url = ft.TextField(label="Dirección de la imagen (snapshot) *", value=c["url"] if c else "",
                           hint_text="Ej.: http://192.168.0.20/snapshot.jpg", dense=True, border_radius=10, text_size=13)
        prueba = ft.Text("", size=12)
        error = ft.Text("", size=12, color=RED)

        def probar(e):
            prueba.value, prueba.color = "Probando…", TEXT_MUTED
            prueba.update()
            res = repo.capturar({"url": (url.value or "").strip()})
            prueba.value = {"ok": f"✓ Funciona ({res['detalle']})", "sin_senal": "Responde, pero no está transmitiendo",
                            "error": f"✗ {res['detalle']}"}[res["estado"]]
            prueba.color = GREEN if res["estado"] == "ok" else (GOLD_DARK if res["estado"] == "sin_senal" else RED)
            prueba.update()

        def guardar(e):
            try:
                if c:
                    repo.editar(c["id"], nombre.value, ubicacion.value, url.value)
                else:
                    repo.agregar(nombre.value, ubicacion.value, url.value)
            except ValueError as ex:
                error.value = str(ex)
                error.update()
                return
            except Exception as ex:
                error.value = f"No se pudo guardar: {ex}"
                error.update()
                return
            self.page.pop_dialog()
            self._avisar(f"✓ Cámara «{nombre.value.strip()}» {'actualizada' if c else 'agregada'}")
            self._recargar()

        self.page.show_dialog(ft.AlertDialog(
            modal=True, title=ft.Text("Editar cámara" if c else "Agregar cámara", weight=ft.FontWeight.W_600,
                                      font_family="Poppins"),
            content=ft.Column([
                nombre, ubicacion, url,
                ft.Text("Las cámaras IP tienen una dirección que devuelve una foto del momento (suele terminar en "
                        "snapshot.jpg o image.jpg; figura en el manual o en la configuración de la cámara).",
                        size=11.5, color=TEXT_MUTED),
                ft.Row([ft.OutlinedButton("Probar conexión", icon=ft.Icons.WIFI_TETHERING, on_click=probar), prueba],
                       spacing=10),
                error,
            ], spacing=12, tight=True, width=460),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.FilledButton("Guardar", on_click=guardar, style=ft.ButtonStyle(bgcolor=GOLD, color=DARK))],
            actions_alignment=ft.MainAxisAlignment.END))

    def _confirmar(self, titulo, texto, al_confirmar):
        def si(e):
            self.page.pop_dialog()
            try:
                al_confirmar()
            except Exception as ex:
                self._avisar(f"No se pudo: {ex}", RED)
            self._recargar()
        self.page.show_dialog(ft.AlertDialog(
            modal=True, title=ft.Text(titulo, weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Text(texto, size=13, color=TEXT_MUTED, width=420),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.TextButton("Quitar", on_click=si, style=ft.ButtonStyle(color=RED))],
            actions_alignment=ft.MainAxisAlignment.END))

    def _confirmar_quitar(self, c):
        self._confirmar("¿Quitar esta cámara?", f"«{c['nombre']}» deja de verse acá. Las capturas guardadas no se borran.",
                        lambda: (repo.quitar(c["id"]), self._avisar(f"Cámara «{c['nombre']}» quitada", GOLD_DARK)))

    def _confirmar_quitar_pruebas(self):
        self._confirmar("¿Quitar las cámaras de prueba?",
                        "Se quitan las 6 de Los Ángeles. Las que agregaste vos quedan. Se pueden volver a poner.",
                        lambda: (repo.quitar_pruebas(), self._avisar("Cámaras de prueba quitadas", GOLD_DARK)))

    def _restaurar_pruebas(self):
        try:
            repo.restaurar_pruebas()
            self._avisar("✓ Volvieron las cámaras de prueba")
        except Exception as ex:
            self._avisar(f"No se pudo: {ex}", RED)
        self._recargar()


def build_camaras(page: ft.Page = None, rol: str = "dueno") -> ft.Column:
    return CamarasView(page, rol).build()
