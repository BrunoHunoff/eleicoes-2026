from flask import Blueprint, render_template, request

from app.services import modelos_service
from app.services.dados_service import ROTULOS

modelos_bp = Blueprint("modelos", __name__)


@modelos_bp.get("/modelos")
def index():
    resultados = modelos_service.carregar_resultados_mock()
    modelo_atual = modelos_service.escolher_modelo(request.args.get("modelo"))
    modelo = resultados["modelos"][modelo_atual]
    importancias = modelo["importancia_variaveis"]
    return render_template(
        "modelos.html",
        resultados=resultados,
        rotulos=ROTULOS,
        modelos=modelos_service.MODELOS_DISPONIVEIS,
        modelo_atual=modelo_atual,
        modelo=modelo,
        metricas=modelos_service.calcular_metricas(modelo, resultados["baseline"]),
        resumo=modelos_service.resumir_treino(resultados, modelo),
        comparacao=modelos_service.montar_comparacao(resultados),
        matriz_confusao=modelos_service.grafico_matriz_confusao(modelo["matriz_confusao"], resultados["classes"]),
        importancia=modelos_service.grafico_importancia(importancias) if importancias else None,
    )
