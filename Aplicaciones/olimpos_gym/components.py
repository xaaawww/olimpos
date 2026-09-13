import flet as ft
from theme import *


def stat_badge(text: str, variant: str = "green") -> ft.Container:
    palettes = {
        "green": (BADGE_GREEN_BG, BADGE_GREEN_TEXT),
        "red":   (BADGE_RED_BG,   BADGE_RED_TEXT),
        "gold":  (BADGE_GOLD_BG,  BADGE_GOLD_TEXT),
        "blue":  (BADGE_BLUE_BG,  BADGE_BLUE_TEXT),
    }
    bg, fg = palettes.get(variant, palettes["green"])
    return ft.Container(
        content=ft.Text(text, size=10, weight=ft.FontWeight.W_800, color=fg),
        bgcolor=bg,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
    )


def status_pill(label: str, variant: str = "active") -> ft.Container:
    palettes = {
        "active":    ("#DCFCE7", "#16A34A"),
        "inactive":  ("#FEE2E2", "#DC2626"),
        "pending":   ("#FEF3C7", "#D97706"),
        "suspended": ("#F3F4F6", "#6B7280"),
        "debt":      ("#FEF3C7", "#D97706"),
    }
    bg, fg = palettes.get(variant, palettes["active"])
    dot = ft.Container(width=5, height=5, border_radius=3, bgcolor=fg)
    return ft.Container(
        content=ft.Row([dot, ft.Text(label, size=11, weight=ft.FontWeight.W_800, color=fg)],
                       tight=True, spacing=5),
        bgcolor=bg,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )


def avatar(initials: str, variant: str = "gold") -> ft.Container:
    palettes = {
        "gold":   (GOLD_LIGHT, GOLD, DARK),
        "dark":   (DARK2, DARK2, GOLD),
        "green":  ("#DCFCE7", "#DCFCE7", "#16A34A"),
        "blue":   ("#DBEAFE", "#DBEAFE", "#1D4ED8"),
        "red":    ("#FEE2E2", "#FEE2E2", "#DC2626"),
        "purple": ("#F3E8FF", "#F3E8FF", "#9333EA"),
    }
    bg1, bg2, fg = palettes.get(variant, palettes["gold"])
    return ft.Container(
        content=ft.Text(initials, size=12, weight=ft.FontWeight.W_900, color=fg),
        width=34, height=34,
        border_radius=10,
        bgcolor=bg1,
        alignment=ft.Alignment.CENTER,
    )


def section_card(content: ft.Control, padding: int = 20) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=WHITE,
        border_radius=16,
        border=ft.border.all(1.5, GRAY_LIGHT),
        shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.with_opacity(0.08, DARK)),
        padding=padding,
    )


def page_header(title: str, subtitle: str, actions: list = None) -> ft.Column:
    row_children = [
        ft.Column([
            ft.Text(title, size=22, weight=ft.FontWeight.W_800, color=DARK, font_family="Poppins"),
            ft.Text(subtitle, size=13, color=TEXT_MUTED),
        ], spacing=2)
    ]
    if actions:
        row_children.append(ft.Row(actions, spacing=8))
    return ft.Column([
        ft.Row(row_children, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
    ], spacing=0)


def action_button(label: str, variant: str = "outline", on_click=None) -> ft.ElevatedButton:
    if variant == "gold":
        return ft.ElevatedButton(
            label, on_click=on_click,
            style=ft.ButtonStyle(
                color=DARK,
                bgcolor=GOLD,
                shadow_color=ft.Colors.with_opacity(0.3, GOLD),
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_700, font_family="Poppins"),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )
        )
    elif variant == "dark":
        return ft.ElevatedButton(
            label, on_click=on_click,
            style=ft.ButtonStyle(
                color=GOLD,
                bgcolor=DARK,
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_700, font_family="Poppins"),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
            )
        )
    else:  # outline
        return ft.OutlinedButton(
            label, on_click=on_click,
            style=ft.ButtonStyle(
                color=DARK,
                side=ft.BorderSide(1.5, GRAY_LIGHT),
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_700, font_family="Poppins"),
                padding=ft.padding.symmetric(horizontal=12, vertical=5),
            )
        )


def stat_card(label: str, value: str, badge_text: str, badge_variant: str = "green",
              is_gold: bool = False) -> ft.Container:
    bg = ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                           colors=[GOLD_BG, GOLD_BG2]) if is_gold else WHITE
    border_color = GOLD_LIGHT if is_gold else GRAY_LIGHT
    return ft.Container(
        content=ft.Column([
            ft.Text(label.upper(), size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_700,
),
            ft.Text(value, size=30, weight=ft.FontWeight.W_900, color=DARK, font_family="Poppins",
                    height=1.1),
            stat_badge(badge_text, badge_variant),
        ], spacing=6),
        bgcolor=bg if not is_gold else None,
        gradient=bg if is_gold else None,
        border_radius=16,
        border=ft.border.all(1.5, border_color),
        shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.with_opacity(0.08, DARK)),
        padding=18,
        expand=True,
    )


def data_table_row(cells: list, is_last: bool = False) -> ft.Container:
    return ft.Container(
        content=ft.Row(cells, spacing=0),
        border=ft.border.only(bottom=ft.BorderSide(1, GRAY_LIGHT)) if not is_last else None,
        padding=ft.padding.symmetric(vertical=10, horizontal=4),
    )


def progress_bar(label: str, value: float, color: str = GOLD) -> ft.Column:
    return ft.Column([
        ft.Row([
            ft.Text(label, size=12, weight=ft.FontWeight.W_700),
            ft.Text(f"{int(value*100)}%", size=12, weight=ft.FontWeight.W_700),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(
            content=ft.Stack([
                ft.Container(bgcolor=GRAY_LIGHT, border_radius=3, height=6, expand=True),
                ft.Container(bgcolor=color, border_radius=3, height=6, expand=False),
            ]),
            bgcolor=GRAY_LIGHT,
            border_radius=3,
            height=6,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
    ], spacing=5)


def divider() -> ft.Divider:
    return ft.Divider(height=1, color=GRAY_LIGHT, thickness=1)


def card_header(title: str, action_label: str = None, on_action=None) -> ft.Row:
    children = [ft.Text(title, size=14, weight=ft.FontWeight.W_700, color=DARK, font_family="Poppins")]
    if action_label:
        children.append(
            ft.TextButton(action_label, on_click=on_action,
                          style=ft.ButtonStyle(color=GOLD_DARK,
                                               text_style=ft.TextStyle(size=11.5, weight=ft.FontWeight.W_700)))
        )
    return ft.Row(children, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
