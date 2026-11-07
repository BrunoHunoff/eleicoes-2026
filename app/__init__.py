from flask import Flask

from app.routes.analise_routes import analise_bp
from app.routes.dados_routes import dados_bp
from app.routes.inicio_routes import inicio_bp
from app.routes.modelos_routes import modelos_bp
from app.routes.predicao_routes import predicao_bp
from app.utils import formatar_numero
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.add_template_filter(formatar_numero, "numero")

    app.register_blueprint(inicio_bp)
    app.register_blueprint(dados_bp)
    app.register_blueprint(analise_bp)
    app.register_blueprint(modelos_bp)
    app.register_blueprint(predicao_bp)

    return app
