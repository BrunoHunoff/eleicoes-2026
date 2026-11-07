from flask import Blueprint, render_template, request

from app.services import modelos_service, predicao_service
from app.services.analise_service import CORES_PARTIDOS
from app.services.dados_service import ROTULOS, carregar_base_atual

predicao_bp = Blueprint("predicao", __name__)


@predicao_bp.get("/predicao")
def index():
    resultados = modelos_service.carregar_resultados_mock()
    modelo_atual = modelos_service.escolher_modelo(request.args.get("modelo"))
    mapa_atual = "estados" if request.args.get("mapa") == "estados" else "municipios"

    salvas = predicao_service.carregar_predicoes_salvas_mock()
    if mapa_atual == "estados":
        mapa_predicao = predicao_service.mapa_por_estado(salvas)
    else:
        mapa_predicao = predicao_service.mapa_por_municipio(salvas)
    por_uf = predicao_service.resumir_por_grupo(salvas, "sg_uf")
    teste = predicao_service.carregar_predicoes_teste_mock(modelo_atual)

    return render_template(
        "predicao.html",
        resultados=resultados,
        rotulos=ROTULOS,
        modelos=modelos_service.MODELOS_DISPONIVEIS,
        modelo_atual=modelo_atual,
        mapa_atual=mapa_atual,
        cores_partidos=CORES_PARTIDOS,
        ufs=sorted(carregar_base_atual()["sg_uf"].unique()),
        previstos=predicao_service.resumir_previstos(salvas),
        por_regiao=predicao_service.resumir_por_grupo(salvas, "regiao").to_dict("records"),
        por_uf=por_uf.to_dict("records"),
        municipios_previstos=salvas.to_dict("records"),
        grafico_previstos_regiao=predicao_service.grafico_previstos_por_regiao(salvas),
        grafico_probabilidade_uf=predicao_service.grafico_probabilidade_por_uf(por_uf),
        mapa_predicao=mapa_predicao,
        acertos=predicao_service.resumir_acertos(teste),
        acertos_por_regiao=predicao_service.acertos_por_regiao(teste).to_dict("records"),
        grafico_real_previsto=predicao_service.grafico_real_previsto(teste),
        grafico_probabilidade_votos=predicao_service.grafico_probabilidade_votos(teste),
        mapa_acertos=predicao_service.mapa_acertos(teste),
    )
