import flet as ft
from db import db_connector
from vistas.vista_ventas_flet import vista_ventas
from vistas.vista_productos_flet import vista_productos
from vistas.vista_reportes_flet import vista_reportes
from vistas.vista_empleados_flet import vista_empleados

# --- ESTADO DE SESIÓN GLOBAL ---
sesion_actual = {"id": None, "nombre": "", "cargo": ""}


def main(page: ft.Page):
    # --- CONFIGURACIÓN GLOBAL ---
    page.title = "Oracle POS | Professional"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, use_material3=True)
    page.window.maximized = True

    # Iniciar conexión a BD al arrancar
    if not db_connector.init_pool():
        page.add(ft.Text("Error Fatal: No se pudo conectar a Oracle", color="red"))
        return

    # --- VARIABLES MENU ---
    btn_ventas_ref = ft.Ref[ft.Container]()
    btn_prod_ref = ft.Ref[ft.Container]()
    btn_rep_ref = ft.Ref[ft.Container]()
    btn_emp_ref = ft.Ref[ft.Container]()

    # --- UI HELPERS ---
    def crear_boton_menu(icono, texto, on_click, ref_control=None, activo=False):
        color_bg = ft.Colors.WHITE10 if activo else ft.Colors.TRANSPARENT
        return ft.Container(
            ref=ref_control,
            content=ft.Row([
                ft.Icon(icono, color=ft.Colors.WHITE70),
                ft.Text(texto, color=ft.Colors.WHITE, size=14, weight="w500")
            ], spacing=15),
            padding=ft.padding.symmetric(vertical=12, horizontal=15),
            border_radius=8,
            bgcolor=color_bg,
            on_click=on_click,
            ink=True,
            on_hover=lambda e: resaltar_boton(e, activo)
        )

    def resaltar_boton(e, activo_fijo):
        if not activo_fijo:
            e.control.bgcolor = ft.Colors.WHITE10 if e.data == "true" else ft.Colors.TRANSPARENT
            e.control.update()

    # --- DASHBOARD ---
    def mostrar_dashboard():
        page.clean()
        es_admin = (sesion_actual["cargo"] == "Administrador")

        contenedor_vistas = ft.Container(expand=True, padding=30)

        def cambiar_vista(nombre):
            if btn_ventas_ref.current: btn_ventas_ref.current.bgcolor = ft.Colors.TRANSPARENT
            if btn_prod_ref.current: btn_prod_ref.current.bgcolor = ft.Colors.TRANSPARENT
            if btn_rep_ref.current: btn_rep_ref.current.bgcolor = ft.Colors.TRANSPARENT
            if btn_emp_ref.current: btn_emp_ref.current.bgcolor = ft.Colors.TRANSPARENT

            control = None
            if nombre == "ventas":
                # SOLUCIÓN: Pasamos la sesión como argumento, no asignando propiedad
                control = vista_ventas(page, sesion_actual)
                if btn_ventas_ref.current: btn_ventas_ref.current.bgcolor = ft.Colors.INDIGO_600

            elif nombre == "productos":
                control = vista_productos(page)
                if btn_prod_ref.current: btn_prod_ref.current.bgcolor = ft.Colors.INDIGO_600

            elif nombre == "empleados":
                control = vista_empleados(page)
                if btn_emp_ref.current: btn_emp_ref.current.bgcolor = ft.Colors.INDIGO_600

            elif nombre == "reportes":
                control = vista_reportes(page)
                if btn_rep_ref.current: btn_rep_ref.current.bgcolor = ft.Colors.INDIGO_600

            contenedor_vistas.content = control
            contenedor_vistas.update()
            page.update()

        # Sidebar
        sidebar = ft.Container(
            width=260, bgcolor="#1e293b", padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.STORE, color=ft.Colors.INDIGO_400, size=30),
                    ft.Text("ORACLE POS", color=ft.Colors.WHITE, weight="bold", size=20)
                ], alignment="center", spacing=10),
                ft.Divider(color=ft.Colors.WHITE10, height=30),

                ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(content=ft.Icon(ft.Icons.PERSON), bgcolor=ft.Colors.INDIGO_500, radius=18),
                        ft.Column([
                            ft.Text(sesion_actual["nombre"], color=ft.Colors.WHITE, weight="bold", size=13),
                            ft.Text(sesion_actual["cargo"], color=ft.Colors.WHITE54, size=11)
                        ], spacing=2)
                    ]),
                    padding=10, bgcolor=ft.Colors.WHITE10, border_radius=10
                ),
                ft.Divider(color="transparent", height=20),

                ft.Text("GENERAL", color=ft.Colors.WHITE24, size=11, weight="bold"),
                crear_boton_menu(ft.Icons.SHOPPING_CART_OUTLINED, "Punto de Venta", lambda e: cambiar_vista("ventas"),
                                 btn_ventas_ref, True),

                ft.Column([
                    ft.Divider(color="transparent", height=10),
                    ft.Text("ADMINISTRACIÓN", color=ft.Colors.WHITE24, size=11, weight="bold"),
                    crear_boton_menu(ft.Icons.INVENTORY_2_OUTLINED, "Inventario", lambda e: cambiar_vista("productos"),
                                     btn_prod_ref),
                    crear_boton_menu(ft.Icons.PEOPLE_OUTLINE, "Empleados", lambda e: cambiar_vista("empleados"),
                                     btn_emp_ref),
                    crear_boton_menu(ft.Icons.BAR_CHART_OUTLINED, "Reportes", lambda e: cambiar_vista("reportes"),
                                     btn_rep_ref),
                ], visible=es_admin),

                ft.Container(expand=True),
                ft.Divider(color=ft.Colors.WHITE10),
                crear_boton_menu(ft.Icons.LOGOUT, "Cerrar Sesión", lambda e: reiniciar_app())
            ])
        )

        page.add(
            ft.Row([sidebar, ft.Container(contenedor_vistas, expand=True, bgcolor="#f1f5f9")], expand=True, spacing=0))
        cambiar_vista("ventas")

    def reiniciar_app():
        sesion_actual["id"] = None
        page.clean()
        mostrar_login()

    # --- LOGIN ---
    def mostrar_login():
        user_txt = ft.TextField(label="Usuario", bgcolor=ft.Colors.GREY_100, filled=True, prefix_icon=ft.Icons.PERSON)
        pass_txt = ft.TextField(label="Contraseña", bgcolor=ft.Colors.GREY_100, filled=True, prefix_icon=ft.Icons.LOCK,
                                password=True, can_reveal_password=True)
        lbl_error = ft.Text("", color="red", size=12)

        def evento_login(e):
            if not user_txt.value or not pass_txt.value:
                lbl_error.value = "Ingrese usuario y contraseña"
                lbl_error.update()
                return

            exito, data = db_connector.validar_usuario_app(user_txt.value, pass_txt.value)

            if exito:
                sesion_actual.update(data)
                mostrar_dashboard()
            else:
                lbl_error.value = data  # Mensaje de error
                lbl_error.update()

        card = ft.Container(
            width=400, padding=50, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=100, color="#20000000"),
            content=ft.Column([
                ft.Icon(ft.Icons.TOKEN, size=60, color=ft.Colors.INDIGO),
                ft.Text("Bienvenido", size=26, weight="bold", color=ft.Colors.BLUE_GREY_900),
                ft.Text("Sistema de Gestión", size=14, color=ft.Colors.GREY),
                ft.Divider(height=30, color="transparent"),
                user_txt, pass_txt, lbl_error,
                ft.Divider(height=20, color="transparent"),
                ft.ElevatedButton("INICIAR SESIÓN", width=300, height=50,
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO, color="white"),
                                  on_click=evento_login)
            ], horizontal_alignment="center")
        )
        page.add(ft.Container(card, alignment=ft.alignment.center, expand=True, bgcolor="#e2e8f0"))

    mostrar_login()


ft.app(target=main)