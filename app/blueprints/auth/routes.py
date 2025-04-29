from flask import Blueprint, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app.db import get_main_connection, get_connection_for_user
import datetime
import re

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Usuario y contraseña son requeridos"
            })

        try:
            conn = get_main_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM usuarios WHERE USERNAME = %s", (username,))
                usuario = cursor.fetchone()

            if not usuario:
                return jsonify({
                    "success": False,
                    "message": "Usuario no encontrado. ¿Deseas registrarte?",
                    "redirect": url_for('auth.registro')  
                })

            if check_password_hash(usuario['PASSWORD'], password):
                session['user_id'] = usuario['ID']
                session['username'] = usuario['USERNAME']
                session['nombre'] = usuario['NOMBRE']
                return jsonify({
                    "success": True,
                    "message": "Inicio de sesión exitoso",
                    "redirect": url_for('dashboard.show_dashboard')
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Credenciales incorrectas"
                })

        except Exception as e:
            print("Error en login:", e)
            return jsonify({
                "success": False,
                "message": "Error interno del servidor",
                "redirect": url_for('auth.login') 
            })

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

         # Validación del nombre de usuario
        if not re.fullmatch(r'[A-Za-z0-9]+', username):
            return jsonify({
                "success": False,
                "message": "El nombre de usuario solo puede contener letras y números (sin espacios ni símbolos).",
                "redirect": url_for('registro')
            }), 

        try:
            from app.db import get_main_connection
            connection = get_main_connection()
            with connection.cursor() as cursor:
                # Verificar si ya existe el username
                cursor.execute("SELECT * FROM usuarios WHERE USERNAME = %s", (username,))
                if cursor.fetchone():
                     return jsonify({
                        "success": False,
                        "message": "El nombre de usuario ya está en uso. Elige otro.",
                        "redirect": url_for('registro')
                    }), 

                # Verificar si ya existe el email
                cursor.execute("SELECT * FROM usuarios WHERE EMAIL = %s", (email,))
                if cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "message": "El correo electrónico ya está registrado.",
                        "redirect": url_for('registro')
                    }), 
                # Verificar si ya existe la base de datos
                cursor.execute("SHOW DATABASES LIKE %s", (f"db_{username}",))
                if cursor.fetchone():
                    return jsonify({
                        "success": False,
                        "message": "Ya existe una cuenta con ese nombre de usuario (base de datos existente). Intenta con otro.",
                        "redirect": url_for('registro')
                    }), 
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

            return jsonify({
                "success": True,
                "message": "Registro exitoso. Ahora puedes iniciar sesión.",
                "redirect": url_for('login')
            }), 

        except Exception as e:
            print(f"Error al registrar: {e}")
            return jsonify({
                "success": False,
                "message": "Ocurrió un error durante el registro.",
                "redirect": url_for('registro')
            }), 

    return render_template('registro.html')



@auth_bp.route('/logout')
def logout():
    session.clear()
    print("Sesión cerrada")
    return jsonify({
        "success": True,
        "message": "Sesión cerrada con exito",
        "redirect": url_for('index')
    })