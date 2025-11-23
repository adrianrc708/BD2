import flet as ft
import matplotlib
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart
from db import db_connector
from fpdf import FPDF
import datetime
import os  # Importar os para manejo de rutas

matplotlib.use("svg")


def vista_reportes(page: ft.Page):
    # --- ESTADO ---
    estado = {"reporte_actual": ""}

    # --- COMPONENTES UI ---

    # 1. Gráfico de Ventas
    def crear_grafico_ventas(datos):
        datos_grafico = datos[::-1]
        meses = [d[0] for d in datos_grafico]
        totales = [d[1] for d in datos_grafico]

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_alpha(0)

        barras = ax.bar(meses, totales, color="#5C6BC0", zorder=3, width=0.6)
        ax.set_title("Tendencia de Ingresos Mensuales", fontsize=12, weight='bold', color="#333333", pad=15)
        ax.set_ylabel("Monto ($)", fontsize=9, color="grey")
        ax.tick_params(axis='x', colors="#555555", labelsize=9)
        ax.tick_params(axis='y', colors="#555555", labelsize=9)
        ax.grid(axis='y', linestyle='--', alpha=0.4, color="grey", zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#CCCCCC')

        # AQUI AGREGAMOS EL SIMBOLO DE DINERO AL TEXTO
        for bar in barras:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + (height * 0.01),
                    f'${height:,.2f}',
                    ha='center', va='bottom', fontsize=8, color="#333333", weight="bold")

        plt.tight_layout()
        return MatplotlibChart(fig, expand=True, transparent=True)

    contenedor_grafico = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.BAR_CHART, size=40, color=ft.Colors.GREY_300),
            ft.Text("Seleccione 'Ventas Mensuales' para visualizar estadísticas", color="grey")
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        height=350, bgcolor="white", padding=20, border_radius=12,
        alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12),
        visible=False
    )

    # 2. Tabla de Resultados
    tabla_resultados = ft.DataTable(
        width=float("inf"),
        columns=[ft.DataColumn(ft.Text("Detalle"))],
        rows=[],
        heading_row_color=ft.Colors.GREY_100,
        data_row_min_height=50,
        border=ft.border.all(1, ft.Colors.GREY_200),
        border_radius=8,
        column_spacing=30
    )

    contenedor_tabla = ft.Container(
        content=ft.Column([tabla_resultados], scroll=ft.ScrollMode.AUTO),
        expand=True, bgcolor="white", padding=10, border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
    )

    # --- LÓGICA PDF CON FILE PICKER ---

    def guardar_archivo_resultado(e: ft.FilePickerResultEvent):
        if not e.path:
            return  # Usuario canceló

        ruta_destino = e.path
        # Asegurarse que tenga extensión .pdf
        if not ruta_destino.lower().endswith(".pdf"):
            ruta_destino += ".pdf"

        conn = db_connector.get_connection()
        if not conn: return

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Reporte General del Sistema", ln=True, align='C')
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
            pdf.ln(10)

            def agregar_seccion(titulo, sp_name, params, headers):
                pdf.set_font("Arial", "B", 12)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(0, 10, titulo, ln=True, fill=True)
                pdf.ln(2)

                pdf.set_font("Arial", "B", 9)
                ancho_col = 190 / len(headers)
                for h in headers:
                    pdf.cell(ancho_col, 8, h, border=1, align='C')
                pdf.ln()

                pdf.set_font("Arial", "", 9)
                cur = conn.cursor()
                out_cur = conn.cursor()
                cur.callproc(sp_name, params + [out_cur])

                for row in out_cur:
                    for val in row:
                        texto = str(val)
                        if isinstance(val, (int, float)) and ("$" in str(headers) or "Precio" in str(headers)):
                            texto = f"${val:,.2f}"
                        pdf.cell(ancho_col, 8, texto[:25], border=1)
                    pdf.ln()
                pdf.ln(10)

            agregar_seccion("1. Historial de Ventas", "pkg_reportes.rep_ventas_por_mes", [], ["Mes", "Total ($)"])
            agregar_seccion("2. Productos con Stock Bajo", "pkg_reportes.rep_productos_stock_bajo", [5],
                            ["ID", "Producto", "Stock"])
            agregar_seccion("3. Top Productos Vendidos", "pkg_reportes.rep_productos_mas_vendidos", [],
                            ["Producto", "Total U."])
            agregar_seccion("4. Valorización de Inventario", "pkg_reportes.rep_valor_inventario", [],
                            ["Cat.", "Items", "Stock", "Valor ($)"])
            agregar_seccion("5. Auditoría de Precios", "pkg_reportes.rep_auditoria_cambios", [],
                            ["Producto", "Ant.", "Nuevo", "Fecha", "User"])

            pdf.output(ruta_destino)

            page.snack_bar = ft.SnackBar(ft.Text(f"✅ PDF guardado en: {ruta_destino}"), bgcolor="green")
            page.snack_bar.open = True
            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error generando PDF: {ex}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
        finally:
            db_connector.release_connection(conn)

    # Inicializar FilePicker
    file_picker = ft.FilePicker(on_result=guardar_archivo_resultado)
    page.overlay.append(file_picker)  # AGREGAR AL OVERLAY ES OBLIGATORIO

    def abrir_selector_archivo(e):
        nombre_defecto = f"Reporte_OraclePOS_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        file_picker.save_file(
            dialog_title="Guardar Reporte PDF",
            file_name=nombre_defecto,
            allowed_extensions=["pdf"]
        )

    # --- LÓGICA VISUALIZACIÓN ---
    def ejecutar_reporte(titulo, proc_name, params, columnas_header, es_grafico=False):
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            out_cur = conn.cursor()
            cur.callproc(proc_name, params + [out_cur])
            rows = list(out_cur)

            lbl_titulo_seccion.value = f"Reporte: {titulo}"
            tabla_resultados.columns = [ft.DataColumn(ft.Text(h, weight="bold", color=ft.Colors.INDIGO_900)) for h in
                                        columnas_header]
            tabla_resultados.rows.clear()

            for r in rows:
                celdas = []
                for i, val in enumerate(r):
                    header_name = columnas_header[i]
                    texto_formateado = str(val)
                    if isinstance(val, (int, float)):
                        if "($)" in header_name or "Precio" in header_name or "Valor" in header_name:
                            texto_formateado = f"${val:,.2f}"
                    celdas.append(ft.DataCell(ft.Text(texto_formateado, size=13, color=ft.Colors.GREY_800)))
                tabla_resultados.rows.append(ft.DataRow(cells=celdas))

            if es_grafico and rows:
                contenedor_grafico.content = crear_grafico_ventas(rows)
                contenedor_grafico.visible = True
            else:
                contenedor_grafico.visible = False

            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
        finally:
            db_connector.release_connection(conn)

    # --- UI CARDS ---
    def crear_card_reporte(icon, titulo, subtitulo, color_icon, func):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color_icon, size=32),
                ft.Text(titulo, weight="bold", size=14, color=ft.Colors.BLUE_GREY_900),
                ft.Text(subtitulo, size=11, color=ft.Colors.GREY_600, text_align="center")
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15, width=150, height=110, bgcolor="white", border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.BLACK12, offset=ft.Offset(2, 2)),
            ink=True, on_click=func, animate=ft.Animation(200, "easeOut")
        )

    def ver_ventas(e):
        ejecutar_reporte("Ventas Mensuales", "pkg_reportes.rep_ventas_por_mes", [], ["Mes", "Total ($)"], True)

    def ver_stock(e):
        ejecutar_reporte("Stock Crítico", "pkg_reportes.rep_productos_stock_bajo", [5],
                         ["ID", "Producto", "Stock Actual"])

    def ver_top(e):
        ejecutar_reporte("Más Vendidos", "pkg_reportes.rep_productos_mas_vendidos", [],
                         ["Producto", "Total Unidades Vendidas"])

    def ver_valor(e):
        ejecutar_reporte("Valorización", "pkg_reportes.rep_valor_inventario", [],
                         ["Categoría", "Items", "Stock Total", "Valor Total ($)"])

    def ver_audit(e):
        ejecutar_reporte("Auditoría", "pkg_reportes.rep_auditoria_cambios", [],
                         ["Producto", "Precio Ant. ($)", "Precio Nuevo ($)", "Fecha Cambio", "Usuario Oracle"])

    lbl_titulo_seccion = ft.Text("Inteligencia de Negocios", size=24, weight="bold", color=ft.Colors.BLUE_GREY_900)

    # BOTÓN DE GENERAR PDF (ACTUALIZADO)
    btn_pdf = ft.ElevatedButton(
        "Generar Reporte",
        icon=ft.Icons.PICTURE_AS_PDF,
        bgcolor=ft.Colors.RED_600,
        color="white",
        on_click=abrir_selector_archivo  # Ahora abre el selector
    )

    fila_cards = ft.Row([
        crear_card_reporte(ft.Icons.BAR_CHART_ROUNDED, "Ventas", "Histórico Mensual", ft.Colors.INDIGO, ver_ventas),
        crear_card_reporte(ft.Icons.WARNING_ROUNDED, "Stock Bajo", "Alerta Inventario", ft.Colors.ORANGE, ver_stock),
        crear_card_reporte(ft.Icons.STAR_ROUNDED, "Top Productos", "Lo más vendido", ft.Colors.PURPLE, ver_top),
        crear_card_reporte(ft.Icons.MONETIZATION_ON_ROUNDED, "Finanzas", "Valor del Stock", ft.Colors.GREEN, ver_valor),
        crear_card_reporte(ft.Icons.SECURITY_ROUNDED, "Auditoría", "Cambios de Precio", ft.Colors.RED, ver_audit),
    ], scroll=ft.ScrollMode.HIDDEN, spacing=20)

    return ft.Container(
        content=ft.Column([
            ft.Row([lbl_titulo_seccion, btn_pdf], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=20, color="transparent"),
            fila_cards,
            ft.Divider(height=20, color="transparent"),
            ft.Column([
                contenedor_grafico,
                ft.Divider(height=15, color="transparent"),
                ft.Text("Detalle de Datos", weight="bold", color="grey"),
                contenedor_tabla
            ], expand=True, scroll=ft.ScrollMode.AUTO)
        ], expand=True),
        expand=True,
        padding=30
    )