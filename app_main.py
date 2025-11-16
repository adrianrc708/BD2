import customtkinter as ctk
from db import db_connector

from vistas import vista_productos
from vistas import vista_ventas
from vistas import vista_reportes


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AppTiendaOracle")
        self.root.geometry("1100x720")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.header_frame = ctk.CTkFrame(root, height=60, fg_color="#F8659B", corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="new")

        self.header_label = ctk.CTkLabel(self.header_frame, text="AppTiendaOracle",
                                         font=ctk.CTkFont(size=20, weight="bold"),
                                         text_color="white")
        self.header_label.place(relx=0.5, rely=0.5, anchor="center")

        self.sidebar_frame = ctk.CTkFrame(root, width=250, fg_color="#F2F2F2", corner_radius=0)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.sidebar_label = ctk.CTkLabel(self.sidebar_frame, text="Navegación",
                                          font=ctk.CTkFont(size=18, weight="bold"),
                                          text_color="#333333")
        self.sidebar_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_productos = ctk.CTkButton(self.sidebar_frame, text="Gestión de Productos",
                                           command=self.show_products_frame,
                                           fg_color="white", text_color="black",
                                           hover_color="#E5E5E5", corner_radius=8,
                                           font=ctk.CTkFont(size=14))
        self.btn_productos.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_ventas = ctk.CTkButton(self.sidebar_frame, text="Registrar Venta",
                                        command=self.show_sales_frame,
                                        fg_color="white", text_color="black",
                                        hover_color="#E5E5E5", corner_radius=8,
                                        font=ctk.CTkFont(size=14))
        self.btn_ventas.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_reportes = ctk.CTkButton(self.sidebar_frame, text="Reportes",
                                          command=self.show_reports_frame,
                                          fg_color="white", text_color="black",
                                          hover_color="#E5E5E5", corner_radius=8,
                                          font=ctk.CTkFont(size=14))
        self.btn_reportes.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.btn_volver = ctk.CTkButton(self.sidebar_frame, text="Volver al Panel",
                                        command=self.show_welcome_frame,
                                        fg_color="#7F8C8D", text_color="white",
                                        hover_color="#95A5A6", corner_radius=8,
                                        font=ctk.CTkFont(size=14))
        self.btn_volver.grid(row=5, column=0, padx=20, pady=20, sticky="ews")

        self.content_frame = ctk.CTkFrame(root, fg_color="white", corner_radius=0)
        self.content_frame.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)

        self.show_welcome_frame()

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_welcome_frame(self):
        self.clear_content_frame()

        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        placeholder_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        placeholder_frame.grid(row=0, column=0, sticky="nsew")

        placeholder_frame.columnconfigure(0, weight=1)
        placeholder_frame.rowconfigure(0, weight=1)
        placeholder_frame.rowconfigure(1, weight=1)
        placeholder_frame.rowconfigure(2, weight=1)

        icon_label = ctk.CTkLabel(placeholder_frame, text="🗃️", font=ctk.CTkFont(size=100))
        icon_label.grid(row=0, column=0, pady=(0, 20), sticky="s")

        welcome_label = ctk.CTkLabel(placeholder_frame, text="Sistema de Gestión",
                                     font=ctk.CTkFont(size=32, weight="bold"),
                                     text_color="#333333")
        welcome_label.grid(row=1, column=0, sticky="n")

        info_label = ctk.CTkLabel(placeholder_frame,
                                  text="Seleccione una opción del menú de la izquierda para comenzar.",
                                  font=ctk.CTkFont(size=16),
                                  text_color="#666666")
        info_label.grid(row=2, column=0, pady=(10, 0), sticky="n")

    def show_products_frame(self):
        self.clear_content_frame()
        vista_productos.create_products_view(self.content_frame)

    def show_sales_frame(self):
        self.clear_content_frame()
        vista_ventas.create_sales_view(self.content_frame)

    def show_reports_frame(self):
        self.clear_content_frame()
        vista_reportes.create_reports_view(self.content_frame)


def on_app_close(root_window):
    print("Cerrando la aplicación... cerrando pool de conexiones.")
    db_connector.close_connection_pool()
    root_window.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    db_connector.init_connection_pool()

    root = ctk.CTk()
    app = App(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_app_close(root))
    root.mainloop()