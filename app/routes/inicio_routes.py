from flask import Blueprint, render_template

inicio_bp = Blueprint("inicio", __name__)


@inicio_bp.get("/")
def index():
    """Página inicial com um cartão para cada seção."""
    return render_template("inicio.html")
