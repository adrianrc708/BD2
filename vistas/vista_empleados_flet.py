import flet as ft
from db import db_connector
import hashlib


def vista_empleados(page: ft.Page):
    estado = {"id": 0, "modo_edicion": False}

    # --- CONTROLES FORMULARIO ---
    lbl_titulo = ft.Text("Nuevo Empleado", size=18, weight="bold", color=ft.Colors.INDIGO_800)

    txt_nombre = ft.TextField(label="Nombre", height=40, text_size=13, content_padding=10)
    txt_apellido = ft.TextField(label="Apellido", height=40, text_size=13, content_padding=10)

    txt_cargo = ft.Dropdown(
        label="Cargo",
        options=[ft.dropdown.Option("Vendedor"), ft.dropdown.Option("Administrador")],
        text_size=13,
        content_padding=10
    )

    txt_salario = ft.TextField(label="Salario", height=40, text_size=13, keyboard_type=ft.KeyboardType.NUMBER,
                               content_padding=10)

    # Credenciales App
    txt_usuario = ft.TextField(label="Usuario Sistema", height=40, text_size=13, prefix_icon=ft.Icons.PERSON,
                               content_padding=10)
    txt_pass = ft.TextField(
        label="Contraseña",
        height=40, text_size=13,
        password=True, can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK,
        hint_text="Dejar vacío para mantener actual",
        content_padding=10
    )

    # --- BUSCADOR ---
    txt_buscar = ft.TextField(
        hint_text="Buscar por nombre...",
        prefix_icon=ft.Icons.SEARCH,
        height=40,
        text_size=13,
        expand=True,
        content_padding=10,
        bgcolor=ft.Colors.GREY_50,
        on_change=lambda e: cargar_tabla(e.control.value)
    )

    def encriptar(p):
        return hashlib.sha256(p.encode()).hexdigest()

    # --- LÓGICA DE CONFIRMACIÓN Y GUARDADO ---

    def confirmar_guardado(e):
        if not txt_nombre.value or not txt_usuario.value:
            return mostrar_snack("Nombre y Usuario son obligatorios", "red")
        if estado["id"] == 0 and not txt_pass.value:
            return mostrar_snack("Contraseña obligatoria para nuevos", "red")

        accion = "ACTUALIZAR" if estado["modo_edicion"] else "CREAR"

        dlg_confirm = ft.AlertDialog(
            title=ft.Text(f"¿{accion} Empleado?"),
            content=ft.Text(f"¿Está seguro de que desea guardar los datos de {txt_nombre.value}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_confirm)),
                ft.ElevatedButton("CONFIRMAR", bgcolor="green", color="white",
                                  on_click=lambda e: ejecutar_guardado(dlg_confirm))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg_confirm)

    def ejecutar_guardado(dlg):
        page.close(dlg)
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            pass_hash = encriptar(txt_pass.value) if txt_pass.value else None

            if estado["id"] == 0:  # INSERT
                cur.execute(
                    "INSERT INTO empleados (nombre, apellido, cargo, salario, usuario_app, password_hash) VALUES (:1,:2,:3,:4,:5,:6)",
                    [txt_nombre.value, txt_apellido.value, txt_cargo.value, float(txt_salario.value),
                     txt_usuario.value.upper(), pass_hash])
            else:  # UPDATE
                if pass_hash:
                    cur.execute(
                        "UPDATE empleados SET nombre=:1, apellido=:2, cargo=:3, salario=:4, usuario_app=:5, password_hash=:6 WHERE id_empleado=:7",
                        [txt_nombre.value, txt_apellido.value, txt_cargo.value, float(txt_salario.value),
                         txt_usuario.value.upper(), pass_hash, estado["id"]])
                else:
                    cur.execute(
                        "UPDATE empleados SET nombre=:1, apellido=:2, cargo=:3, salario=:4, usuario_app=:5 WHERE id_empleado=:6",
                        [txt_nombre.value, txt_apellido.value, txt_cargo.value, float(txt_salario.value),
                         txt_usuario.value.upper(), estado["id"]])
            conn.commit()
            limpiar();
            cargar_tabla();
            mostrar_snack("Operación Exitosa", "green")
        except Exception as ex:
            mostrar_snack(str(ex), "red")
        finally:
            db_connector.release_connection(conn)

    # --- LÓGICA DE CONFIRMACIÓN Y ELIMINACIÓN ---

    def confirmar_eliminacion(id_emp):
        # --- PROTECCIÓN DEL SUPER ADMIN ---
        if id_emp == 1:
            mostrar_snack("¡Error Crítico! No se puede eliminar al Super Administrador.", "red")
            return
        # ----------------------------------

        dlg_delete = ft.AlertDialog(
            title=ft.Text("¿Eliminar Empleado?"),
            content=ft.Text("Esta acción borrará el acceso al sistema de este usuario. ¿Continuar?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_delete)),
                ft.ElevatedButton("ELIMINAR", bgcolor="red", color="white",
                                  on_click=lambda e: ejecutar_eliminacion(id_emp, dlg_delete))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg_delete)

    def ejecutar_eliminacion(id_emp, dlg):
        page.close(dlg)
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM empleados WHERE id_empleado = :1", [id_emp])
            conn.commit()
            cargar_tabla()
            mostrar_snack("Empleado eliminado", "orange")
            if estado["id"] == id_emp: limpiar()
        except:
            pass
        finally:
            db_connector.release_connection(conn)

    # --- TABLA ---
    tabla = ft.DataTable(
        width=float("inf"),
        column_spacing=20,
        columns=[
            ft.DataColumn(ft.Text("ID", weight="bold")),
            ft.DataColumn(ft.Text("Nombre", weight="bold")),
            ft.DataColumn(ft.Text("Cargo", weight="bold")),
            ft.DataColumn(ft.Text("Usuario", weight="bold")),
            ft.DataColumn(ft.Text("Acciones", weight="bold"))
        ],
        rows=[],
        heading_row_color=ft.Colors.GREY_100,
        data_row_min_height=50,
        border=ft.border.all(1, ft.Colors.GREY_200),
        border_radius=8
    )

    def cargar_tabla(filtro=""):
        conn = db_connector.get_connection()
        try:
            cur = conn.cursor()
            sql = "SELECT id_empleado, nombre, apellido, cargo, salario, usuario_app FROM empleados"
            if filtro:
                sql += f" WHERE LOWER(nombre) LIKE '%{filtro.lower()}%' OR LOWER(apellido) LIKE '%{filtro.lower()}%'"
            sql += " ORDER BY id_empleado ASC"

            cur.execute(sql)
            tabla.rows.clear()
            for r in cur.fetchall():
                tabla.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(r[0]))),
                    ft.DataCell(ft.Text(f"{r[1]} {r[2]}")),
                    ft.DataCell(ft.Container(
                        content=ft.Text(r[3], size=10, weight="bold", color="blue"),
                        bgcolor=ft.Colors.BLUE_50, padding=5, border_radius=5
                    )),
                    ft.DataCell(ft.Text(r[5] or "Sin Acceso", size=12)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_color="blue", tooltip="Editar",
                                      on_click=lambda e, x=r: editar(x)),
                        ft.IconButton(ft.Icons.DELETE, icon_color="red", tooltip="Eliminar",
                                      on_click=lambda e, x=r[0]: confirmar_eliminacion(x))
                    ], spacing=0))
                ]))
            page.update()
        except:
            pass
        finally:
            db_connector.release_connection(conn)

    def editar(r):
        estado["id"] = r[0];
        estado["modo_edicion"] = True
        txt_nombre.value, txt_apellido.value, txt_cargo.value = r[1], r[2], r[3]
        txt_salario.value, txt_usuario.value = str(r[4]), r[5]
        lbl_titulo.value = "Editar Empleado";
        btn_guardar.text = "ACTUALIZAR"
        page.update()

    def limpiar():
        estado["id"] = 0;
        estado["modo_edicion"] = False
        txt_nombre.value = "";
        txt_apellido.value = "";
        txt_usuario.value = "";
        txt_pass.value = "";
        txt_salario.value = ""
        lbl_titulo.value = "Nuevo Empleado";
        btn_guardar.text = "GUARDAR";
        page.update()

    def mostrar_snack(t, c):
        page.snack_bar = ft.SnackBar(ft.Text(t), bgcolor=c); page.snack_bar.open = True; page.update()

    # BOTONES
    btn_guardar = ft.ElevatedButton("GUARDAR", bgcolor="green", color="white", height=45, width=float("inf"),
                                    on_click=confirmar_guardado)

    btn_limpiar = ft.OutlinedButton("LIMPIAR", height=45, width=float("inf"), on_click=lambda e: limpiar())

    # --- LAYOUT FINAL ---

    panel_izq = ft.Container(
        expand=True,
        bgcolor="white",
        padding=20,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
        content=ft.Column([
            ft.Row([
                ft.Text("Directorio", size=20, weight="bold", color="grey"),
                ft.Container(expand=True),
                ft.Container(width=250, content=txt_buscar)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Column([tabla], scroll=ft.ScrollMode.AUTO, expand=True)
        ])
    )

    panel_der = ft.Container(
        width=320,
        bgcolor="white",
        padding=25,
        border_radius=10,
        margin=ft.margin.only(left=15),
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
        content=ft.Column([
            lbl_titulo,
            ft.Divider(),
            ft.Text("Datos Personales", size=12, weight="bold", color="grey"),
            txt_nombre, txt_apellido, txt_cargo, txt_salario,
            ft.Divider(),
            ft.Text("Acceso al Sistema", size=12, weight="bold", color="blue"),
            txt_usuario, txt_pass,
            ft.Divider(height=20, color="transparent"),
            btn_guardar, btn_limpiar
        ], scroll=ft.ScrollMode.AUTO)
    )

    cargar_tabla()

    return ft.Row([panel_izq, panel_der], expand=True)