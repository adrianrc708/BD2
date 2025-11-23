import flet as ft
import matplotlib
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart
from db import db_connector

matplotlib.use("svg")


def vista_reportes(page: ft.Page):
    # --- ESTADO ---
    estado = {"reporte_actual": ""}

    # --- COMPONENTES UI ---

    # 1. Gráfico de Ventas (MEJORADO)
    def crear_grafico_ventas(datos):
        # Invertimos los datos para que el orden sea cronológico (Enero -> Diciembre)
        # Ya que la BD suele devolver DESC (el más reciente primero)
        datos_grafico = datos[::-1]

        meses = [d[0] for d in datos_grafico]
        totales = [d[1] for d in datos_grafico]

        # Configuración de figura con estilo limpio
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_alpha(0)  # Fondo transparente para integrarse mejor

        # Barras color índigo corporativo
        barras = ax.bar(meses, totales, color="#5C6BC0", zorder=3, width=0.6)

        ax.set_title("Tendencia de Ingresos Mensuales", fontsize=12, weight='bold', color="#333333", pad=15)

        # Estilizar Ejes
        ax.set_ylabel("Monto ($)", fontsize=9, color="grey")
        ax.tick_params(axis='x', colors="#555555", labelsize=9)
        ax.tick_params(axis='y', colors="#555555", labelsize=9)

        # Grid horizontal sutil
        ax.grid(axis='y', linestyle='--', alpha=0.4, color="grey", zorder=0)

        # Quitar bordes feos (spines)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#CCCCCC')  # Línea base sutil

        # Etiquetas de valor sobre las barras
        for bar in barras:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + (height * 0.01),
                    f'${height:,.0f}',
                    ha='center', va='bottom', fontsize=8, color="#333333", weight="bold")

        plt.tight_layout()
        return MatplotlibChart(fig, expand=True, transparent=True)

    # Contenedor del gráfico
    contenedor_grafico = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.BAR_CHART, size=40, color=ft.Colors.GREY_300),
            ft.Text("Seleccione 'Ventas Mensuales' para visualizar estadísticas", color="grey")
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        height=350,
        bgcolor="white",
        padding=20,
        border_radius=12,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12),
        visible=False  # Oculto por defecto
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
        expand=True,
        bgcolor="white",
        padding=10,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
    )

    # --- LÓGICA DE DATOS ---

    def ejecutar_reporte(titulo, proc_name, params, columnas_header, es_grafico=False):
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            out_cur = conn.cursor()
            all_params = params + [out_cur]

            cur.callproc(proc_name, all_params)
            rows = list(out_cur)

            lbl_titulo_seccion.value = f"Reporte: {titulo}"

            # Configurar columnas
            tabla_resultados.columns = [ft.DataColumn(ft.Text(h, weight="bold", color=ft.Colors.INDIGO_900)) for h in
                                        columnas_header]
            tabla_resultados.rows.clear()

            # --- PROCESAMIENTO Y FORMATO DE FILAS ---
            for r in rows:
                celdas = []
                for i, val in enumerate(r):
                    header_name = columnas_header[i]
                    texto_formateado = str(val)

                    # Regla: Si es numérico y el encabezado sugiere dinero, formatear
                    if isinstance(val, (int, float)):
                        if "($)" in header_name or "Precio" in header_name or "Valor" in header_name:
                            texto_formateado = f"${val:,.2f}"

                    # Diseño de celda
                    celdas.append(ft.DataCell(ft.Text(texto_formateado, size=13, color=ft.Colors.GREY_800)))

                tabla_resultados.rows.append(ft.DataRow(cells=celdas))

            # Manejo del Gráfico
            if es_grafico and rows:
                contenedor_grafico.content = crear_grafico_ventas(rows)
                contenedor_grafico.visible = True
            else:
                contenedor_grafico.visible = False

            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error al generar reporte: {ex}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
        finally:
            db_connector.release_connection(conn)

    # --- BOTONES TIPO TARJETA ---
    def crear_card_reporte(icon, titulo, subtitulo, color_icon, func):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color_icon, size=32),
                ft.Text(titulo, weight="bold", size=14, color=ft.Colors.BLUE_GREY_900),
                ft.Text(subtitulo, size=11, color=ft.Colors.GREY_600, text_align="center")
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            width=150,
            height=110,
            bgcolor="white",
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.BLACK12, offset=ft.Offset(2, 2)),
            ink=True,
            on_click=func,
            # CORRECCIÓN: ft.Animation en lugar de ft.animation.Animation
            animate=ft.Animation(200, "easeOut")
        )

    # Funciones Wrapper con Nombres Corregidos
    def ver_ventas(e):
        ejecutar_reporte("Ventas Mensuales", "pkg_reportes.rep_ventas_por_mes", [], ["Mes", "Total ($)"], True)

    def ver_stock(e):
        ejecutar_reporte("Stock Crítico", "pkg_reportes.rep_productos_stock_bajo", [5],
                         ["ID", "Producto", "Stock Actual"])

    def ver_top(e):
        # CAMBIO SOLICITADO: Titulo de columna más claro
        ejecutar_reporte("Más Vendidos", "pkg_reportes.rep_productos_mas_vendidos", [],
                         ["Producto", "Total Unidades Vendidas"])

    def ver_valor(e):
        ejecutar_reporte("Valorización", "pkg_reportes.rep_valor_inventario", [],
                         ["Categoría", "Items", "Stock Total", "Valor Total ($)"])

    def ver_audit(e):
        ejecutar_reporte("Auditoría", "pkg_reportes.rep_auditoria_cambios", [],
                         ["Producto", "Precio Ant. ($)", "Precio Nuevo ($)", "Fecha Cambio", "Usuario Oracle"])

    # --- LAYOUT ---

    lbl_titulo_seccion = ft.Text("Inteligencia de Negocios", size=24, weight="bold", color=ft.Colors.BLUE_GREY_900)

    fila_cards = ft.Row([
        crear_card_reporte(ft.Icons.BAR_CHART_ROUNDED, "Ventas", "Histórico Mensual", ft.Colors.INDIGO, ver_ventas),
        crear_card_reporte(ft.Icons.WARNING_ROUNDED, "Stock Bajo", "Alerta Inventario", ft.Colors.ORANGE, ver_stock),
        crear_card_reporte(ft.Icons.STAR_ROUNDED, "Top Productos", "Lo más vendido", ft.Colors.PURPLE, ver_top),
        crear_card_reporte(ft.Icons.MONETIZATION_ON_ROUNDED, "Finanzas", "Valor del Stock", ft.Colors.GREEN, ver_valor),
        crear_card_reporte(ft.Icons.SECURITY_ROUNDED, "Auditoría", "Cambios de Precio", ft.Colors.RED, ver_audit),
    ], scroll=ft.ScrollMode.HIDDEN, spacing=20)

    return ft.Container(
        content=ft.Column([
            lbl_titulo_seccion,
            ft.Divider(height=20, color="transparent"),
            fila_cards,
            ft.Divider(height=20, color="transparent"),
            # Área dinámica: Gráfico arriba (si aplica), tabla abajo
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