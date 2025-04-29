from app import create_app, socketio
from app.db import create_default_tables_for_user, get_all_usernames, user_database_exists
from livereload import Server  # 👈 importamos livereload
import webbrowser
import threading

app = create_app()

def open_browser():
    webbrowser.open_new("http://localhost:5000/")

# Comando CLI
@app.cli.command("init-user-tables")
def init_user_tables():
    """Verifica usuarios y crea tablas si la base de datos existe"""
    usernames = get_all_usernames()
    if not usernames:
        print("⚠️ No se encontraron usuarios registrados.")
        return

    for username in usernames:
        db_name = f"db_{username.lower()}"
        
        if user_database_exists(username):
            try:
                create_default_tables_for_user(db_name)
                print(f"✔️ Tablas creadas en {db_name}")
            except Exception as e:
                print(f"❌ Error al crear tablas en {db_name}: {e}")
        else:
            print(f"⚠️ Base de datos {db_name} no existe para el usuario {username}. No se crearon tablas.")

    print("✅ Verificación completa.")

if __name__ == '__main__':
    """threading.Timer(1.5, open_browser).start()

    server = Server(app.wsgi_app)
    server.serve(port=5000, debug=True)
    if __name__ == '__main__':"""
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

#if __name__ == '__main__':
#    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)  # Se agrega el parámetro allow_unsafe_werkzeug