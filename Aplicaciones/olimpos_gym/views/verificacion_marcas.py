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


class VerificacionMarcasView:
    def __init__(self, page: ft.Page, verificado_por: str = "Entrenador"):
        self.page = page
        self.verificado_por = verificado_por
        self.error_carga = None
        try:
            self.marcas = repo.cargar_marcas()
        except Exception as ex:
            self.marcas = []
            self.error_carga = str(ex)
        self.tab = "pendientes"
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
                        "Confirmá los levantamientos de tus socios antes de que cuenten como verificados")
        )
        if self.error_carga:
            self.root.controls.append(ft.Container(
                content=ft.Text(f"⚠️ No se pudo conectar con Firebase: {self.error_carga}",
                                size=12, color="#DC2626", weight=ft.FontWeight.W_700),
                bgcolor="#FEE2E2", border_radius=10, padding=12,
            ))
        self.root.controls.append(self._tabs())
        self.root.controls.append(self._vista_pendientes() if self.tab == "pendientes" else self._vista_ranking())
        if self._montado:
            self.root.update()

    def _tabs(self) -> ft.Row:
        pendientes = sum(1 for m in self.marcas if not m.get("verificado"))
        return ft.Row([
            self._boton_tab("pendientes", f"⏳ Pendientes ({pendientes})"),
            self._boton_tab("ranking", "📊 Ranking general"),
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

    def _cambiar_tab(self, tab: str):
        self.tab = tab
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
        rm = repo.calcular_1rm(repo.carga_total(m), m.get("repeticiones", 0))
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
        resumen = repo.resumen_por_socio(self.marcas)
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
