# OLIMPOS GYM — Verificación de Marcas (Dueño / Entrenador)
#
# El Bodygraph de la app móvil calcula el rango de cada músculo a partir de
# las marcas (peso × repeticiones) que carga el socio en la Calculadora —
# ese cálculo corre siempre, pero queda marcado como "no verificado" hasta
# que alguien del gimnasio lo confirma acá. Dos pestañas: la cola de marcas
# pendientes (con Verificar/Rechazar) y un ranking general de socios.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import section_card, action_button, page_header, status_pill, divider
import marcas_repo as repo
import auth_repo


class VerificacionMarcasView:
    def __init__(self, page: ft.Page, verificado_por: str = "Entrenador"):
        self.page = page
        self.verificado_por = verificado_por
        self.error_carga = None
        try:
            self.marcas = repo.cargar_marcas()
            self.datos_fisicos = repo.datos_fisicos_de_todos()
            self.socios_app = {s["uid"]: s for s in auth_repo.listar_accesos_socios() if "uid" in s}
            self.dni_por_uid = auth_repo.dni_de_todos()
        except Exception as ex:
            self.marcas = []
            self.datos_fisicos = {}
            self.socios_app = {}
            self.dni_por_uid = {}
            self.error_carga = str(ex)
        self.tab = "pendientes"
        self.nivel_seleccionado: str | None = None
        self.busqueda_rango = ""
        self.root = ft.Column(spacing=16, expand=True)
        self._montado = False

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _render(self):
        self.root.controls.clear()
        self.root.controls.append(
            page_header("🏆 Verificación de Marcas",
                        "Confirmá los levantamientos de tus socios antes de que cuenten como verificados",
                        actions=[action_button("🔄 Actualizar", "outline", on_click=self._refrescar_todo)])
        )
        if self.error_carga:
            self.root.controls.append(ft.Container(
                content=ft.Text(f"⚠️ No se pudo conectar con Firebase: {self.error_carga}",
                                size=12, color="#DC2626", weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))
        self.root.controls.append(self._tabs())
        if self.tab == "pendientes":
            contenido = self._vista_pendientes()
        elif self.tab == "ranking":
            contenido = self._vista_ranking()
        else:
            contenido = self._vista_rangos()
        self.root.controls.append(contenido)
        if self._montado:
            self.root.update()

    def _tabs(self) -> ft.Row:
        pendientes = sum(1 for m in self.marcas if not m.get("verificado"))
        return ft.Row([
            self._boton_tab("pendientes", f"⏳ Pendientes ({pendientes})"),
            self._boton_tab("ranking", "📊 Ranking general"),
            self._boton_tab("rangos", "🏛️ Rangos"),
        ], spacing=8)

    def _boton_tab(self, tab: str, label: str) -> ft.Container:
        activo = self.tab == tab
        return ft.Container(
            content=ft.Text(label, size=12.5, weight=ft.FontWeight.W_700, color=DARK if activo else TEXT_MUTED),
            bgcolor=GOLD if activo else WHITE,
            border=ft.border.all(1.5, GOLD if activo else GRAY_LIGHT),
            border_radius=10, padding=ft.padding.symmetric(horizontal=14, vertical=9),
            on_click=lambda e, t=tab: self._cambiar_tab(t), ink=True,
        )

    def _refrescar_todo(self, e):
        """Fuerza una relectura real de Firestore en las 4 colecciones que
        usa esta pantalla — todas se cachean en memoria (para que abrir la
        pantalla sea instantáneo), así que esto es para cuando otro
        empleado hizo algo desde otra máquina."""
        try:
            self.marcas = repo.cargar_marcas(forzar=True)
            self.datos_fisicos = repo.datos_fisicos_de_todos(forzar=True)
            self.socios_app = {s["uid"]: s for s in auth_repo.listar_accesos_socios(forzar=True) if "uid" in s}
            self.dni_por_uid = auth_repo.dni_de_todos(forzar=True)
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    def _cambiar_tab(self, tab: str):
        self.tab = tab
        self.nivel_seleccionado = None
        self.busqueda_rango = ""
        self._render()

    # ══════════════════════════ PENDIENTES ══════════════════════════
    def _vista_pendientes(self) -> ft.Column:
        pendientes = [m for m in self.marcas if not m.get("verificado")]
        if not pendientes:
            return ft.Column([section_card(ft.Column([
                ft.Text("✅", size=34),
                ft.Text("No hay marcas pendientes de verificar.", size=13, weight=ft.FontWeight.W_700, color=DARK),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)])

        return ft.Column([self._tarjeta_marca(m) for m in pendientes], spacing=10)

    def _tarjeta_marca(self, m: dict) -> ft.Container:
        peso_corporal = self.datos_fisicos.get(m.get("socio_id"), {}).get("peso_kg", repo.PESO_CORPORAL_REFERENCIA)
        rm = repo.calcular_1rm(repo.carga_total(m, peso_corporal), m.get("repeticiones", 0))
        return section_card(
            ft.Row([
                ft.Column([
                    ft.Text(m.get("socio_nombre", "Socio"), size=13.5, weight=ft.FontWeight.W_800, color=DARK),
                    ft.Text(f"{m.get('ejercicio', '?')} · {m.get('peso', 0):.0f}kg × {m.get('repeticiones', 0)}",
                            size=12.5, color=TEXT_MUTED),
                    ft.Text(f"{m.get('fecha', '')} · 1RM est. {rm:.0f}kg", size=11, color=TEXT_MUTED),
                ], spacing=2, expand=True),
                ft.Row([
                    action_button("✅ Verificar", "gold", on_click=lambda e, mid=m["id"]: self._verificar(mid)),
                    self._boton_texto("🗑️ Rechazar", RED, lambda e, mid=m["id"]: self._rechazar(mid)),
                ], spacing=6),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14,
        )

    def _verificar(self, marca_id: str):
        try:
            repo.verificar_marca(marca_id, verificado_por=self.verificado_por)
            self.marcas = repo.cargar_marcas()
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    def _rechazar(self, marca_id: str):
        try:
            repo.rechazar_marca(marca_id)
            self.marcas = repo.cargar_marcas()
        except Exception as ex:
            self.error_carga = str(ex)
        self._render()

    # ══════════════════════════ RANKING ══════════════════════════
    def _vista_ranking(self) -> ft.Column:
        resumen = repo.resumen_por_socio(self.marcas, self.datos_fisicos)
        if not resumen:
            return ft.Column([section_card(ft.Column([
                ft.Text("📭", size=34),
                ft.Text("Todavía no hay marcas cargadas por ningún socio.", size=13, weight=ft.FontWeight.W_700, color=DARK),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)])

        filas = sorted(resumen.values(), key=lambda r: sum(r["puntajes"].values()), reverse=True)
        return ft.Column([self._fila_ranking(i + 1, r) for i, r in enumerate(filas)], spacing=8)

    def _fila_ranking(self, posicion: int, r: dict) -> ft.Container:
        estado = status_pill("Todo verificado", "active") if r["pendientes"] == 0 else \
                 status_pill(f"{r['pendientes']} pendiente(s)", "pending")
        return section_card(
            ft.Row([
                ft.Container(
                    content=ft.Text(f"#{posicion}", size=14, weight=ft.FontWeight.W_900, color=GOLD_DARK),
                    width=36,
                ),
                ft.Column([
                    ft.Text(r["nombre"], size=13.5, weight=ft.FontWeight.W_800, color=DARK),
                    ft.Text(f"Nivel promedio: {r['nivel_promedio']} · {r['total_marcas']} marca(s)",
                            size=11.5, color=TEXT_MUTED),
                ], spacing=2, expand=True),
                estado,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14,
        )

    # ══════════════════════════ RANGOS (grilla 5x5) ══════════════════════════
    def _vista_rangos(self) -> ft.Column:
        if self.nivel_seleccionado:
            return self._vista_miembros_de_rango(self.nivel_seleccionado)
        return ft.Column([
            ft.Text(
                "Tocá un rango para ver a todos los socios que llegaron ahí, del más fuerte al más flojo.",
                size=12.5, color=TEXT_MUTED,
            ),
            self._grilla_rangos(),
        ], spacing=12)

    def _grilla_rangos(self) -> ft.Column:
        ranking = repo.ranking_por_rango(self.marcas, self.datos_fisicos)
        niveles = repo.todos_los_niveles()  # Dios primero, Mortal 1 al final
        filas = [niveles[i:i + 5] for i in range(0, len(niveles), 5)]
        return ft.Column(
            [ft.Row([self._tile_rango(n, len(ranking.get(n, []))) for n in fila], spacing=12) for fila in filas],
            spacing=12,
        )

    def _tile_rango(self, nivel: str, cantidad: int) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Image(src=repo.imagen_de_nivel(nivel), width=52, height=52, fit=ft.BoxFit.CONTAIN),
                ft.Text(nivel, size=10.5, weight=ft.FontWeight.W_800, color=DARK, text_align=ft.TextAlign.CENTER),
                ft.Text(f"{cantidad} socio(s)", size=9.5, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            bgcolor=WHITE, border_radius=14, border=ft.border.all(1.5, GRAY_LIGHT),
            padding=12, width=140, height=120, alignment=ft.Alignment.CENTER,
            tooltip=nivel, ink=True,
            on_click=lambda e, n=nivel: self._seleccionar_nivel(n),
        )

    def _seleccionar_nivel(self, nivel: str):
        self.nivel_seleccionado = nivel
        self.busqueda_rango = ""
        self._render()

    def _volver_a_grilla(self, e=None):
        self.nivel_seleccionado = None
        self.busqueda_rango = ""
        self._render()

    def _vista_miembros_de_rango(self, nivel: str) -> ft.Column:
        todos = repo.ranking_por_rango(self.marcas, self.datos_fisicos).get(nivel, [])
        # La lista de resultados vive en su propio Column, que se actualiza
        # solo a sí mismo en cada letra tipeada (ft.Column.update()), en vez
        # de llamar a self._render() y reconstruir toda la pantalla — si no,
        # el campo de búsqueda se recrea en cada tecla y pierde el foco.
        resultados_col = ft.Column(spacing=8)

        def _coincide(s: dict, query: str) -> bool:
            uid = s["socio_id"]
            email = self.socios_app.get(uid, {}).get("email", "")
            dni = self.dni_por_uid.get(uid, "")
            return (query in s["nombre"].lower() or query in uid.lower()
                    or query in email.lower() or query in dni.lower())

        def _refrescar_resultados(actualizar_en_vivo: bool):
            query = self.busqueda_rango.strip().lower()
            filtrados = [s for s in todos if _coincide(s, query)] if query else todos
            if not filtrados:
                resultados_col.controls = [section_card(ft.Column([
                    ft.Text("🔍" if query else "📭", size=30),
                    ft.Text(
                        "Nadie coincide con esa búsqueda." if query else "Todavía nadie llegó a este rango.",
                        size=13, weight=ft.FontWeight.W_700, color=DARK,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), padding=30)]
            else:
                resultados_col.controls = [self._fila_miembro_rango(i + 1, s) for i, s in enumerate(filtrados)]
            # En la construcción inicial resultados_col todavía no está
            # agregado a la página (recién se agrega cuando _render() termina
            # y hace self.root.update()) — llamar a su .update() acá tira
            # "Control must be added to the page first". Solo se actualiza a
            # sí mismo en vivo, desde el on_change del campo de búsqueda.
            if actualizar_en_vivo:
                resultados_col.update()

        def _on_buscar(e):
            self.busqueda_rango = e.control.value or ""
            _refrescar_resultados(actualizar_en_vivo=True)

        _refrescar_resultados(actualizar_en_vivo=False)

        encabezado = ft.Row([
            ft.Container(
                content=ft.Text("← Volver a los rangos", size=12.5, weight=ft.FontWeight.W_700, color=GOLD_DARK),
                on_click=self._volver_a_grilla, ink=True,
                padding=ft.padding.symmetric(vertical=6),
            ),
        ])

        titulo = ft.Row([
            ft.Image(src=repo.imagen_de_nivel(nivel), width=40, height=40, fit=ft.BoxFit.CONTAIN),
            ft.Text(nivel, size=18, weight=ft.FontWeight.W_900, color=DARK, font_family="Poppins"),
        ], spacing=10)

        buscador = ft.TextField(
            label="Buscar por nombre, id, email o DNI",
            value=self.busqueda_rango,
            on_change=_on_buscar,
            prefix_icon=ft.Icons.SEARCH,
            width=380,
        )

        return ft.Column([encabezado, titulo, buscador, resultados_col], spacing=14)

    def _fila_miembro_rango(self, posicion: int, s: dict) -> ft.Container:
        uid = s["socio_id"]
        email = self.socios_app.get(uid, {}).get("email", "")
        dni = self.dni_por_uid.get(uid, "")
        return section_card(
            ft.Row([
                ft.Container(
                    content=ft.Text(f"#{posicion}", size=14, weight=ft.FontWeight.W_900, color=GOLD_DARK),
                    width=36,
                ),
                ft.Column([
                    ft.Text(s["nombre"], size=13.5, weight=ft.FontWeight.W_800, color=DARK),
                    ft.Text(
                        " · ".join(filter(None, [email, f"DNI {dni}" if dni else ""])) or uid,
                        size=11.5, color=TEXT_MUTED,
                    ),
                ], spacing=2, expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14,
        )

    # ══════════════════════════ util ══════════════════════════
    def _boton_texto(self, texto: str, color: str, on_click) -> ft.Container:
        return ft.Container(
            content=ft.Text(texto, size=11.5, weight=ft.FontWeight.W_700, color=color),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.3, color)),
            border_radius=8, on_click=on_click, ink=True,
        )


def build_verificacion_marcas(page: ft.Page, verificado_por: str = "Entrenador") -> ft.Column:
    return VerificacionMarcasView(page, verificado_por).build()
