from flask import Blueprint, render_template, session, abort, request, redirect, url_for, flash
from app.db import get_connection_for_user
from pymysql.cursors import DictCursor

fondos_bp = Blueprint('fondos', __name__, url_prefix='/fondos')

@fondos_bp.route('/')
def fondos():
    # 1) Verificar usuario en sesión
    username = session.get('username')
    if not username:
        abort(401)  # No autorizado, o podrías hacer redirect(url_for('auth.login'))

    # 2) Conectar a la base de datos
    conn = get_connection_for_user(username)

    # 3) Hacer la consulta a FONDOS
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre, cantidad FROM FONDOS ORDER BY nombre ASC")
        fondos = cur.fetchall()
    conn.close()

    # 4) Renderizar el template
    return render_template('fondos/fondos.html', fondos=fondos, username=username)

@fondos_bp.route('/fondos/agregar', methods=['POST'])
def agregar_fondo():
    nombre = request.form.get('nombre')
    tipo = request.form.get('tipo')
    cantidad = request.form.get('cantidad')
    username = session.get('username')

    conn = get_connection_for_user(username)
    cur = conn.cursor()

    # 1. Verificar si el fondo ya existe
    cur.execute("SELECT id FROM FONDOS WHERE nombre = %s", (nombre,))
    fondo_existente = cur.fetchone()

    if fondo_existente:
        # Fondo ya existe, mostrar error
        flash('Ya existe un fondo con ese nombre.', 'danger')  # <-- Agrega este flash
        conn.close()
        return redirect(url_for('fondos.fondos'))

    # 2. Si no existe, insertarlo
    cur.execute("INSERT INTO FONDOS (nombre, tipo, cantidad) VALUES (%s, %s, %s)", (nombre, tipo, cantidad))
    conn.commit()
    conn.close()

    flash('Fondo agregado exitosamente.', 'success')  # <-- Otro flash de éxito
    return redirect(url_for('fondos.fondos'))

@fondos_bp.route('/fondo_detalle/<int:id>')
def fondo_detalle(id):
    username = session.get('username')
    conn = get_connection_for_user(username)

    cur = conn.cursor(DictCursor)
    cur.execute("SELECT * FROM FONDOS WHERE id = %s", (id,))
    fondo = cur.fetchone()

    conn.close()

    if not fondo:
        flash('Fondo no encontrado', 'danger')
        return redirect(url_for('fondos.fondos'))

    # ✅ Pasamos el objeto fondo completo a la plantilla
    return render_template('fondos/fondo_detail.html', fondo=fondo)

from flask import jsonify

@fondos_bp.route('/fondos/fondos/eliminar/<int:id>', methods=['POST'])
def eliminar_fondo(id):
    username = session.get('username')
    conn = get_connection_for_user(username)
    cur = conn.cursor(DictCursor)

    cur.execute("SELECT * FROM FONDOS WHERE ID = %s", (id,))
    fondo = cur.fetchone()

    if not fondo:
        conn.close()
        return jsonify({'success': False, 'message': 'Fondo no encontrado.'}), 404

    # Verificar si hay movimientos asociados al fondo
    cur.execute("SELECT COUNT(*) FROM MOVIMIENTOS WHERE FONDO_ID = %s", (id,))
    movimientos_count = cur.fetchone()['COUNT(*)']

    if movimientos_count > 0:
        conn.close()
        # Enviar el mensaje con la cantidad de movimientos
        return jsonify({
            'success': False,
            'message': f"Este fondo tiene {movimientos_count} movimientos recientes y no puede ser eliminado actualmente."
        }), 400

    # Si no hay movimientos, proceder con la eliminación
    cur.execute("DELETE FROM FONDOS WHERE ID = %s", (id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Fondo eliminado correctamente.'})
