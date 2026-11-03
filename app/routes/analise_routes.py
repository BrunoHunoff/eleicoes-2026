from flask import Blueprint, render_template

analise_bp = Blueprint("analise", __name__)


@analise_bp.get("/analise")
def index():
    return render_template("analise.html")
