from flask import render_template, request, redirect, url_for, session, jsonify
from app.db import get_connection_for_user
from app.blueprints.movimientos import movimientos_bp

@movimientos_bp.route('/')
def movimientos():
    username = session.get('username')
    if not username:
        return redirect(url_for('auth.login'))
    
    conn = get_connection_for_user(username)
    cur = conn.cursor()

    # Traemos movimientos y nombre de fondo relacionado
    cur.execute("""
        SELECT m.id, m.fecha, m.tipo, m.descripcion, m.monto, f.nombre as fondo_nombre
        FROM MOVIMIENTOS m
        JOIN FONDOS f ON m.fondo_id = f.id
        ORDER BY m.fecha DESC
    """)
    movimientos = cur.fetchall()

    # Traemos los fondos para el formulario
    cur.execute("SELECT id, nombre FROM FONDOS ORDER BY nombre ASC")
    fondos = cur.fetchall()

    conn.close()
    
    return render_template('movimientos/movimientos.html', movimientos=movimientos, fondos=fondos)

@movimientos_bp.route('/agregar', methods=['POST'])
def agregar_movimiento_ajax():
    data = request.get_json()
    fecha = data.get('fecha')
    tipo = data.get('tipo')
    descripcion = data.get('descripcion')
    monto = data.get('monto')
    fondo_id = data.get('fondo_id')

    if not all([fecha, tipo, descripcion, monto, fondo_id]):
        return jsonify({'success': False, 'message': 'Faltan datos para completar el movimiento.'})

    conn = get_connection_for_user(session['username'])
    cur = conn.cursor()

    cur.execute("SELECT cantidad FROM FONDOS WHERE id = %s", (fondo_id,))
    fondo = cur.fetchone()

    if not fondo:
        conn.close()
        return jsonify({'success': False, 'message': 'Fondo no encontrado.'})

    cantidad_fondo = fondo['cantidad']

    if tipo == 'egreso' and cantidad_fondo < monto:
        conn.close()
        return jsonify({'success': False, 'fondo_suficiente': False, 'message': 'No hay suficientes fondos para realizar este movimiento.'})

    # Registrar el movimiento
    cur.execute("INSERT INTO MOVIMIENTOS (fecha, tipo, descripcion, monto, fondo_id) VALUES (%s, %s, %s, %s, %s)",
                (fecha, tipo, descripcion, monto, fondo_id))
    conn.commit()

    # Actualizar el fondo
    if tipo == 'egreso':
        cur.execute("UPDATE FONDOS SET cantidad = cantidad - %s WHERE id = %s", (monto, fondo_id))
    else:  # 👈 agregar también para ingresos
        cur.execute("UPDATE FONDOS SET cantidad = cantidad + %s WHERE id = %s", (monto, fondo_id))
    conn.commit()

    # Obtener el nuevo saldo actualizado
    cur.execute("SELECT cantidad FROM FONDOS WHERE id = %s", (fondo_id,))
    nuevo_fondo = cur.fetchone()
    nuevo_saldo = nuevo_fondo['cantidad']

    conn.close()

    return jsonify({'success': True, 'message': 'Movimiento registrado correctamente.', 'nuevo_saldo': nuevo_saldo})
