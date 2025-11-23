import customtkinter as ctk
from tkinter import messagebox
from db import db_connector

from vistas import vista_productos
from vistas import vista_ventas
from vistas import vista_reportes


# --- CLASE PRINCIPAL QUE GESTIONA TODO ---
class MainApp:
    def __init__(self):
        # Configuración inicial única de la ventana
        ctk.set_appearance_mode("light")
        self.root = ctk.CTk()
        self.root.title("AppTiendaOracle")

        # Iniciamos mostrando el Login
        self.mostrar_login()

        # Protocolo de cierre seguro
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.mainloop()

    def cerrar_aplicacion(self):
        """Cierra la conexión a BD y la ventana"""
        db_connector.close_connection_pool()
        self.root.destroy()

    # --- VISTA DE LOGIN ---
    def mostrar_login(self):
        self.limpiar_ventana()
        self.root.geometry("400x500")
        self.root.title("Acceso - AppTiendaOracle")

        # Frame Central del Login
        frame = ctk.CTkFrame(self.root, width=320, height=360, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="Iniciar Sesión", font=ctk.CTkFont(size=26, weight="bold")).place(relx=0.5, rely=0.15,
                                                                                                   anchor="center")

        user_entry = ctk.CTkEntry(frame, width=220, placeholder_text="Usuario (ej. adrian)")
        user_entry.place(relx=0.5, rely=0.35, anchor="center")

        pass_entry = ctk.CTkEntry(frame, width=220, placeholder_text="Contraseña", show="*")
        pass_entry.place(relx=0.5, rely=0.5, anchor="center")

        # Función interna para procesar el login
        def intentar_login():
            u = user_entry.get()
            p = pass_entry.get()
            if not u or not p:
                messagebox.showwarning("Datos", "Ingrese usuario y contraseña")
                return

            if db_connector.login_y_conectar(u, p):
                # Si conecta, cambiamos a la vista principal
                self.mostrar_dashboard(u)

        btn_login = ctk.CTkButton(frame, text="INGRESAR", width=220, height=40, command=intentar_login)
        btn_login.place(relx=0.5, rely=0.7, anchor="center")

    # --- VISTA DEL DASHBOARD (APP PRINCIPAL) ---
    def mostrar_dashboard(self, usuario):
        self.limpiar_ventana()
        self.root.geometry("1100x720")
        self.root.title(f"AppTiendaOracle - Usuario: {usuario.upper()}")

        # Inicializamos la lógica del Dashboard pasándole el root actual
        DashboardLogic(self.root, usuario, self.logout)

    def limpiar_ventana(self):
        """Elimina todos los widgets de la ventana actual sin cerrarla"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def logout(self):
        """Cierra sesión y vuelve al login"""
        db_connector.close_connection_pool()
        self.mostrar_login()


# --- LÓGICA DEL DASHBOARD (Separada para orden) ---
class DashboardLogic:
    def __init__(self, root, usuario, logout_callback):
        self.root = root
        self.usuario_actual = usuario.upper()
        self.logout_callback = logout_callback
        self.es_admin = self.verificar_permisos_admin()

        # Configuración del Grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(root, height=60, fg_color="#2C3E50", corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="new")
        ctk.CTkLabel(self.header_frame, text=f"Sistema de Tienda ({self.usuario_actual})",
                     font=ctk.CTkFont(size=20, weight="bold"), text_color="white").place(relx=0.5, rely=0.5,
                                                                                         anchor="center")

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(root, width=250, fg_color="#F2F2F2", corner_radius=0)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="Menú Principal", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0,
                                                                                                               column=0,
                                                                                                               pady=20)

        # Botones
        self.crear_botones_menu()

        # Área de Contenido
        self.content_frame = ctk.CTkFrame(root, fg_color="white", corner_radius=0)
        self.content_frame.grid(row=1, column=1, sticky="nsew")

        # Mensaje de Bienvenida
        ctk.CTkLabel(self.content_frame, text=f"Bienvenido, {self.usuario_actual}", font=ctk.CTkFont(size=30)).place(
            relx=0.5, rely=0.4, anchor="center")

    def crear_botones_menu(self):
        # Botón Ventas (Para todos)
        ctk.CTkButton(self.sidebar_frame, text="🛒 Registrar Venta", command=self.ver_ventas, fg_color="#2980B9").grid(
            row=1, column=0, padx=20, pady=10, sticky="ew")

        # Botones Admin
        if self.es_admin:
            ctk.CTkButton(self.sidebar_frame, text="📦 Gestión Productos", command=self.ver_productos,
                          fg_color="#27AE60").grid(row=2, column=0, padx=20, pady=10, sticky="ew")
            ctk.CTkButton(self.sidebar_frame, text="📊 Reportes", command=self.ver_reportes, fg_color="#8E44AD").grid(
                row=3, column=0, padx=20, pady=10, sticky="ew")
        else:
            ctk.CTkLabel(self.sidebar_frame, text="[Modo Vendedor]\nAcceso Limitado", text_color="gray").grid(row=4,
                                                                                                              column=0,
                                                                                                              pady=20)

        # Botón Salir
        ctk.CTkButton(self.sidebar_frame, text="Cerrar Sesión", fg_color="#C0392B", command=self.logout_callback).grid(
            row=5, column=0, padx=20, pady=20, sticky="s")

    def verificar_permisos_admin(self):
        if self.usuario_actual == 'ADRIAN': return True
        conn = db_connector.get_connection()
        if not conn: return False
        try:
            cur = conn.cursor()
            cur.execute("SELECT role FROM session_roles")
            roles = [r[0] for r in cur.fetchall()]
            # Si tiene rol vendedor, NO es admin
            if 'ROL_VENDEDOR' in roles: return False
            return True
        except:
            return False
        finally:
            db_connector.release_connection(conn)

    def limpiar_contenido(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()

    def ver_ventas(self):
        self.limpiar_contenido()
        vista_ventas.create_sales_view(self.content_frame)

    def ver_productos(self):
        self.limpiar_contenido()
        vista_productos.create_products_view(self.content_frame)

    def ver_reportes(self):
        self.limpiar_contenido()
        vista_reportes.create_reports_view(self.content_frame)


if __name__ == "__main__":
    # Arrancamos la app
    MainApp()