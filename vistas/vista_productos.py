import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
from db import db_connector
import datetime
import oracledb


def create_products_view(parent_frame):
    parent_frame.grid_columnconfigure(0, weight=1)

    title_label = ctk.CTkLabel(
        parent_frame,
        text="Gestión de Stock (Integración Total BD)",
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

    # TABLA (Solo referencia visual)
    table_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    table_frame.grid(row=3, column=0, padx=20, pady=10)

    columns = ("ID", "Nombre", "Categoría", "Precio", "Marca", "Stock", "Ingreso", "Vencimiento", "Descripción",
               "Modelo", "Proveedor", "Ubicación")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120)

    tree.grid(row=0, column=0)

    # --- FUNCIONES AUXILIARES ---
    current_product_id = ctk.StringVar(value="0")

    def cargar_tabla():
        # Carga masiva solo para ver el panorama
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
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

    def cargar_producto_en_formulario(id_prod):
        # Llena el formulario completo con un SELECT * tras obtener el ID del SP de navegación
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM productos WHERE id_producto = :1", [id_prod])
            row = cursor.fetchone()

            if row:
                # Mapeo manual basado en CREATE TABLE
                limpiar_campos()
                entries["ID Producto:"].configure(state="normal")
                entries["ID Producto:"].insert(0, str(row[0]))
                entries["ID Producto:"].configure(state="disabled")
                current_product_id.set(str(row[0]))

                entries["Nombre:"].insert(0, row[1] or "")
                entries["Categoría:"].insert(0, row[2] or "")
                entries["Descripción:"].insert(0, row[3] or "")
                entries["Marca:"].insert(0, row[4] or "")
                entries["Modelo:"].insert(0, row[5] or "")
                entries["Precio:"].insert(0, str(row[6] or 0))
                entries["Stock:"].insert(0, str(row[7] or 0))
                entries["Proveedor:"].insert(0, row[8] or "")

                # Sincronizar selección en treeview
                for item in tree.get_children():
                    if str(tree.item(item, "values")[0]) == str(row[0]):
                        tree.selection_set(item)
                        tree.see(item)
                        break

        except Exception as e:
            print(f"Error cargando detalle: {e}")
        finally:
            db_connector.release_connection(conn)

    cargar_tabla()

    # --- NAVEGACIÓN (USANDO TUS PROCEDIMIENTOS ALMACENADOS) ---
    def navegar_bd(direccion):
        conn = db_connector.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()

            # Variables de salida que pide tu script SQL
            out_id = cursor.var(oracledb.NUMBER)
            out_nombre = cursor.var(oracledb.STRING)
            out_marca = cursor.var(oracledb.STRING)
            out_stock = cursor.var(oracledb.NUMBER)

            proc_name = ""
            params = []

            # Obtener ID actual
            try:
                curr = int(current_product_id.get())
            except:
                curr = 0

            # Mapeo a tu paquete pkg_gestion_productos
            if direccion == "first":
                proc_name = "pkg_gestion_productos.sp_get_primero"
                params = [out_id, out_nombre, out_marca, out_stock]
            elif direccion == "last":
                proc_name = "pkg_gestion_productos.sp_get_ultimo"
                params = [out_id, out_nombre, out_marca, out_stock]
            elif direccion == "next":
                proc_name = "pkg_gestion_productos.sp_get_siguiente"
                params = [curr, out_id, out_nombre, out_marca, out_stock]
            elif direccion == "prev":
                proc_name = "pkg_gestion_productos.sp_get_anterior"
                params = [curr, out_id, out_nombre, out_marca, out_stock]

            # Ejecutar SP
            cursor.callproc(proc_name, params)

            # Tu SP devuelve NULL en el ID si no encuentra nada
            new_id = out_id.getvalue()

            if new_id is not None:
                cargar_producto_en_formulario(int(new_id))
            else:
                messagebox.showinfo("Navegación", "No hay más registros en esa dirección.")

        except Exception as e:
            messagebox.showerror("Error BD", f"Error de navegación: {e}")
        finally:
            db_connector.release_connection(conn)

    # --- OPERACIONES CRUD (USANDO TUS PROCEDIMIENTOS) ---

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

        fecha_venc = datetime.datetime.now() + datetime.timedelta(days=180)

        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Llamada exacta a tu SP
            cursor.callproc("pkg_gestion_productos.sp_registrar", [
                nombre, categoria, descripcion, marca, modelo,
                precio, stock, proveedor, fecha_venc, 'Activo', ubicacion
            ])
            conn.commit()
            messagebox.showinfo("Éxito", "Producto registrado vía SP.")
            cargar_tabla()
            limpiar_campos()
            navegar_bd("last")

        except Exception as e:
            messagebox.showerror("Error BD", str(e))
        finally:
            db_connector.release_connection(conn)

    def modificar():
        try:
            id_producto = int(current_product_id.get())
        except:
            messagebox.showwarning("Atención", "No hay producto seleccionado.")
            return

        if id_producto == 0: return

        nombre = entries["Nombre:"].get()
        categoria = entries["Categoría:"].get()
        try:
            precio = float(entries["Precio:"].get())
            stock = int(entries["Stock:"].get())
        except:
            messagebox.showerror("Error", "Precio/Stock inválidos")
            return

        marca = entries["Marca:"].get()
        descripcion = entries["Descripción:"].get()
        modelo = entries["Modelo:"].get()
        proveedor = entries["Proveedor:"].get()
        fecha_venc = datetime.datetime.now() + datetime.timedelta(days=180)
        ubicacion = "Almacén"
        estado = "Activo"

        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
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

    def eliminar():
        try:
            id_producto = int(current_product_id.get())
        except:
            return

        if not messagebox.askyesno("Confirmar", "¿Eliminar este producto?"):
            return

        conn = db_connector.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.callproc("pkg_gestion_productos.sp_eliminar", [id_producto])
            conn.commit()
            cargar_tabla()
            limpiar_campos()
            messagebox.showinfo("Éxito", "Producto eliminado vía SP.")
        except Exception as e:
            messagebox.showerror("Error BD", str(e))
        finally:
            db_connector.release_connection(conn)

    def limpiar_campos():
        current_product_id.set("0")
        for label, entry in entries.items():
            entry.configure(state="normal")
            entry.delete(0, "end")
        entries["Ubicación:"].insert(0, "Almacén")
        entries["Ubicación:"].configure(state="disabled", fg_color="#EEEEEE")
        entries["ID Producto:"].configure(state="disabled", fg_color="#EEEEEE")
        tree.selection_remove(tree.selection())

    # Botones CRUD
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

    # NAVEGACIÓN (Botones llamando a la BD)
    nav_frame = ctk.CTkFrame(main_form_frame, fg_color="transparent")
    nav_frame.grid(row=2, column=0, padx=20, pady=10)

    ctk.CTkButton(nav_frame, text="<< Primero", width=80, command=lambda: navegar_bd("first")).grid(row=0, column=0,
                                                                                                    padx=5)
    ctk.CTkButton(nav_frame, text="< Anterior", width=80, command=lambda: navegar_bd("prev")).grid(row=0, column=1,
                                                                                                   padx=5)
    ctk.CTkButton(nav_frame, text="Siguiente >", width=80, command=lambda: navegar_bd("next")).grid(row=0, column=2,
                                                                                                    padx=5)
    ctk.CTkButton(nav_frame, text="Último >>", width=80, command=lambda: navegar_bd("last")).grid(row=0, column=3,
                                                                                                  padx=5)