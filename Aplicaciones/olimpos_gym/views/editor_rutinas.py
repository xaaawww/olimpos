# OLIMPOS GYM — Asignación de Rutinas (Dueño / Entrenador)
#
# Antes de esto, la app móvil mostraba la misma rutina fija ("Empuje
# pesado") a cualquier socio que abriera "Entrenar", atribuida siempre a
# un entrenador de ejemplo — nadie la asignaba de verdad. Acá se elige un
# socio de la lista y se le arma su rutina real.
#
# Los ejercicios de una rutina NO se escriben libremente: se eligen del
# mismo catálogo que arma "Editor Visual de Ejercicios" (ejercicios_repo),
# buscando por nombre (con resultados en vivo) o tocando un botón de la
# lista — así la rutina hereda automáticamente la técnica y las zonas
# musculares reales de ese ejercicio (el "bodygraph"), en vez de que cada
# entrenador tipee un nombre suelto sin información detrás. Si no existe
# todavía, se puede crear ahí mismo como borrador nuevo.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import section_card, action_button, page_header, status_pill, divider, avatar
import auth_repo
import ejercicios_repo
import rutinas_repo as repo

# Tamaño chico del bodygraph dentro de una fila de ejercicio de la rutina
# (mucho menor que el editor de ejercicios, que ocupa toda la pantalla).
MINI_CANVAS_W = 46
MINI_CANVAS_H = 92


class EditorRutinasView:
    def __init__(self, page: ft.Page, nombre_entrenador: str):
        self.page = page
        self.nombre_entrenador = nombre_entrenador
        self.error_carga = None
        try:
            self.socios = auth_repo.listar_accesos_socios()
            self.rutinas = repo.cargar_rutinas()
            self.catalogo = ejercicios_repo.cargar_ejercicios()
        except Exception as ex:
            self.socios, self.rutinas, self.catalogo = [], {}, []
            self.error_carga = str(ex)
        self.vista = "lista"     # lista | editor
        self.socio_id = None
        self.rutina = None
        self.aviso = None
        # Estado de UI por fila de ejercicio (no se guarda en Firestore):
        # texto de búsqueda en curso y si su bodygraph está expandido.
        self.busqueda: dict[int, str] = {}
        self.info_abierta: set[int] = set()
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls.clear()
        if self.vista == "lista":
            self.root.controls.append(self._vista_lista())
        else:
            self.root.controls.append(self._vista_editor())
        if self._montado:
            self.root.update()

    # ══════════════════════════ LISTA DE SOCIOS ══════════════════════════
    def _vista_lista(self) -> ft.Column:
        avisos = []
        if self.error_carga:
            avisos.append(ft.Container(
                content=ft.Text(f"⚠️ No se pudo conectar con Firebase: {self.error_carga}",
                                size=12, color="#DC2626", weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))

        if not self.socios:
            filas = [section_card(ft.Column([
                ft.Text("📋", size=34),
                ft.Text("Todavía no hay socios con acceso a la app.", size=13, weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Dales de alta desde \"Socios\" para poder asignarles una rutina.", size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)]
        else:
            ordenados = sorted(self.socios, key=lambda s: s.get("nombre", ""))
            filas = [self._fila_socio(s) for s in ordenados]

        return ft.Column([
            page_header(
                "📋 Asignación de Rutinas", "Elegí un socio para armar o editar su rutina de Entrenar",
                actions=[action_button("🔄 Actualizar", "outline", on_click=self._refrescar)],
            ),
            *avisos,
            section_card(ft.Column(filas, spacing=8), padding=14),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _fila_socio(self, socio: dict) -> ft.Container:
        uid = socio["uid"]
        rutina = self.rutinas.get(uid)
        nombre = socio.get("nombre", "?")
        iniciales = "".join(p[0] for p in nombre.split()[:2]).upper() or "?"
        estado = status_pill(f"✓ {rutina['nombre']}", "active") if rutina else status_pill("Sin rutina asignada", "pending")

        return ft.Container(
            content=ft.Row([
                avatar(iniciales),
                ft.Column([
                    ft.Text(nombre, size=13.5, weight=ft.FontWeight.W_700, color=DARK),
                    ft.Text(socio.get("email", ""), size=11.5, color=TEXT_MUTED),
                ], spacing=1, expand=True),
                estado,
                action_button("✏️ Editar rutina" if rutina else "➕ Asignar rutina", "outline",
                              on_click=lambda e, u=uid: self._abrir_editor(u)),
            ], spacing=12, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

    def _refrescar(self, e):
        try:
            self.socios = auth_repo.listar_accesos_socios(forzar=True)
            self.rutinas = repo.cargar_rutinas(forzar=True)
            self.catalogo = ejercicios_repo.cargar_ejercicios(forzar=True)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ EDITOR ══════════════════════════
    def _abrir_editor(self, socio_id: str):
        self.socio_id = socio_id
        self.rutina = repo.obtener_rutina(socio_id) or repo.nueva_rutina(socio_id, self.nombre_entrenador)
        # Copia superficial de la lista de ejercicios para poder editar sin
        # tocar la caché hasta que se guarde de verdad.
        self.rutina = {**self.rutina, "ejercicios": [dict(ej) for ej in self.rutina["ejercicios"]]}
        self.busqueda = {}
        self.info_abierta = set()
        self.aviso = None
        self.vista = "editor"
        self._render()

    def _nombre_socio(self, socio_id: str) -> str:
        return next((s["nombre"] for s in self.socios if s["uid"] == socio_id), "?")

    def _vista_editor(self) -> ft.Column:
        campo_nombre = ft.TextField(
            label="Nombre de la rutina", value=self.rutina["nombre"], width=320,
            on_change=lambda e: self._set_rutina_campo("nombre", e.control.value),
        )

        avisos = []
        if self.aviso:
            avisos.append(ft.Container(
                content=ft.Text(self.aviso, size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))

        filas_ejercicios = [self._fila_ejercicio(i, ej) for i, ej in enumerate(self.rutina["ejercicios"])]
        if not filas_ejercicios:
            filas_ejercicios = [ft.Text(
                "Todavía no agregaste ningún ejercicio. Usá \"+ Agregar ejercicio\" para empezar.",
                size=12.5, color=TEXT_MUTED,
            )]

        return ft.Column([
            page_header(
                f"Rutina de {self._nombre_socio(self.socio_id)}", "Armá los ejercicios, series y peso de partida",
                actions=[action_button("← Volver al listado", "outline", on_click=self._volver_lista)],
            ),
            *avisos,
            section_card(campo_nombre, padding=16),
            section_card(ft.Column([
                ft.Row([
                    ft.Text("EJERCICIOS", size=11, weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=True),
                    action_button("+ Agregar ejercicio", "outline", on_click=self._agregar_ejercicio),
                ]),
                divider(),
                ft.Column(filas_ejercicios, spacing=10),
            ], spacing=10), padding=16),
            ft.Row([
                action_button("💾 Guardar rutina", "gold", on_click=self._guardar),
                self._boton_texto("🗑️ Eliminar rutina asignada", RED, self._eliminar) if repo.obtener_rutina(self.socio_id) else ft.Container(),
            ], spacing=8),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    # ── Fila de un ejercicio: dos estados — buscando (sin elegir todavía)
    # o ya elegido (con su bodygraph y campos de series/peso). ──
    def _fila_ejercicio(self, i: int, ejercicio: dict) -> ft.Control:
        if not ejercicio.get("ejercicio_id"):
            return self._fila_busqueda(i, ejercicio)
        return self._fila_elegida(i, ejercicio)

    def _fila_busqueda(self, i: int, ejercicio: dict) -> ft.Container:
        texto = self.busqueda.get(i, "")
        campo = ft.TextField(
            label="Buscar ejercicio del catálogo...", value=texto, dense=True,
            autofocus=True,
            on_change=lambda e, idx=i: self._buscar(idx, e.control.value),
        )

        coincidencias = [
            e for e in self.catalogo if texto.lower().strip() in e["nombre"].lower()
        ] if texto.strip() else list(self.catalogo)
        coincidencias.sort(key=lambda e: e["nombre"])

        if texto.strip() and not coincidencias:
            resultados = ft.Column([
                ft.Text(f"No se encontró ningún ejercicio llamado \"{texto.strip()}\".",
                        size=12, color=TEXT_MUTED),
                action_button(f"➕ Crear \"{texto.strip()}\" como ejercicio nuevo", "outline",
                              on_click=lambda e, idx=i, n=texto.strip(): self._crear_y_elegir(idx, n)),
            ], spacing=8)
        else:
            botones = [
                ft.Container(
                    content=ft.Text(ex["nombre"], size=12, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                    bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=20,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    on_click=lambda e, idx=i, eid=ex["id"]: self._elegir(idx, eid),
                    ink=True,
                )
                for ex in coincidencias
            ]
            resultados = ft.Row(botones, spacing=6, run_spacing=6, wrap=True) if botones else ft.Text(
                "Todavía no hay ejercicios en el catálogo. Creá el primero escribiendo su nombre arriba.",
                size=12, color=TEXT_MUTED,
            )

        campo.expand = True
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    campo,
                    self._boton_texto("🗑️", RED, lambda e, idx=i: self._eliminar_ejercicio(idx)),
                ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=10),
                resultados,
            ], spacing=8),
            bgcolor=CREAM, border=ft.border.all(1, GRAY_LIGHT), border_radius=10, padding=10,
        )

    def _fila_elegida(self, i: int, ejercicio: dict) -> ft.Column:
        catalogo_ej = ejercicios_repo.obtener_ejercicio(self.catalogo, ejercicio["ejercicio_id"])
        expandida = i in self.info_abierta

        fila = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=self._mini_bodygraph(catalogo_ej),
                    on_click=lambda e, idx=i: self._alternar_info(idx),
                    tooltip="Ver técnica y músculos trabajados",
                    ink=True, border_radius=8,
                ),
                ft.Column([
                    ft.Text(ejercicio["nombre"], size=13.5, weight=ft.FontWeight.W_800, color=DARK),
                    ft.TextButton(
                        "Cambiar ejercicio", on_click=lambda e, idx=i: self._volver_a_buscar(idx),
                        style=ft.ButtonStyle(color=GOLD_DARK, text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_700)),
                    ),
                ], spacing=0, expand=True),
                ft.TextField(
                    label="Series", value=str(ejercicio["series_objetivo"]), width=70, dense=True,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=lambda e, ej=ejercicio: self._set_ejercicio_entero(ej, "series_objetivo", e.control.value),
                ),
                ft.TextField(
                    label="Peso de partida (kg)", value=str(ejercicio["peso_base_kg"]), width=130, dense=True,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_change=lambda e, ej=ejercicio: self._set_ejercicio_flotante(ej, "peso_base_kg", e.control.value),
                ),
                ft.Column([
                    ft.Text("Peso corporal", size=10, color=TEXT_MUTED),
                    ft.Switch(
                        value=ejercicio["es_peso_corporal"], active_color=GOLD,
                        on_change=lambda e, ej=ejercicio: self._set_ejercicio_campo(ej, "es_peso_corporal", e.control.value),
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                self._boton_texto("🗑️", RED, lambda e, idx=i: self._eliminar_ejercicio(idx)),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CREAM, border=ft.border.all(1, GRAY_LIGHT), border_radius=10, padding=10,
        )

        controles = [fila]
        if expandida:
            controles.append(self._panel_info(catalogo_ej))
        return ft.Column(controles, spacing=6)

    def _panel_info(self, catalogo_ej: dict | None) -> ft.Container:
        if not catalogo_ej:
            return ft.Container(
                content=ft.Text("Este ejercicio ya no está en el catálogo (pudo haberse borrado).",
                                size=12, color=TEXT_MUTED),
                bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=10, padding=12,
            )
        zonas = [ejercicios_repo.ZONAS_MUSCULARES[p["zona"]] for p in catalogo_ej.get("puntos", [])]
        return ft.Container(
            content=ft.Column([
                ft.Text(catalogo_ej["nombre"], size=13, weight=ft.FontWeight.W_800, font_family="Poppins"),
                ft.Text(catalogo_ej.get("descripcion") or "Sin descripción todavía.", size=12, color=TEXT_MUTED),
                ft.Row(
                    [status_pill(f"{z['emoji']} {z['etiqueta']}", "pending") for z in zonas],
                    spacing=6, run_spacing=6, wrap=True,
                ) if zonas else ft.Text("Todavía sin zonas musculares asignadas.", size=11.5, color=TEXT_MUTED),
                ft.Row(
                    [status_pill(t, "active") for t in catalogo_ej.get("tags", [])],
                    spacing=6, run_spacing=6, wrap=True,
                ) if catalogo_ej.get("tags") else ft.Container(),
            ], spacing=8),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=10, padding=12,
        )

    def _mini_bodygraph(self, catalogo_ej: dict | None) -> ft.Row:
        seleccionadas = {p["zona"] for p in catalogo_ej.get("puntos", [])} if catalogo_ej else set()

        def vista_stack(vista: str) -> ft.Stack:
            capas = [ft.Image(src=f"cuerpo/base_{vista}.png", width=MINI_CANVAS_W, height=MINI_CANVAS_H, fit=ft.BoxFit.FILL)]
            for zona in ejercicios_repo.ZONAS_POR_VISTA[vista]:
                if zona in seleccionadas:
                    capas.append(ft.Image(src=f"cuerpo/zona_{vista}_{zona}.png", width=MINI_CANVAS_W, height=MINI_CANVAS_H, fit=ft.BoxFit.FILL))
            return ft.Stack(capas, width=MINI_CANVAS_W, height=MINI_CANVAS_H)

        return ft.Row([vista_stack("frente"), vista_stack("espalda")], spacing=2)

    # ── acciones de búsqueda / selección ──
    def _buscar(self, i: int, texto: str):
        self.busqueda[i] = texto
        self._render()

    def _elegir(self, i: int, ejercicio_id: str):
        catalogo_ej = ejercicios_repo.obtener_ejercicio(self.catalogo, ejercicio_id)
        if not catalogo_ej:
            return
        self.rutina["ejercicios"][i]["ejercicio_id"] = ejercicio_id
        self.rutina["ejercicios"][i]["nombre"] = catalogo_ej["nombre"]
        self.busqueda.pop(i, None)
        self._render()

    def _crear_y_elegir(self, i: int, nombre: str):
        nuevo = ejercicios_repo.nuevo_ejercicio(nombre)
        try:
            self.catalogo = ejercicios_repo.guardar_ejercicio(self.catalogo, nuevo)
        except Exception as ex:
            self.aviso = f"No se pudo crear el ejercicio: {ex}"
            self._render()
            return
        self.rutina["ejercicios"][i]["ejercicio_id"] = nuevo["id"]
        self.rutina["ejercicios"][i]["nombre"] = nuevo["nombre"]
        self.busqueda.pop(i, None)
        self.aviso = (
            f"\"{nuevo['nombre']}\" se creó como borrador sin técnica ni zonas musculares todavía — "
            "completalo desde \"Editor Visual de Ejercicios\" cuando puedas."
        )
        self._render()

    def _volver_a_buscar(self, i: int):
        self.rutina["ejercicios"][i]["ejercicio_id"] = None
        self.info_abierta.discard(i)
        self._render()

    def _alternar_info(self, i: int):
        if i in self.info_abierta:
            self.info_abierta.discard(i)
        else:
            self.info_abierta.add(i)
        self._render()

    def _agregar_ejercicio(self, e):
        self.rutina["ejercicios"].append(repo.nuevo_ejercicio_rutina())
        self._render()

    def _eliminar_ejercicio(self, idx: int):
        del self.rutina["ejercicios"][idx]
        self.busqueda.pop(idx, None)
        self.info_abierta.discard(idx)
        self._render()

    def _set_rutina_campo(self, campo: str, valor):
        self.rutina[campo] = valor

    def _set_ejercicio_campo(self, ejercicio: dict, campo: str, valor):
        # Sin re-render acá a propósito: el control (TextField o Switch) ya
        # refleja el cambio por su cuenta con la interacción del usuario;
        # esto solo actualiza el modelo en memoria para cuando se guarde.
        ejercicio[campo] = valor

    def _set_ejercicio_entero(self, ejercicio: dict, campo: str, valor: str):
        try:
            ejercicio[campo] = max(1, int(valor))
        except ValueError:
            pass

    def _set_ejercicio_flotante(self, ejercicio: dict, campo: str, valor: str):
        try:
            ejercicio[campo] = max(0.0, float(valor.replace(",", ".")))
        except ValueError:
            pass

    def _guardar(self, e):
        ejercicios_validos = [ej for ej in self.rutina["ejercicios"] if ej.get("ejercicio_id")]
        if not ejercicios_validos:
            self.aviso = "Agregá al menos un ejercicio del catálogo antes de guardar."
            self._render()
            return
        self.rutina["ejercicios"] = ejercicios_validos
        try:
            self.rutinas = repo.guardar_rutina(self.rutina)
            self.aviso = "Rutina guardada ✓ Ya está disponible en la app del socio."
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
        self._render()

    def _eliminar(self, e):
        try:
            self.rutinas = repo.eliminar_rutina(self.socio_id)
        except Exception as ex:
            self.aviso = f"No se pudo eliminar: {ex}"
            self._render()
            return
        self._volver_lista()

    def _volver_lista(self, e=None):
        self.socio_id = None
        self.rutina = None
        self.vista = "lista"
        self._render()

    # ══════════════════════════ util ══════════════════════════
    def _boton_texto(self, texto: str, color: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(texto, size=11.5, weight=ft.FontWeight.W_700, color=color),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.3, color)),
            border_radius=8, on_click=on_click, ink=True,
        )


def build_editor_rutinas(page: ft.Page, nombre_entrenador: str) -> ft.Column:
    return EditorRutinasView(page, nombre_entrenador).build()
