from flask import Flask

from app.routes.analise_routes import analise_bp
from app.routes.dados_routes import dados_bp
from app.routes.inicio_routes import inicio_bp
from app.routes.modelos_routes import modelos_bp
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(inicio_bp)
    app.register_blueprint(dados_bp)
    app.register_blueprint(analise_bp)
    app.register_blueprint(modelos_bp)

    return app
