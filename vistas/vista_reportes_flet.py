import flet as ft
import matplotlib
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart
from db import db_connector
from fpdf import FPDF
import datetime
import os
import oracledb

matplotlib.use("svg")

# --- CONFIGURACIÓN PARA EL SCROLL ---
fila_cards_ref = ft.Ref[ft.Row]()


def vista_reportes(page: ft.Page):
    # ==================================================
    # 1. CONTROLES Y LÓGICA DE FILTROS (DEFINICIONES)
    # ==================================================

    # 1. Definición de Controles de Filtro
    dd_filtro_mes = ft.Dropdown(
        label="Filtro Mes (YYYY-MM)",
        hint_text="Global (Todos)",
        width=180, text_size=13,
        bgcolor=ft.Colors.GREY_50, border_color=ft.Colors.GREY_300,
        options=[ft.dropdown.Option(text="Global (Todos)", key="None")],
        value="None"
    )

    dd_empleado_filtro = ft.Dropdown(
        label="Filtro Empleado",
        hint_text="Global (Todos)",
        width=250, text_size=13,
        bgcolor=ft.Colors.GREY_50, border_color=ft.Colors.GREY_300,
        options=[ft.dropdown.Option(text="Global (Todos)", key="0")],
        value="0"
    )

    def cargar_empleados():
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("SELECT id_empleado, nombre, apellido FROM empleados WHERE id_empleado <= 100 ORDER BY nombre")
            rows = cur.fetchall()

            dd_empleado_filtro.options.clear()
            dd_empleado_filtro.options.append(ft.dropdown.Option(text="Global (Todos)", key="0"))

            for r in rows:
                dd_empleado_filtro.options.append(ft.dropdown.Option(text=f"{r[1]} {r[2]}", key=str(r[0])))

            dd_empleado_filtro.update()
        except:
            pass
        finally:
            db_connector.release_connection(conn)

    def cargar_meses():
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT TO_CHAR(fecha_venta, 'YYYY-MM') FROM ventas ORDER BY 1 DESC")
            rows = cur.fetchall()

            dd_filtro_mes.options.clear()
            dd_filtro_mes.options.append(ft.dropdown.Option(text="Global (Todos)", key="None"))

            for r in rows:
                dd_filtro_mes.options.append(ft.dropdown.Option(text=r[0], key=r[0]))

            dd_filtro_mes.update()
        except:
            pass
        finally:
            db_connector.release_connection(conn)

    cargar_empleados()
    cargar_meses()

    # 2. Lógica para aplicar el filtro (llamada por el botón)
    def aplicar_filtro_kpi(e):
        filtro_mes = dd_filtro_mes.value if dd_filtro_mes.value != "None" else None

        filtro_empleado_id = None
        if dd_empleado_filtro.value and dd_empleado_filtro.value != "0":
            try:
                filtro_empleado_id = int(dd_empleado_filtro.value)
            except ValueError:
                filtro_empleado_id = None

        params = [filtro_mes, filtro_empleado_id]

        ejecutar_reporte("KPIs (Filtrado)", "pkg_reportes.rep_resumen_estadistico",
                         params,
                         ["Ámbito", "Ticket Prom. ($)", "Máximo", "Mínimo", "Total Trans."])

    # 3. Botón y Contenedor de Filtros 
    btn_aplicar_filtro = ft.ElevatedButton(
        "APLICAR FILTRO",
        icon=ft.Icons.CHECK,
        bgcolor=ft.Colors.INDIGO,
        color="white",
        on_click=aplicar_filtro_kpi
    )

    contenedor_filtros_kpi = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.FILTER_LIST, color=ft.Colors.INDIGO, size=20),
            ft.Text("Filtros de Análisis:", weight="bold", color=ft.Colors.BLUE_GREY_700, size=14),
            dd_filtro_mes,
            dd_empleado_filtro,
            btn_aplicar_filtro
        ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=10,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
        border=ft.border.all(1, ft.Colors.INDIGO_200),
        visible=False  
    )

    # ==================================================

    # --- LÓGICA DE SCROLL LATERAL ---
    def mover_cards(e, direccion):
        fila = fila_cards_ref.current
        paso_scroll = 1500

        current_offset = fila.offset if fila.offset is not None else 0

        if direccion == 'left':
            new_offset = max(0, current_offset - paso_scroll)
        else:
            new_offset = current_offset + paso_scroll

        fila.scroll_to(offset=new_offset, duration=300)
        page.update()

    # --- DEFINICIÓN DE CONTROLES PRINCIPALES ---
    lbl_titulo_seccion = ft.Text("Inteligencia de Negocios", size=24, weight="bold",
                                 color=ft.Colors.BLUE_GREY_900)

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
        columns=[
            ft.DataColumn(ft.Text("Col 1")),
            ft.DataColumn(ft.Text("Col 2")),
            ft.DataColumn(ft.Text("Col 3")),
            ft.DataColumn(ft.Text("Col 4")),
        ],
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

    # --- LÓGICA PDF  ---
    def guardar_archivo_resultado(e: ft.FilePickerResultEvent):
        if not e.path:
            return

        ruta_destino = e.path
        if not ruta_destino.lower().endswith(".pdf"):
            ruta_destino += ".pdf"

        conn = db_connector.get_connection()
        if not conn: return

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Reporte General del Sistema (10 Items)", ln=True, align='C')
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
            pdf.ln(10)

            def agregar_seccion(titulo, sp_name, params, headers, is_agg=True):
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
                    data_row = list(row)

                    if sp_name in ('pkg_reportes.rep_mejores_clientes', 'pkg_reportes.rep_empleados_ingresos'):
                      
                        nombre_completo = f"{data_row[0]}" if len(data_row) == 3 else f"{data_row[0]} {data_row[1]}"

                        pdf.cell(ancho_col, 8, nombre_completo[:25], border=1)

                        start_index = 1 if len(data_row) == 3 else 2

                        for val in data_row[start_index:]:
                            texto = str(val)
                            if isinstance(val, (int, float)):
                                texto = f"${val:,.2f}"
                            pdf.cell(ancho_col, 8, texto[:25], border=1)

                    else:
                        for val in data_row:
                            texto = str(val)
                            if isinstance(val, (int, float)) and is_agg:
                                texto = f"${val:,.2f}"
                            pdf.cell(ancho_col, 8, texto[:25], border=1)

                    pdf.ln()
                pdf.ln(10)

            agregar_seccion("1. Historial de Ventas", "pkg_reportes.rep_ventas_por_mes", [], ["Mes", "Total ($)"])
            agregar_seccion("2. Productos con Stock Bajo", "pkg_reportes.rep_productos_stock_bajo", [5],
                            ["ID", "Producto", "Stock"], False)
            agregar_seccion("3. Top Productos Vendidos", "pkg_reportes.rep_productos_mas_vendidos", [],
                            ["Producto", "Total U."])
            agregar_seccion("4. Valorización de Inventario", "pkg_reportes.rep_valor_inventario", [],
                            ["Cat.", "Items", "Stock", "Valor ($)"])
            agregar_seccion("5. Auditoría de Precios", "pkg_reportes.rep_auditoria_cambios", [],
                            ["Producto", "Ant.", "Nuevo", "Fecha", "User"], False)
            agregar_seccion("6. Top Clientes", "pkg_reportes.rep_mejores_clientes", [],
                            ["Nombre Completo", "N° Compras", "Total Gastado ($)"])
            agregar_seccion("7. Rendimiento Empleados", "pkg_reportes.rep_empleados_ingresos", [],
                            ["Empleado", "N° Ventas", "Generado ($)"])
            agregar_seccion("8. Ventas por Categoría", "pkg_reportes.rep_ventas_por_categoria", [],
                            ["Categoría", "Items", "Ingresos ($)"])
            agregar_seccion("9. Productos Sin Ventas", "pkg_reportes.rep_productos_sin_ventas", [],
                            ["Producto", "Stock Actual", "Categoría"], False)
          
            agregar_seccion("10. KPIs Globales", "pkg_reportes.rep_resumen_estadistico", [None, None],
                            ["Ámbito", "Ticket Prom. ($)", "Máximo", "Mínimo", "Total Trans."])

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

    file_picker = ft.FilePicker(on_result=guardar_archivo_resultado)
    page.overlay.append(file_picker)

    def abrir_selector_archivo(e):
        nombre_defecto = f"Reporte_OraclePOS_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        file_picker.save_file(
            dialog_title="Guardar Reporte PDF",
            file_name=nombre_defecto,
            allowed_extensions=["pdf"]
        )

    # --- LÓGICA DE EJECUCIÓN DEL REPORTE ---
    def ejecutar_reporte(titulo, proc_name, params, columnas_header, es_grafico=False):
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            out_cur = conn.cursor()
            cur.callproc(proc_name, params + [out_cur])
            rows = list(out_cur)

            lbl_titulo_seccion.value = f"Reporte: {titulo}"

            # 1. Limpiar filas ANTES de actualizar la estructura de columnas
            tabla_resultados.rows.clear()

            # 2. Ajuste de encabezados
            if proc_name in ("pkg_reportes.rep_mejores_clientes", "pkg_reportes.rep_empleados_ingresos"):
                visual_headers = ["Nombre Completo", columnas_header[2], columnas_header[3]]
            else:
                visual_headers = columnas_header

            # 3. Aplicar las columnas definidas
            tabla_resultados.columns = [ft.DataColumn(ft.Text(h, weight="bold", color=ft.Colors.INDIGO_900)) for h in
                                        visual_headers]

            # 4. Rellenar las filas
            for r in rows:
                celdas = []
                data_row = list(r)

                if proc_name in ("pkg_reportes.rep_mejores_clientes", "pkg_reportes.rep_empleados_ingresos"):

                    # CELL 1: Nombre Completo
                    nombre_completo = f"{data_row[0]} {data_row[1]}"
                    celdas.append(ft.DataCell(ft.Text(nombre_completo, size=13, weight="bold")))

                    # CELL 2: N° Compras/Ventas
                    val_c_v = data_row[2]
                    header_name_2 = visual_headers[1]
                    texto_formateado_2 = str(val_c_v)
                    if isinstance(val_c_v, (int, float)):
                        if "($)" in header_name_2 or "Generado" in header_name_2 or "Gastado" in header_name_2:
                            texto_formateado_2 = f"${val_c_v:,.2f}"
                    celdas.append(ft.DataCell(ft.Text(texto_formateado_2, size=13, color=ft.Colors.GREY_800)))

                    # CELL 3: Total Gastado/Generado
                    val_total = data_row[3]
                    header_name_3 = visual_headers[2]
                    texto_formateado_3 = str(val_total)
                    if isinstance(val_total, (int, float)):
                        if "($)" in header_name_3 or "Generado" in header_name_3 or "Gastado" in header_name_3:
                            texto_formateado_3 = f"${val_total:,.2f}"
                    celdas.append(ft.DataCell(ft.Text(texto_formateado_3, size=13, color=ft.Colors.GREY_800)))

                else:
                    for i, val in enumerate(data_row):
                        header_name = visual_headers[i]
                        texto_formateado = str(val)
                        if isinstance(val, (int, float)):
                            if "($)" in header_name or "Precio" in header_name or "Valor" in header_name:
                                texto_formateado = f"${val:,.2f}"
                        celdas.append(ft.DataCell(ft.Text(texto_formateado, size=13, color=ft.Colors.GREY_800)))

                tabla_resultados.rows.append(ft.DataRow(cells=celdas))

            if es_grafico and rows:
                data_for_chart = [[r[0], r[1]] for r in rows]
                contenedor_grafico.content = crear_grafico_ventas(data_for_chart)
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

    # --- UI CARDS y BOTONES ---
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

    # Manejadores de eventos de Reportes (llaman a la función ejecutar_reporte)
    # ------------------------------------------------------------------------------------------------------------------
    # MANEJADORES PARA LA VISIBILIDAD DE FILTROS 
    # ------------------------------------------------------------------------------------------------------------------

    def ocultar_filtros_kpi():
        contenedor_filtros_kpi.visible = False
        contenedor_filtros_kpi.update()

    def ver_ventas(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Ventas Mensuales", "pkg_reportes.rep_ventas_por_mes", [], ["Mes", "Total ($)"], True)

    def ver_stock(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Stock Crítico", "pkg_reportes.rep_productos_stock_bajo", [5], ["ID", "Producto", "Stock"])

    def ver_top(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Más Vendidos", "pkg_reportes.rep_productos_mas_vendidos", [], ["Producto", "Total U."])

    def ver_valor(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Valorización", "pkg_reportes.rep_valor_inventario", [],
                         ["Cat.", "Items", "Stock", "Valor ($)"])

    def ver_audit(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Auditoría", "pkg_reportes.rep_auditoria_cambios", [],
                         ["Producto", "Ant.", "Nuevo", "Fecha", "User"])

    # Nuevos Reportes
    def ver_clientes(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Mejores Clientes", "pkg_reportes.rep_mejores_clientes", [],
                         ["Nombre", "Apellido", "N° Compras", "Total Gastado ($)"])

    def ver_empleados(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Rendimiento Empleados", "pkg_reportes.rep_empleados_ingresos", [],
                         ["Nombre", "Apellido", "N° Ventas", "Generado ($)"])

    def ver_categorias(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Ventas por Categoría", "pkg_reportes.rep_ventas_por_categoria", [],
                         ["Categoría", "Items", "Ingresos ($)"])

    def ver_sin_rotacion(e):
        ocultar_filtros_kpi()
        ejecutar_reporte("Productos Sin Rotación", "pkg_reportes.rep_productos_sin_ventas", [],
                         ["Producto", "Stock Actual", "Categoría"])

    def ver_kpi(e):
        # Muestra los filtros
        contenedor_filtros_kpi.visible = True
        contenedor_filtros_kpi.update()

        # Al hacer clic en la tarjeta KPI, se aplica el filtro inicial (Global)
        aplicar_filtro_kpi(e)

    # ------------------------------------------------------------------------------------------------------------------

    # --- IMPLEMENTACIÓN DE SCROLL CON FLECHAS ---

    # 1. Definición de la fila de cards
    fila_cards = ft.Row(
        ref=fila_cards_ref,
        controls=[
            # Fila 1
            crear_card_reporte(ft.Icons.BAR_CHART_ROUNDED, "Ventas", "Histórico", ft.Colors.INDIGO, ver_ventas),
            crear_card_reporte(ft.Icons.WARNING_ROUNDED, "Stock Bajo", "Alerta", ft.Colors.ORANGE, ver_stock),
            crear_card_reporte(ft.Icons.STAR_ROUNDED, "Top Prod.", "Vendidos", ft.Colors.PURPLE, ver_top),
            crear_card_reporte(ft.Icons.MONETIZATION_ON_ROUNDED, "Finanzas", "Valor Stock", ft.Colors.GREEN, ver_valor),
            crear_card_reporte(ft.Icons.SECURITY_ROUNDED, "Auditoría", "Cambios", ft.Colors.RED, ver_audit),
            crear_card_reporte(ft.Icons.PEOPLE_ROUNDED, "Clientes VIP", "Top Compradores", ft.Colors.TEAL,
                               ver_clientes),
            crear_card_reporte(ft.Icons.BADGE_ROUNDED, "Empleados", "Rendimiento", ft.Colors.CYAN, ver_empleados),
            crear_card_reporte(ft.Icons.CATEGORY_ROUNDED, "Categorías", "Ingresos", ft.Colors.PINK, ver_categorias),
            crear_card_reporte(ft.Icons.REMOVE_SHOPPING_CART_ROUNDED, "Huesos", "Sin Ventas", ft.Colors.BROWN,
                               ver_sin_rotacion),
            crear_card_reporte(ft.Icons.ANALYTICS_ROUNDED, "KPIs", "Resumen", ft.Colors.BLUE_GREY, ver_kpi),
        ],
        scroll=ft.ScrollMode.HIDDEN,  
        spacing=20
    )

    # 2. Iconos de Navegación
    btn_scroll_left = ft.IconButton(
        ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
        icon_color=ft.Colors.INDIGO_400,
        icon_size=20,
        tooltip="Anterior",
        on_click=lambda e: mover_cards(e, 'left')
    )

    btn_scroll_right = ft.IconButton(
        ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
        icon_color=ft.Colors.INDIGO_400,
        icon_size=20,
        tooltip="Siguiente",
        on_click=lambda e: mover_cards(e, 'right')
    )

    # 3. Contenedor de las Cards con flechas
    fila_con_navegacion = ft.Row([
        btn_scroll_left,
        ft.Container(fila_cards, expand=True, padding=0),
        btn_scroll_right
    ], alignment=ft.MainAxisAlignment.CENTER)

    return ft.Container(
        content=ft.Column([
            ft.Row([lbl_titulo_seccion, ft.ElevatedButton(
                "Exportar PDF Completo",
                icon=ft.Icons.PICTURE_AS_PDF,
                bgcolor=ft.Colors.RED_600,
                color="white",
                on_click=abrir_selector_archivo
            )], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=20, color="transparent"),

            # --- FILA DE CARDS (ARRIBA) ---
            fila_con_navegacion,

            ft.Divider(height=20, color="transparent"),

            # FILTROS (ABAJO DE LAS CARDS)
            contenedor_filtros_kpi,
            ft.Divider(height=20, color="transparent"),

            ft.Column([
                contenedor_grafico,
                ft.Divider(height=15, color="transparent"),
                ft.Text("Detalle de Datos", weight="bold", color="grey"),
                contenedor_tabla
            ], expand=True, scroll=ft.ScrollMode.AUTO)
        ], expand=True),
        expand=True, padding=30
    )
