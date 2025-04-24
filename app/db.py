from flask import current_app as app  # 👈 agrega esto arriba en tu db.py
import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv
import sys

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
                SALDO DECIMAL(10,2) DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS MOVIMIENTOS (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                FECHA DATETIME,
                TIPO VARCHAR(20), -- ingreso, egreso, aporte, deuda
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
                FECHA_CREACION DATETIME,
            )
        """)

        # Puedes añadir más: INGRESOS, APORTES, NEGOCIOS, CLIENTES, etc.

    conn.commit()
    conn.close()

# Obtener conexión a la base de datos personalizada del usuario
def get_connection_for_user(username):
    """
    Devuelve una conexión pymysql a la base de datos personalizada del usuario.
    Se espera que la BD exista y se llame 'db_<username_lower>'.
    """
    if not username or not isinstance(username, str):
        raise ValueError("El parámetro 'username' debe ser una cadena no vacía.")

    db_name = f"db_{username.lower()}"

    # Leer credenciales desde .env o usar valores por defecto
    host     = os.getenv("DB_HOST", "localhost")
    user     = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")

    try:
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
        # 1049 = Unknown database
        if e.args[0] == 1049:
            raise RuntimeError(f"La base de datos '{db_name}' no existe.") from e
        else:
            # Propaga otros errores de conexión
            raise
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

    # Cada fila es {'USERNAME': 'DexterWarp'}, devolvemos la lista de strings
    return [r['USERNAME'] for r in rows]

