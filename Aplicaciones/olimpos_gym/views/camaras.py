# OLIMPOS GYM — Cámaras (Dueño / Seguridad)
#
# Grilla con cada cámara EN VIVO: si la cámara tiene dirección de video (RTSP,
# como las cámaras IP de seguridad, o HLS .m3u8) se reproduce con flet-video;
# si no tiene, o si el video falla, se muestra su foto (snapshot), que se
# vuelve a pedir sola cada N segundos en segundo plano. El modo "Fotos" usa
# solo las fotos (gasta mucho menos internet).
# Tocar una cámara la agranda (con controles y pantalla completa); "Guardar
# captura" guarda la foto del momento en Imágenes\OlimpOS - Cámaras. Las
# cámaras se agregan, editan y quitan desde acá (ver camaras_repo.py). Al
# salir de la sección el menú llama a "al_salir" y se corta todo.

import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
import camaras_repo as repo

try:
    import flet_video as fv
except ImportError:          # sin flet-video: todo funciona igual, con fotos
    fv = None

INTERVALOS = {10: "Fotos cada 10 s", 30: "Fotos cada 30 s", 60: "Fotos cada 1 min"}
ESTADOS = {
    "vivo": ("En vivo", "#FEE2E2", "#DC2626"),
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
        self.modo = "video" if fv else "fotos"
        self.pausado = False
        self.error = None
        self.estado: dict[str, dict] = {}        # id -> último resultado de capturar() (fotos)
        self.video_ok: set[str] = set()          # cámaras cuyo video ya arrancó
        self.video_fallo: set[str] = set()       # cámaras cuyo video falló (pasan a foto)
        self.tarjetas: dict[str, dict] = {}
        self.reproductores: dict[str, object] = {}   # id -> el Video que está en pantalla ahora
        self.ampliada = None                    # (id, imagen, texto) de la cámara agrandada en modo foto
        self.mensaje = ft.Text("", size=12.5, weight=ft.FontWeight.W_500)
        self.texto_resumen = ft.Text("", size=12.5, color=TEXT_MUTED)
        self.root = ft.Column(spacing=0)
        self._vivo = True
        self._despertar = threading.Event()
        self._cargar_lista()

    def build(self) -> ft.Column:
        self._render()
        self.root.data = {"al_salir": self.detener}
        if self.page is not None:
            self.page.run_thread(self._bucle)        # con run_thread el hilo puede redibujar
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

    def _usa_video(self, c: dict) -> bool:
        return bool(fv and self.modo == "video" and c.get("video") and c["id"] not in self.video_fallo)

    # ── hilo que refresca las FOTOS (solo de las cámaras que no están en video) ──
    def _bucle(self):
        time.sleep(0.5)
        while self._vivo:
            if not self.pausado:
                self._refrescar_fotos()
            self._despertar.wait(self.intervalo)
            self._despertar.clear()

    def _refrescar_fotos(self):
        camaras = [c for c in self.camaras if not self._usa_video(c)]
        if camaras:
            with ThreadPoolExecutor(min(8, len(camaras))) as ex:
                for camara, res in zip(camaras, ex.map(repo.capturar, camaras)):
                    if not self._vivo:
                        return
                    self.estado[camara["id"]] = res
                    self._pintar(camara["id"])
        self._pintar_resumen()

    def _pintar(self, id_camara: str):
        t, res = self.tarjetas.get(id_camara), self.estado.get(id_camara)
        if not t or not res or "imagen" not in t:
            return
        self._aplicar_foto(t, res)
        try:
            t["caja"].update()
        except Exception:
            pass
        if self.ampliada and self.ampliada[0] == id_camara and res["imagen"]:
            self.ampliada[1].src = res["imagen"]
            self.ampliada[2].value = f"{ESTADOS[res['estado']][0]} · última imagen {res['hora']:%H:%M:%S}"
            try:
                self.ampliada[1].update()
                self.ampliada[2].update()
            except Exception:
                pass

    def _aplicar_foto(self, t: dict, res: dict):
        if res["imagen"]:
            t["imagen"].src, t["imagen"].visible, t["vacio"].visible = res["imagen"], True, False
        else:
            t["imagen"].visible, t["vacio"].visible = False, True
            t["vacio"].content.controls[1].value = res["detalle"]
        self._aplicar_estado(t, res["estado"])
        t["hora"].value = f"Última imagen {res['hora']:%H:%M:%S}" if res["imagen"] else res["detalle"]

    @staticmethod
    def _aplicar_estado(t: dict, estado: str):
        etiqueta, fondo, color = ESTADOS[estado]
        t["estado"].bgcolor = fondo
        t["estado"].content.controls[0].bgcolor = color
        t["estado"].content.controls[1].value, t["estado"].content.controls[1].color = etiqueta, color

    def _pintar_resumen(self):
        en_video = sum(1 for c in self.camaras if self._usa_video(c) and c["id"] in self.video_ok)
        fotos_ok = sum(1 for c in self.camaras if not self._usa_video(c)
                       and self.estado.get(c["id"], {}).get("estado") == "ok")
        problemas = sum(1 for c in self.camaras if not self._usa_video(c)
                        and self.estado.get(c["id"], {}).get("estado") in ("error", "sin_senal"))
        partes = []
        if en_video:
            partes.append(f"{en_video} en vivo")
        if fotos_ok:
            partes.append(f"{fotos_ok} con foto")
        partes.append(f"{problemas} con problemas")
        self.texto_resumen.value = " · ".join(partes) + f" · {time.strftime('%H:%M:%S')}"
        try:
            self.texto_resumen.update()
        except Exception:
            pass

    # ── video ──
    def _es_actual(self, id_camara: str, e) -> bool:
        """Ignora eventos de reproductores viejos: al rearmar la pantalla, los
        Video que se descartan avisan "error" al cerrarse."""
        return getattr(e, "control", None) is self.reproductores.get(id_camara)

    def _video_cargo(self, id_camara: str, e=None):
        if e is not None and not self._es_actual(id_camara, e):
            return
        self.video_ok.add(id_camara)
        t = self.tarjetas.get(id_camara)
        if t:
            self._aplicar_estado(t, "vivo")
            t["hora"].value = "Transmisión en vivo"
            try:
                t["caja"].update()
            except Exception:
                pass
        self._pintar_resumen()

    def _video_fallo(self, id_camara: str, e=None):
        if id_camara in self.video_fallo or (e is not None and not self._es_actual(id_camara, e)):
            return
        camara = next((c for c in self.camaras if c["id"] == id_camara), None)
        url = (camara or {}).get("video", "")
        if url.startswith("http") and self.page is not None:
            # el reproductor a veces avisa el error de OTRA cámara: se confirma antes de cambiar a foto
            self.page.run_thread(self._confirmar_caida, id_camara, url)
        else:
            self._caer_a_foto(id_camara)

    def _confirmar_caida(self, id_camara: str, url: str):
        import requests
        try:
            if requests.get(url, timeout=8, headers={"User-Agent": "OlimpOS"}).ok:
                return                      # la transmisión responde: el aviso no era de esta cámara
        except Exception:
            pass
        self._caer_a_foto(id_camara)

    def _caer_a_foto(self, id_camara: str):
        if id_camara in self.video_fallo:
            return
        self.video_fallo.add(id_camara)
        self.video_ok.discard(id_camara)
        self.reproductores.pop(id_camara, None)
        camara = next((c for c in self.camaras if c["id"] == id_camara), None)
        if camara:
            self._avisar(f"{camara['nombre']}: el video en vivo no responde, se muestra la foto.", GOLD_DARK)
        t = self.tarjetas.get(id_camara)
        if camara and t:
            # se cambia SOLO esa tarjeta por su foto (rearmar todo cortaría los demás videos)
            t["visor"].content = self._visor_foto(camara, t)
            self._aplicar_estado(t, "cargando")
            t["hora"].value = "El video no respondió: se muestra la foto"
            try:
                t["caja"].update()
            except Exception:
                pass
        self._pintar_resumen()
        self._despertar.set()

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

        def opcion_modo(clave, texto, icono):
            activo = self.modo == clave
            return ft.Container(ft.Row([ft.Icon(icono, size=16, color=DARK if activo else TEXT_MUTED),
                                        ft.Text(texto, size=12.5, weight=ft.FontWeight.W_500 if activo else ft.FontWeight.W_400,
                                                color=DARK if activo else TEXT_MUTED)], spacing=6, tight=True),
                                bgcolor=GOLD if activo else None, border_radius=10,
                                padding=ft.padding.symmetric(horizontal=12, vertical=8), ink=True,
                                on_click=lambda e: self._cambiar_modo(clave))
        modo = ft.Container(ft.Row([opcion_modo("video", "En vivo", ft.Icons.VIDEOCAM),
                                    opcion_modo("fotos", "Fotos", ft.Icons.PHOTO_OUTLINED)], spacing=2, tight=True),
                            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=12, padding=3,
                            visible=fv is not None,
                            tooltip="Fotos gasta mucho menos internet que el video en vivo")
        intervalo = ft.Dropdown(value=str(self.intervalo), width=170, dense=True, border_radius=12, border_color=GRAY_LIGHT,
                                bgcolor=WHITE, text_size=13,
                                options=[ft.DropdownOption(key=str(k), text=v) for k, v in INTERVALOS.items()],
                                on_select=self._cambiar_intervalo)
        pausa = ft.IconButton(ft.Icons.PLAY_ARROW if self.pausado else ft.Icons.PAUSE,
                              tooltip="Reanudar las fotos" if self.pausado else "Pausar las fotos",
                              on_click=self._alternar_pausa)
        ahora = ft.IconButton(ft.Icons.REFRESH, tooltip="Actualizar ahora", on_click=lambda e: self._reintentar())
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Seguridad", size=13, color=TEXT_MUTED),
                ft.Text("Cámaras", size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.15)),
                ft.Text("Video en vivo de cada cámara." if fv else "Imagen de cada cámara, actualizada sola.",
                        size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            modo, intervalo, pausa, ahora, agregar,
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.END)
        controles = [cabecera]
        if any(c.get("prueba") for c in self.camaras):
            controles.append(ft.Container(ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color="#1D4ED8"),
                ft.Text("Estas son cámaras de PRUEBA: tráfico en vivo de Los Ángeles, públicas y gratuitas (Caltrans). "
                        "Cuando el gimnasio tenga cámaras IP, agregalas con su dirección de video (rtsp://…) y "
                        "quitá las de prueba.", size=12, color="#1E3A8A", expand=True),
                ft.TextButton("Quitar las de prueba", on_click=lambda e: self._confirmar_quitar_pruebas()),
            ], spacing=10), bgcolor="#EFF6FF", border=ft.border.all(1, "#BFDBFE"), border_radius=12, padding=12))
        if fv is None:
            controles.append(ft.Text("Para ver video en vivo falta instalar flet-video (está en install.txt). "
                                     "Mientras tanto se muestran fotos.", size=12, color=GOLD_DARK))
        if self.error:
            controles.append(ft.Text(f"⚠️ No se pudo leer la lista de cámaras: {self.error}", color=RED))
        if self.mensaje.value:
            controles.append(self.mensaje)
        controles.append(ft.Row([ft.Text(f"{len(self.camaras)} cámaras", size=13, weight=ft.FontWeight.W_500,
                                         color=DARK), self.texto_resumen], spacing=12))
        if self.camaras:
            self.tarjetas, self.reproductores = {}, {}
            controles.append(ft.ResponsiveRow([self._tarjeta(c) for c in self.camaras], spacing=16, run_spacing=16))
        else:
            controles.append(ft.Container(ft.Column([
                ft.Icon(ft.Icons.VIDEOCAM_OFF_OUTLINED, size=40, color=GRAY),
                ft.Text("No hay cámaras cargadas.", size=14, weight=ft.FontWeight.W_500, color=DARK),
                ft.TextButton("Volver a poner las cámaras de prueba", on_click=lambda e: self._restaurar_pruebas()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=40, alignment=ft.Alignment.CENTER,
                bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16))
        return ft.Column(controles, spacing=16)

    def _visor_foto(self, c: dict, t: dict) -> ft.Control:
        imagen = ft.Image(src="L21.png", fit=ft.BoxFit.COVER, expand=True, visible=False, gapless_playback=True)
        vacio = ft.Container(ft.Column([ft.ProgressRing(width=22, height=22, stroke_width=2.5, color=GOLD),
                                        ft.Text("Conectando…", size=11.5, color="#C8C4B4")],
                                       horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                             alignment=ft.Alignment.CENTER, expand=True)
        t.update({"imagen": imagen, "vacio": vacio})
        return ft.Stack([vacio, imagen], expand=True, fit=ft.StackFit.EXPAND)

    def _visor_video(self, c: dict) -> ft.Control:
        video = fv.Video(playlist=[fv.VideoMedia(c["video"])], autoplay=True, muted=True, show_controls=False,
                         fit=ft.BoxFit.COVER, fill_color="#1C1A12", expand=True,
                         on_load=lambda e, i=c["id"]: self._video_cargo(i, e),
                         on_error=lambda e, i=c["id"]: self._video_fallo(i, e))
        self.reproductores[c["id"]] = video
        etiqueta = ft.Container(ft.Row([ft.Container(width=7, height=7, border_radius=4, bgcolor=WHITE),
                                        ft.Text("EN VIVO", size=10.5, weight=ft.FontWeight.W_700, color=WHITE)],
                                       spacing=5, tight=True),
                                bgcolor="#DC2626", border_radius=6, padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                left=10, top=10)
        return ft.Stack([video, etiqueta], expand=True, fit=ft.StackFit.EXPAND)

    def _tarjeta(self, c: dict) -> ft.Container:
        t: dict = {}
        en_video = self._usa_video(c)
        estado = ft.Container(ft.Row([ft.Container(width=7, height=7, border_radius=4, bgcolor="#6B6656"),
                                      ft.Text("Conectando…", size=11, weight=ft.FontWeight.W_500, color="#6B6656")],
                                     spacing=6, tight=True),
                              bgcolor="#F1F0EA", border_radius=10, padding=ft.padding.symmetric(horizontal=8, vertical=3))
        hora = ft.Text("Transmisión en vivo" if en_video and c["id"] in self.video_ok else "", size=11, color=TEXT_MUTED)
        t.update({"estado": estado, "hora": hora})
        menu = ft.PopupMenuButton(icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Opciones", items=[
            ft.PopupMenuItem(content=ft.Text("🔍  Agrandar"), on_click=lambda e, x=c: self._ampliar(x)),
            ft.PopupMenuItem(content=ft.Text("📸  Guardar captura"), on_click=lambda e, x=c: self._capturar(x)),
            ft.PopupMenuItem(content=ft.Text("✏️  Editar"), on_click=lambda e, x=c: self._dialogo_camara(x)),
            ft.PopupMenuItem(content=ft.Text("🗑️  Quitar", color=RED), on_click=lambda e, x=c: self._confirmar_quitar(x)),
        ])
        contenido = self._visor_video(c) if en_video else self._visor_foto(c, t)
        visor = ft.Container(contenido, height=210, bgcolor="#1C1A12",
                             border_radius=ft.border_radius.only(top_left=16, top_right=16),
                             clip_behavior=ft.ClipBehavior.ANTI_ALIAS, on_click=lambda e, x=c: self._ampliar(x),
                             tooltip="Tocá para agrandar")
        caja = ft.Container(ft.Column([
            visor,
            ft.Container(ft.Row([
                ft.Column([ft.Text(c["nombre"], size=13.5, weight=ft.FontWeight.W_600, color=DARK, max_lines=1,
                                   overflow=ft.TextOverflow.ELLIPSIS),
                           ft.Text(c.get("ubicacion") or c.get("video") or c.get("url", ""), size=11.5, color=TEXT_MUTED,
                                   max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                           ft.Row([estado, hora], spacing=8)], spacing=3, expand=True),
                menu,
            ], vertical_alignment=ft.CrossAxisAlignment.START), padding=ft.padding.only(left=14, right=4, top=10, bottom=12)),
        ], spacing=0), bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16,
            col={"xs": 12, "md": 6, "xl": 4})
        t["caja"], t["visor"] = caja, visor
        self.tarjetas[c["id"]] = t
        if en_video and c["id"] in self.video_ok:
            self._aplicar_estado(t, "vivo")
        elif not en_video and c["id"] in self.estado:
            self._aplicar_foto(t, self.estado[c["id"]])
        return caja

    # ── controles ──
    def _cambiar_modo(self, modo: str):
        if modo == self.modo:
            return
        self.modo = modo
        self.video_ok.clear()
        self._render()
        self._despertar.set()

    def _cambiar_intervalo(self, e):
        self.intervalo = int(e.control.value)
        self._despertar.set()

    def _alternar_pausa(self, e):
        self.pausado = not self.pausado
        self._render()
        if not self.pausado:
            self._despertar.set()

    def _reintentar(self):
        """Actualizar ahora: vuelve a intentar los videos que fallaron y pide fotos nuevas."""
        if self.video_fallo:
            self.video_fallo.clear()
            self._render()
        self._despertar.set()

    def _avisar(self, texto, color=GREEN):
        self.mensaje.value, self.mensaje.color = texto, color

    def _recargar(self):
        self._cargar_lista()
        ids = {c["id"] for c in self.camaras}
        self.estado = {k: v for k, v in self.estado.items() if k in ids}
        self.video_ok &= ids
        self.video_fallo &= ids
        self._render()
        self._despertar.set()

    # ── agrandar y capturar ──
    def _ampliar(self, c: dict):
        texto = ft.Text("", size=12, color=TEXT_MUTED)
        if self._usa_video(c):
            visor = fv.Video(playlist=[fv.VideoMedia(c["video"])], autoplay=True, muted=True, show_controls=True,
                             fit=ft.BoxFit.CONTAIN, fill_color="#1C1A12", width=720, height=405)
            texto.value = "Video en vivo · con los controles de abajo se pausa o se pasa a pantalla completa"
            self.ampliada = None
        else:
            res = self.estado.get(c["id"])
            visor = ft.Image(src=res["imagen"] if res and res["imagen"] else "L21.png", fit=ft.BoxFit.CONTAIN,
                             width=720, height=460, gapless_playback=True)
            texto.value = (f"{ESTADOS[res['estado']][0]} · última imagen {res['hora']:%H:%M:%S}" if res else "Conectando…")
            self.ampliada = (c["id"], visor, texto)

        def cerrar(e):
            self.ampliada = None
            self.page.pop_dialog()
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Column([ft.Text(c["nombre"], weight=ft.FontWeight.W_600, font_family="Poppins"),
                             ft.Text(c.get("ubicacion") or "", size=12, color=TEXT_MUTED)], spacing=2),
            content=ft.Column([ft.Container(visor, bgcolor="#1C1A12", border_radius=12,
                                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS), texto], tight=True, spacing=8),
            actions=[ft.TextButton("Guardar captura", icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
                                   on_click=lambda e: self._capturar(c, texto)),
                     ft.TextButton("Cerrar", on_click=cerrar)],
            on_dismiss=lambda e: setattr(self, "ampliada", None)))

    def _capturar(self, c: dict, texto_dialogo: ft.Text | None = None):
        """Guarda la foto del momento (si está en video, pide una foto nueva a la cámara)."""
        res = self.estado.get(c["id"])
        if self._usa_video(c) or not res or not res["imagen"]:
            res = repo.capturar(c)
        if not res["imagen"]:
            self._avisar(f"{c['nombre']}: no se pudo obtener una imagen ({res['detalle']}).", RED)
        else:
            try:
                ruta = repo.guardar_captura(c, res["imagen"])
                self._avisar(f"📸 Captura guardada en {ruta}")
            except Exception as ex:
                self._avisar(f"No se pudo guardar la captura: {ex}", RED)
        if texto_dialogo is not None:
            texto_dialogo.value = self.mensaje.value
            try:
                texto_dialogo.update()
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
        video = ft.TextField(label="Video en vivo", value=c.get("video", "") if c else "",
                             hint_text="Ej.: rtsp://usuario:clave@192.168.0.20:554/stream1", dense=True, border_radius=10,
                             text_size=13)
        url = ft.TextField(label="Foto (snapshot)", value=c.get("url", "") if c else "",
                           hint_text="Ej.: http://192.168.0.20/snapshot.jpg", dense=True, border_radius=10, text_size=13)
        prueba = ft.Text("", size=12)
        error = ft.Text("", size=12, color=RED)

        def probar(e):
            if not (url.value or "").strip():
                prueba.value, prueba.color = "Poné la dirección de la foto para probarla.", TEXT_MUTED
                prueba.update()
                return
            prueba.value, prueba.color = "Probando…", TEXT_MUTED
            prueba.update()
            res = repo.capturar({"url": url.value.strip()})
            prueba.value = {"ok": f"✓ La foto funciona ({res['detalle']})",
                            "sin_senal": "Responde, pero no está transmitiendo", "error": f"✗ {res['detalle']}"}[res["estado"]]
            prueba.color = GREEN if res["estado"] == "ok" else (GOLD_DARK if res["estado"] == "sin_senal" else RED)
            prueba.update()

        def guardar(e):
            try:
                if c:
                    repo.editar(c["id"], nombre.value, ubicacion.value, url.value, video.value)
                else:
                    repo.agregar(nombre.value, ubicacion.value, url.value, video.value)
            except ValueError as ex:
                error.value = str(ex)
                error.update()
                return
            except Exception as ex:
                error.value = f"No se pudo guardar: {ex}"
                error.update()
                return
            self.page.pop_dialog()
            if c:
                self.video_fallo.discard(c["id"])
            self._avisar(f"✓ Cámara «{nombre.value.strip()}» {'actualizada' if c else 'agregada'}")
            self._recargar()

        self.page.show_dialog(ft.AlertDialog(
            modal=True, title=ft.Text("Editar cámara" if c else "Agregar cámara", weight=ft.FontWeight.W_600,
                                      font_family="Poppins"),
            content=ft.Column([
                nombre, ubicacion, video, url,
                ft.Text("Video en vivo: la dirección RTSP de la cámara IP (figura en su manual o en su app). "
                        "Foto: la dirección que devuelve una imagen del momento; se usa de respaldo y para las "
                        "capturas. Con una de las dos alcanza.", size=11.5, color=TEXT_MUTED),
                ft.Row([ft.OutlinedButton("Probar la foto", icon=ft.Icons.WIFI_TETHERING, on_click=probar), prueba],
                       spacing=10),
                error,
            ], spacing=12, tight=True, width=480),
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
