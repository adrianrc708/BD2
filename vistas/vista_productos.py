import customtkinter as ctk
from db import db_connector


def create_products_view(parent_frame):
    parent_frame.grid_columnconfigure(0, weight=1)

    title_label = ctk.CTkLabel(parent_frame, text="Gestión de Stock y Productos",
                               font=ctk.CTkFont(size=24, weight="bold"),
                               text_color="#333333")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    main_form_frame = ctk.CTkFrame(parent_frame, fg_color="#F9F9F9", corner_radius=10)
    main_form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

    form_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    form_frame.grid(row=0, column=0, padx=20, pady=10)

    labels = ["ID Producto:", "Nombre:", "Categoría:", "Precio:", "Marca:", "Stock:"]
    for i, label in enumerate(labels):
        lbl = ctk.CTkLabel(form_frame, text=label, text_color="#555555", font=ctk.CTkFont(size=14))
        lbl.grid(row=i, column=0, padx=10, pady=12, sticky="e")

        entry = ctk.CTkEntry(form_frame, width=200, fg_color="white", border_color="#CCCCCC", text_color="black")
        entry.grid(row=i, column=1, padx=10, pady=12, sticky="w")
        if label == "ID Producto:":
            entry.configure(state="disabled", fg_color="#EEEEEE")

    button_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    button_frame.grid(row=1, column=0, padx=20, pady=20)

    btn_registrar = ctk.CTkButton(button_frame, text="Registrar", fg_color="#52B788", hover_color="#45A274")
    btn_registrar.grid(row=0, column=0, padx=10)

    btn_modificar = ctk.CTkButton(button_frame, text="Modificar", fg_color="#4E89AE", hover_color="#427391")
    btn_modificar.grid(row=0, column=1, padx=10)

    btn_eliminar = ctk.CTkButton(button_frame, text="Eliminar", fg_color="#D9534F", hover_color="#B54541")
    btn_eliminar.grid(row=0, column=2, padx=10)

    nav_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, padx=20, pady=10)

    btn_primero = ctk.CTkButton(nav_frame, text="<< Primero", fg_color="#F0AD4E", hover_color="#D59740")
    btn_primero.grid(row=0, column=0, padx=5)

    btn_anterior = ctk.CTkButton(nav_frame, text="< Anterior", fg_color="#F0AD4E", hover_color="#D59740")
    btn_anterior.grid(row=0, column=1, padx=5)

    btn_siguiente = ctk.CTkButton(nav_frame, text="Siguiente >", fg_color="#F0AD4E", hover_color="#D59740")
    btn_siguiente.grid(row=0, column=2, padx=5)

    btn_ultimo = ctk.CTkButton(nav_frame, text="Último >>", fg_color="#F0AD4E", hover_color="#D59740")
    btn_ultimo.grid(row=0, column=3, padx=5)