import flet as ft
from db import db_connector


def vista_reportes(page: ft.Page):
    # Tabla Dinámica: Agregamos columna inicial para evitar AssertionError
    tabla_resultados = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Información del Reporte"))],
        rows=[],
        heading_row_color=ft.Colors.GREY_100,
        border=ft.border.all(1, ft.Colors.GREY_200),
        vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_100),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_100),
    )

    lbl_titulo_reporte = ft.Text("Seleccione un reporte para visualizar", size=20, weight="bold",
                                 color=ft.Colors.GREY_700)

    # --- LÓGICA DE GENERACIÓN ---
    def ejecutar_reporte(titulo, proc_name, params, columnas_header):
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            out_cur = conn.cursor()

            all_params = params + [out_cur]
            cur.callproc(proc_name, all_params)

            rows = list(out_cur)

            lbl_titulo_reporte.value = titulo

            # Sobrescribimos las columnas dinámicamente
            tabla_resultados.columns = [ft.DataColumn(ft.Text(h, weight="bold")) for h in columnas_header]

            tabla_resultados.rows.clear()
            for r in rows:
                celdas = [ft.DataCell(ft.Text(str(val))) for val in r]
                tabla_resultados.rows.append(ft.DataRow(cells=celdas))

            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
        finally:
            db_connector.release_connection(conn)

    # --- BOTONES DE REPORTES ---
    def btn_rep(texto, icono, color, func):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icono, color="white"),
                ft.Text(texto, color="white", weight="bold")
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=color,
            padding=15,
            border_radius=10,
            ink=True,
            on_click=func,
            col={"sm": 6, "md": 4, "lg": 2}
        )

    def rep_ventas(e):
        ejecutar_reporte("Ventas por Mes", "pkg_reportes.rep_ventas_por_mes", [], ["Mes", "Total ($)"])

    def rep_stock(e):
        ejecutar_reporte("Stock Bajo (<5)", "pkg_reportes.rep_productos_stock_bajo", [5], ["ID", "Producto", "Stock"])

    def rep_top(e):
        ejecutar_reporte("Más Vendidos", "pkg_reportes.rep_productos_mas_vendidos", [], ["Producto", "Total Vendido"])

    def rep_valor(e):
        ejecutar_reporte("Valor de Inventario", "pkg_reportes.rep_valor_inventario", [],
                         ["Categoría", "Items", "Stock", "Valor Total"])

    def rep_audit(e):
        ejecutar_reporte("Auditoría de Precios", "pkg_reportes.rep_auditoria_cambios", [],
                         ["Producto", "Ant.", "Nuevo", "Fecha", "Usuario"])

    # --- LAYOUT ---

    fila_botones = ft.ResponsiveRow([
        btn_rep("Ventas Mensuales", ft.Icons.CALENDAR_MONTH, ft.Colors.BLUE_500, rep_ventas),
        btn_rep("Stock Crítico", ft.Icons.WARNING_AMBER, ft.Colors.ORANGE_500, rep_stock),
        btn_rep("Más Vendidos", ft.Icons.STAR, ft.Colors.PURPLE_500, rep_top),
        btn_rep("Valorización", ft.Icons.MONETIZATION_ON, ft.Colors.GREEN_600, rep_valor),
        btn_rep("Auditoría", ft.Icons.SECURITY, ft.Colors.RED_400, rep_audit),
    ], run_spacing=10)

    panel_resultados = ft.Container(
        padding=20,
        bgcolor="white",
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
        expand=True,
        content=ft.Column([
            lbl_titulo_reporte,
            ft.Divider(),
            ft.Container(tabla_resultados, expand=True, padding=5)
        ], scroll=ft.ScrollMode.AUTO)
    )

    return ft.Column([
        ft.Text("CENTRO DE REPORTES", size=24, weight="bold", color=ft.Colors.BLUE_GREY_800),
        fila_botones,
        ft.Divider(height=20, color="transparent"),
        panel_resultados
    ], expand=True)