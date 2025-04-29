from flask import current_app as app  # 👈 agrega esto arriba en tu db.py
import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env

# Conexión a la base de datos principal
def get_main_connection():
    try:
        app.logger.info("Intentando conectar a la base de datos:")
        app.logger.info(f"HOST: {os.getenv('DB_HOST')}")
        app.logger.info(f"USER: {os.getenv('DB_USER')}")
        app.logger.info(f"DATABASE: {os.getenv('DB_NAME')}")
        
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            cursorclass=DictCursor
        )
        app.logger.info("Conexión exitosa a la base de datos.")
        return connection
    except pymysql.MySQLError as e:
        app.logger.error(f"Error al conectar a la base de datos: {e}")
        return None

def user_database_exists(username):
    """
    Verifica si la base de datos del usuario existe (sin crearla).
    Retorna True si existe, False si no.
    """
    if not username or not isinstance(username, str):
        return False

    db_name = f"db_{username.lower()}"
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")

    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=DictCursor,
            connect_timeout=2
        )
        conn.close()
        return True  # Si conecta exitosamente, existe
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1049:  # Error de base de datos desconocida
            return False
        else:
            raise e  # Otro error (de conexión, credenciales, etc.)

# Crea una nueva base de datos para el usuario
def create_user_database(user_id):
    db_name = f"user_data_{user_id}"

    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursorclass=DictCursor
    )

    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    conn.commit()
    conn.close()

    # Después de crearla, también creamos sus tablas por defecto
    create_default_tables_for_user(db_name)

    return db_name

# Crea las tablas iniciales de un usuario
def create_default_tables_for_user(db_name):
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=db_name,
        cursorclass=DictCursor
    )

    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS FONDOS (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                NOMBRE VARCHAR(100),
                TIPO VARCHAR(50), -- Ahorros, Efectivo, etc.
                SALDO DECIMAL(10,2) DEFAULT 0,
                FECHA_SISTEMA DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Fecha automática del sistema
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS MOVIMIENTOS (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                FECHA_USUARIO DATETIME,  -- Fecha que ingresa el usuario
                FECHA_SISTEMA DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Fecha automática del sistema
                TIPO VARCHAR(20), -- ingreso, egreso
                FONDO_ID INT,
                MONTO DECIMAL(10,2),
                DESCRIPCION TEXT,
                FOREIGN KEY (FONDO_ID) REFERENCES FONDOS(ID)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS DEUDAS (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                NOMBRE_FONDO VARCHAR(255),
                DESCRIPCION TEXT,
                MONTO_TOTAL DECIMAL(10,2),
                SALDO_RESTANTE DECIMAL(10,2),
                FECHA_ADQUISICION DATETIME,  -- Fecha real de la deuda
                FECHA_REGISTRO DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Cuando se registró en el sistema
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS APORTES_DEUDA (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                DEUDA_ID INT,
                FECHA_APORTE DATETIME,  -- Fecha del aporte (usuario)
                FECHA_REGISTRO DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Fecha sistema
                MONTO DECIMAL(10,2),
                FOREIGN KEY (DEUDA_ID) REFERENCES DEUDAS(ID) ON DELETE CASCADE
            )
        """)
        # Puedes añadir más: INGRESOS, APORTES, NEGOCIOS, CLIENTES, etc.

    conn.commit()
    conn.close()

# Obtener conexión a la base de datos personalizada del usuario
def get_connection_for_user(username):
    """
    Devuelve una conexión pymysql a la base de datos personalizada del usuario.
    Si la BD no existe, intenta crearla primero.
    """
    if not username or not isinstance(username, str):
        return None
        
    db_name = f"db_{username.lower()}"
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    
    try:
        # Primero intentamos conectar a la base de datos del usuario
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=DictCursor,
            charset="utf8mb4",
            autocommit=False
        )
        return conn
    except pymysql.err.OperationalError as e:
        # Si la base de datos no existe (error 1049), intentamos crearla
        if e.args[0] == 1049:  # Unknown database
            try:
                # Conectar sin especificar una base de datos
                root_conn = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    charset="utf8mb4"
                )
                
                with root_conn.cursor() as cursor:
                    # Crear la base de datos para el usuario
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                root_conn.commit()
                root_conn.close()
                
                # Crear las tablas por defecto
                create_default_tables_for_user(db_name)
                
                # Ahora intentamos conectar de nuevo a la base de datos del usuario
                conn = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=db_name,
                    cursorclass=DictCursor,
                    charset="utf8mb4",
                    autocommit=False
                )
                app.logger.info(f"Base de datos {db_name} creada con éxito para el usuario {username}")
                return conn
            except Exception as create_error:
                app.logger.error(f"Error al crear la base de datos: {create_error}")
                return None
        else:
            app.logger.error(f"Error de conexión: {e}")
            return None
    except Exception as general_error:
        app.logger.error(f"Error general: {general_error}")
        return None
def get_all_usernames():
    """
    Devuelve una lista de todos los USERNAME registrados en la base de datos principal.
    """
    from app.db import get_main_connection

    conn = get_main_connection()
    if conn is None:
        raise RuntimeError("No fue posible conectar a la base de datos principal")

    with conn.cursor() as cur:
        cur.execute("SELECT USERNAME FROM usuarios")
        rows = cur.fetchall()
    conn.close()

    # Cada fila es {'USERNAME': 'nickname'}, devolvemos la lista de strings
    return [r['USERNAME'] for r in rows]

