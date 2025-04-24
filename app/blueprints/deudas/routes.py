# app/blueprints/deudas/routes.py

from flask import Blueprint, render_template, session, abort, request, redirect, url_for, flash, jsonify
from app.db import get_connection_for_user
from pymysql.cursors import DictCursor

deudas_bp = Blueprint('deudas', __name__, url_prefix='/deudas')

@deudas_bp.route('/')
def deudas():
    username = session.get('username')
    if not username:
        abort(401)

    conn = get_connection_for_user(username)

    with conn.cursor(DictCursor) as cur:
        cur.execute("SELECT id, descripcion, monto_total, saldo_pendiente, fecha FROM DEUDAS ORDER BY descripcion ASC")
        deudas = cur.fetchall()
    conn.close()

    return render_template('deudas/deudas.html', deudas=deudas, username=username)

@deudas_bp.route('/agregar', methods=['POST'])
def agregar_deuda():
    nombre = request.form.get('nombre')
    monto = request.form.get('monto')
    estado = request.form.get('estado')  # Por ejemplo: 'pendiente' o 'pagado'
    username = session.get('username')

    if not (nombre and monto and estado):
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('deudas.deudas'))

    conn = get_connection_for_user(username)
    cur = conn.cursor()

    # Verificar si la deuda ya existe
    cur.execute("SELECT id FROM DEUDAS WHERE nombre = %s", (nombre,))
    deuda_existente = cur.fetchone()

    if deuda_existente:
        flash('Ya existe una deuda con ese nombre.', 'danger')
        conn.close()
        return redirect(url_for('deudas.deudas'))

    # Insertar nueva deuda
    cur.execute("INSERT INTO DEUDAS (nombre, monto, estado) VALUES (%s, %s, %s)", (nombre, monto, estado))
    conn.commit()
    conn.close()

    flash('Deuda agregada exitosamente.', 'success')
    return redirect(url_for('deudas.deudas'))

@deudas_bp.route('/detalle/<int:id>')
def deuda_detalle(id):
    username = session.get('username')
    conn = get_connection_for_user(username)
    cur = conn.cursor(DictCursor)

    cur.execute("SELECT * FROM DEUDAS WHERE id = %s", (id,))
    deuda = cur.fetchone()
    conn.close()

    if not deuda:
        flash('Deuda no encontrada', 'danger')
        return redirect(url_for('deudas.deudas'))

    return render_template('deudas/deuda_detail.html', deuda=deuda)

@deudas_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_deuda(id):
    username = session.get('username')
    conn = get_connection_for_user(username)
    cur = conn.cursor(DictCursor)

    cur.execute("SELECT * FROM DEUDAS WHERE id = %s", (id,))
    deuda = cur.fetchone()

    if not deuda:
        conn.close()
        return jsonify({'success': False, 'message': 'Deuda no encontrada.'}), 404

    if deuda['estado'] != 'pagado':
        conn.close()
        return jsonify({'success': False, 'message': 'Solo puedes eliminar deudas pagadas.'}), 400

    cur.execute("DELETE FROM DEUDAS WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Deuda eliminada correctamente.'})
