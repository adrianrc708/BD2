import flet as ft
from db import db_connector

# --- CONFIGURACIÓN ---
DEFAULT_CLIENTE_ID = 1
DEFAULT_CLIENTE_NOMBRE = "Público General"

# --- ESTADO GLOBAL ---
carrito_productos = []
cliente_seleccionado = {"id": DEFAULT_CLIENTE_ID, "nombre": DEFAULT_CLIENTE_NOMBRE}
producto_actual = {"id": None, "nombre": "", "precio": 0, "stock": 0}

# ESTADO DEL EMPLEADO (Se llena desde el Dashboard)
empleado_actual = {"id": None, "nombre": "Desconocido"}


# AHORA RECIBE LA SESIÓN COMO PARÁMETRO
def vista_ventas(page: ft.Page, info_sesion=None):
    # Si recibimos datos de sesión, actualizamos el empleado actual
    if info_sesion:
        empleado_actual["id"] = info_sesion["id"]
        empleado_actual["nombre"] = info_sesion["nombre"]

    # ==========================
    # SECCIÓN: HEADER (INFO EMPLEADO)
    # ==========================
    color_estado = ft.Colors.GREEN_600 if empleado_actual["id"] else ft.Colors.RED_400
    txt_vendedor_info = ft.Text(f"Atendiendo: {empleado_actual['nombre']}", color=color_estado, weight="bold", size=16)

    # ==========================
    # SECCIÓN: CLIENTES
    # ==========================

    txt_buscar_cliente = ft.TextField(
        label="Buscar Cliente",
        prefix_icon=ft.Icons.SEARCH,
        height=40, text_size=14, expand=True,
        bgcolor=ft.Colors.GREY_50, border_color=ft.Colors.GREY_300,
        on_submit=lambda e: buscar_cliente(e)
    )

    dd_clientes = ft.Dropdown(
        hint_text="Resultados...",
        text_size=14, expand=True,
        bgcolor=ft.Colors.GREY_50, border_color=ft.Colors.GREY_300,
        options=[], dense=True, visible=False,
        on_change=lambda e: on_dd_cliente_change(e)
    )

    icon_cliente = ft.Icon(ft.Icons.STOREFRONT, color=ft.Colors.GREY)
    txt_cliente_display = ft.Text(f"Cliente: {DEFAULT_CLIENTE_NOMBRE}", weight="bold", color=ft.Colors.GREY_700)

    info_cliente_card = ft.Container(
        padding=10, border_radius=8,
        bgcolor=ft.Colors.GREY_100, border=ft.border.all(1, ft.Colors.GREY_300),
        content=ft.Row([icon_cliente, txt_cliente_display], alignment=ft.MainAxisAlignment.CENTER)
    )

    # ==========================
    # SECCIÓN: PRODUCTOS
    # ==========================

    txt_buscar_producto = ft.TextField(
        label="Buscar Producto (Nombre)",
        prefix_icon=ft.Icons.INVENTORY_2,
        height=40, text_size=14, expand=True,
        bgcolor=ft.Colors.GREY_50, border_color=ft.Colors.GREY_300,
        on_submit=lambda e: buscar_producto(e)
    )

    dd_productos = ft.Dropdown(
        hint_text="Seleccione un producto...",
        text_size=14, expand=True,
        bgcolor=ft.Colors.GREY_50, border_color=ft.Colors.GREY_300,
        options=[], dense=True, visible=False,
        on_change=lambda e: on_dd_producto_change(e)
    )

    # Control de Cantidad
    def cambiar_cantidad(delta):
        try:
            val = int(txt_cant.value)
            new_val = val + delta
            if new_val < 1: new_val = 1
            txt_cant.value = str(new_val)
            txt_cant.update()
        except:
            txt_cant.value = "1"
            txt_cant.update()

    btn_menos = ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: cambiar_cantidad(-1), icon_color=ft.Colors.RED_400)
    txt_cant = ft.TextField(value="1", width=60, text_align="center", read_only=True, border_color=ft.Colors.GREY_300)
    btn_mas = ft.IconButton(ft.Icons.ADD, on_click=lambda e: cambiar_cantidad(1), icon_color=ft.Colors.GREEN_400)

    # ==========================
    # TABLA Y TOTALES
    # ==========================

    lbl_total = ft.Text("$ 0.00", size=30, weight="bold", color=ft.Colors.GREEN_700)

    tabla_carrito = ft.DataTable(
        width=float("inf"),
        columns=[
            ft.DataColumn(ft.Text("Producto", weight="bold")),
            ft.DataColumn(ft.Text("Precio", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Cant.", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Acción", weight="bold")),
        ],
        rows=[],
        heading_row_color=ft.Colors.GREY_100,
        data_row_min_height=50,
        divider_thickness=0.5
    )

    # ==========================
    # LÓGICA DE CLIENTES
    # ==========================

    def actualizar_ui_cliente():
        es_generico = (cliente_seleccionado["id"] == DEFAULT_CLIENTE_ID)
        txt_cliente_display.value = f"{cliente_seleccionado['nombre']}"

        if es_generico:
            info_cliente_card.bgcolor = ft.Colors.GREY_100
            icon_cliente.name = ft.Icons.STOREFRONT
            icon_cliente.color = ft.Colors.GREY
            txt_cliente_display.color = ft.Colors.GREY_700
        else:
            info_cliente_card.bgcolor = ft.Colors.INDIGO_50
            icon_cliente.name = ft.Icons.PERSON
            icon_cliente.color = ft.Colors.INDIGO
            txt_cliente_display.color = ft.Colors.INDIGO_900

        if info_cliente_card.page: info_cliente_card.update()

    def seleccionar_generico(e=None):
        cliente_seleccionado["id"] = DEFAULT_CLIENTE_ID
        cliente_seleccionado["nombre"] = DEFAULT_CLIENTE_NOMBRE
        txt_buscar_cliente.value = ""
        dd_clientes.visible = False
        actualizar_ui_cliente()
        if page: page.update()

    def buscar_cliente(e):
        termino = txt_buscar_cliente.value
        if not termino: return
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            sql = "SELECT id_cliente, nombre, apellido FROM clientes WHERE LOWER(nombre) LIKE LOWER(:1) OR LOWER(apellido) LIKE LOWER(:1)"
            cur.execute(sql, [f"%{termino}%"])
            rows = cur.fetchall()

            dd_clientes.visible = True
            dd_clientes.options = [ft.dropdown.Option(text=f"{r[1]} {r[2]}", key=str(r[0])) for r in rows]

            if not rows:
                dd_clientes.hint_text = "Sin resultados"
                dd_clientes.value = None
            else:
                dd_clientes.hint_text = "Seleccione..."
                dd_clientes.value = str(rows[0][0])
                cambiar_cliente(str(rows[0][0]), f"{rows[0][1]} {rows[0][2]}")
            page.update()
        except:
            pass
        finally:
            db_connector.release_connection(conn)

    def on_dd_cliente_change(e):
        for opt in dd_clientes.options:
            if opt.key == dd_clientes.value:
                cambiar_cliente(opt.key, opt.text)
                break

    def cambiar_cliente(k, t):
        cliente_seleccionado["id"] = int(k)
        cliente_seleccionado["nombre"] = t
        actualizar_ui_cliente()

    # ==========================
    # LÓGICA DE PRODUCTOS
    # ==========================

    def buscar_producto(e):
        termino = txt_buscar_producto.value
        if not termino: return
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            sql = "SELECT id_producto, nombre, precio, stock FROM productos WHERE LOWER(nombre) LIKE LOWER(:1)"
            cur.execute(sql, [f"%{termino}%"])
            rows = cur.fetchall()
            dd_productos.visible = True
            opts = []
            for r in rows:
                opts.append(ft.dropdown.Option(text=f"{r[1]} - ${r[2]} (Disp: {r[3]})", key=str(r[0])))
            dd_productos.options = opts
            if not rows:
                dd_productos.hint_text = "No encontrado"
                producto_actual["id"] = None
            else:
                dd_productos.hint_text = "Seleccione..."
                dd_productos.value = str(rows[0][0])
                cargar_producto_seleccionado(rows[0][0])
            page.update()
        except Exception as ex:
            print(ex)
        finally:
            db_connector.release_connection(conn)

    def on_dd_producto_change(e):
        pk = dd_productos.value
        if pk: cargar_producto_seleccionado(int(pk))

    def cargar_producto_seleccionado(id_prod):
        conn = db_connector.get_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("SELECT id_producto, nombre, precio, stock FROM productos WHERE id_producto = :1", [id_prod])
            row = cur.fetchone()
            if row:
                producto_actual["id"] = row[0]
                producto_actual["nombre"] = row[1]
                producto_actual["precio"] = row[2]
                producto_actual["stock"] = row[3]
        except:
            pass
        finally:
            db_connector.release_connection(conn)

    def agregar_producto_al_carrito(e):
        if not producto_actual["id"]: return mostrar_snack("Seleccione producto", "orange")
        cant = int(txt_cant.value)
        if producto_actual["stock"] < cant: return mostrar_snack(f"Stock insuficiente ({producto_actual['stock']})",
                                                                 "red")

        carrito_productos.append({
            "id": producto_actual["id"], "nombre": producto_actual["nombre"],
            "precio": producto_actual["precio"], "cantidad": cant,
            "subtotal": producto_actual["precio"] * cant
        })
        actualizar_tabla()
        # Reset UI
        txt_buscar_producto.value = "";
        dd_productos.visible = False
        txt_cant.value = "1";
        producto_actual["id"] = None;
        txt_buscar_producto.focus()
        page.update()

    def borrar_item(idx):
        carrito_productos.pop(idx)
        actualizar_tabla()

    def actualizar_tabla():
        tabla_carrito.rows.clear()
        tot = sum(it["subtotal"] for it in carrito_productos)
        for i, it in enumerate(carrito_productos):
            tabla_carrito.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(it["nombre"])), ft.DataCell(ft.Text(f"${it['precio']:.2f}")),
                ft.DataCell(ft.Text(str(it["cantidad"]))),
                ft.DataCell(ft.Text(f"${it['subtotal']:.2f}", weight="bold")),
                ft.DataCell(
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, x=i: borrar_item(x)))
            ]))
        lbl_total.value = f"$ {tot:,.2f}"
        page.update()

    def finalizar_venta(e):
        if not carrito_productos: return mostrar_snack("Carrito vacío", "orange")
        if not empleado_actual["id"]: return mostrar_snack("ERROR: Vendedor no identificado", "red")

        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            id_v = cur.var(int)
            # USAMOS EL ID DEL EMPLEADO QUE LLEGÓ POR PARÁMETRO
            cur.execute(
                "INSERT INTO ventas (id_cliente, id_empleado, total) VALUES (:1, :2, :3) RETURNING id_venta INTO :4",
                [cliente_seleccionado["id"], empleado_actual["id"], 0, id_v])
            v_id = id_v.getvalue()[0]
            for it in carrito_productos:
                cur.execute(
                    "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, subtotal) VALUES (:1, :2, :3, :4)",
                    [v_id, it["id"], it["cantidad"], it["subtotal"]])
            conn.commit()
            page.open(
                ft.AlertDialog(title=ft.Text("Venta Exitosa"), content=ft.Text(f"Venta #{int(v_id)} registrada.")))
            carrito_productos.clear();
            actualizar_tabla();
            seleccionar_generico()
        except Exception as ex:
            conn.rollback()
            msg = "Stock insuficiente" if "ORA-20002" in str(ex) else str(ex)
            mostrar_snack(f"Error: {msg}", "red")
        finally:
            db_connector.release_connection(conn)

    def mostrar_snack(txt, color):
        page.snack_bar = ft.SnackBar(ft.Text(txt), bgcolor=color)
        page.snack_bar.open = True;
        page.update()

    # --- MODAL NUEVO CLIENTE ---
    txt_new_nombre = ft.TextField(label="Nombre", height=40)
    txt_new_apellido = ft.TextField(label="Apellido", height=40)
    txt_new_dni = ft.TextField(label="DNI", height=40)

    def guardar_nuevo_cliente(e):
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor();
            id_new = cur.var(int)
            cur.execute("INSERT INTO clientes (nombre, apellido, dni) VALUES (:1, :2, :3) RETURNING id_cliente INTO :4",
                        [txt_new_nombre.value, txt_new_apellido.value, txt_new_dni.value, id_new])
            conn.commit();
            nom = f"{txt_new_nombre.value} {txt_new_apellido.value}"
            cambiar_cliente(str(int(id_new.getvalue()[0])), nom)
            page.close(dialog_nuevo_cliente);
            mostrar_snack(f"Cliente {nom} creado", "green")
            txt_new_nombre.value = "";
            txt_new_apellido.value = "";
            txt_new_dni.value = ""
        except Exception as ex:
            mostrar_snack(str(ex), "red")
        finally:
            db_connector.release_connection(conn)

    dialog_nuevo_cliente = ft.AlertDialog(title=ft.Text("Nuevo Cliente"),
                                          content=ft.Column([txt_new_nombre, txt_new_apellido, txt_new_dni], height=200,
                                                            width=300),
                                          actions=[ft.TextButton("Cancelar",
                                                                 on_click=lambda e: page.close(dialog_nuevo_cliente)),
                                                   ft.ElevatedButton("Guardar", on_click=guardar_nuevo_cliente)])

    actualizar_ui_cliente()

    col_controles = ft.Column([
        txt_vendedor_info, ft.Divider(),
        ft.Text("CLIENTE", color="grey", weight="bold", size=12),
        ft.Row(
            [txt_buscar_cliente, ft.IconButton(ft.Icons.SEARCH, on_click=buscar_cliente, icon_color=ft.Colors.INDIGO)],
            spacing=5), dd_clientes,
        ft.Row([ft.ElevatedButton("Nuevo", on_click=lambda e: page.open(dialog_nuevo_cliente),
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL_500, color="white"), expand=True),
                ft.ElevatedButton("Público", on_click=seleccionar_generico,
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_300, color="white"), expand=True)]),
        info_cliente_card, ft.Divider(height=30, color="transparent"),
        ft.Text("PRODUCTO", color="grey", weight="bold", size=12),
        ft.Row([txt_buscar_producto,
                ft.IconButton(ft.Icons.SEARCH, on_click=buscar_producto, icon_color=ft.Colors.INDIGO)], spacing=5),
        dd_productos,
        ft.Row([ft.Text("Cant:", weight="bold"), btn_menos, txt_cant, btn_mas], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton("AGREGAR", icon=ft.Icons.ADD_SHOPPING_CART,
                          style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO, color="white"), width=float("inf"), height=45,
                          on_click=agregar_producto_al_carrito)
    ], scroll=ft.ScrollMode.AUTO)

    col_tabla = ft.Column([
        ft.Text("CARRITO", weight="bold", size=16),
        ft.Container(tabla_carrito, border=ft.border.all(1, ft.Colors.GREY_200), border_radius=8, padding=5,
                     expand=True),
        ft.Divider(),
        ft.Row([ft.Column([ft.Text("TOTAL", size=12, color="grey"), lbl_total]),
                ft.ElevatedButton("COBRAR", icon=ft.Icons.CHECK,
                                  style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color="white"), height=50,
                                  on_click=finalizar_venta)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ])

    return ft.ResponsiveRow([
        ft.Container(col_controles, padding=20, col={"md": 4}, bgcolor="white", border_radius=10,
                     shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12)),
        ft.Container(col_tabla, padding=20, col={"md": 8}, bgcolor="white", border_radius=10,
                     shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12))
    ], expand=True)