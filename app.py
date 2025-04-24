from app import create_app, socketio
from app.db import create_default_tables_for_user, get_all_usernames


app = create_app()
# ──────── Aquí agregas el comando Flask‑CLI ────────
@app.cli.command("init-user-tables")
def init_user_tables():
    """
    Crea las tablas por defecto (FONDOS, MOVIMIENTOS, DEUDAS)
    en cada base de datos db_<username> encontrada en la BD principal.
    """
    usernames = get_all_usernames()
    if not usernames:
        print("⚠️  No se encontraron usuarios registrados.")
        return

    for username in usernames:
        db_name = f"db_{username.lower()}"
        try:
            create_default_tables_for_user(db_name)
            print(f"✔️  Tablas creadas en {db_name}")
        except Exception as e:
            print(f"❌  Error en {db_name}: {e}")

    print("✅ Todas las bases de usuario están listas.")
# ────────────────────────────────────────────────────
@socketio.on('message')
def handle_message(msg):
    print(f'Mensaje recibido: {msg}')
    socketio.send(msg)
if __name__ == '__main__':
    app.run(debug=True)
