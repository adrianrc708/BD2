import customtkinter as ctk
from db import db_connector
import oracledb


def create_reports_view(parent_frame):
    parent_frame.grid_columnconfigure(0, weight=1)
    parent_frame.grid_rowconfigure(2, weight=1)

    title_label = ctk.CTkLabel(parent_frame, text="Generador de Reportes (Vía SYS_REFCURSOR)",
                               font=ctk.CTkFont(size=24, weight="bold"),
                               text_color="#333333")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    button_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")

    # Funciones Lambda para botones
    def run_ventas(): ejecutar_reporte_cursor("pkg_reportes.rep_ventas_por_mes", [], formatear_ventas)

    def run_stock(): ejecutar_reporte_cursor("pkg_reportes.rep_productos_stock_bajo", [5], formatear_stock)

    def run_vendidos(): ejecutar_reporte_cursor("pkg_reportes.rep_productos_mas_vendidos", [], formatear_vendidos)

    def run_valor(): ejecutar_reporte_cursor("pkg_reportes.rep_valor_inventario", [], formatear_valor)

    def run_auditoria(): ejecutar_reporte_cursor("pkg_reportes.rep_auditoria_cambios", [], formatear_auditoria)

    # Botones
    ctk.CTkButton(button_frame, text="Ventas por Mes", command=run_ventas, width=140, fg_color="#5BC0DE").grid(row=0,
                                                                                                               column=0,
                                                                                                               padx=5,
                                                                                                               pady=5)
    ctk.CTkButton(button_frame, text="Stock Bajo (<5)", command=run_stock, width=140, fg_color="#5BC0DE").grid(row=0,
                                                                                                               column=1,
                                                                                                               padx=5,
                                                                                                               pady=5)
    ctk.CTkButton(button_frame, text="Más Vendidos", command=run_vendidos, width=140, fg_color="#5BC0DE").grid(row=0,
                                                                                                               column=2,
                                                                                                               padx=5,
                                                                                                               pady=5)
    ctk.CTkButton(button_frame, text="Valor Inventario", command=run_valor, width=140, fg_color="#F0AD4E").grid(row=1,
                                                                                                                column=0,
                                                                                                                padx=5,
                                                                                                                pady=5)
    ctk.CTkButton(button_frame, text="Auditoría Precios", command=run_auditoria, width=140, fg_color="#D9534F").grid(
        row=1, column=1, padx=5, pady=5)

    global textbox
    textbox = ctk.CTkTextbox(parent_frame, fg_color="#F9F9F9", text_color="black", border_color="#E0E0E0",
                             border_width=2)
    textbox.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
    textbox.insert("0.0", "Seleccione un reporte...")


# ================================================================
# FUNCIÓN GENÉRICA PARA EJECUTAR SP CON CURSOR DE SALIDA
# ================================================================
def ejecutar_reporte_cursor(proc_name, params_in, format_func):
    textbox.delete("1.0", "end")
    conn = db_connector.get_connection()
    if conn is None: return

    try:
        cur = conn.cursor()
        out_cur = conn.cursor()  # Cursor variable para recibir los datos

        # Combinamos parámetros de entrada con el cursor de salida al final
        all_params = params_in + [out_cur]

        cur.callproc(proc_name, all_params)

        # Leemos los datos del cursor devuelto
        rows = list(out_cur)
        format_func(textbox, rows)

    except Exception as e:
        textbox.insert("end", f"Error ejecutando reporte: {e}")
    finally:
        db_connector.release_connection(conn)


# ================================================================
# FORMATOS DE SALIDA (PYTHON SE ENCARGA DEL DISEÑO)
# ================================================================
def formatear_ventas(tb, rows):
    tb.insert("end", "--- VENTAS POR MES ---\n\n")
    tb.insert("end", f"{'MES':<15} | {'TOTAL'}\n")
    tb.insert("end", "-" * 30 + "\n")
    for r in rows:
        tb.insert("end", f"{r[0]:<15} | ${r[1]:,.2f}\n")


def formatear_stock(tb, rows):
    tb.insert("end", "--- STOCK BAJO ---\n\n")
    for r in rows:
        tb.insert("end", f"[ID {r[0]}] {r[1]} -> Stock: {r[2]}\n")


def formatear_vendidos(tb, rows):
    tb.insert("end", "--- PRODUCTOS MÁS VENDIDOS ---\n\n")
    for r in rows:
        tb.insert("end", f"{r[0]} -> {r[1]} unidades\n")


def formatear_valor(tb, rows):
    tb.insert("end", "--- VALORIZACIÓN DE INVENTARIO ---\n\n")
    tb.insert("end", f"{'CATEGORIA':<20} | {'STOCK':<8} | {'VALOR ($)'}\n")
    tb.insert("end", "-" * 50 + "\n")
    total = 0
    for r in rows:
        # r[0]=cat, r[1]=items, r[2]=stock, r[3]=valor
        tb.insert("end", f"{r[0]:<20} | {r[2]:<8} | ${r[3]:,.2f}\n")
        if r[3]: total += r[3]
    tb.insert("end", "-" * 50 + "\n")
    tb.insert("end", f"VALOR TOTAL: ${total:,.2f}")


def formatear_auditoria(tb, rows):
    tb.insert("end", "--- AUDITORÍA DE CAMBIOS DE PRECIO ---\n\n")
    if not rows: tb.insert("end", "No hay registros.")
    for r in rows:
        # r[0]=nom, r[1]=ant, r[2]=nue, r[3]=fecha, r[4]=user
        tb.insert("end", f"[{r[3]}] {r[0]}\n")
        tb.insert("end", f"   Cambió de ${r[1]} a ${r[2]} (Por: {r[4]})\n\n")