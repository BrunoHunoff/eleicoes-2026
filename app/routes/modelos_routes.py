from flask import Blueprint, render_template

modelos_bp = Blueprint("modelos", __name__)


@modelos_bp.get("/modelos")
def index():
    return render_template("modelos.html")
