# OLIMPOS GYM — Gestión del personal (Dueño / Administrador)
#
# A la izquierda, la tabla de empleados (rol, turno, sueldo y si cobró el
# sueldo de este mes); al tocar uno se abre a la derecha su panel:
#   Datos      editar sus datos, rol, turno y sueldo; restablecer contraseña;
#              dar de baja o reactivar
#   Sueldo     si cobró este mes, registrar pagos (sueldo, adelanto, bono),
#              historial de pagos y de aumentos
#   Actividad  ingresos al sistema y lo que hizo según su rol
# Reglas: nadie se da de baja ni se cambia el rol a sí mismo, y el
# administrador no puede modificar al dueño ni nombrar dueños.
# Los cálculos y la base están en personal_repo.py.

import os
import sys
from datetime import date, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from theme import *
from components import status_pill
import empleados_credenciales
import personal_repo as repo
import validaciones as val

COLOR_ROL = {
    "dueno": ("#FEF3C7", "#B45309"), "admin": ("#DBEAFE", "#1D4ED8"), "entrenador": ("#DCFCE7", "#15803D"),
    "nutricionista": ("#FCE7F3", "#BE185D"), "seguridad": ("#FEE2E2", "#B91C1C"), "recepcionista": ("#EDE9FE", "#6D28D9"),
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def _plata(v) -> str:
    return "—" if v is None else "$" + f"{v:,.0f}".replace(",", ".")


def _iniciales(nombre: str) -> str:
    p = [x for x in nombre.split() if x]
    return ((p[0][0] + (p[1][0] if len(p) > 1 else "")) if p else "?").upper()


def _avatar(e: dict, lado: int = 38) -> ft.Container:
    fondo, color = COLOR_ROL.get(e["rol"], ("#F1F0EA", "#6B6656"))
    return ft.Container(ft.Text(_iniciales(e["nombre_completo"]), size=lado * 0.34, weight=ft.FontWeight.W_600, color=color),
                        width=lado, height=lado, border_radius=lado / 2, bgcolor=fondo, alignment=ft.Alignment.CENTER,
                        opacity=1 if e["estado"] == "activo" else 0.5)


def _chip_rol(rol: str) -> ft.Container:
    fondo, color = COLOR_ROL.get(rol, ("#F1F0EA", "#6B6656"))
    return ft.Container(ft.Text(repo.ROLES.get(rol, rol), size=11.5, weight=ft.FontWeight.W_500, color=color),
                        bgcolor=fondo, border_radius=12, padding=ft.padding.symmetric(horizontal=10, vertical=3))


def _chip(texto: str, fondo: str, color: str, icono=None) -> ft.Container:
    return ft.Container(ft.Row(([ft.Icon(icono, size=13, color=color)] if icono else []) +
                               [ft.Text(texto, size=11.5, weight=ft.FontWeight.W_500, color=color)], spacing=4, tight=True),
                        bgcolor=fondo, border_radius=12, padding=ft.padding.symmetric(horizontal=10, vertical=3))


def _hace(fecha) -> str:
    if not fecha:
        return "Nunca entró"
    seg = (datetime.now(fecha.tzinfo) - fecha).total_seconds()
    if seg < 3600:
        return f"hace {max(1, int(seg // 60))} min"
    if seg < 86400:
        return f"hace {int(seg // 3600)} h"
    dias = int(seg // 86400)
    return "ayer" if dias == 1 else f"hace {dias} días"


def _antiguedad(ingreso: date | None) -> str:
    if not ingreso:
        return ""
    meses = (date.today().year - ingreso.year) * 12 + date.today().month - ingreso.month
    if meses < 1:
        return "menos de un mes"
    if meses < 12:
        return f"{meses} {'mes' if meses == 1 else 'meses'}"
    anios, resto = divmod(meses, 12)
    return f"{anios} {'año' if anios == 1 else 'años'}" + (f" y {resto} {'mes' if resto == 1 else 'meses'}" if resto else "")


def _fecha(texto: str) -> date | None:
    try:
        return datetime.strptime((texto or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _reglas_empleado(nombre, apellido, dni, telefono, email, sueldo, ingreso, id_empleado=None,
                     usuario=None, dni_obligatorio=True) -> list:
    """Las reglas de cada campo del empleado (alta o edición), para mostrar
    todos los errores juntos. Incluye DNI, email y usuario repetidos."""
    excluir = ("id_empleado", id_empleado) if id_empleado else None

    def regla_dni(v):
        limpio = val.dni(v, obligatorio=dni_obligatorio)
        if val.ya_existe("empleados", "dni", limpio, excluir):
            raise ValueError("Ya hay un empleado con ese DNI.")

    def regla_email(v):
        if val.ya_existe("empleados", "email", val.email(v), excluir, sin_mayusculas=True):
            raise ValueError("Ya hay un empleado con ese email.")

    def regla_usuario(v):
        if val.ya_existe("empleados", "usuario", val.usuario(v), sin_mayusculas=True):
            raise ValueError("Ese usuario ya existe: elegí otro.")

    reglas = [
        (nombre, lambda v: val.nombre_persona(v, "el nombre")),
        (apellido, lambda v: val.nombre_persona(v, "el apellido")),
        (dni, regla_dni),
        (telefono, lambda v: val.telefono(v)),
        (email, regla_email),
        (sueldo, lambda v: val.decimal(v, "el sueldo", minimo=0, maximo=repo.SUELDO_MAXIMO, obligatorio=False)),
        (ingreso, lambda v: val.fecha(v, "la fecha de ingreso", minimo=date(1990, 1, 1), maximo=date.today())),
    ]
    if usuario is not None:
        reglas.append((usuario, regla_usuario))
    return reglas


class PersonalView:
    def __init__(self, page: ft.Page, rol: str = "dueno"):
        self.page = page
        self.rol_actual = rol
        self.yo = empleados_credenciales.id_empleado_actual()
        self.firma = empleados_credenciales.nombre_para_firmar()
        self.filtro = "activos"
        self.busqueda = ""
        self.sel = None
        self.pestana = "datos"
        self.mensaje = ft.Text("", size=12.5, weight=ft.FontWeight.W_500)
        self.buscador = ft.TextField(
            hint_text="Buscar por nombre, usuario o DNI...", prefix_icon=ft.Icons.SEARCH, expand=True, dense=True,
            border_radius=12, border_color=GRAY_LIGHT, bgcolor=WHITE, on_change=self._buscar,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=13))
        self.root = ft.Column(spacing=0)
        self._montado = False
        self._cargar()

    def build(self) -> ft.Column:
        self._render()
        self._montado = True
        return self.root

    def _cargar(self):
        try:
            self.lista = repo.empleados()
            self.res = repo.resumen(self.lista)
            self.error = None
        except Exception as ex:
            self.lista, self.res, self.error = [], None, str(ex)

    def _render(self):
        self.root.controls = [self._pantalla()]
        if self._montado:
            self.root.update()

    def _recargar(self):
        self._cargar()
        self._render()

    def _avisar(self, texto: str, color: str = GREEN):
        self.mensaje.value, self.mensaje.color = texto, color

    def _emp(self) -> dict | None:
        return next((e for e in self.lista if e["id_empleado"] == self.sel), None)

    def _puede_editar(self, e: dict) -> bool:
        """El administrador no puede tocar al dueño."""
        return not (self.rol_actual != "dueno" and e["rol"] == "dueno")

    # ══════════════ PANTALLA ══════════════
    def _pantalla(self) -> ft.Column:
        agregar = ft.Container(
            ft.Row([ft.Icon(ft.Icons.PERSON_ADD_ALT, size=18, color=DARK),
                    ft.Text("Agregar empleado", size=14, weight=ft.FontWeight.W_500, color=DARK)], spacing=8, tight=True),
            bgcolor=GOLD, border_radius=12, padding=ft.padding.symmetric(horizontal=22, vertical=13),
            on_click=lambda e: self._dialogo_alta(), ink=True)
        cabecera = ft.Row([
            ft.Column([
                ft.Text("Administración", size=13, color=TEXT_MUTED),
                ft.Text("Gestión del personal", size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.15)),
                ft.Text("Altas, bajas, sueldos y actividad de cada empleado.", size=13.5, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            agregar,
        ], vertical_alignment=ft.CrossAxisAlignment.END)
        if self.error:
            return ft.Column([cabecera, ft.Text(f"⚠️ No se pudo leer la base de datos: {self.error}", color=RED)], spacing=20)
        izquierda = ft.Column([self._filtros(), self.buscador, self._tabla()], spacing=14, expand=True)
        cuerpo = ft.Row([izquierda] + ([self._panel()] if self._emp() else []), spacing=20,
                        vertical_alignment=ft.CrossAxisAlignment.START)
        return ft.Column([cabecera,
                          ft.Row([self.mensaje], alignment=ft.MainAxisAlignment.END) if self.mensaje.value else ft.Container(),
                          self._tarjetas(), cuerpo], spacing=20)

    def _tarjetas(self) -> ft.Row:
        r = self.res
        mes = MESES[date.today().month - 1]

        def tarjeta(icono, fondo, color, titulo, valor, pie):
            return ft.Container(ft.Row([
                ft.Container(ft.Icon(icono, size=22, color=color), width=46, height=46, border_radius=23, bgcolor=fondo,
                             alignment=ft.Alignment.CENTER),
                ft.Column([ft.Text(titulo, size=12.5, color=TEXT_MUTED),
                           ft.Text(valor, size=24, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                                   style=ft.TextStyle(height=1.1)),
                           ft.Text(pie, size=11.5, color=TEXT_MUTED)], spacing=2, expand=True),
            ], spacing=14), bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16, padding=18, expand=True)

        return ft.Row([
            tarjeta(ft.Icons.BADGE_OUTLINED, GOLD_BG2, GOLD_DARK, "Empleados activos", str(r["activos"]),
                    f"{r['de_baja']} dados de baja" if r["de_baja"] else "Nadie dado de baja"),
            tarjeta(ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "#EDE9FE", "#6D28D9", "Sueldos por mes",
                    _plata(r["masa_salarial"]),
                    f"{r['sin_sueldo']} sin sueldo cargado" if r["sin_sueldo"] else "Todos tienen sueldo cargado"),
            tarjeta(ft.Icons.TASK_ALT, "#DCFCE7", "#15803D", f"Pagados en {mes}", f"{r['pagados']} de {r['a_pagar']}",
                    f"{_plata(r['pagado_mes'])} pagado (con adelantos y bonos)"),
            tarjeta(ft.Icons.PENDING_ACTIONS, "#FEE2E2", "#B91C1C", "Falta pagar", _plata(r["pendiente"]),
                    f"{r['a_pagar'] - r['pagados']} sueldos de {mes}" if r["a_pagar"] - r["pagados"] else "Todos cobraron"),
        ], spacing=14)

    def _filtros(self) -> ft.Row:
        roles = sorted({e["rol"] for e in self.lista}, key=list(repo.ROLES).index)
        opciones = [("activos", f"Activos ({self.res['activos']})"), ("baja", f"De baja ({self.res['de_baja']})"),
                    ("todos", f"Todos ({len(self.lista)})")]
        opciones += [(r, repo.ROLES[r]) for r in roles]

        def pill(clave, texto):
            activo = clave == self.filtro
            return ft.Container(ft.Text(texto, size=12.5, weight=ft.FontWeight.W_500 if activo else ft.FontWeight.W_400,
                                        color=DARK),
                                bgcolor=GOLD if activo else "#F4F2EB", border_radius=20,
                                padding=ft.padding.symmetric(horizontal=16, vertical=8), ink=True,
                                on_click=lambda e, c=clave: self._cambiar_filtro(c))
        return ft.Row([pill(c, t) for c, t in opciones], spacing=8, wrap=True, run_spacing=8)

    def _visibles(self) -> list[dict]:
        lista = self.lista
        if self.filtro == "activos":
            lista = [e for e in lista if e["estado"] == "activo"]
        elif self.filtro == "baja":
            lista = [e for e in lista if e["estado"] != "activo"]
        elif self.filtro in repo.ROLES:
            lista = [e for e in lista if e["rol"] == self.filtro]
        t = self.busqueda
        if t:
            lista = [e for e in lista if t in e["nombre_completo"].lower() or t in (e["usuario"] or "").lower()
                     or t in (e["dni"] or "")]
        return lista

    def _tabla(self) -> ft.Container:
        abierto = self._emp() is not None
        cols = [("EMPLEADO", 4), ("ROL", 2)] + ([] if abierto else [("TURNO", 2), ("SUELDO", 2)]) + \
               [("ESTE MES", 2), ("", 0)]

        def celda(c, p):
            return ft.Container(c, expand=p) if p else ft.Container(c, width=44)
        filas = []
        for e in self._visibles():
            menu = ft.PopupMenuButton(icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Más opciones", items=[
                ft.PopupMenuItem(content=ft.Text("👤  Ver perfil"), on_click=lambda ev, x=e: self._abrir(x["id_empleado"])),
                ft.PopupMenuItem(content=ft.Text("💵  Registrar pago"), disabled=e["estado"] != "activo",
                                 on_click=lambda ev, x=e: self._dialogo_pago(x)),
            ])
            if e["estado"] != "activo":
                este_mes = _chip("De baja", "#F1F0EA", "#6B6656")
            elif not e["sueldo"]:
                este_mes = _chip("Sin sueldo", "#F1F0EA", "#6B6656")
            elif e["cobro_mes"]:
                este_mes = _chip("Pagado", "#DCFCE7", "#15803D", ft.Icons.CHECK)
            else:
                este_mes = _chip("Pendiente", "#FEF3C7", "#B45309")
            celdas = [ft.Row([_avatar(e), ft.Column([
                ft.Text(e["nombre_completo"], size=13.5, weight=ft.FontWeight.W_500, color=DARK, max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"@{e['usuario']}", size=11.5, color=TEXT_MUTED)], spacing=0, expand=True)], spacing=12),
                _chip_rol(e["rol"])]
            if not abierto:
                celdas += [ft.Text(e["turno"] or "—", size=12.5, color=TEXT_MUTED),
                           ft.Text(_plata(e["sueldo"]), size=13, weight=ft.FontWeight.W_500, color=DARK)]
            celdas += [este_mes, menu]
            filas.append(ft.Container(
                ft.Row([celda(c, p) for c, (_, p) in zip(celdas, cols)], spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=16, vertical=8), ink=True,
                bgcolor=GOLD_BG if e["id_empleado"] == self.sel else None,
                border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
                on_click=lambda ev, x=e: self._abrir(x["id_empleado"])))
        encabezado = ft.Container(ft.Row([celda(ft.Text(t, size=11, weight=ft.FontWeight.W_500, color=TEXT_MUTED), p)
                                          for t, p in cols], spacing=10),
                                  padding=ft.padding.symmetric(horizontal=16, vertical=12))
        return ft.Container(ft.Column([encabezado] + (filas or [ft.Container(
            ft.Text("Ningún empleado coincide.", size=13, color=TEXT_MUTED), padding=20)]), spacing=0),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def _cambiar_filtro(self, c):
        self.filtro = c
        self._render()

    def _buscar(self, e):
        self.busqueda = (e.control.value or "").strip().lower()
        self._render()

    # ══════════════ PANEL ══════════════
    def _abrir(self, id_empleado: int):
        self.sel = id_empleado
        self.pestana = "datos"
        self.mensaje.value = ""
        self._render()

    def _cerrar(self, e=None):
        self.sel = None
        self._render()

    def _panel(self) -> ft.Container:
        e = self._emp()
        activo = e["estado"] == "activo"

        def tab(clave, texto):
            elegida = self.pestana == clave
            return ft.Container(ft.Text(texto, size=14, weight=ft.FontWeight.W_500 if elegida else ft.FontWeight.W_400,
                                        color=DARK if elegida else TEXT_MUTED),
                                padding=ft.padding.only(bottom=10), expand=True, alignment=ft.Alignment.CENTER,
                                border=ft.border.only(bottom=ft.BorderSide(2.5, GOLD if elegida else ft.Colors.TRANSPARENT)),
                                on_click=lambda ev: self._cambiar_pestana(clave))
        contenido = {"datos": self._tab_datos, "sueldo": self._tab_sueldo, "actividad": self._tab_actividad}[self.pestana](e)
        cabecera = [
            ft.Container(ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=16, color=DARK), ft.Text("Volver", size=13, color=DARK)],
                                spacing=8, tight=True), on_click=self._cerrar, ink=True, border_radius=8, padding=4),
            ft.Row([
                _avatar(e, 64),
                ft.Column([
                    ft.Text(e["nombre_completo"], size=20, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins"),
                    ft.Row([_chip_rol(e["rol"]),
                            status_pill("Activo" if activo else "De baja", "active" if activo else "inactive")], spacing=8),
                    ft.Text(f"@{e['usuario']} · Ingresó el {e['ingreso']:%d/%m/%Y} ({_antiguedad(e['ingreso'])})"
                            if e["ingreso"] else f"@{e['usuario']}", size=12, color=TEXT_MUTED),
                ], spacing=4, expand=True),
            ], spacing=16),
        ]
        if not activo:
            cabecera.append(ft.Container(ft.Column([
                ft.Text(f"Dado de baja el {e['fecha_baja']:%d/%m/%Y}" if e["fecha_baja"] else "Dado de baja",
                        size=13, weight=ft.FontWeight.W_500, color="#B91C1C"),
                ft.Text(e["motivo_baja"] or "Sin motivo cargado", size=12, color="#7F1D1D"),
                ft.Text("No puede entrar al sistema.", size=11.5, color="#7F1D1D"),
            ], spacing=2), bgcolor="#FEF2F2", border=ft.border.all(1, "#FECACA"), border_radius=12, padding=12))
        return ft.Container(ft.Column(cabecera + [
            ft.Container(ft.Row([tab("datos", "Datos"), tab("sueldo", "Sueldo"), tab("actividad", "Actividad")], spacing=0),
                         border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)), margin=ft.margin.only(top=6)),
            contenido,
        ], spacing=12), width=500, bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=18,
            padding=ft.padding.symmetric(horizontal=24, vertical=18))

    def _cambiar_pestana(self, clave):
        self.pestana = clave
        self._render()

    # ── Datos ──
    def _tab_datos(self, e: dict) -> ft.Column:
        editable = self._puede_editar(e)
        yo = e["id_empleado"] == self.yo

        def campo(etiqueta, valor, **k):
            return ft.TextField(label=etiqueta, value=valor or "", dense=True, border_radius=10, border_color=GRAY_LIGHT,
                                text_size=13, disabled=not editable, expand=k.pop("expand", True), error_max_lines=2, **k)
        nombre = campo("Nombre *", e["nombre"], input_filter=val.NOMBRE, max_length=val.MAX_NOMBRE)
        apellido = campo("Apellido *", e["apellido"], input_filter=val.NOMBRE, max_length=val.MAX_NOMBRE)
        dni = campo("DNI *", e["dni"], keyboard_type=ft.KeyboardType.NUMBER, input_filter=val.SOLO_DIGITOS, max_length=8)
        telefono = campo("Teléfono", e["telefono"], keyboard_type=ft.KeyboardType.PHONE, input_filter=val.TELEFONO,
                         max_length=20)
        email = campo("Email *", e["email"], keyboard_type=ft.KeyboardType.EMAIL, input_filter=val.EMAIL,
                      max_length=val.MAX_EMAIL)
        direccion = campo("Dirección", e["direccion"], max_length=val.MAX_DIRECCION)
        roles = [(k, v) for k, v in repo.ROLES.items() if self.rol_actual == "dueno" or k != "dueno"]
        rol = ft.Dropdown(label="Rol", value=e["rol"], dense=True, border_radius=10, border_color=GRAY_LIGHT, text_size=13,
                          options=[ft.DropdownOption(key=k, text=v) for k, v in roles], expand=True,
                          disabled=not editable or yo)
        turno = ft.Dropdown(label="Turno", value=e["turno"], dense=True, border_radius=10, border_color=GRAY_LIGHT,
                            text_size=13, options=[ft.DropdownOption(key=t, text=t) for t in repo.TURNOS], expand=True,
                            disabled=not editable)
        especialidad = campo("Especialidad", e["especialidad"], hint_text="Ej.: Musculación, Nutrición deportiva",
                             max_length=120)
        ingreso = campo("Fecha de ingreso *", f"{e['ingreso']:%d/%m/%Y}" if e["ingreso"] else "", hint_text="dd/mm/aaaa",
                        input_filter=val.FECHA, max_length=10)
        sueldo = campo("Sueldo mensual", f"{e['sueldo']:.0f}" if e["sueldo"] else "", prefix="$ ",
                       keyboard_type=ft.KeyboardType.NUMBER, input_filter=val.MONTO, max_length=15)
        fila_esp = ft.Row([especialidad], visible=e["rol"] in repo.CON_ESPECIALIDAD)

        def cambio_rol(ev):
            fila_esp.visible = rol.value in repo.CON_ESPECIALIDAD
            fila_esp.update()
        rol.on_select = cambio_rol
        error = ft.Text("", size=12, color=RED)

        campos = {"apellido": apellido, "nombre": nombre, "DNI": dni, "email": email, "teléfono": telefono,
                  "dirección": direccion, "especialidad": especialidad, "ingreso": ingreso, "sueldo": sueldo}

        def guardar(ev):
            reglas = _reglas_empleado(nombre, apellido, dni, telefono, email, sueldo, ingreso, e["id_empleado"],
                                      dni_obligatorio=bool(e["dni"]))
            if not val.revisar_varios(reglas):
                error.value = "Revisá los campos marcados en rojo."
                self.page.update()
                return
            try:
                f = val.fecha(ingreso.value, "la fecha de ingreso")
                repo.actualizar(e["id_empleado"], {
                    "nombre": nombre.value, "apellido": apellido.value, "dni": dni.value, "email": email.value,
                    "telefono": telefono.value, "direccion": direccion.value, "rol": rol.value, "turno": turno.value,
                    "especialidad": especialidad.value, "sueldo": sueldo.value, "ingreso": f}, self.firma)
            except ValueError as ex:
                val.error_en_campo(str(ex), campos, error)
                self.page.update()
                return
            self._avisar(f"✓ Datos de {nombre.value.strip()} guardados")
            self._recargar()

        acciones = []
        if editable:
            acciones.append(ft.Container(ft.Text("Guardar cambios", size=14, weight=ft.FontWeight.W_500, color=DARK),
                                         bgcolor=GOLD, border_radius=12, height=44, alignment=ft.Alignment.CENTER,
                                         on_click=guardar, ink=True))
            otras = [ft.OutlinedButton("Restablecer contraseña", icon=ft.Icons.KEY_OUTLINED,
                                       on_click=lambda ev: self._confirmar_password(e))]
            if not yo:
                otras.append(ft.OutlinedButton("Dar de baja", icon=ft.Icons.PERSON_OFF_OUTLINED,
                                               style=ft.ButtonStyle(color=RED), on_click=lambda ev: self._dialogo_baja(e))
                             if e["estado"] == "activo" else
                             ft.OutlinedButton("Reactivar", icon=ft.Icons.PERSON_ADD_ALT,
                                               style=ft.ButtonStyle(color=GREEN), on_click=lambda ev: self._reactivar(e)))
            acciones.append(ft.Row(otras, spacing=10, wrap=True))
        else:
            acciones.append(ft.Text("Solo el dueño puede modificar al dueño.", size=12, color=TEXT_MUTED))
        if yo:
            acciones.append(ft.Text("Es tu propio usuario: no podés cambiarte el rol ni darte de baja.",
                                    size=11.5, color=TEXT_MUTED))
        return ft.Column([
            ft.Container(height=4),
            ft.Row([nombre, apellido], spacing=10), ft.Row([dni, telefono], spacing=10),
            ft.Row([email]), ft.Row([direccion]), ft.Row([rol, turno], spacing=10), fila_esp,
            ft.Row([ingreso, sueldo], spacing=10),
            error, *acciones,
        ], spacing=10)

    # ── Sueldo ──
    def _tab_sueldo(self, e: dict) -> ft.Column:
        try:
            pagos, historial = repo.pagos(e["id_empleado"]), repo.historial_sueldo(e["id_empleado"])
        except Exception as ex:
            return ft.Column([ft.Text(f"⚠️ {ex}", color=RED)])
        mes = repo.mes_actual()
        sueldo_mes = next((p for p in pagos if p["periodo"] == mes and p["concepto"] == "Sueldo"
                           and p["estado"] == "pagado"), None)
        extras_mes = sum(p["monto"] for p in pagos if p["periodo"] == mes and p["concepto"] != "Sueldo"
                         and p["estado"] == "pagado")
        anio = sum(p["monto"] for p in pagos if p["periodo"].year == mes.year and p["estado"] == "pagado")
        nombre_mes = MESES[mes.month - 1]
        if e["estado"] != "activo":
            estado = ft.Text("Está dado de baja: no se le registran pagos nuevos.", size=12.5, color=TEXT_MUTED)
        elif not e["sueldo"]:
            estado = ft.Text("Todavía no tiene sueldo cargado. Cargalo en la pestaña Datos.", size=12.5, color=TEXT_MUTED)
        elif sueldo_mes:
            estado = ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color="#15803D", size=26), ft.Column([
                ft.Text(f"Sueldo de {nombre_mes} pagado", size=14, weight=ft.FontWeight.W_600, color="#15803D"),
                ft.Text(f"{_plata(sueldo_mes['monto'])} · {sueldo_mes['medio']} · "
                        f"{sueldo_mes['fecha_pago'].astimezone():%d/%m/%Y}", size=12, color=TEXT_MUTED)], spacing=0)],
                spacing=10)
        else:
            estado = ft.Row([ft.Icon(ft.Icons.SCHEDULE, color="#B45309", size=26), ft.Column([
                ft.Text(f"Falta pagar el sueldo de {nombre_mes}", size=14, weight=ft.FontWeight.W_600, color="#B45309"),
                ft.Text(f"{_plata(e['sueldo'])}" + (f" · ya cobró {_plata(extras_mes)} en adelantos/bonos" if extras_mes
                                                     else ""), size=12, color=TEXT_MUTED)], spacing=0, expand=True)],
                spacing=10)
        boton = ft.Container(ft.Row([ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=17, color=DARK),
                                     ft.Text("Registrar pago", size=13.5, weight=ft.FontWeight.W_500, color=DARK)],
                                    spacing=8, tight=True),
                             bgcolor=GOLD, border_radius=12, padding=ft.padding.symmetric(horizontal=16, vertical=10),
                             ink=True, on_click=lambda ev: self._dialogo_pago(e)) if e["estado"] == "activo" else None
        ultimo_aumento = next((h for h in historial if h["sueldo_anterior"]), None)
        datos = [("Sueldo mensual", _plata(e["sueldo"])), (f"Cobrado en {mes.year}", _plata(anio))]
        if ultimo_aumento:
            pct = (ultimo_aumento["sueldo_nuevo"] - ultimo_aumento["sueldo_anterior"]) / ultimo_aumento["sueldo_anterior"] * 100
            datos.append(("Último cambio", f"{pct:+.0f}% · {ultimo_aumento['fecha'].astimezone():%m/%Y}"))
        cuadritos = ft.Row([ft.Container(ft.Column([ft.Text(t, size=11, color=TEXT_MUTED),
                                                    ft.Text(v, size=15, weight=ft.FontWeight.W_600, color=DARK)], spacing=2),
                                         bgcolor="#FBFAF6", border_radius=12, padding=12, expand=True) for t, v in datos],
                           spacing=8)
        filas_pagos = []
        for p in pagos[:12]:
            anulado = p["estado"] != "pagado"
            color = {"Sueldo": ("#DCFCE7", "#15803D"), "Adelanto": ("#FEF3C7", "#B45309"),
                     "Bono": ("#DBEAFE", "#1D4ED8")}[p["concepto"]]
            filas_pagos.append(ft.Container(ft.Row([
                _chip(p["concepto"], *color),
                ft.Column([ft.Text(f"{MESES[p['periodo'].month - 1].capitalize()} {p['periodo'].year}", size=12.5,
                                   color=DARK, weight=ft.FontWeight.W_500),
                           ft.Text(f"{p['fecha_pago'].astimezone():%d/%m/%Y} · {p['medio']}" +
                                   (f" · {p['nota']}" if p["nota"] else ""), size=11, color=TEXT_MUTED, max_lines=1,
                                   overflow=ft.TextOverflow.ELLIPSIS)], spacing=0, expand=True),
                ft.Text(_plata(p["monto"]) if not anulado else "Anulado", size=13, weight=ft.FontWeight.W_600,
                        color=TEXT_MUTED if anulado else DARK),
                ft.IconButton(ft.Icons.BLOCK, icon_size=16, icon_color=TEXT_MUTED, tooltip="Anular este pago",
                              on_click=lambda ev, x=p: self._confirmar_anular(e, x), disabled=anulado),
            ], spacing=10), padding=ft.padding.symmetric(vertical=6), opacity=0.55 if anulado else 1,
                border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT))))
        filas_hist = [ft.Row([
            ft.Text(f"{h['fecha'].astimezone():%d/%m/%Y}", size=12, color=TEXT_MUTED, width=80),
            ft.Text(f"{_plata(h['sueldo_anterior'])} → {_plata(h['sueldo_nuevo'])}" if h["sueldo_anterior"]
                    else f"Sueldo inicial {_plata(h['sueldo_nuevo'])}", size=12.5, color=DARK, expand=True),
            ft.Text(f"{(h['sueldo_nuevo'] - h['sueldo_anterior']) / h['sueldo_anterior'] * 100:+.0f}%"
                    if h["sueldo_anterior"] else "", size=12, weight=ft.FontWeight.W_600, color="#15803D"),
        ], spacing=8) for h in historial[:6]]
        return ft.Column([
            ft.Container(height=4),
            ft.Container(ft.Column([estado] + ([boton] if boton else []), spacing=12),
                         bgcolor="#FBFAF6", border_radius=14, padding=14),
            cuadritos,
            ft.Text("Pagos", size=14, weight=ft.FontWeight.W_600, color=DARK),
            *(filas_pagos or [ft.Text("Todavía no se le registró ningún pago.", size=12, color=TEXT_MUTED)]),
            ft.Text("Cambios de sueldo", size=14, weight=ft.FontWeight.W_600, color=DARK),
            *(filas_hist or [ft.Text("Sin cambios registrados.", size=12, color=TEXT_MUTED)]),
        ], spacing=10)

    # ── Actividad ──
    def _tab_actividad(self, e: dict) -> ft.Column:
        try:
            a = repo.actividad(e)
        except Exception as ex:
            return ft.Column([ft.Text(f"⚠️ {ex}", color=RED)])
        rol = e["rol"]
        todos = rol == "dueno"

        def dato(icono, titulo, valor, detalle="", alerta=False):
            fondo, color = ("#FEE2E2", "#B91C1C") if alerta else (GOLD_BG2, GOLD_DARK)
            return ft.Container(ft.Row([
                ft.Container(ft.Icon(icono, size=19, color=color), width=38, height=38, border_radius=19, bgcolor=fondo,
                             alignment=ft.Alignment.CENTER),
                ft.Column([ft.Text(titulo, size=12, color=TEXT_MUTED),
                           ft.Text(valor, size=16, weight=ft.FontWeight.W_600, color=DARK)] +
                          ([ft.Text(detalle, size=11, color=TEXT_MUTED)] if detalle else []), spacing=0, expand=True),
            ], spacing=12), bgcolor="#FBFAF6", border_radius=12, padding=12, col={"xs": 12, "md": 6})

        items = [
            dato(ft.Icons.LOGIN, "Último ingreso al sistema", _hace(a["ultimo"]),
                 f"{a['ultimo'].astimezone():%d/%m/%Y %H:%M}" if a["ultimo"] else ""),
            dato(ft.Icons.EVENT_AVAILABLE, "Días que entró (30 días)", str(a["dias_30"]), f"{a['ingresos_30']} ingresos"),
            dato(ft.Icons.GPP_MAYBE_OUTLINED, "Contraseña mal escrita (30 días)", str(a["fallidos_30"]),
                 "Puede ser un intento de entrar con su usuario" if a["fallidos_30"] >= 3 else "",
                 alerta=a["fallidos_30"] >= 3),
        ]
        if todos or rol == "entrenador":
            items += [dato(ft.Icons.FORMAT_LIST_BULLETED, "Rutinas creadas", str(a["rutinas"]),
                           f"{a['socios_rutina']} socios con una rutina suya vigente"),
                      dato(ft.Icons.EMOJI_EVENTS_OUTLINED, "Marcas revisadas", str(a["marcas"] + a["marcas_rechazadas"]),
                           f"{a['marcas']} verificadas · {a['marcas_rechazadas']} rechazadas")]
        if todos or rol == "nutricionista":
            items.append(dato(ft.Icons.RESTAURANT, "Dietas asignadas", str(a["dietas"])))
        if todos or rol in ("admin", "recepcionista"):
            items.append(dato(ft.Icons.CARD_MEMBERSHIP, "Membresías asignadas o cobradas", str(a["membresias"])))
        items.append(dato(ft.Icons.AUTO_AWESOME_OUTLINED, "Consultas a Argos (30 días)", str(a["argos_30"])))
        return ft.Column([
            ft.Container(height=4),
            ft.Text("Lo que hizo en el sistema, según su rol.", size=12, color=TEXT_MUTED),
            ft.ResponsiveRow(items, spacing=8, run_spacing=8),
        ], spacing=10)

    # ══════════════ DIÁLOGOS ══════════════
    def _dialogo(self, titulo, contenido, acciones, ancho=440):
        self.page.show_dialog(ft.AlertDialog(
            modal=True, title=ft.Text(titulo, weight=ft.FontWeight.W_600, font_family="Poppins"),
            content=ft.Column(contenido, spacing=12, tight=True, width=ancho), actions=acciones,
            actions_alignment=ft.MainAxisAlignment.END))

    def _boton_ok(self, texto, al_tocar, color=GOLD):
        return ft.FilledButton(texto, on_click=al_tocar, style=ft.ButtonStyle(bgcolor=color, color=DARK if color == GOLD else WHITE))

    def _cancelar(self):
        return ft.TextButton("Cancelar", on_click=lambda ev: self.page.pop_dialog())

    def _dialogo_alta(self):
        def campo(etiqueta, **k):
            return ft.TextField(label=etiqueta, dense=True, border_radius=10, text_size=13, expand=True, error_max_lines=2,
                                counter=ft.Text(""), **k)
        nombre = campo("Nombre *", input_filter=val.NOMBRE, max_length=val.MAX_NOMBRE,
                       capitalization=ft.TextCapitalization.WORDS)
        apellido = campo("Apellido *", input_filter=val.NOMBRE, max_length=val.MAX_NOMBRE,
                         capitalization=ft.TextCapitalization.WORDS)
        dni = campo("DNI *", input_filter=val.SOLO_DIGITOS, max_length=8, keyboard_type=ft.KeyboardType.NUMBER,
                    hint_text="Solo números")
        telefono = campo("Teléfono", input_filter=val.TELEFONO, max_length=20, keyboard_type=ft.KeyboardType.PHONE)
        email = campo("Email *", input_filter=val.EMAIL, max_length=val.MAX_EMAIL, keyboard_type=ft.KeyboardType.EMAIL)
        usuario = campo("Usuario para entrar *", input_filter=val.USUARIO, max_length=30)
        roles = [(k, v) for k, v in repo.ROLES.items() if self.rol_actual == "dueno" or k != "dueno"]
        rol = ft.Dropdown(label="Rol *", dense=True, border_radius=10, text_size=13, expand=True,
                          options=[ft.DropdownOption(key=k, text=v) for k, v in roles])
        turno = ft.Dropdown(label="Turno", dense=True, border_radius=10, text_size=13, expand=True,
                            options=[ft.DropdownOption(key=t, text=t) for t in repo.TURNOS])
        sueldo = campo("Sueldo mensual", prefix="$ ", keyboard_type=ft.KeyboardType.NUMBER, input_filter=val.MONTO,
                       max_length=15)
        ingreso = campo("Fecha de ingreso *", value=date.today().strftime("%d/%m/%Y"), input_filter=val.FECHA,
                        max_length=10, hint_text="dd/mm/aaaa")
        especialidad = campo("Especialidad", max_length=120)
        fila_esp = ft.Row([especialidad], visible=False)
        error = ft.Text("", size=12, color=RED)

        def sugerir(ev):
            if not usuario.value and nombre.value and apellido.value:
                try:
                    usuario.value = repo.sugerir_usuario(nombre.value.strip(), apellido.value.strip())
                    usuario.update()
                except Exception:
                    pass
        apellido.on_blur = sugerir

        def cambio_rol(ev):
            fila_esp.visible = rol.value in repo.CON_ESPECIALIDAD
            fila_esp.update()
        rol.on_select = cambio_rol

        campos = {"apellido": apellido, "nombre": nombre, "DNI": dni, "email": email, "teléfono": telefono,
                  "usuario": usuario, "especialidad": especialidad, "ingreso": ingreso, "sueldo": sueldo}

        def crear(ev):
            reglas = _reglas_empleado(nombre, apellido, dni, telefono, email, sueldo, ingreso, usuario=usuario)
            todo_bien = val.revisar_varios(reglas)
            if not rol.value:
                error.value = "Elegí el rol."
                todo_bien = False
            elif not todo_bien:
                error.value = "Revisá los campos marcados en rojo."
            if not todo_bien:
                self.page.update()
                return
            error.value = ""
            try:
                f = val.fecha(ingreso.value, "la fecha de ingreso")
                nuevo, password = repo.crear({
                    "nombre": nombre.value, "apellido": apellido.value, "dni": dni.value, "email": email.value,
                    "telefono": telefono.value, "direccion": None, "rol": rol.value, "turno": turno.value,
                    "especialidad": especialidad.value, "sueldo": sueldo.value, "ingreso": f}, usuario.value, self.firma)
            except ValueError as ex:
                val.error_en_campo(str(ex), campos, error)
                self.page.update()
                return
            self.page.pop_dialog()
            self.sel, self.pestana, self.filtro = nuevo, "datos", "activos"
            self._avisar(f"✓ {nombre.value.strip()} {apellido.value.strip()} dado de alta")
            self._recargar()
            self._mostrar_credenciales(f"{nombre.value.strip()} {apellido.value.strip()}",
                                       usuario.value.strip().lower(), password, nuevo=True)

        self._dialogo("Agregar empleado", [
            ft.Row([nombre, apellido], spacing=10), ft.Row([dni, telefono], spacing=10), ft.Row([email]),
            ft.Row([rol, turno], spacing=10), fila_esp, ft.Row([sueldo, ingreso], spacing=10), ft.Row([usuario]),
            ft.Text("La contraseña se genera sola y se muestra una única vez al crear el usuario.",
                    size=11.5, color=TEXT_MUTED), error,
        ], [self._cancelar(), self._boton_ok("Dar de alta", crear)], ancho=480)

    def _mostrar_credenciales(self, nombre, usuario, password, nuevo=False):
        async def copiar(ev):
            await self.page.clipboard.set(f"Usuario: {usuario}\nContraseña: {password}")
            aviso.value = "✓ Copiado"
            aviso.update()
        aviso = ft.Text("", size=12, color=GREEN)
        demo = usuario in {u["usuario"] for u in empleados_credenciales.USUARIOS_DEMO}
        self._dialogo("Datos para entrar al sistema", [
            ft.Text(f"{'Usuario creado para' if nuevo else 'Nueva contraseña de'} {nombre}. Pasáselos en persona: "
                    "la contraseña no se vuelve a mostrar.", size=12.5, color=TEXT_MUTED),
            ft.Container(ft.Column([
                ft.Row([ft.Text("Usuario", size=12, color=TEXT_MUTED, width=90),
                        ft.Text(usuario, size=15, weight=ft.FontWeight.W_600, selectable=True)]),
                ft.Row([ft.Text("Contraseña", size=12, color=TEXT_MUTED, width=90),
                        ft.Text(password, size=15, weight=ft.FontWeight.W_600, selectable=True,
                                font_family="Consolas")]),
            ], spacing=8), bgcolor="#FBFAF6", border_radius=12, padding=14),
            *([ft.Text("Ojo: es un usuario de demostración y el panel del login va a seguir mostrando la contraseña "
                       "vieja.", size=11.5, color="#B45309")] if demo else []),
            aviso,
        ], [ft.TextButton("Copiar", icon=ft.Icons.CONTENT_COPY, on_click=copiar),
            self._boton_ok("Listo", lambda ev: self.page.pop_dialog())])

    def _confirmar_password(self, e):
        def si(ev):
            self.page.pop_dialog()
            try:
                password = repo.restablecer_password(e["id_empleado"])
            except Exception as ex:
                self._avisar(f"No se pudo cambiar la contraseña: {ex}", RED)
                self._render()
                return
            self._mostrar_credenciales(e["nombre_completo"], e["usuario"], password)
        self._dialogo("¿Restablecer la contraseña?", [
            ft.Text(f"Se genera una contraseña nueva para {e['nombre_completo']} y la actual deja de funcionar.",
                    size=13, color=TEXT_MUTED)], [self._cancelar(), self._boton_ok("Restablecer", si)])

    def _dialogo_baja(self, e):
        fecha = ft.TextField(label="Fecha de baja *", value=date.today().strftime("%d/%m/%Y"), dense=True,
                             border_radius=10, text_size=13, input_filter=val.FECHA, max_length=10, hint_text="dd/mm/aaaa")
        motivo = ft.TextField(label="Motivo *", dense=True, border_radius=10, text_size=13, multiline=True,
                              min_lines=2, max_length=255)
        error = ft.Text("", size=12, color=RED)

        def si(ev):
            try:
                f = val.fecha(fecha.value, "la fecha de baja")
                repo.dar_de_baja(e["id_empleado"], f, motivo.value)
            except ValueError as ex:
                val.error_en_campo(str(ex), {"fecha": fecha, "motivo": motivo}, error)
                self.page.update()
                return
            self.page.pop_dialog()
            self._avisar(f"{e['nombre_completo']} quedó dado de baja", GOLD_DARK)
            self._recargar()
        self._dialogo(f"Dar de baja a {e['nombre_completo']}", [
            ft.Text("No se borra nada: queda en el historial con sus pagos y su actividad, pero ya no puede entrar "
                    "al sistema. Se puede reactivar.", size=12.5, color=TEXT_MUTED),
            fecha, motivo, error], [self._cancelar(), self._boton_ok("Dar de baja", si, RED)])

    def _reactivar(self, e):
        try:
            repo.reactivar(e["id_empleado"])
            self._avisar(f"✓ {e['nombre_completo']} reactivado: ya puede entrar al sistema")
        except Exception as ex:
            self._avisar(f"No se pudo reactivar: {ex}", RED)
        self._recargar()

    def _dialogo_pago(self, e):
        hoy = repo.mes_actual()
        meses = []
        a, m = hoy.year, hoy.month
        for _ in range(6):
            meses.append(date(a, m, 1))
            a, m = (a - 1, 12) if m == 1 else (a, m - 1)
        concepto = ft.Dropdown(label="Concepto", value="Sueldo", dense=True, border_radius=10, text_size=13, expand=True,
                               options=[ft.DropdownOption(key=c, text=c) for c in repo.CONCEPTOS])
        periodo = ft.Dropdown(label="Mes que corresponde", value=hoy.isoformat(), dense=True, border_radius=10,
                              text_size=13, expand=True,
                              options=[ft.DropdownOption(key=p.isoformat(), text=f"{MESES[p.month - 1].capitalize()} {p.year}")
                                       for p in meses])
        monto = ft.TextField(label="Monto *", value=f"{e['sueldo']:.0f}" if e["sueldo"] else "", prefix="$ ", dense=True,
                             border_radius=10, text_size=13, expand=True, keyboard_type=ft.KeyboardType.NUMBER,
                             input_filter=val.MONTO, max_length=15)
        medio = ft.Dropdown(label="Cómo se pagó", value="Transferencia", dense=True, border_radius=10, text_size=13,
                            expand=True, options=[ft.DropdownOption(key=x, text=x) for x in repo.MEDIOS])
        nota = ft.TextField(label="Nota (opcional)", dense=True, border_radius=10, text_size=13, max_length=255)
        error = ft.Text("", size=12, color=RED)

        def cambio_concepto(ev):
            if concepto.value == "Sueldo" and e["sueldo"]:
                monto.value = f"{e['sueldo']:.0f}"
                monto.update()
        concepto.on_select = cambio_concepto

        def guardar(ev):
            try:
                valor = val.monto(monto.value, maximo=repo.SUELDO_MAXIMO)
                repo.registrar_pago(e["id_empleado"], date.fromisoformat(periodo.value), concepto.value, valor,
                                    medio.value, nota.value, self.firma)
            except ValueError as ex:
                val.error_en_campo(str(ex), {"monto": monto, "nota": nota}, error)
                self.page.update()
                return
            except Exception as ex:
                error.value = f"No se pudo registrar: {ex}"
                error.update()
                return
            self.page.pop_dialog()
            self._avisar(f"✓ {concepto.value} de {e['nombre_completo']} registrado ({_plata(valor)})")
            self.sel, self.pestana = e["id_empleado"], "sueldo"
            self._recargar()
        self._dialogo(f"Registrar pago a {e['nombre_completo']}", [
            ft.Row([concepto, periodo], spacing=10), ft.Row([monto, medio], spacing=10), nota, error,
        ], [self._cancelar(), self._boton_ok("Registrar", guardar)])

    def _confirmar_anular(self, e, p):
        def si(ev):
            self.page.pop_dialog()
            try:
                repo.anular_pago(p["id_liquidacion"])
                self._avisar("Pago anulado (queda en el historial)", GOLD_DARK)
            except Exception as ex:
                self._avisar(f"No se pudo anular: {ex}", RED)
            self._recargar()
        self._dialogo("¿Anular este pago?", [
            ft.Text(f"{p['concepto']} de {MESES[p['periodo'].month - 1]} por {_plata(p['monto'])}. Deja de contar como "
                    "pagado pero queda en el historial.", size=13, color=TEXT_MUTED)],
            [self._cancelar(), self._boton_ok("Anular", si, RED)])


def build_personal(page: ft.Page = None, rol: str = "dueno") -> ft.Column:
    return PersonalView(page, rol).build()
