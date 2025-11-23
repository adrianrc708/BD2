import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox
import oracledb
from db import db_connector

# --- VARIABLES GLOBALES ---
carrito_productos = []
cliente_seleccionado = {"id": None, "nombre": "Público General"}
DEFAULT_EMPLEADO_ID = 1


def create_sales_view(parent_frame):
    global tree_carrito, lbl_total_valor, entry_id_prod, entry_cantidad
    global lbl_cliente_actual, entry_buscar_apellido, combo_clientes_encontrados
    global opciones_clientes_encontrados

    # Reiniciar estado
    carrito_productos.clear()
    cliente_seleccionado["id"] = 1
    cliente_seleccionado["nombre"] = "Cliente Genérico (ID 1)"
    opciones_clientes_encontrados = []

    # Configuración Visual
    parent_frame.grid_columnconfigure(0, weight=1)
    parent_frame.grid_columnconfigure(1, weight=2)
    parent_frame.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(parent_frame, text="Punto de Venta (Con Triggers Activos)",
                 font=ctk.CTkFont(size=24, weight="bold"), text_color="#333").grid(row=0, column=0, columnspan=2,
                                                                                   padx=20, pady=20, sticky="w")

    # === PANEL IZQUIERDO ===
    left_frame = ctk.CTkFrame(parent_frame, fg_color="#F9F9F9", corner_radius=10)
    left_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)

    # Cliente
    ctk.CTkLabel(left_frame, text="Cliente", font=ctk.CTkFont(size=16, weight="bold"), text_color="#555").pack(
        pady=(15, 5))
    lbl_cliente_actual = ctk.CTkLabel(left_frame, text=f"Seleccionado: {cliente_seleccionado['nombre']}",
                                      text_color="#2980B9", font=ctk.CTkFont(weight="bold"))
    lbl_cliente_actual.pack(pady=5)

    search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
    search_frame.pack(pady=5, padx=10, fill="x")
    entry_buscar_apellido = ctk.CTkEntry(search_frame, placeholder_text="Buscar Apellido...")
    entry_buscar_apellido.pack(side="left", fill="x", expand=True, padx=(0, 5))
    ctk.CTkButton(search_frame, text="🔍", width=40, command=buscar_cliente, fg_color="#3498DB").pack(side="right")

    combo_clientes_encontrados = ctk.CTkComboBox(left_frame, values=["Sin resultados"], command=seleccionar_cliente)
    combo_clientes_encontrados.pack(pady=5, padx=10, fill="x")
    ctk.CTkButton(left_frame, text="➕ Nuevo Cliente", command=ventana_nuevo_cliente, fg_color="#27AE60",
                  height=30).pack(pady=(5, 15), padx=10, fill="x")
    ctk.CTkFrame(left_frame, height=2, fg_color="#E0E0E0").pack(fill="x", padx=20, pady=10)

    # Producto
    ctk.CTkLabel(left_frame, text="Producto", font=ctk.CTkFont(size=16, weight="bold"), text_color="#555").pack(pady=5)
    ctk.CTkLabel(left_frame, text="ID Producto:", text_color="#555").pack()
    entry_id_prod = ctk.CTkEntry(left_frame, width=200, fg_color="white", text_color="black")
    entry_id_prod.pack(pady=5)
    entry_id_prod.bind('<Return>', lambda e: agregar_producto())

    ctk.CTkLabel(left_frame, text="Cantidad:", text_color="#555").pack()
    entry_cantidad = ctk.CTkEntry(left_frame, width=200, fg_color="white", text_color="black")
    entry_cantidad.pack(pady=5)
    entry_cantidad.insert(0, "1")
    entry_cantidad.bind('<Return>', lambda e: agregar_producto())
    ctk.CTkButton(left_frame, text="Agregar 🛒", command=agregar_producto, fg_color="#5BC0DE").pack(pady=20)

    # === PANEL DERECHO: CARRITO ===
    right_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    right_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)

    columns = ("id", "nombre", "precio", "cantidad", "subtotal")
    tree_carrito = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
    headers = ["ID", "Producto", "Precio", "Cant.", "Subtotal"]
    for col, head in zip(columns, headers):
        tree_carrito.heading(col, text=head)
        tree_carrito.column(col, width=80)
    tree_carrito.pack(fill="both", expand=True)

    # === PIE DE PÁGINA ===
    bottom_frame = ctk.CTkFrame(parent_frame, fg_color="white", height=80)
    bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
    ctk.CTkLabel(bottom_frame, text="TOTAL:", font=ctk.CTkFont(size=16)).pack(side="left", padx=20)
    lbl_total_valor = ctk.CTkLabel(bottom_frame, text="$ 0.00", font=ctk.CTkFont(size=24, weight="bold"),
                                   text_color="#27AE60")
    lbl_total_valor.pack(side="left", padx=10)
    ctk.CTkButton(bottom_frame, text="✅ CONFIRMAR VENTA", command=finalizar_venta_segura, fg_color="#28a745", width=200,
                  height=40).pack(side="right", padx=20)


# ================= LÓGICA =================

def buscar_cliente():
    apellido = entry_buscar_apellido.get().strip()
    if not apellido: return
    conn = db_connector.get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_cliente, nombre, apellido, dni FROM clientes WHERE LOWER(apellido) LIKE LOWER(:1)",
                       [f"%{apellido}%"])
        rows = cursor.fetchall()
        opciones_clientes_encontrados.clear()
        lista_visual = []
        if rows:
            for r in rows:
                opciones_clientes_encontrados.append({"id": r[0], "nombre": f"{r[1]} {r[2]}"})
                lista_visual.append(f"{r[2]}, {r[1]} (DNI: {r[3]})")
            combo_clientes_encontrados.configure(values=lista_visual)
            combo_clientes_encontrados.set(lista_visual[0])
            seleccionar_cliente(lista_visual[0])
        else:
            combo_clientes_encontrados.configure(values=["No encontrado"])
            combo_clientes_encontrados.set("No encontrado")
    except Exception as e:
        print(e)
    finally:
        db_connector.release_connection(conn)


def seleccionar_cliente(valor):
    if not opciones_clientes_encontrados: return
    vals = combo_clientes_encontrados.cget("values")
    if valor in vals:
        idx = vals.index(valor)
        sel = opciones_clientes_encontrados[idx]
        cliente_seleccionado["id"] = sel["id"]
        cliente_seleccionado["nombre"] = sel["nombre"]
        lbl_cliente_actual.configure(text=f"Seleccionado: {cliente_seleccionado['nombre']}")


def ventana_nuevo_cliente():
    top = ctk.CTkToplevel()
    top.geometry("300x350")
    campos = {}
    for txt in ["Nombre", "Apellido", "DNI", "Correo"]:
        ctk.CTkEntry(top, placeholder_text=txt).pack(pady=5, padx=20, fill="x")
        campos[txt] = top.winfo_children()[-1]

    def guardar():
        vals = [campos[k].get() for k in ["Nombre", "Apellido", "DNI", "Correo"]]
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            id_new = cur.var(oracledb.NUMBER)
            cur.execute(
                "INSERT INTO clientes (nombre, apellido, dni, correo) VALUES (:1,:2,:3,:4) RETURNING id_cliente INTO :5",
                vals + [id_new])
            conn.commit()
            cliente_seleccionado["id"] = id_new.getvalue()[0]
            cliente_seleccionado["nombre"] = f"{vals[0]} {vals[1]}"
            lbl_cliente_actual.configure(text=f"Seleccionado: {cliente_seleccionado['nombre']}")
            top.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=top)
        finally:
            db_connector.release_connection(conn)

    ctk.CTkButton(top, text="Guardar", command=guardar).pack(pady=20)


def agregar_producto():
    id_p = entry_id_prod.get().strip()
    cant_p = entry_cantidad.get().strip()
    if not id_p or not cant_p: return

    conn = db_connector.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT nombre, precio, stock FROM productos WHERE id_producto = :1", [id_p])
        row = cur.fetchone()
        if row:
            cant = int(cant_p)
            # Validación preventiva (opcional, el trigger también protege)
            if row[2] < cant:
                messagebox.showwarning("Stock", f"Stock insuficiente. Disponible: {row[2]}")
                return
            subtotal = row[1] * cant
            carrito_productos.append(
                {"id": int(id_p), "nombre": row[0], "precio": row[1], "cantidad": cant, "subtotal": subtotal})
            tree_carrito.insert("", "end", values=(id_p, row[0], f"{row[1]:.2f}", cant, f"{subtotal:.2f}"))
            lbl_total_valor.configure(text=f"$ {sum(i['subtotal'] for i in carrito_productos):.2f}")
            entry_id_prod.delete(0, "end");
            entry_cantidad.delete(0, "end");
            entry_cantidad.insert(0, "1")
        else:
            messagebox.showerror("Error", "Producto no encontrado")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        db_connector.release_connection(conn)


def finalizar_venta_segura():
    if not carrito_productos: return
    total = sum(i["subtotal"] for i in carrito_productos)
    conn = db_connector.get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        id_venta = cursor.var(oracledb.NUMBER)

        # 1. Crear Venta
        cursor.execute("""
                       INSERT INTO ventas (id_cliente, id_empleado, total)
                       VALUES (:1, :2, :3) RETURNING id_venta
                       INTO :4
                       """, [cliente_seleccionado["id"], DEFAULT_EMPLEADO_ID, total, id_venta])

        venta_generada = id_venta.getvalue()[0]

        # 2. Insertar Detalle (Esto dispara el TRIGGER 'trg_control_stock' en la BD)
        #    El trigger se encargará de restar el stock y validar si alcanza.
        for item in carrito_productos:
            cursor.execute("""
                           INSERT INTO detalle_venta (id_venta, id_producto, cantidad, subtotal)
                           VALUES (:1, :2, :3, :4)
                           """, [venta_generada, item["id"], item["cantidad"], item["subtotal"]])

        # ¡IMPORTANTE! YA NO HACEMOS UPDATE MANUAL A PRODUCTOS AQUÍ.

        conn.commit()
        messagebox.showinfo("Venta Exitosa", f"Venta {int(venta_generada)} registrada.")
        carrito_productos.clear()
        for item in tree_carrito.get_children(): tree_carrito.delete(item)
        lbl_total_valor.configure(text="$ 0.00")

    except Exception as e:
        conn.rollback()
        # Si el trigger falla (ej. stock insuficiente), el error vendrá aquí.
        err_msg = str(e)
        if "ORA-20002" in err_msg:
            messagebox.showerror("Stock Insuficiente", "El trigger bloqueó la venta: Stock insuficiente en la BD.")
        elif "ORA-20005" in err_msg:
            messagebox.showerror("Producto Vencido", "El trigger bloqueó la venta: Intenta vender un producto vencido.")
        else:
            messagebox.showerror("Error en Venta", f"Error: {e}")
    finally:
        db_connector.release_connection(conn)