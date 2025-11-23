import customtkinter as ctk
from db import db_connector

def create_reports_view(parent_frame):
    parent_frame.grid_columnconfigure(0, weight=1)
    parent_frame.grid_rowconfigure(2, weight=1)

    # ---------------------------------------------------
    # TÍTULO
    # ---------------------------------------------------
    title_label = ctk.CTkLabel(parent_frame, text="Generador de Reportes (5 Tipos)",
                               font=ctk.CTkFont(size=24, weight="bold"),
                               text_color="#333333")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    # ---------------------------------------------------
    # FRAME DE BOTONES (Organizados en 2 filas)
    # ---------------------------------------------------
    button_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")

    # Funciones lambda o wrappers
    def run_ventas(): mostrar_reporte_ventas(textbox)
    def run_stock(): mostrar_reporte_stock(textbox)
    def run_vendidos(): mostrar_reporte_vendidos(textbox)
    def run_valor(): mostrar_reporte_valor_inventario(textbox)
    def run_auditoria(): mostrar_reporte_auditoria(textbox)

    # --- FILA 1 DE BOTONES (Originales) ---
    btn_mes = ctk.CTkButton(button_frame, text="Ventas por Mes", command=run_ventas, width=140, fg_color="#5BC0DE", hover_color="#469DB8")
    btn_mes.grid(row=0, column=0, padx=5, pady=5)

    btn_stock = ctk.CTkButton(button_frame, text="Stock Bajo", command=run_stock, width=140, fg_color="#5BC0DE", hover_color="#469DB8")
    btn_stock.grid(row=0, column=1, padx=5, pady=5)

    btn_top = ctk.CTkButton(button_frame, text="Más Vendidos", command=run_vendidos, width=140, fg_color="#5BC0DE", hover_color="#469DB8")
    btn_top.grid(row=0, column=2, padx=5, pady=5)

    # --- FILA 2 DE BOTONES (Nuevos / Elaborados) ---
    btn_valor = ctk.CTkButton(button_frame, text="Valor Inventario ($)", command=run_valor, width=140, fg_color="#F0AD4E", hover_color="#D58512")
    btn_valor.grid(row=1, column=0, padx=5, pady=5)

    btn_audit = ctk.CTkButton(button_frame, text="Auditoría Precios", command=run_auditoria, width=140, fg_color="#D9534F", hover_color="#C9302C")
    btn_audit.grid(row=1, column=1, padx=5, pady=5)


    # ---------------------------------------------------
    # TEXTBOX
    # ---------------------------------------------------
    global textbox
    textbox = ctk.CTkTextbox(parent_frame, fg_color="#F9F9F9", text_color="black", border_color="#E0E0E0", border_width=2)
    textbox.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
    textbox.insert("0.0", "Seleccione un reporte para ver los resultados...")


# ================================================================
# 1) REPORTE: VENTAS POR MES (ORIGINAL)
# ================================================================
def mostrar_reporte_ventas(textbox):
    textbox.delete("1.0", "end")
    textbox.insert("end", "Generando reporte de ventas por mes...\n\n")
    conn = db_connector.get_connection()
    if conn is None: return
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT TO_CHAR(fecha_venta, 'YYYY-MM') AS mes, SUM(total) AS total_mes
            FROM ventas GROUP BY TO_CHAR(fecha_venta, 'YYYY-MM') ORDER BY mes DESC
        """)
        textbox.insert("end", "--- VENTAS POR MES ---\n\n")
        for mes, total in cur:
            textbox.insert("end", f"Mes: {mes}   Total: {total}\n")
    except Exception as e: textbox.insert("end", f"Error: {e}")
    finally: db_connector.release_connection(conn)


# ================================================================
# 2) REPORTE: STOCK BAJO (ORIGINAL)
# ================================================================
def mostrar_reporte_stock(textbox):
    textbox.delete("1.0", "end")
    textbox.insert("end", "Generando reporte de stock bajo (<= 5)...\n\n")
    conn = db_connector.get_connection()
    if conn is None: return
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_producto, nombre, stock FROM productos WHERE stock <= 5 ORDER BY stock ASC")
        textbox.insert("end", "--- STOCK BAJO ---\n\n")
        for idp, nombre, stock in cur:
            textbox.insert("end", f"{idp} | {nombre} | Stock: {stock}\n")
    except Exception as e: textbox.insert("end", f"Error: {e}")
    finally: db_connector.release_connection(conn)


# ================================================================
# 3) REPORTE: MÁS VENDIDOS (ORIGINAL)
# ================================================================
def mostrar_reporte_vendidos(textbox):
    textbox.delete("1.0", "end")
    textbox.insert("end", "Generando ranking de productos...\n\n")
    conn = db_connector.get_connection()
    if conn is None: return
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.nombre, SUM(d.cantidad) vendidos
            FROM productos p JOIN detalle_venta d ON p.id_producto = d.id_producto
            GROUP BY p.nombre ORDER BY vendidos DESC
        """)
        textbox.insert("end", "--- MÁS VENDIDOS ---\n\n")
        for nombre, vendidos in cur:
            textbox.insert("end", f"{nombre} | Vendidos: {vendidos}\n")
    except Exception as e: textbox.insert("end", f"Error: {e}")
    finally: db_connector.release_connection(conn)


# ================================================================
# 4) REPORTE: VALOR DE INVENTARIO (NUEVO)
# ================================================================
def mostrar_reporte_valor_inventario(textbox):
    textbox.delete("1.0", "end")
    textbox.insert("end", "Calculando dinero invertido en almacén...\n\n")
    conn = db_connector.get_connection()
    if conn is None: return
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT categoria, COUNT(*) as items, SUM(stock) as stock_total, SUM(precio * stock) as valor_total
            FROM productos WHERE stock > 0 GROUP BY categoria ORDER BY valor_total DESC
        """)
        textbox.insert("end", "--- VALORIZACIÓN (DINERO EN PRODUCTOS) ---\n\n")
        textbox.insert("end", f"{'CATEGORÍA':<20} | {'STOCK':<5} | {'VALOR ($)'}\n")
        textbox.insert("end", "-"*50 + "\n")
        
        gt = 0
        for cat, items, stock, valor in cur:
            textbox.insert("end", f"{cat:<20} | {stock:<5} | ${valor:,.2f}\n")
            gt += valor
        textbox.insert("end", "-"*50 + "\n")
        textbox.insert("end", f"TOTAL GENERAL: ${gt:,.2f}")
    except Exception as e: textbox.insert("end", f"Error: {e}")
    finally: db_connector.release_connection(conn)


# ================================================================
# 5) REPORTE: AUDITORÍA (NUEVO - REQUERIDO POR TRIGGER)
# ================================================================
def mostrar_reporte_auditoria(textbox):
    textbox.delete("1.0", "end")
    textbox.insert("end", "Consultando bitácora de cambios de precios...\n\n")
    conn = db_connector.get_connection()
    if conn is None: return
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.nombre, h.precio_anterior, h.precio_nuevo, TO_CHAR(h.fecha_cambio, 'DD/MM HH24:MI') as fecha, h.usuario_modifico
            FROM historial_precios h JOIN productos p ON h.id_producto = p.id_producto
            ORDER BY h.fecha_cambio DESC
        """)
        textbox.insert("end", "--- AUDITORÍA DE PRECIOS ---\n\n")
        rows = cur.fetchall()
        if not rows:
            textbox.insert("end", "No hay cambios registrados aún.")
        else:
            for nombre, ant, nue, fecha, user in rows:
                textbox.insert("end", f"[{fecha}] {nombre}\n")
                textbox.insert("end", f"   Cambio: ${ant} -> ${nue} (User: {user})\n\n")
    except Exception as e: textbox.insert("end", f"Error: {e}")
    finally: db_connector.release_connection(conn)
