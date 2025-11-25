import oracledb
import hashlib
from tkinter import messagebox

# --- CONFIGURACIÓN MAESTRA (Dueño del Esquema) ---
DB_USER = "adrian"
DB_PASS = "adrian_pwd"
DB_DSN = "localhost:1521/XE"

connection_pool = None


# 1. Iniciar Pool Global (Se conecta como ADRIAN al abrir la app)
def init_pool():
    global connection_pool
    try:
        oracledb.init_oracle_client()
    except:
        pass
    try:
        connection_pool = oracledb.create_pool(
            user=DB_USER,
            password=DB_PASS,
            dsn=DB_DSN,
            min=1, max=5, increment=1
        )
        print("Pool de conexión iniciado correctamente.")
        return True
    except Exception as e:
        print(f"Error fatal DB: {e}")
        return False


# 2. Validar Login contra Tabla EMPLEADOS
def validar_usuario_app(usuario, password_plano):
    """
    Retorna: (True, datos_empleado) si es correcto, (False, msg) si falla.
    datos_empleado = (id_empleado, nombre_completo, cargo)
    """
    conn = get_connection()
    if not conn: return False, "Sin conexión a BD"

    try:
        # Hashear la contraseña ingresada
        pass_hash = hashlib.sha256(password_plano.encode()).hexdigest()

        cur = conn.cursor()
        sql = """SELECT id_empleado, nombre, apellido, cargo
                 FROM empleados
                 WHERE UPPER(usuario_app) = UPPER(:1) \
                   AND password_hash = :2"""
        cur.execute(sql, [usuario, pass_hash])
        row = cur.fetchone()

        if row:
            # Login Exitoso
            return True, {"id": row[0], "nombre": f"{row[1]} {row[2]}", "cargo": row[3]}
        else:
            return False, "Usuario o contraseña incorrectos"
    except Exception as e:
        return False, str(e)
    finally:
        release_connection(conn)


def get_connection():
    global connection_pool
    if not connection_pool: init_pool()  
    if connection_pool:
        try:
            return connection_pool.acquire()
        except:
            return None
    return None


def release_connection(conn):
    if connection_pool and conn:
        try:
            connection_pool.release(conn)
        except:
            pass


def close_connection_pool():
    if connection_pool:
        connection_pool.close()
