import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from db import db_connector
import datetime


def create_products_view(parent_frame):
    parent_frame.grid_columnconfigure(0, weight=1)

    title_label = ctk.CTkLabel(
        parent_frame,
        text="Gestión de Stock y Productos (Proc. Almacenados)",
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
        "ID Producto:", "Nombre:", "Categoría:", "Precio:",
        "Marca:", "Stock:", "Descripción:", "Modelo:",
        "Proveedor:", "Ubicación:"
    ]

    entries = {}

    for i, label in enumerate(labels):
        lbl = ctk.CTkLabel(form_frame, text=label, text_color="#555555", font=ctk.CTkFont(size=14))
        lbl.grid(row=i, column=0, padx=10, pady=12, sticky="e")

        entry = ctk.CTkEntry(form_frame, width=200, fg_color="white", border_color="#CCCCCC", text_color="black")
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

    columns = ("ID", "Nombre", "Categoría", "Precio", "Marca", "Stock", "Ingreso", "Vencimiento", "Descripción",
               "Modelo", "Proveedor", "Ubicación")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    tree.grid(row=0, column=0)

    # FUNCIONES

    def cargar_tabla():
        conn = db_connector.get_connection()
        if not conn: return
        cursor = conn.cursor()
        try:
            # Nota: La lectura (SELECT) se puede mantener directa o usar cursores de referencia.
            # Para simplificar y dado que el SP de navegación devuelve de 1 en 1,
            # mantendremos el SELECT masivo para la grilla.
            cursor.execute("""
                           SELECT ID_PRODUCTO,
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
            for row in rows: tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la tabla: {e}")
        finally:
            db_connector.release_connection(conn)

    cargar_tabla()

    # REGISTRAR (USANDO SP)

    def registrar():
        nombre = entries["Nombre:"].get()
        categoria = entries["Categoría:"].get()
        precio_str = entries["Precio:"].get()
        marca = entries["Marca:"].get()
        stock_str = entries["Stock:"].get()
        descripcion = entries["Descripción:"].get()
        modelo = entries["Modelo:"].get()
        proveedor = entries["Proveedor:"].get()
        ubicacion = "Almacén"

        if not nombre or not precio_str or not stock_str:
            messagebox.showwarning("Datos", "Nombre, Precio y Stock obligatorios.")
            return

        try:
            precio = float(precio_str)
            stock = int(stock_str)
        except:
            messagebox.showwarning("Error", "Formato numérico incorrecto.")
            return

        # Calculamos fecha de vencimiento (6 meses a futuro) en Python
        fecha_venc = datetime.datetime.now() + datetime.timedelta(days=180)

        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()

            # LLAMADA AL PROCEDIMIENTO ALMACENADO
            # sp_registrar(p_nombre, p_categoria, p_descripcion, p_marca, p_modelo,
            #              p_precio, p_stock, p_proveedor, p_fecha_venc, p_estado, p_ubicacion)

            cursor.callproc("pkg_gestion_productos.sp_registrar", [
                nombre, categoria, descripcion, marca, modelo,
                precio, stock, proveedor, fecha_venc, 'Activo', ubicacion
            ])

            conn.commit()
            messagebox.showinfo("Éxito", "Producto registrado vía SP.")
            cargar_tabla()
            limpiar_campos()

        except Exception as e:
            # Capturamos errores, incluyendo el raise_application_error del PL/SQL
            messagebox.showerror("Error BD", str(e))
        finally:
            db_connector.release_connection(conn)

    # MODIFICAR (USANDO SP)

    def modificar():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Atención", "Selecciona un producto.")
            return

        values = tree.item(selected, "values")
        id_producto = int(values[0])

        # Recogemos datos actuales de los inputs
        nombre = entries["Nombre:"].get()
        categoria = entries["Categoría:"].get()
        precio = float(entries["Precio:"].get())
        marca = entries["Marca:"].get()
        stock = int(entries["Stock:"].get())
        descripcion = entries["Descripción:"].get()
        modelo = entries["Modelo:"].get()
        proveedor = entries["Proveedor:"].get()

        # Fecha vencimiento y ubicación mantenemos lógica o valores fijos por simplicidad
        fecha_venc = datetime.datetime.now() + datetime.timedelta(days=180)
        ubicacion = "Almacén"
        estado = "Activo"

        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()

            # LLAMADA AL SP
            cursor.callproc("pkg_gestion_productos.sp_modificar", [
                id_producto, nombre, categoria, descripcion, marca, modelo,
                precio, stock, proveedor, fecha_venc, estado, ubicacion
            ])

            conn.commit()
            cargar_tabla()
            messagebox.showinfo("Éxito", "Producto modificado vía SP.")

        except Exception as e:
            messagebox.showerror("Error BD", str(e))
        finally:
            db_connector.release_connection(conn)

    # ELIMINAR (USANDO SP)

    def eliminar():
        selected = tree.focus()
        if not selected: return

        values = tree.item(selected, "values")
        id_producto = int(values[0])

        if not messagebox.askyesno("Confirmar", "¿Eliminar producto?"):
            return

        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            # LLAMADA AL SP
            cursor.callproc("pkg_gestion_productos.sp_eliminar", [id_producto])

            conn.commit()
            cargar_tabla()
            messagebox.showinfo("Éxito", "Producto eliminado vía SP.")

        except Exception as e:
            messagebox.showerror("Error BD", str(e))
        finally:
            db_connector.release_connection(conn)

    def limpiar_campos():
        for label, entry in entries.items():
            entry.configure(state="normal")
            entry.delete(0, "end")
        entries["Ubicación:"].insert(0, "Almacén")
        entries["Ubicación:"].configure(state="disabled", fg_color="#EEEEEE")
        tree.selection_remove(tree.selection())

    # Botones
    button_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    button_frame.grid(row=1, column=0, padx=20, pady=20)

    ctk.CTkButton(button_frame, text="Registrar (SP)", fg_color="#52B788", hover_color="#45A274",
                  command=registrar).grid(row=0, column=0, padx=10)
    ctk.CTkButton(button_frame, text="Modificar (SP)", fg_color="#4E89AE", hover_color="#427391",
                  command=modificar).grid(row=0, column=1, padx=10)
    ctk.CTkButton(button_frame, text="Eliminar (SP)", fg_color="#D9534F", hover_color="#B54541", command=eliminar).grid(
        row=0, column=2, padx=10)
    ctk.CTkButton(button_frame, text="Limpiar", fg_color="#6C757D", hover_color="#555B61", command=limpiar_campos).grid(
        row=0, column=3, padx=10)

    # Navegación (Visual en tabla)
    nav_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, padx=20, pady=10)

    def navegar(pos):
        if not tree.get_children(): return
        items = tree.get_children()

        if pos == "first":
            target = items[0]
        elif pos == "last":
            target = items[-1]
        elif pos in ["next", "prev"]:
            cur = tree.focus()
            if not cur:
                target = items[0]
            else:
                idx = items.index(cur)
                if pos == "next" and idx < len(items) - 1:
                    target = items[idx + 1]
                elif pos == "prev" and idx > 0:
                    target = items[idx - 1]
                else:
                    target = cur

        tree.selection_set(target)
        tree.focus(target)
        tree.see(target)

    ctk.CTkButton(nav_frame, text="<< Primero", width=80, command=lambda: navegar("first")).grid(row=0, column=0,
                                                                                                 padx=5)
    ctk.CTkButton(nav_frame, text="< Anterior", width=80, command=lambda: navegar("prev")).grid(row=0, column=1, padx=5)
    ctk.CTkButton(nav_frame, text="Siguiente >", width=80, command=lambda: navegar("next")).grid(row=0, column=2,
                                                                                                 padx=5)
    ctk.CTkButton(nav_frame, text="Último >>", width=80, command=lambda: navegar("last")).grid(row=0, column=3, padx=5)