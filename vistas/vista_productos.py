import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from db import db_connector


def create_products_view(parent_frame):

    parent_frame.grid_columnconfigure(0, weight=1)

    title_label = ctk.CTkLabel(
        parent_frame,
        text="Gestión de Stock y Productos",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color="#333333"
    )
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    main_form_frame = ctk.CTkFrame(parent_frame, fg_color="#F9F9F9", corner_radius=10)
    main_form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

    # FORMULARIO

    form_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    form_frame.grid(row=0, column=0, padx=20, pady=10)

    labels = [
        "ID Producto:",
        "Nombre:",
        "Categoría:",
        "Precio:",
        "Marca:",
        "Stock:",
        "Descripción:",
        "Modelo:",
        "Proveedor:",
        "Ubicación:"
    ]

    entries = {}

    for i, label in enumerate(labels):
        lbl = ctk.CTkLabel(
            form_frame,
            text=label,
            text_color="#555555",
            font=ctk.CTkFont(size=14)
        )
        lbl.grid(row=i, column=0, padx=10, pady=12, sticky="e")

        entry = ctk.CTkEntry(
            form_frame,
            width=200,
            fg_color="white",
            border_color="#CCCCCC",
            text_color="black"
        )

        entry.grid(row=i, column=1, padx=10, pady=12, sticky="w")

        if label == "ID Producto:":
            entry.configure(state="disabled", fg_color="#EEEEEE")

        if label == "Ubicación:":
            entry.insert(0, "Almacén")
            entry.configure(state="disabled", fg_color="#EEEEEE")

        entries[label] = entry


    # TABLA

    table_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    table_frame.grid(row=3, column=0, padx=20, pady=10)

    columns = (
        "ID", "Nombre", "Categoría", "Precio",
        "Marca", "Stock", "Ingreso", "Vencimiento",
        "Descripción", "Modelo", "Proveedor", "Ubicación"
    )

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    tree.grid(row=0, column=0)


    # FUNCIONES 


    def cargar_tabla():
        conn = db_connector.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    ID_PRODUCTO,
                    NOMBRE,
                    CATEGORIA,
                    PRECIO,
                    MARCA,
                    STOCK,
                    TO_CHAR(FECHA_INGRESO, 'YYYY-MM-DD'),
                    TO_CHAR(FECHA_VENCIMIENTO, 'YYYY-MM-DD'),
                    DESCRIPCION,
                    MODELO,
                    PROVEEDOR,
                    UBICACION
                FROM PRODUCTOS
                ORDER BY ID_PRODUCTO
            """)

            rows = cursor.fetchall()

            tree.delete(*tree.get_children())

            for row in rows:
                tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la tabla: {e}")

        finally:
            db_connector.release_connection(conn)

    cargar_tabla()


    # REGISTRAR


    def registrar():
        nombre = entries["Nombre:"].get()
        categoria = entries["Categoría:"].get()
        precio = entries["Precio:"].get()
        marca = entries["Marca:"].get()
        stock = entries["Stock:"].get()
        descripcion = entries["Descripción:"].get()
        modelo = entries["Modelo:"].get()
        proveedor = entries["Proveedor:"].get()
        ubicacion = "Almacén"

        if nombre == "" or precio == "" or stock == "":
            messagebox.showwarning("Campos Requeridos", "Nombre, precio y stock son obligatorios.")
            return

        try:
            precio = float(precio)
            stock = int(stock)
        except:
            messagebox.showwarning("Error", "Precio debe ser decimal y stock debe ser entero.")
            return

        conn = db_connector.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO PRODUCTOS(
                    NOMBRE, CATEGORIA, PRECIO, MARCA, STOCK,
                    FECHA_INGRESO, FECHA_VENCIMIENTO,
                    DESCRIPCION, MODELO, PROVEEDOR, UBICACION
                ) VALUES (
                    :1, :2, :3, :4, :5,
                    SYSDATE,
                    ADD_MONTHS(SYSDATE, 6),
                    :6, :7, :8, :9
                )
            """, (nombre, categoria, precio, marca, stock,
                  descripcion, modelo, proveedor, ubicacion))

            conn.commit()

            messagebox.showinfo("Éxito", "Producto registrado correctamente.")
            cargar_tabla()

        except Exception as e:
            messagebox.showerror("Error SQL", str(e))

        finally:
            db_connector.release_connection(conn)


    # MODIFICAR

    def modificar():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Selecciona un producto", "No has seleccionado ningún producto.")
            return

        values = tree.item(selected, "values")
        id_producto = values[0]

        nombre = entries["Nombre:"].get()
        categoria = entries["Categoría:"].get()
        precio = entries["Precio:"].get()
        marca = entries["Marca:"].get()
        stock = entries["Stock:"].get()
        descripcion = entries["Descripción:"].get()
        modelo = entries["Modelo:"].get()
        proveedor = entries["Proveedor:"].get()

        conn = db_connector.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE PRODUCTOS SET
                    NOMBRE = :1,
                    CATEGORIA = :2,
                    PRECIO = :3,
                    MARCA = :4,
                    STOCK = :5,
                    DESCRIPCION = :6,
                    MODELO = :7,
                    PROVEEDOR = :8
                WHERE ID_PRODUCTO = :9
            """, (
                nombre, categoria, precio, marca, stock,
                descripcion, modelo, proveedor,
                id_producto
            ))

            conn.commit()
            cargar_tabla()
            messagebox.showinfo("Éxito", "Producto modificado.")

        except Exception as e:
            messagebox.showerror("Error SQL", str(e))

        finally:
            db_connector.release_connection(conn)


    # ELIMINAR


    def eliminar():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Selecciona un producto", "No has seleccionado ninguno.")
            return

        values = tree.item(selected, "values")
        id_producto = values[0]

        if not messagebox.askyesno("Confirmar", "¿Eliminar producto?"):
            return

        conn = db_connector.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM PRODUCTOS WHERE ID_PRODUCTO = :1", (id_producto,))
            conn.commit()

            cargar_tabla()
            messagebox.showinfo("Éxito", "Producto eliminado.")

        except Exception as e:
            messagebox.showerror("Error SQL", str(e))

        finally:
            db_connector.release_connection(conn)


    # LIMPIAR CAMPOS

    def limpiar_campos():
        for label, entry in entries.items():
            entry.configure(state="normal")
            entry.delete(0, "end")

        # restaurar ubicación
        entries["Ubicación:"].insert(0, "Almacén")
        entries["Ubicación:"].configure(state="disabled", fg_color="#EEEEEE")

        # quitar selección de tabla
        tree.selection_remove(tree.selection())


    # Botones 
  
    button_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    button_frame.grid(row=1, column=0, padx=20, pady=20)

    ctk.CTkButton(button_frame, text="Registrar", fg_color="#52B788",
                  hover_color="#45A274", command=registrar).grid(row=0, column=0, padx=10)

    ctk.CTkButton(button_frame, text="Modificar", fg_color="#4E89AE",
                  hover_color="#427391", command=modificar).grid(row=0, column=1, padx=10)

    ctk.CTkButton(button_frame, text="Eliminar", fg_color="#D9534F",
                  hover_color="#B54541", command=eliminar).grid(row=0, column=2, padx=10)

  
    ctk.CTkButton(button_frame, text="Limpiar", fg_color="#6C757D",
                  hover_color="#555B61", command=limpiar_campos).grid(row=0, column=3, padx=10)

    # ==============================
    # Navegación
    # ==============================
    nav_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, padx=20, pady=10)

    def navegar(pos):
        if tree.get_children():
            items = tree.get_children()
            if pos == "first":
                tree.selection_set(items[0])
                tree.focus(items[0])
            elif pos == "last":
                tree.selection_set(items[-1])
                tree.focus(items[-1])
            elif pos == "next":
                cur = tree.focus()
                idx = items.index(cur)
                if idx < len(items) - 1:
                    tree.selection_set(items[idx + 1])
                    tree.focus(items[idx + 1])
            elif pos == "prev":
                cur = tree.focus()
                idx = items.index(cur)
                if idx > 0:
                    tree.selection_set(items[idx - 1])
                    tree.focus(items[idx - 1])

    ctk.CTkButton(nav_frame, text="<< Primero", fg_color="#F0AD4E",
                  hover_color="#D59740", command=lambda: navegar("first")).grid(row=0, column=0, padx=5)

    ctk.CTkButton(nav_frame, text="< Anterior", fg_color="#F0AD4E",
                  hover_color="#D59740", command=lambda: navegar("prev")).grid(row=0, column=1, padx=5)

    ctk.CTkButton(nav_frame, text="Siguiente >", fg_color="#F0AD4E",
                  hover_color="#D59740", command=lambda: navegar("next")).grid(row=0, column=2, padx=5)

    ctk.CTkButton(nav_frame, text="Último >>", fg_color="#F0AD4E",
                  hover_color="#D59740", command=lambda: navegar("last")).grid(row=0, column=3, padx=5)
