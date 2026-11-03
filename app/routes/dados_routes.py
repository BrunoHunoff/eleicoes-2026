from flask import Blueprint, render_template

dados_bp = Blueprint("dados", __name__)


@dados_bp.get("/dados")
def index():
    return render_template("dados.html")
