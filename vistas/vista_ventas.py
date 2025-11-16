import customtkinter as ctk
from db import db_connector


def create_sales_view(parent_frame):
    parent_frame.grid_columnconfigure(0, weight=1)

    title_label = ctk.CTkLabel(parent_frame, text="Registrar Nueva Venta",
                               font=ctk.CTkFont(size=24, weight="bold"),
                               text_color="#333333")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    placeholder = ctk.CTkLabel(parent_frame, text="Aquí va el formulario de Gerardo (Mockup 2)",
                               font=ctk.CTkFont(size=16), text_color="#666666")
    placeholder.grid(row=1, column=0, padx=20, pady=20)