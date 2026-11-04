from flask import Blueprint, render_template

from app.services import analise_service, dados_service

analise_bp = Blueprint("analise", __name__)

# Variável do histograma e da dispersão enquanto o filtro não funciona (será ligado na entrega final)
VARIAVEL_PADRAO = "pib_per_capita"


@analise_bp.get("/analise")
def index():
    df = dados_service.carregar_base_atual()
    return render_template(
        "analise.html",
        indicadores=analise_service.calcular_indicadores(df),
        cores_partidos=analise_service.CORES_PARTIDOS,
        regioes=dados_service.REGIOES,
        ufs=sorted(df["sg_uf"].unique()),
        variaveis=dados_service.COLUNAS_NUMERICAS,
        rotulos=dados_service.ROTULOS,
        variavel_atual=VARIAVEL_PADRAO,
        barras=analise_service.grafico_barras_vencedores(df),
        pizza=analise_service.grafico_pizza_vencedores(df),
        histograma=analise_service.grafico_histograma(df, VARIAVEL_PADRAO),
        dispersao=analise_service.grafico_dispersao(df, VARIAVEL_PADRAO),
        mapa=analise_service.mapa_municipios(df),
        correlacao=analise_service.mapa_calor_correlacao(df),
    )
