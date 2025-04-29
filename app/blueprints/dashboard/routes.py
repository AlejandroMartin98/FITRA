from flask     import Blueprint, render_template, session, abort, redirect, url_for, flash
from app.db    import get_connection_for_user
    
dashboard_bp = Blueprint('dashboard', __name__)


# Protegemos todo el blueprint
@dashboard_bp.before_request
def require_login_dashboard():
    if 'username' not in session:
        flash('Por favor inicia sesión para continuar.', 'warning')
        return redirect(url_for('auth.index'))  # Ajusta si el index se llama diferente
    
@dashboard_bp.route('/dashboard')
def show_dashboard():
    # 1) Comprueba que exista un usuario en sesión
    username = session.get('username')
    if not username:
        return render_template('index.html')

    # 2) Conéctate a la BD del usuario
    try:
        conn = get_connection_for_user(username)
        
        # Verifica si la conexión es None
        if conn is None:
            flash('No se pudo conectar a tu base de datos. Por favor, contacta con soporte.', 'danger')
            # Cerrar la sesión del usuario y enviarlo al login
            flash('Hubo un problema con tu base de datos. Por favor intenta más tarde.', 'danger')
            return redirect(url_for('auth.index'))

        
        # 3) Consulta tus métricas
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM FONDOS")
            total_fondos = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) AS total FROM MOVIMIENTOS")
            total_movimientos = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) AS total FROM DEUDAS")
            total_deudas = cur.fetchone()['total']
        conn.close()

        # 4) Renderiza
        return render_template('dashboard.html',
                              total_fondos=total_fondos,
                              total_movimientos=total_movimientos,
                              total_deudas=total_deudas,
                              username=username)
                              
    except Exception as e:
        flash(f'Ocurrió un error al acceder a tus datos.', 'danger')
        session.clear()
        return redirect(url_for('auth.index'))


