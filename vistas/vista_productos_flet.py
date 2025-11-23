import flet as ft
from db import db_connector
import datetime
import oracledb

def vista_productos(page: ft.Page):
    estado = {
        "id": 0,
        "fecha_venc": None,
        "modo_edicion": False
    }

    # ==================================================
    # HELPER: MOSTRAR ALERTA MODAL (CORREGIDO)
    # ==================================================
    def mostrar_alerta_error(titulo, mensaje):
        contenido_dialogo = ft.Container(
            width=400,
            content=ft.Column([
                # Encabezado Rojo
                ft.Container(
                    bgcolor=ft.Colors.RED_700,
                    padding=15,
                    border_radius=ft.border_radius.only(top_left=12, top_right=12),
                    content=ft.Row([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color="white", size=28),
                        ft.Text(titulo, color="white", weight="bold", size=18)
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)
                ),
                # Cuerpo del Mensaje
                ft.Container(
                    padding=20,
                    bgcolor="white",
                    border_radius=ft.border_radius.only(bottom_left=12, bottom_right=12),
                    content=ft.Column([
                        ft.Text(mensaje, size=15, color=ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=20, color="transparent"),
                        ft.ElevatedButton(
                            "ENTENDIDO",
                            style=ft.ButtonStyle(
                                # CORRECCIÓN AQUÍ: Se usa ControlState
                                bgcolor={ft.ControlState.DEFAULT: ft.Colors.RED_600, ft.ControlState.HOVERED: ft.Colors.RED_700},
                                color="white",
                                shape=ft.RoundedRectangleBorder(radius=8)
                            ),
                            width=float("inf"),
                            height=45,
                            on_click=lambda e: page.close(dlg_error)
                        )
                    ])
                )
            ], spacing=0)
        )

        dlg_error = ft.AlertDialog(
            content=contenido_dialogo,
            modal=True,
            bgcolor=ft.Colors.TRANSPARENT,
            content_padding=0,
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        page.open(dlg_error)

    # ... (Resto del código idéntico) ...
    # ... (Incluyo el resto para que sea un archivo completo y no falle)

    # ==================================================
    # 1. CONTROLES DEL PANEL LATERAL (FORMULARIO)
    # ==================================================

    lbl_titulo_panel = ft.Text("Nuevo Producto", size=18, weight="bold", color=ft.Colors.INDIGO_800)
    lbl_info_bloqueada = ft.Text("Edición: Datos base bloqueados por seguridad.", size=11, color="grey", visible=False)

    # -- Campos de Datos Base --
    txt_nombre = ft.TextField(label="Nombre", height=40, text_size=13, content_padding=10)
    txt_categoria = ft.TextField(label="Categoría", height=40, text_size=13, content_padding=10, expand=True)
    txt_marca = ft.TextField(label="Marca", height=40, text_size=13, content_padding=10, expand=True)
    txt_modelo = ft.TextField(label="Modelo", height=40, text_size=13, content_padding=10)
    txt_descripcion = ft.TextField(label="Descripción", multiline=True, height=60, text_size=13, content_padding=10)

    # -- Campos Clave --
    txt_precio = ft.TextField(label="Precio ($)", width=100, height=40, text_size=13, content_padding=10,
                              keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.Colors.GREEN_400)
    txt_stock = ft.TextField(label="Stock", width=100, height=40, text_size=13, content_padding=10,
                             keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.Colors.GREEN_400)
    txt_proveedor = ft.TextField(label="Proveedor", height=40, text_size=13, content_padding=10,
                                 prefix_icon=ft.Icons.LOCAL_SHIPPING)
    txt_ubicacion = ft.TextField(label="Ubicación", height=40, text_size=13, content_padding=10,
                                 prefix_icon=ft.Icons.LOCATION_ON, value="Almacén")

    # Selector de Fecha
    txt_fecha_display = ft.TextField(label="Vencimiento", expand=True, read_only=True, height=40, text_size=13,
                                     content_padding=10, icon=ft.Icons.CALENDAR_MONTH)

    def on_date_change(e):
        if date_picker.value:
            estado["fecha_venc"] = date_picker.value
            txt_fecha_display.value = date_picker.value.strftime("%Y-%m-%d")
            txt_fecha_display.update()

    date_picker = ft.DatePicker(
        on_change=on_date_change,
        first_date=datetime.datetime(2023, 1, 1),
        last_date=datetime.datetime(2030, 12, 31)
    )

    btn_calendario = ft.IconButton(ft.Icons.EDIT_CALENDAR, on_click=lambda e: page.open(date_picker),
                                   tooltip="Cambiar Fecha", icon_size=20)

    # Botones de Acción
    btn_guardar = ft.ElevatedButton("GUARDAR NUEVO", icon=ft.Icons.SAVE,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color="white"),
                                    width=float("inf"), height=40)
    btn_cancelar = ft.OutlinedButton("CANCELAR / LIMPIAR", width=float("inf"), height=40)

    # ==================================================
    # 2. TABLA DE DATOS Y BUSCADOR
    # ==================================================

    txt_busqueda = ft.TextField(
        hint_text="Buscar por Nombre, Marca o Categoría...",
        prefix_icon=ft.Icons.SEARCH,
        height=40, text_size=13, expand=True, content_padding=10,
        on_submit=lambda e: cargar_tabla(txt_busqueda.value)
    )

    tabla = ft.DataTable(
        width=float("inf"),
        columns=[
            ft.DataColumn(ft.Text("ID", weight="bold")),
            ft.DataColumn(ft.Text("Producto", weight="bold")),
            ft.DataColumn(ft.Text("Marca", weight="bold")),
            ft.DataColumn(ft.Text("Stock", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Precio", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Ubicación", weight="bold")),
            ft.DataColumn(ft.Text("Vencimiento", weight="bold")),
            ft.DataColumn(ft.Text("Acciones", weight="bold")),
        ],
        rows=[],
        heading_row_color=ft.Colors.GREY_100,
        data_row_min_height=45,
        column_spacing=10,
    )

    # ==================================================
    # 3. DEFINICIÓN DE PANELES
    # ==================================================

    # Panel Derecho (Formulario)
    panel_derecho = ft.Container(
        width=320,
        bgcolor="white",
        padding=20,
        border_radius=10,
        margin=ft.margin.only(left=10),
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
        content=ft.Column([
            lbl_titulo_panel,
            lbl_info_bloqueada,
            ft.Divider(height=15),

            ft.Text("DATOS CLAVE (Editables)", color="blue", size=11, weight="bold"),
            ft.Row([txt_precio, txt_stock], spacing=5),
            txt_proveedor,
            txt_ubicacion,
            ft.Row([txt_fecha_display, btn_calendario], spacing=5),

            ft.Divider(height=15),
            ft.Text("DATOS BASE", color="grey", size=11, weight="bold"),
            txt_nombre,
            ft.Row([txt_categoria, txt_marca], spacing=10),
            txt_modelo,
            txt_descripcion,

            ft.Divider(height=15),
            ft.Column([btn_guardar, btn_cancelar], spacing=5)
        ], scroll=ft.ScrollMode.AUTO)
    )

    # Panel Izquierdo (Tabla)
    panel_izquierdo = ft.Container(
        expand=True,
        bgcolor="white",
        padding=15,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.INVENTORY_2, color=ft.Colors.INDIGO_900),
                ft.Text("Inventario General", size=24, weight="bold", color=ft.Colors.BLUE_GREY_800),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.REFRESH, icon_color="blue", tooltip="Actualizar",
                              on_click=lambda e: cargar_tabla())
            ]),
            ft.Container(height=5),

            # Buscador
            ft.Container(
                content=txt_busqueda,
                bgcolor=ft.Colors.GREY_50,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=2
            ),
            ft.Divider(),

            # Contenedor de Tabla con scroll
            ft.Container(
                content=ft.Column([tabla], scroll=ft.ScrollMode.AUTO),
                border=ft.border.all(1, ft.Colors.GREY_200),
                border_radius=8,
                expand=True,
                padding=0
            )
        ])
    )

    # ==================================================
    # 4. LÓGICA DE NEGOCIO
    # ==================================================

    def configurar_panel(modo_edicion=False):
        estado["modo_edicion"] = modo_edicion

        if modo_edicion:
            lbl_titulo_panel.value = f"Editar ID #{estado['id']}"
            lbl_info_bloqueada.visible = True

            # Bloquear base
            txt_nombre.disabled = True
            txt_categoria.disabled = True
            txt_marca.disabled = True
            txt_modelo.disabled = True
            txt_descripcion.disabled = True

            btn_guardar.text = "ACTUALIZAR"
            btn_guardar.style.bgcolor = ft.Colors.ORANGE_600

        else:
            lbl_titulo_panel.value = "Nuevo Producto"
            lbl_info_bloqueada.visible = False

            # Desbloquear base
            txt_nombre.disabled = False
            txt_categoria.disabled = False
            txt_marca.disabled = False
            txt_modelo.disabled = False
            txt_descripcion.disabled = False

            btn_guardar.text = "GUARDAR NUEVO"
            btn_guardar.style.bgcolor = ft.Colors.GREEN_600

            limpiar_campos_visuales()

        panel_derecho.update()

    def limpiar_campos_visuales():
        if not estado["modo_edicion"]:
            estado["id"] = 0
            txt_nombre.value = ""
            txt_categoria.value = ""
            txt_marca.value = ""
            txt_modelo.value = ""
            txt_descripcion.value = ""

        txt_precio.value = ""
        txt_stock.value = ""
        txt_proveedor.value = ""
        txt_ubicacion.value = "Almacén"
        txt_fecha_display.value = ""
        estado["fecha_venc"] = None

    def seleccionar_producto(id_prod):
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM productos WHERE id_producto = :1", [id_prod])
            row = cur.fetchone()
            if row:
                estado["id"] = row[0]
                # Cargar datos
                txt_nombre.value = row[1]
                txt_categoria.value = row[2] or ""
                txt_descripcion.value = row[3] or ""
                txt_marca.value = row[4] or ""
                txt_modelo.value = row[5] or ""
                txt_precio.value = str(row[6])
                txt_stock.value = str(row[7])
                txt_proveedor.value = row[8] or ""

                if row[10]:
                    estado["fecha_venc"] = row[10]
                    txt_fecha_display.value = row[10].strftime("%Y-%m-%d")
                else:
                    estado["fecha_venc"] = None
                    txt_fecha_display.value = ""

                txt_ubicacion.value = row[12] or ""

                configurar_panel(modo_edicion=True)

        except Exception as e:
            print(e)
        finally:
            db_connector.release_connection(conn)

    def preparar_guardado(e):
        if not txt_precio.value or not txt_stock.value:
            mostrar_snack("Precio y Stock son obligatorios", "red")
            return

        accion = "ACTUALIZAR" if estado["modo_edicion"] else "CREAR"

        dlg_confirmar = ft.AlertDialog(
            title=ft.Text(f"¿Confirmar {accion}?"),
            content=ft.Text(f"¿Está seguro de que desea {accion.lower()} este producto?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_confirmar)),
                ft.ElevatedButton("Sí, Confirmar", bgcolor="green", color="white",
                                  on_click=lambda e: ejecutar_guardado_bd(dlg_confirmar))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg_confirmar)

    def ejecutar_guardado_bd(dlg):
        page.close(dlg)
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            fecha_final = estado["fecha_venc"]
            if not fecha_final:
                fecha_final = datetime.datetime.now() + datetime.timedelta(days=365)

            params = [
                txt_nombre.value, txt_categoria.value, txt_descripcion.value,
                txt_marca.value, txt_modelo.value, float(txt_precio.value),
                int(txt_stock.value), txt_proveedor.value, fecha_final,
                'Activo', txt_ubicacion.value
            ]

            if estado["id"] == 0:
                cur.callproc("pkg_gestion_productos.sp_registrar", params)
                mostrar_snack("Producto Creado Exitosamente", "green")
            else:
                params.insert(0, estado["id"])
                cur.callproc("pkg_gestion_productos.sp_modificar", params)
                mostrar_snack("Producto Actualizado", "orange")

            conn.commit()
            configurar_panel(modo_edicion=False)
            cargar_tabla()

        except oracledb.DatabaseError as e:
            error_obj, = e.args
            # APROVECHAMIENTO AL 100% CON DIALOGO VISUAL MEJORADO
            if error_obj.code == 20010:
                mensaje_completo = error_obj.message.split(': ', 1)[
                    1] if ': ' in error_obj.message else error_obj.message
                mensaje_limpio = mensaje_completo.splitlines()[0]

                mostrar_alerta_error("Producto Duplicado", mensaje_limpio)
                mostrar_alerta_error("Producto Duplicado", mensaje_limpio)
            else:
                mostrar_alerta_error("Error de Base de Datos", f"Código {error_obj.code}\n{error_obj.message}")

        except Exception as ex:
            mostrar_snack(f"Error inesperado: {ex}", "red")
        finally:
            db_connector.release_connection(conn)

    def preparar_eliminacion(id_prod):
        dlg_borrar = ft.AlertDialog(
            title=ft.Text("¿Eliminar Producto?"),
            content=ft.Text("Esta acción es irreversible. ¿Desea continuar?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_borrar)),
                ft.ElevatedButton("ELIMINAR", bgcolor="red", color="white",
                                  on_click=lambda e: ejecutar_borrado_bd(id_prod, dlg_borrar))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg_borrar)

    def ejecutar_borrado_bd(id_prod, dlg):
        page.close(dlg)
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            cur.callproc("pkg_gestion_productos.sp_eliminar", [id_prod])
            conn.commit()
            mostrar_snack("Producto Eliminado", "red")
            if estado["id"] == id_prod:
                configurar_panel(modo_edicion=False)
            cargar_tabla()
        except Exception as ex:
            mostrar_snack(str(ex), "red")
        finally:
            db_connector.release_connection(conn)

    def cargar_tabla(filtro=""):
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            sql = """
                  SELECT id_producto, \
                         nombre, \
                         marca, \
                         categoria, \
                         precio, \
                         stock, \
                         ubicacion, \
                         fecha_vencimiento
                  FROM productos
                  WHERE LOWER(nombre) LIKE LOWER(:1)
                     OR LOWER(marca) LIKE LOWER(:1)
                     OR LOWER(categoria) LIKE LOWER(:1)
                  ORDER BY id_producto DESC \
                  """
            cur.execute(sql, [f"%{filtro}%"])
            rows = cur.fetchall()

            tabla.rows.clear()
            for r in rows:
                fecha_str = r[7].strftime("%d/%m/%Y") if r[7] else "-"
                tabla.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(r[0]))),
                            ft.DataCell(ft.Text(r[1], width=100, no_wrap=True, tooltip=r[1])),
                            ft.DataCell(ft.Text(r[2] or "-")),
                            ft.DataCell(ft.Container(
                                content=ft.Text(str(r[5]), color="white", weight="bold", size=11),
                                bgcolor=ft.Colors.RED_400 if r[5] < 10 else ft.Colors.GREEN_400,
                                padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=10
                            )),
                            ft.DataCell(ft.Text(f"${r[4]:.2f}")),
                            ft.DataCell(ft.Text(r[6] or "-")),
                            ft.DataCell(ft.Text(fecha_str, size=11)),
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(ft.Icons.EDIT, icon_color="blue", tooltip="Editar", icon_size=18,
                                                  on_click=lambda e, x=r[0]: seleccionar_producto(x)),
                                    ft.IconButton(ft.Icons.DELETE, icon_color="red", tooltip="Eliminar", icon_size=18,
                                                  on_click=lambda e, x=r[0]: preparar_eliminacion(x))
                                ], spacing=0)
                            ),
                        ],
                    )
                )
            page.update()
        except:
            pass
        finally:
            db_connector.release_connection(conn)

    def mostrar_snack(txt, color):
        page.snack_bar = ft.SnackBar(ft.Text(txt), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    # --- INICIALIZACIÓN ---
    btn_guardar.on_click = preparar_guardado
    btn_cancelar.on_click = lambda e: configurar_panel(modo_edicion=False)

    cargar_tabla()

    return ft.Row([panel_izquierdo, panel_derecho], expand=True, spacing=0)