import oracledb
import sys
from tkinter import messagebox

# Variable global para el pool (se llena al hacer login)
connection_pool = None

def login_y_conectar(usuario, password):
    """
    Intenta crear el pool de conexiones con las credenciales ingresadas.
    Retorna True si tiene éxito, False si falla.
    """
    global connection_pool
    try:
        # Inicializa el cliente Oracle si es necesario (solo una vez)
        try:
            oracledb.init_oracle_client()
        except:
            pass # Ya estaba iniciado

        # Intentamos conectar. Si usuario/pass están mal, Oracle lanzará error aquí.
        connection_pool = oracledb.create_pool(
            user=usuario,
            password=password,
            dsn="localhost:1521/XE",  # <--- VERIFICA TU DSN AQUÍ
            min=1,
            max=5,
            increment=1
        )
        print(f"Login exitoso para: {usuario}")
        return True

    except oracledb.Error as e:
        error_obj = e.args[0]
        # ORA-01017: credenciales inválidas
        if error_obj.code == 1017:
            messagebox.showerror("Login Fallido", "Usuario o contraseña incorrectos.")
        else:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a Oracle:\n{e}")
        return False

def get_connection():
    global connection_pool
    if connection_pool is None:
        messagebox.showerror("Error Crítico", "No hay sesión iniciada. Reinicie la app.")
        return None

    try:
        conn = connection_pool.acquire()
        return conn
    except Exception as e:
        messagebox.showerror("Error de Pool", f"No se pudo obtener conexión: {e}")
        return None

def release_connection(conn):
    global connection_pool
    if connection_pool and conn:
        try:
            connection_pool.release(conn)
        except Exception as e:
            print(f"Error al liberar conexión: {e}")

def close_connection_pool():
    global connection_pool
    if connection_pool:
        try:
            connection_pool.close()
        except:
            pass