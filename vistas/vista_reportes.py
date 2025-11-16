import customtkinter as ctk
from db import db_connector


def create_reports_view(parent_frame):
    parent_frame.grid_columnconfigure(0, weight=1)
    parent_frame.grid_rowconfigure(2, weight=1)

    title_label = ctk.CTkLabel(parent_frame, text="Generador de Reportes",
                               font=ctk.CTkFont(size=24, weight="bold"),
                               text_color="#333333")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    button_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")

    btn_rep_mes = ctk.CTkButton(button_frame, text="Ventas por Mes", fg_color="#5BC0DE", hover_color="#469DB8")
    btn_rep_mes.grid(row=0, column=0, padx=10)

    btn_rep_stock = ctk.CTkButton(button_frame, text="Stock Bajo", fg_color="#5BC0DE", hover_color="#469DB8")
    btn_rep_stock.grid(row=0, column=1, padx=10)

    btn_rep_vendidos = ctk.CTkButton(button_frame, text="Más Vendidos", fg_color="#5BC0DE", hover_color="#469DB8")
    btn_rep_vendidos.grid(row=0, column=2, padx=10)

    textbox = ctk.CTkTextbox(parent_frame, fg_color="#F9F9F9", text_color="black", border_color="#E0E0E0",
                             border_width=2)
    textbox.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
    textbox.insert("0.0", "Los resultados de los reportes (pkg_reportes) aparecerán aquí...")