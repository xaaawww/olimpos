import urllib.parse

import flet as ft
from theme import *
from components import stat_card, section_card, status_pill, avatar, action_button, page_header
import auth_repo
import socios_repo


def _link_whatsapp(telefono: str, nombre: str, email: str, password: str) -> str:
    """Arma un enlace wa.me con el mensaje ya redactado — no manda nada solo,
    el empleado lo confirma y lo envía él mismo al tocar "Enviar" en
    WhatsApp. No hay ninguna cuenta de SMS/WhatsApp Business conectada al
    proyecto; esto no tiene costo ni depende de un servicio externo."""
    solo_digitos = "".join(c for c in telefono if c.isdigit())
    mensaje = (
        f"Hola {nombre}! Ya está listo tu acceso a la app OlimpΩs.\n\n"
        f"Email: {email}\n"
        f"Contraseña: {password}\n\n"
        f"La primera vez que entres te va a pedir que la cambies por una que prefieras."
    )
    return f"https://wa.me/{solo_digitos}?text={urllib.parse.quote(mensaje)}"


AVATAR_VARIANTES = ["gold", "blue", "red", "purple", "green", "dark"]
PILL_POR_ESTADO = {"Activo": "active", "Plan vencido": "debt", "Sin plan": "suspended", "Inactivo": "inactive"}


def _iniciales(nombre: str) -> str:
    partes = [p for p in (nombre or "").split() if p]
    return "".join(p[0] for p in partes[:2]).upper() or "?"


def _dialogo_perfil(page: ft.Page, s: dict):
    def fila(etiqueta, valor):
        return ft.Row([
            ft.Text(etiqueta, size=12, weight=ft.FontWeight.W_600, color=TEXT_MUTED, width=150),
            ft.Text(str(valor) if valor not in (None, "") else "—", size=12.5, color=DARK, selectable=True, expand=True),
        ], spacing=8)

    def titulo(texto):
        return ft.Text(texto, size=11, weight=ft.FontWeight.W_600, color=GOLD_DARK, font_family="Poppins")

    acceso = "No tiene cuenta en la app"
    if s["tiene_app"]:
        acceso = "Pendiente: debe cambiar la contraseña temporal" if s["debe_cambiar_password"] else "Activo"

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            _avatar_redondo(s["nombre"], s["id_socio"], 46),
            ft.Column([
                ft.Text(s["nombre"], weight=ft.FontWeight.W_600, font_family="Poppins", size=17),
                ft.Text(f"Socio #{s['id_socio']:04d}", size=11.5, color=TEXT_MUTED),
            ], spacing=0),
            status_pill(s["estado"], PILL_POR_ESTADO[s["estado"]]),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        content=ft.Column([
            titulo("DATOS PERSONALES"),
            fila("DNI", s["dni"]),
            fila("Email", s["email"]),
            fila("Teléfono", s["telefono"]),
            fila("Dirección", s["direccion"]),
            fila("Sexo", s["sexo"]),
            fila("Fecha de nacimiento", socios_repo.fecha_corta(s["fecha_nacimiento"]) if s["fecha_nacimiento"] else None),
            fila("Edad", s["edad"]),
            fila("Registrado el", socios_repo.fecha_corta(s["registro"])),
            ft.Divider(height=10, color=GRAY_LIGHT),
            titulo("MEMBRESÍA"),
            fila("Plan", s["plan"] or "Sin plan asignado"),
            fila("Desde", socios_repo.fecha_corta(s["plan_inicio"]) if s["plan"] else None),
            fila("Vence", socios_repo.fecha_corta(s["vencimiento"]) if s["plan"] else None),
            fila("Asignado por", s["asignado_por"]),
            ft.Divider(height=10, color=GRAY_LIGHT),
            titulo("ENTRENAMIENTO"),
            fila("Objetivo", (s["objetivo"] or "").capitalize() or None),
            fila("Nivel", s["nivel_experiencia"]),
            fila("Último peso", f"{s['peso']:g} kg" if s["peso"] else None),
            fila("Días entrenados", s["dias_entrenados"]),
            fila("Último entrenamiento", socios_repo.fecha_corta(s["ultimo_entrenamiento"]) if s["ultimo_entrenamiento"] else "Nunca"),
            fila("Marcas verificadas", s["marcas_verificadas"]),
            fila("Acceso a la app", acceso),
        ], tight=True, spacing=6, width=460, scroll=ft.ScrollMode.AUTO),
        actions=[action_button("Cerrar", "gold", on_click=lambda e: page.pop_dialog())],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


# ══════════════ Crear acceso a la app (Firebase Auth) ══════════════
# El socio no se registra solo: acá un empleado le crea la cuenta y
# después le pasa el email/contraseña en persona o por WhatsApp — la app
# móvil ya no tiene forma de "crear cuenta" (ver LoginScreen.kt).

def _dialogo_credenciales(page: ft.Page, nombre: str, email: str, password: str, telefono: str) -> ft.AlertDialog:
    def _enviar_whatsapp(e):
        page.launch_url(_link_whatsapp(telefono, nombre, email, password))

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("✅ Acceso creado", weight=ft.FontWeight.W_600, font_family="Poppins"),
        content=ft.Column([
            ft.Text(f"Pasale estos datos a {nombre} para que entre a la app OlimpΩs:",
                    size=12.5, color=TEXT_MUTED),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Email:", size=12, weight=ft.FontWeight.W_600, color=DARK),
                        ft.Text(email, size=12, selectable=True, color=DARK),
                    ], spacing=6),
                    ft.Row([
                        ft.Text("Contraseña:", size=12, weight=ft.FontWeight.W_600, color=DARK),
                        ft.Text(password, size=12, selectable=True, color=DARK),
                    ], spacing=6),
                ], spacing=6),
                bgcolor=CREAM, border_radius=10, padding=14,
            ),
            ft.Text(
                "Guardá esto ahora: por seguridad, Firebase no permite volver a ver "
                "esta contraseña más adelante.",
                size=11, color=RED, weight=ft.FontWeight.W_500,
            ),
        ], tight=True, spacing=10, width=360),
        actions=[
            action_button("📲 Enviar por WhatsApp", "outline", on_click=_enviar_whatsapp),
            action_button("Listo", "gold", on_click=lambda e: page.pop_dialog()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return dialog


def _dialogo_nuevo_socio(page: ft.Page, on_creado=None):
    campo_nombre = ft.TextField(label="Nombre y apellido", width=360, autofocus=True)
    campo_dni = ft.TextField(label="DNI", width=360, keyboard_type=ft.KeyboardType.NUMBER)
    campo_telefono = ft.TextField(label="Teléfono (con código de área)", width=360,
                                   keyboard_type=ft.KeyboardType.PHONE, hint_text="Ej: 5491122334455")
    campo_email = ft.TextField(label="Email", width=360, keyboard_type=ft.KeyboardType.EMAIL)
    campo_password = ft.TextField(label="Contraseña", width=270, value=auth_repo.generar_password())
    error_text = ft.Text("", size=12, color=RED, weight=ft.FontWeight.W_500, visible=False)

    def _regenerar(e):
        campo_password.value = auth_repo.generar_password()
        page.update()

    def _crear(e):
        nombre = (campo_nombre.value or "").strip()
        dni = (campo_dni.value or "").strip()
        telefono = (campo_telefono.value or "").strip()
        email = (campo_email.value or "").strip()
        password = (campo_password.value or "").strip()
        if not nombre or not dni or not telefono or not email or not password:
            error_text.value = "Completá nombre, DNI, teléfono, email y contraseña."
            error_text.visible = True
            page.update()
            return
        ok, resultado = auth_repo.crear_acceso_socio(nombre, email, password, dni)
        if not ok:
            error_text.value = resultado
            error_text.visible = True
            page.update()
            return
        page.pop_dialog()
        if on_creado:
            on_creado()
        page.show_dialog(_dialogo_credenciales(page, nombre, email, password, telefono))

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Crear acceso a la app", weight=ft.FontWeight.W_600, font_family="Poppins"),
        content=ft.Column([
            ft.Text(
                "Se crea una cuenta real (Firebase) para que este socio entre a la "
                "app OlimpΩs. El teléfono es para mandarle el email y la contraseña "
                "por WhatsApp apenas se cree el acceso.",
                size=12, color=TEXT_MUTED,
            ),
            campo_nombre,
            campo_dni,
            campo_telefono,
            campo_email,
            ft.Row([campo_password, action_button("🎲 Generar", "outline", on_click=_regenerar)],
                   spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            error_text,
        ], tight=True, spacing=12, width=380),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
            action_button("Crear acceso", "gold", on_click=_crear),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


COLORES_AVATAR = [  # fondo, letra
    ("#FEF3C7", "#A16207"), ("#DCFCE7", "#15803D"), ("#FCE7F3", "#BE185D"),
    ("#EDE9FE", "#6D28D9"), ("#DBEAFE", "#1D4ED8"), ("#FFEDD5", "#C2410C"),
]


def _avatar_redondo(nombre: str, id_socio: int, tam: int = 42) -> ft.Container:
    fondo, letra = COLORES_AVATAR[id_socio % len(COLORES_AVATAR)]
    return ft.Container(
        ft.Text(_iniciales(nombre), size=tam * 0.36, weight=ft.FontWeight.W_600, color=letra),
        width=tam, height=tam, border_radius=tam / 2, bgcolor=fondo, alignment=ft.Alignment.CENTER,
    )


def _tarjeta_resumen(icono, color_icono: str, fondo_icono: str, titulo: str, valor: int,
                     etiqueta: str, fondo_etq: str, color_etq: str) -> ft.Container:
    return ft.Container(
        content=ft.Row([
            ft.Container(ft.Icon(icono, size=24, color=color_icono), width=52, height=52,
                         border_radius=26, bgcolor=fondo_icono, alignment=ft.Alignment.CENTER),
            ft.Column([
                ft.Text(titulo.upper(), size=11, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
                ft.Text(str(valor), size=28, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                        style=ft.TextStyle(height=1.1)),
                ft.Container(ft.Text(etiqueta, size=11, weight=ft.FontWeight.W_500, color=color_etq),
                             bgcolor=fondo_etq, border_radius=20, padding=ft.padding.symmetric(horizontal=10, vertical=3)),
            ], spacing=4, tight=True),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
        bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16,
        padding=ft.padding.symmetric(horizontal=18, vertical=20), expand=True,
    )


def _confirmar_desactivar(page: ft.Page, s: dict, al_terminar):
    def _desactivar(e):
        page.pop_dialog()
        try:
            uid = socios_repo.uid_de(s["id_socio"])
            auth_repo.desactivar_acceso_socio(uid)
            al_terminar(None)
        except Exception as ex:
            al_terminar(f"No se pudo desactivar: {ex}")

    page.show_dialog(ft.AlertDialog(
        modal=True,
        title=ft.Text("¿Desactivar el acceso a la app?", weight=ft.FontWeight.W_600, font_family="Poppins"),
        content=ft.Text(f"{s['nombre']} no va a poder entrar a la app. Su historial (rutinas, marcas, "
                        "entradas) se conserva y el socio pasa a \"Inactivo\".", size=13, color=TEXT_MUTED),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.pop_dialog()),
            ft.TextButton("Desactivar", on_click=_desactivar, style=ft.ButtonStyle(color=RED)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    ))


def build_socios(page: ft.Page) -> ft.Column:
    estado = {"pestana": "Todos", "texto": ""}
    contenido = ft.Column(spacing=22)
    aviso = ft.Text("", size=12, weight=ft.FontWeight.W_500, color=RED)

    # Columnas de la tabla: mismo ancho relativo en el encabezado y en cada fila.
    COLS = [("SOCIO", 4), ("DNI", 2), ("PLAN", 2), ("VENCIMIENTO", 2), ("ÚLT. ENTRENO", 2), ("ESTADO", 2), ("ACCIONES", 2)]

    def tab(label, cantidad):
        activo = label == estado["pestana"]
        return ft.Container(
            content=ft.Text(f"{label} ({cantidad})", size=13, weight=ft.FontWeight.W_500 if activo else ft.FontWeight.W_500,
                            color=DARK),
            bgcolor=GOLD if activo else ft.Colors.TRANSPARENT, border_radius=22,
            padding=ft.padding.symmetric(horizontal=22, vertical=10),
            on_click=lambda e, l=label: _cambiar_pestana(l), ink=True,
        )

    def fila(s):
        vencido = s["estado"] == "Plan vencido"
        gris = lambda t: ft.Text(t, size=13.5, color=TEXT_MUTED)
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT, icon_color=DARK, tooltip="Más opciones",
            items=[
                ft.PopupMenuItem(content=ft.Text("👤  Ver perfil"), on_click=lambda e, s=s: _dialogo_perfil(page, s)),
                ft.PopupMenuItem(content=ft.Text("📋  Copiar email"), disabled=not s["email"],
                                 on_click=lambda e, s=s: _copiar(s["email"])),
                ft.PopupMenuItem(content=ft.Text("⛔  Desactivar acceso a la app", color=RED),
                                 disabled=not s["tiene_app"] or s["estado"] == "Inactivo",
                                 on_click=lambda e, s=s: _confirmar_desactivar(page, s, _tras_desactivar)),
            ],
        )
        celdas = [
            ft.Row([
                _avatar_redondo(s["nombre"], s["id_socio"]),
                ft.Column([
                    ft.Text(s["nombre"] or "—", size=14, weight=ft.FontWeight.W_500, color=DARK,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(s["email"] or "sin email", size=12, color=TEXT_MUTED,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=1, expand=True),
            ], spacing=14),
            ft.Text(s["dni"] or "—", size=13.5, color=DARK),
            ft.Text(s["plan"], size=13.5, color=DARK) if s["plan"] else gris("Sin plan"),
            ft.Text(socios_repo.fecha_corta(s["vencimiento"]), size=13.5, color=RED if vencido else DARK,
                    weight=ft.FontWeight.W_500 if vencido else ft.FontWeight.NORMAL) if s["plan"] else gris("—"),
            ft.Text(socios_repo.fecha_corta(s["ultimo_entrenamiento"]), size=13.5, color=DARK)
                if s["ultimo_entrenamiento"] else gris("Nunca"),
            ft.Row([status_pill(s["estado"], PILL_POR_ESTADO[s["estado"]])]),
            ft.Row([
                ft.OutlinedButton("Ver perfil", on_click=lambda e, s=s: _dialogo_perfil(page, s),
                                  style=ft.ButtonStyle(color=DARK, shape=ft.RoundedRectangleBorder(radius=10),
                                                       side=ft.BorderSide(1, GRAY_LIGHT),
                                                       padding=ft.padding.symmetric(horizontal=20, vertical=12))),
                menu,
            ], spacing=2),
        ]
        return ft.Container(
            content=ft.Row([ft.Container(c, expand=peso) for c, (_, peso) in zip(celdas, COLS)],
                           spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
        )

    def render(forzar: bool = False, actualizar: bool = True):
        try:
            socios = socios_repo.cargar_socios(forzar=forzar)
        except Exception as ex:
            contenido.controls = [section_card(ft.Text(f"No se pudieron cargar los socios: {ex}", color=RED))]
            if actualizar:
                page.update()
            return
        res = socios_repo.resumen(socios)
        visibles = socios_repo.filtrar(socios, estado["pestana"], estado["texto"])

        tarjetas = ft.Row([
            _tarjeta_resumen(ft.Icons.PEOPLE_OUTLINE, "#15803D", "#DCFCE7", "Activos", res["Activo"],
                             "plan vigente", "#DCFCE7", "#15803D"),
            _tarjeta_resumen(ft.Icons.CALENDAR_TODAY_OUTLINED, GOLD_DARK, "#FEF3C7", "Plan vencido", res["Plan vencido"],
                             "renovar", "#FEF3C7", GOLD_DARK),
            _tarjeta_resumen(ft.Icons.DO_NOT_DISTURB_ALT, "#57534E", "#F3F1EA", "Sin plan", res["Sin plan"],
                             "asignar membresía", BADGE_BLUE_BG, BADGE_BLUE_TEXT),
            _tarjeta_resumen(ft.Icons.HOURGLASS_EMPTY, GOLD_DARK, "#FEF3C7", "Nuevos (30 días)", res["nuevos"],
                             f"de {res['total']}", "#DCFCE7", "#15803D"),
        ], spacing=18)

        pestanas = ft.Container(
            content=ft.Row([tab("Todos", res["total"]), *[tab(e, res[e]) for e in socios_repo.ESTADOS],
                            tab("Nuevos", res["nuevos"])], spacing=2, tight=True),
            bgcolor=WHITE, border_radius=26, border=ft.border.all(1, GRAY_LIGHT), padding=4,
        )

        encabezado = ft.Container(
            content=ft.Row([ft.Container(ft.Text(t, size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED), expand=p)
                            for t, p in COLS], spacing=12),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
        )
        filas = [fila(s) for s in visibles] or [ft.Container(
            ft.Text("No hay socios para mostrar con este filtro.", size=13, color=TEXT_MUTED),
            padding=24, border=ft.border.only(top=ft.BorderSide(1, GRAY_LIGHT)),
        )]
        tabla = ft.Container(
            content=ft.Column([encabezado, *filas], spacing=0),
            bgcolor=WHITE, border=ft.border.all(1, GRAY_LIGHT), border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
        contenido.controls = [tarjetas, ft.Row([pestanas]), tabla]
        if actualizar:
            page.update()

    def _cambiar_pestana(label):
        estado["pestana"] = label
        render()

    def _buscar(e):
        estado["texto"] = e.control.value or ""
        render()

    def _copiar(texto: str):
        # En Flet 0.84 el portapapeles es asíncrono (page.clipboard.set).
        async def _poner():
            await page.clipboard.set(texto)
        page.run_task(_poner)
        aviso.value, aviso.color = f"✓ Copiado: {texto}", GREEN
        page.update()

    def _tras_desactivar(error: str | None):
        aviso.value, aviso.color = (error, RED) if error else ("✓ Acceso desactivado", GREEN)
        render(forzar=True)

    buscador = ft.TextField(
        hint_text="Buscar socio, DNI, nombre...", prefix_icon=ft.Icons.SEARCH, width=340, dense=True,
        border_radius=24, border_color=GRAY_LIGHT, bgcolor=WHITE, on_change=_buscar,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=14),
    )
    nuevo = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.ADD, size=18, color=DARK),
                        ft.Text("Nuevo socio", size=14, weight=ft.FontWeight.W_500, color=DARK)], spacing=8, tight=True),
        bgcolor=GOLD, border_radius=24, padding=ft.padding.symmetric(horizontal=22, vertical=13),
        on_click=lambda e: _dialogo_nuevo_socio(page, on_creado=lambda: render(forzar=True)), ink=True,
    )
    cabecera = ft.Row([
        ft.Column([
            ft.Text("GESTIÓN DE SOCIOS", size=11.5, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
            ft.Text("Socios", size=30, weight=ft.FontWeight.W_600, color=DARK, font_family="Poppins",
                    style=ft.TextStyle(height=1.15)),
            ft.Text("Administrá y consultá la información de los socios del gimnasio.", size=13.5, color=TEXT_MUTED),
        ], spacing=2, expand=True),
        ft.Column([ft.Row([buscador, nuevo], spacing=14), aviso],
                  horizontal_alignment=ft.CrossAxisAlignment.END, spacing=6),
    ], vertical_alignment=ft.CrossAxisAlignment.START)

    render(actualizar=False)
    return ft.Column([cabecera, contenido], spacing=26, scroll=ft.ScrollMode.AUTO)
