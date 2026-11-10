from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services import modelos_service
from app.services.dados_service import ROTULOS, carregar_base_atual

modelos_bp = Blueprint("modelos", __name__)


@modelos_bp.get("/modelos")
def index():
    """Página Modelos: configuração do último treino, métricas, gráficos e comparação dos modelos."""
    resultados = modelos_service.carregar_resultados()
    modelo_atual = modelos_service.escolher_modelo(request.args.get("modelo"))
    modelo = resultados["modelos"][modelo_atual]
    importancias = modelo["importancia_variaveis"]
    return render_template(
        "modelos.html",
        resultados=resultados,
        rotulos=ROTULOS,
        modelos=modelos_service.MODELOS_DISPONIVEIS,
        variaveis=modelos_service.VARIAVEIS_CANDIDATAS,
        modelo_atual=modelo_atual,
        modelo=modelo,
        base_mudou=modelos_service.base_mudou(resultados),
        metricas=modelos_service.calcular_metricas(modelo, resultados["baseline"]),
        resumo=modelos_service.resumir_treino(resultados, modelo),
        comparacao=modelos_service.montar_comparacao(resultados),
        matriz_confusao=modelos_service.grafico_matriz_confusao(modelo["matriz_confusao"], resultados["classes"]),
        importancia=modelos_service.grafico_importancia(importancias) if importancias else None,
    )


@modelos_bp.post("/modelos/treinar")
def treinar():
    """Treina os três modelos com a configuração enviada no formulário."""
    modelo_atual = modelos_service.escolher_modelo(request.form.get("modelo"))
    try:
        parametros, variaveis, tamanho_teste = modelos_service.ler_configuracao(request.form)
        modelos_service.treinar_modelos(carregar_base_atual(), parametros, variaveis, tamanho_teste)
    except ValueError as erro:
        flash(f"Não foi possível treinar: {erro}", "danger")
    else:
        flash("Modelos treinados com a nova configuração.", "success")
    return redirect(url_for("modelos.index", modelo=modelo_atual, _anchor="resultados"))


@modelos_bp.post("/modelos/retreinar")
def retreinar():
    """Treina de novo com a configuração do último treino, usando a base atual."""
    modelo_atual = modelos_service.escolher_modelo(request.form.get("modelo"))
    try:
        modelos_service.retreinar()
    except ValueError as erro:
        flash(f"Não foi possível re-treinar: {erro}", "danger")
    else:
        flash("Modelos re-treinados com a base atual.", "success")
    return redirect(url_for("modelos.index", modelo=modelo_atual, _anchor="resultados"))
