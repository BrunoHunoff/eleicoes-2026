from flask import Blueprint, render_template

from app.services import dados_service

dados_bp = Blueprint("dados", __name__)

LINHAS_AMOSTRA = 10


@dados_bp.get("/dados")
def index():
    df = dados_service.carregar_base_atual()
    amostra = df.head(LINHAS_AMOSTRA)
    return render_template(
        "dados.html",
        resumo=dados_service.resumir_base(df),
        dicionario=dados_service.listar_dicionario(),
        estatisticas=dados_service.calcular_estatisticas(df),
        colunas_amostra=amostra.columns.tolist(),
        linhas_amostra=amostra.values.tolist(),
    )
