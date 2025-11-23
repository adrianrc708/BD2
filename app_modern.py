import flet as ft
from db import db_connector
from vistas.vista_ventas_flet import vista_ventas
from vistas.vista_productos_flet import vista_productos
from vistas.vista_reportes_flet import vista_reportes

def main(page: ft.Page):
    # --- CONFIGURACIÓN GLOBAL ---
    page.title = "Oracle POS | Professional"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    # Usamos una semilla de color Indigo para un look corporativo moderno
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, use_material3=True)
    page.window.maximized = True

    # --- VARIABLES DE ESTADO ---
    # Para saber qué botón del menú resaltar
    btn_ventas_ref = ft.Ref[ft.Container]()
    btn_prod_ref = ft.Ref[ft.Container]()
    btn_rep_ref = ft.Ref[ft.Container]()

    # --- LÓGICA DE ROLES ---
    def es_admin(usuario):
        if usuario.upper() == 'ADRIAN': return True
        conn = db_connector.get_connection()
        if not conn: return False
        try:
            cur = conn.cursor()
            cur.execute("SELECT role FROM session_roles")
            roles = [r[0] for r in cur.fetchall()]
            return 'ROL_VENDEDOR' not in roles
        except:
            return False
        finally:
            db_connector.release_connection(conn)

    # --- COMPONENTES UI REUTILIZABLES ---
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
        # Efecto hover sutil
        if not activo_fijo:
            e.control.bgcolor = ft.Colors.WHITE10 if e.data == "true" else ft.Colors.TRANSPARENT
            e.control.update()

    # --- DASHBOARD ---
    def mostrar_dashboard(usuario):
        page.clean()
        usuario_admin = es_admin(usuario)

        # Area de contenido principal
        contenedor_vistas = ft.Container(expand=True, padding=30)

        def cambiar_vista(nombre):
            # Reseteamos estilos de botones (visual)
            if btn_ventas_ref.current: btn_ventas_ref.current.bgcolor = ft.Colors.TRANSPARENT
            if btn_prod_ref.current: btn_prod_ref.current.bgcolor = ft.Colors.TRANSPARENT
            if btn_rep_ref.current: btn_rep_ref.current.bgcolor = ft.Colors.TRANSPARENT

            control_vista = None
            if nombre == "ventas":
                control_vista = vista_ventas(page)
                if btn_ventas_ref.current: btn_ventas_ref.current.bgcolor = ft.Colors.INDIGO_600
            elif nombre == "productos":
                control_vista = vista_productos(page)  # <--- CAMBIO AQUÍ
                if btn_prod_ref.current: btn_prod_ref.current.bgcolor = ft.Colors.INDIGO_600
            elif nombre == "reportes":
                control_vista = vista_reportes(page)  # <--- CAMBIO AQUÍ
                if btn_rep_ref.current: btn_rep_ref.current.bgcolor = ft.Colors.INDIGO_600

            contenedor_vistas.content = control_vista
            contenedor_vistas.update()
            if btn_ventas_ref.current: page.update()  # Actualizar sidebar

        # Sidebar Profesional
        sidebar = ft.Container(
            width=260,
            bgcolor="#1e293b",  # Slate 800
            padding=20,
            content=ft.Column([
                # Header Sidebar
                ft.Row([
                    ft.Icon(ft.Icons.STORE, color=ft.Colors.INDIGO_400, size=30),
                    ft.Text("ORACLE POS", color=ft.Colors.WHITE, weight="bold", size=20)
                ], alignment="center", spacing=10),
                ft.Divider(color=ft.Colors.WHITE10, height=30),

                # Info Usuario
                ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(
                            content=ft.Icon(ft.Icons.PERSON),
                            bgcolor=ft.Colors.INDIGO_500, radius=18
                        ),
                        ft.Column([
                            ft.Text(usuario.upper(), color=ft.Colors.WHITE, weight="bold", size=13),
                            ft.Text("Administrador" if usuario_admin else "Vendedor", color=ft.Colors.WHITE54, size=11)
                        ], spacing=2)
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.WHITE10,
                    border_radius=10
                ),
                ft.Divider(color="transparent", height=20),

                # Menú
                ft.Text("GENERAL", color=ft.Colors.WHITE24, size=11, weight="bold"),
                crear_boton_menu(ft.Icons.SHOPPING_CART_OUTLINED, "Punto de Venta", lambda e: cambiar_vista("ventas"),
                                 btn_ventas_ref, True),

                # Sección Admin
                ft.Column([
                    ft.Divider(color="transparent", height=10),
                    ft.Text("ADMINISTRACIÓN", color=ft.Colors.WHITE24, size=11, weight="bold"),
                    crear_boton_menu(ft.Icons.INVENTORY_2_OUTLINED, "Inventario", lambda e: cambiar_vista("productos"),
                                     btn_prod_ref),
                    crear_boton_menu(ft.Icons.BAR_CHART_OUTLINED, "Reportes", lambda e: cambiar_vista("reportes"),
                                     btn_rep_ref),
                ], visible=usuario_admin),

                ft.Container(expand=True),
                ft.Divider(color=ft.Colors.WHITE10),
                crear_boton_menu(ft.Icons.LOGOUT, "Cerrar Sesión", lambda e: reiniciar_app())
            ])
        )

        layout = ft.Row([sidebar, ft.Container(contenedor_vistas, expand=True, bgcolor="#f1f5f9")], expand=True,
                        spacing=0)  # bg: Slate 100
        page.add(layout)
        cambiar_vista("ventas")

    def reiniciar_app():
        page.clean()
        db_connector.close_connection_pool()
        mostrar_login()

    # --- LOGIN MEJORADO ---
    def mostrar_login():
        user_txt = ft.TextField(label="Usuario", border_color="transparent", bgcolor=ft.Colors.GREY_100, filled=True,
                                prefix_icon=ft.Icons.PERSON_OUTLINE, height=50)
        pass_txt = ft.TextField(label="Contraseña", border_color="transparent", bgcolor=ft.Colors.GREY_100, filled=True,
                                prefix_icon=ft.Icons.LOCK_OUTLINE, password=True, can_reveal_password=True, height=50)

        def evento_login(e):
            if not user_txt.value or not pass_txt.value:
                user_txt.error_text = "Campo requerido"
                user_txt.update()
                return
            if db_connector.login_y_conectar(user_txt.value, pass_txt.value):
                mostrar_dashboard(user_txt.value)

        card = ft.Container(
            width=400,
            padding=50,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=100, color="#20000000"),
            content=ft.Column([
                ft.Icon(ft.Icons.TOKEN, size=60, color=ft.Colors.INDIGO),
                ft.Text("Bienvenido", size=26, weight="bold", color=ft.Colors.BLUE_GREY_900),
                ft.Text("Ingresa tus credenciales para continuar", size=14, color=ft.Colors.GREY),
                ft.Divider(height=30, color="transparent"),
                user_txt,
                pass_txt,
                ft.Divider(height=20, color="transparent"),
                ft.ElevatedButton("INICIAR SESIÓN", width=300, height=50,
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO, color="white",
                                                       shape=ft.RoundedRectangleBorder(radius=10)),
                                  on_click=evento_login)
            ], horizontal_alignment="center")
        )

        page.add(ft.Container(card, alignment=ft.alignment.center, expand=True, bgcolor="#e2e8f0"))  # Slate 200

    mostrar_login()


ft.app(target=main)