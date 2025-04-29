from flask import Flask, render_template 
from dotenv import load_dotenv
import os
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    load_dotenv()
    # indicamos que las plantillas están en app/templates
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.secret_key = os.getenv('SECRET_KEY') or 'fallback_key'

    # Registro de blueprints
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.fondos.routes import fondos_bp
    from app.blueprints.movimientos.routes import movimientos_bp
    from app.blueprints.deudas.routes import deudas_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(fondos_bp)
    app.register_blueprint(movimientos_bp)
    app.register_blueprint(deudas_bp)
    @app.route('/')   # 👈 Aquí definimos la ruta principal
    def index():
        return render_template('index.html')  # 👈 archivo de inicio

    socketio.init_app(app)
    
    return app
