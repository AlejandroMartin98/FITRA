from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app as app
from app.db import get_main_connection, create_user_database, create_default_tables_for_user, get_connection_for_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import sys

auth_bp = Blueprint('auth', __name__)  # sin template_folder

@auth_bp.route('/')
def index():
    # Si NO hay user_id en sesión, mostramos el landing (index.html)
    if 'user_id' not in session:
        app.logger.info("No hay sesión de usuario, mostrando el landing")
        return render_template('index.html')
    
    app.logger.info("Usuario logueado, redirigiendo al dashboard")
    return redirect(url_for('dashboard.show_dashboard'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_main_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE USERNAME = %s", (username,))
                usuario = cursor.fetchone()

            if usuario and check_password_hash(usuario['PASSWORD'], password):
                session['user_id'] = usuario['ID']
                session['username'] = usuario['USERNAME']  # 👈 NECESARIO PARA USAR SU DB
                session['nombre'] = usuario['NOMBRE']
                return redirect(url_for('dashboard.show_dashboard'))
            else:
                flash('Credenciales incorrectas')

        except Exception as e:
            app.logger.error(f"Error en login: {e}")
            flash('Error en el inicio de sesión')
    
    return render_template('login.html')



@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        fecha_cumple = request.form['fecha_cumple']
        email = request.form['email']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        fecha_registro = datetime.datetime.now()
        ultimo_login = None
        estado = "activo"
        rol_id = 1  # por defecto

        import re
        if not re.fullmatch(r'[A-Za-z0-9]+', username):
            flash("El nombre de usuario solo puede contener letras y números (sin espacios ni símbolos).", "warning")
            return render_template('registro.html')

        try:
            from app.db import get_main_connection
            connection = get_main_connection()
            with connection.cursor() as cursor:
                # Verificar si ya existe el username
                cursor.execute("SELECT * FROM usuarios WHERE USERNAME = %s", (username,))
                if cursor.fetchone():
                    flash("El nombre de usuario ya está en uso. Elige otro.", "warning")
                    return render_template('registro.html')

                # Verificar si ya existe el email
                cursor.execute("SELECT * FROM usuarios WHERE EMAIL = %s", (email,))
                if cursor.fetchone():
                    flash("El correo electrónico ya está registrado.", "warning")
                    return render_template('registro.html')
                # Verificar si ya existe la base de datos
                cursor.execute("SHOW DATABASES LIKE %s", (f"db_{username}",))
                if cursor.fetchone():
                    flash("Ya existe una cuenta con ese nombre de usuario (base de datos existente). Intenta con otro.", "warning")
                    return render_template('registro.html')
                
                # Insertar nuevo usuario
                cursor.execute("""
                    INSERT INTO usuarios (NOMBRE, APELLIDO, FECHA_CUMPLE, EMAIL, USERNAME, PASSWORD, FECHA_REGISTRO, ULTIMO_LOGIN, ESTADO, ROL_ID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (nombre, apellido, fecha_cumple, email, username, password, fecha_registro, ultimo_login, estado, rol_id))
                connection.commit()

                # Crear base de datos del usuario
                cursor.execute(f"CREATE DATABASE db_{username}")
                connection.commit()

            # Conectar a la nueva base y crear tablas
            user_db_connection = get_connection_for_user(username)
            with user_db_connection.cursor() as cursor:
                with user_db_connection.cursor() as cursor:
                # Tabla FONDOS
                    cursor.execute("""
                        CREATE TABLE fondos (
                            ID INT AUTO_INCREMENT PRIMARY KEY,
                            NOMBRE VARCHAR(100),
                            TIPO VARCHAR(50),
                            CANTIDAD DECIMAL(10, 2)
                        );
                    """)

                    # Tabla MOVIMIENTOS
                    cursor.execute("""
                        CREATE TABLE movimientos (
                            ID INT AUTO_INCREMENT PRIMARY KEY,
                            FECHA DATE,
                            TIPO VARCHAR(50),
                            DESCRIPCION TEXT,
                            MONTO DECIMAL(10,2),
                            FONDO_ID INT,
                            FOREIGN KEY (FONDO_ID) REFERENCES fondos(ID)
                        );
                    """)

                    # Tabla DEUDAS
                    cursor.execute("""
                        CREATE TABLE deudas (
                            ID INT AUTO_INCREMENT PRIMARY KEY,
                            DESCRIPCION TEXT,
                            MONTO_TOTAL DECIMAL(10,2),
                            SALDO_PENDIENTE DECIMAL(10,2),
                            FECHA DATE
                        );
                    """)

                    # Tabla APORTES
                    cursor.execute("""
                        CREATE TABLE aportes (
                            ID INT AUTO_INCREMENT PRIMARY KEY,
                            DEUDA_ID INT,
                            MONTO DECIMAL(10,2),
                            FECHA DATE,
                            FOREIGN KEY (DEUDA_ID) REFERENCES deudas(ID)
                        );
                    """)

                user_db_connection.commit()

            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"Error al registrar: {e}")
            flash("Ocurrió un error durante el registro.", "danger")
            return redirect(url_for('auth.registro'))

    return render_template('registro.html')



@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for('auth.login'))
