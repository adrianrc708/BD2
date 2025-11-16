import oracledb
import sys
from tkinter import messagebox

DB_USER = "pon_tu_usuario_aqui"
DB_PASS = "pon_tu_password_aqui"
DB_DSN = "localhost:1521/XE"

connection_pool = None


def init_connection_pool():
    global connection_pool
    try:
        oracledb.init_oracle_client()

        connection_pool = oracledb.create_pool(
            user=DB_USER,
            password=DB_PASS,
            dsn=DB_DSN,
            min=2,
            max=5,
            increment=1
        )
        print("¡Pool de conexiones a Oracle creado exitosamente!")

    except Exception as e:
        print(f"Error fatal: No se pudo inicializar el pool de Oracle: {e}")
        messagebox.showerror("Error Crítico de Conión",
                             f"No se pudo conectar a Oracle: {e}\n\n"
                             "Revisa db_connector.py con tus credenciales.")
        sys.exit(1)


def get_connection():
    global connection_pool
    if connection_pool is None:
        print("Error: El pool de conexiones no está inicializado.")
        return None

    try:
        conn = connection_pool.acquire()
        return conn
    except Exception as e:
        messagebox.showerror("Error de Pool", f"No se pudo obtener una conexión: {e}")
        return None


def release_connection(conn):
    global connection_pool
    if connection_pool and conn:
        try:
            connection_pool.release(conn)
        except Exception as e:
            print(f"Error al devolver conexión al pool: {e}")


def close_connection_pool():
    global connection_pool
    if connection_pool:
        try:
            connection_pool.close()
            print("Pool de conexiones cerrado.")
        except Exception as e:
            print(f"Error al cerrar el pool: {e}")