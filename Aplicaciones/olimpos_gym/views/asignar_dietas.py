# OLIMPOS GYM — Asignación de Dietas por horario (Nutricionista / Dueño)
#
# Se elige un socio de la lista y se le arma su dieta del día: qué platos le
# tocan en Desayuno, Almuerzo y Cena. Los platos son los que ya se publicaron
# en el Editor Visual de Dietas (con sus valores nutricionales: kcal,
# proteínas, carbohidratos y grasas por porción). La app móvil lee esta
# asignación (Dieta > "Mi día") y de ahí calcula la meta diaria de cada socio
# y su racha de dieta — ver dietas_asignadas_repo.py.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import section_card, action_button, page_header, status_pill, divider, avatar
import auth_repo
import dietas_repo
import dietas_asignadas_repo as repo

ETIQUETA_OBJETIVO = {
    "FUERZA": "🏋️ Fuerza",
    "HIPERTROFIA": "💪 Hipertrofia",
    "SALUD": "❤️ Salud general",
}


def _texto_macros(m: dict) -> str:
    return f"{m['kcal']} kcal · P {m['proteinas']} g · C {m['carbs']} g · G {m['grasas']} g"


class AsignarDietasView:
    def __init__(self, page: ft.Page, nombre_asignador: str):
        self.page = page
        self.nombre_asignador = nombre_asignador
        self.error_carga = None
        try:
            self.socios = auth_repo.listar_accesos_socios()
            self.asignaciones = repo.cargar_asignaciones()
            self.todos_platos = dietas_repo.cargar_platos()
            self.perfiles = repo.cargar_perfiles_fisicos()
        except Exception as ex:
            self.socios, self.asignaciones, self.todos_platos, self.perfiles = [], {}, [], {}
            self.error_carga = str(ex)
        self.vista = "lista"     # lista | editor
        self.socio_id = None
        self.asignacion = None
        self.aviso = None
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls.clear()
        self.root.controls.append(self._vista_lista() if self.vista == "lista" else self._vista_editor())
        if self._montado:
            self.root.update()

    @property
    def platos_publicados(self) -> list[dict]:
        return [p for p in self.todos_platos if p.get("publicado")]

    def _plato(self, plato_id: str) -> dict | None:
        return dietas_repo.obtener_plato(self.todos_platos, plato_id)

    def _nombre_socio(self, socio_id: str) -> str:
        return next((s["nombre"] for s in self.socios if s["uid"] == socio_id), "?")

    def _pill_objetivo(self, socio_id: str):
        objetivo = (self.perfiles.get(socio_id) or {}).get("objetivo")
        return status_pill(ETIQUETA_OBJETIVO.get(objetivo, "Objetivo sin definir"),
                           "active" if objetivo in ETIQUETA_OBJETIVO else "suspended")

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
                ft.Text("🍽️", size=34),
                ft.Text("Todavía no hay socios con acceso a la app.", size=13, weight=ft.FontWeight.W_700, color=DARK),
                ft.Text("Dales de alta desde \"Socios\" para poder asignarles una dieta.", size=12, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)]
        else:
            ordenados = sorted(self.socios, key=lambda s: s.get("nombre", ""))
            filas = [self._fila_socio(s) for s in ordenados]

        return ft.Column([
            page_header(
                "🍽️ Asignación de Dietas",
                "Elegí un socio y armale su dieta por horario: desayuno, almuerzo y cena",
                actions=[action_button("🔄 Actualizar", "outline", on_click=self._refrescar)],
            ),
            *avisos,
            section_card(ft.Column(filas, spacing=8), padding=14),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _fila_socio(self, socio: dict) -> ft.Container:
        uid = socio["uid"]
        asignacion = self.asignaciones.get(uid)
        nombre = socio.get("nombre", "?")
        iniciales = "".join(p[0] for p in nombre.split()[:2]).upper() or "?"
        if repo.cantidad_platos(asignacion):
            estado = status_pill(f"✓ {repo.horarios_con_platos(asignacion)}/3 horarios con dieta", "active")
        else:
            estado = status_pill("Sin dieta asignada", "pending")

        return ft.Container(
            content=ft.Row([
                avatar(iniciales),
                ft.Column([
                    ft.Text(nombre, size=13.5, weight=ft.FontWeight.W_700, color=DARK),
                    ft.Text(socio.get("email", ""), size=11.5, color=TEXT_MUTED),
                ], spacing=1, expand=True),
                self._pill_objetivo(uid),
                estado,
                action_button("✏️ Editar dieta" if asignacion else "➕ Asignar dieta", "outline",
                              on_click=lambda e, u=uid: self._abrir_editor(u)),
            ], spacing=12, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=12,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

    def _refrescar(self, e):
        try:
            self.socios = auth_repo.listar_accesos_socios(forzar=True)
            self.asignaciones = repo.cargar_asignaciones(forzar=True)
            self.todos_platos = dietas_repo.cargar_platos(forzar=True)
            self.perfiles = repo.cargar_perfiles_fisicos()
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ EDITOR ══════════════════════════
    def _abrir_editor(self, socio_id: str):
        self.socio_id = socio_id
        existente = repo.obtener_asignacion(socio_id) or repo.nueva_asignacion(socio_id, self.nombre_asignador)
        # Copia para poder editar sin tocar la caché hasta que se guarde.
        self.asignacion = {
            **existente,
            "comidas": {c: list(existente.get("comidas", {}).get(c, [])) for c in repo.CLAVES_MOMENTOS},
        }
        self.aviso = None
        self.vista = "editor"
        self._render()

    def _vista_editor(self) -> ft.Column:
        avisos = []
        if self.aviso:
            avisos.append(ft.Container(
                content=ft.Text(self.aviso, size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                bgcolor=GOLD_BG2, border=ft.border.all(1, GOLD_LIGHT), border_radius=10,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ))
        if not self.platos_publicados:
            avisos.append(ft.Container(
                content=ft.Text(
                    "⚠️ Todavía no hay platos publicados. Creá y publicá uno en el "
                    "\"Editor Visual de Dietas\" (con sus valores nutricionales) para poder asignarlo.",
                    size=12, color="#DC2626", weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))

        perfil = self.perfiles.get(self.socio_id) or {}
        peso = perfil.get("peso_kg")
        resumen_socio = ft.Row([
            ft.Text("Objetivo del socio:", size=12, weight=ft.FontWeight.W_700, color=TEXT_MUTED),
            self._pill_objetivo(self.socio_id),
            ft.Text(f"· Peso: {peso:g} kg" if peso else "", size=12, color=TEXT_MUTED),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        todos = [self._plato(pid) for c in repo.CLAVES_MOMENTOS for pid in self.asignacion["comidas"][c]]
        total = repo.sumar_macros([p for p in todos if p])

        existente = repo.obtener_asignacion(self.socio_id)
        return ft.Column([
            page_header(
                f"Dieta de {self._nombre_socio(self.socio_id)}", "Qué come en cada horario del día",
                actions=[action_button("← Volver al listado", "outline", on_click=self._volver_lista)],
            ),
            *avisos,
            section_card(resumen_socio, padding=14),
            *[self._tarjeta_horario(clave, etiqueta, emoji) for clave, etiqueta, emoji in repo.MOMENTOS],
            section_card(ft.Row([
                ft.Text("TOTAL DEL DÍA (meta diaria del socio en la app)", size=11,
                        weight=ft.FontWeight.W_800, color=TEXT_MUTED, expand=True),
                ft.Text(_texto_macros(total), size=15, weight=ft.FontWeight.W_800, color=GOLD_DARK),
            ]), padding=16),
            ft.Row([
                action_button("💾 Guardar dieta", "gold", on_click=self._guardar),
                self._boton_texto("🗑️ Quitar dieta asignada", RED, self._quitar) if existente else ft.Container(),
            ], spacing=8),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def _tarjeta_horario(self, clave: str, etiqueta: str, emoji: str) -> ft.Container:
        ids = self.asignacion["comidas"][clave]
        platos = [self._plato(pid) for pid in ids]
        filas = [self._fila_plato(clave, pid, plato) for pid, plato in zip(ids, platos)]
        if not filas:
            filas = [ft.Text("Todavía no hay ningún plato en este horario.", size=12, color=TEXT_MUTED)]

        disponibles = [p for p in self.platos_publicados if p["id"] not in ids]
        selector = ft.Dropdown(
            label="Agregar plato…", width=340, disabled=not disponibles,
            options=[
                ft.DropdownOption(key=p["id"], text=f"{p['nombre']} · {repo.macros_de_plato(p)['kcal']} kcal")
                for p in disponibles
            ],
            on_select=lambda e, c=clave: self._agregar_plato(c, e.control.value),
        )
        subtotal = repo.sumar_macros([p for p in platos if p])

        return section_card(ft.Column([
            ft.Row([
                ft.Text(f"{emoji} {etiqueta.upper()}", size=12, weight=ft.FontWeight.W_800,
                        color=DARK, expand=True),
                ft.Text(_texto_macros(subtotal), size=11.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
            ]),
            divider(),
            ft.Column(filas, spacing=8),
            selector,
        ], spacing=10), padding=16)

    def _fila_plato(self, clave: str, plato_id: str, plato: dict | None) -> ft.Container:
        if plato is None:
            info = ft.Column([
                ft.Text("Plato no disponible", size=13, weight=ft.FontWeight.W_700, color=RED),
                ft.Text("Fue borrado del Editor Visual de Dietas — sacalo de este horario.",
                        size=11.5, color=TEXT_MUTED),
            ], spacing=1, expand=True)
            miniatura = ft.Container(width=46, height=46, bgcolor=CREAM, border_radius=8)
        else:
            macros = repo.macros_de_plato(plato)
            sin_macros = not any(macros.values())
            detalle = (
                ft.Text("Sin valores nutricionales cargados — completalos en el Editor Visual de Dietas",
                        size=11.5, color="#D97706", weight=ft.FontWeight.W_600)
                if sin_macros else ft.Text(_texto_macros(macros), size=11.5, color=TEXT_MUTED)
            )
            if not plato.get("publicado"):
                detalle = ft.Text("⚠️ No está publicado: el socio no lo va a ver hasta que lo publiques.",
                                  size=11.5, color=RED, weight=ft.FontWeight.W_700)
            info = ft.Column([
                ft.Text(plato["nombre"], size=13, weight=ft.FontWeight.W_700, color=DARK),
                detalle,
            ], spacing=1, expand=True)
            if plato.get("imagen"):
                miniatura = ft.Container(
                    content=ft.Image(src=plato["imagen"], width=46, height=46, fit=ft.BoxFit.COVER,
                                     cache_width=92, cache_height=92),
                    border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                )
            else:
                miniatura = ft.Container(width=46, height=46, bgcolor=CREAM, border_radius=8)

        return ft.Container(
            content=ft.Row([
                miniatura, info,
                self._boton_texto("✕ Quitar", RED, lambda e, c=clave, pid=plato_id: self._quitar_plato(c, pid)),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CREAM, border_radius=10, padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

    def _agregar_plato(self, clave: str, plato_id: str):
        if plato_id and plato_id not in self.asignacion["comidas"][clave]:
            self.asignacion["comidas"][clave].append(plato_id)
        self._render()

    def _quitar_plato(self, clave: str, plato_id: str):
        self.asignacion["comidas"][clave] = [p for p in self.asignacion["comidas"][clave] if p != plato_id]
        self._render()

    def _guardar(self, e):
        try:
            self.asignaciones = repo.guardar_asignacion(self.asignacion)
        except Exception as ex:
            self.aviso = f"No se pudo guardar: {ex}"
            self._render()
            return
        sin_publicar = sum(
            1 for c in repo.CLAVES_MOMENTOS for pid in self.asignacion["comidas"][c]
            if not (self._plato(pid) or {}).get("publicado")
        )
        self.aviso = "Dieta guardada ✓ Ya está en la app del socio (Dieta > Mi día)."
        if sin_publicar:
            self.aviso += f" ⚠️ {sin_publicar} plato(s) asignado(s) no están publicados y el socio no los va a ver."
        self._render()

    def _quitar(self, e):
        try:
            self.asignaciones = repo.eliminar_asignacion(self.socio_id)
        except Exception as ex:
            self.aviso = f"No se pudo quitar: {ex}"
            self._render()
            return
        self._volver_lista()

    def _volver_lista(self, e=None):
        self.socio_id = None
        self.vista = "lista"
        self._render()

    def _boton_texto(self, texto: str, color: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(texto, size=11.5, weight=ft.FontWeight.W_700, color=color),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.3, color)),
            border_radius=8, on_click=on_click, ink=True,
        )


def build_asignar_dietas(page: ft.Page, nombre_asignador: str) -> ft.Column:
    return AsignarDietasView(page, nombre_asignador).build()
