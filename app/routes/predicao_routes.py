from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from app.services import dados_service, modelos_service, predicao_service
from app.services.analise_service import CORES_PARTIDOS
from app.services.dados_service import ROTULOS

predicao_bp = Blueprint("predicao", __name__)


@predicao_bp.get("/predicao")
def index():
    """Página Predição: formulários, lista de municípios previstos e real × previsto."""
    resultados = modelos_service.carregar_resultados()
    modelo_atual = modelos_service.escolher_modelo(request.args.get("modelo"))
    mapa_atual = "estados" if request.args.get("mapa") == "estados" else "municipios"
    salvas = predicao_service.carregar_predicoes_salvas()
    return render_template(
        "predicao.html",
        resultados=resultados,
        rotulos=ROTULOS,
        modelos=modelos_service.MODELOS_DISPONIVEIS,
        modelo_atual=modelo_atual,
        mapa_atual=mapa_atual,
        cores_partidos=CORES_PARTIDOS,
        ufs=sorted(predicao_service.UFS),
        base_mudou=modelos_service.base_mudou(resultados),
        valores_iniciais=predicao_service.calcular_valores_iniciais(resultados["variaveis"]),
        ultima=predicao_service.ultima_predicao(salvas),
        previstos=predicao_service.resumir_previstos(salvas),
        lista=predicao_service.montar_painel_lista(salvas, mapa_atual),
        real_previsto=predicao_service.montar_real_previsto(modelo_atual),
    )


@predicao_bp.post("/predicao/municipio")
def prever_municipio():
    """Prevê um município digitado no formulário e o salva na lista."""
    modelo_atual = modelos_service.escolher_modelo(request.form.get("modelo"))
    try:
        municipio = predicao_service.montar_municipio(request.form)
        previsto = predicao_service.prever(municipio, modelo_atual)
    except ValueError as erro:
        flash(str(erro), "danger")
    else:
        predicao_service.salvar_predicoes(previsto)
        flash("Município previsto e salvo na lista.", "success")
    return redirect(url_for("predicao.index", modelo=modelo_atual))


@predicao_bp.post("/predicao/arquivo")
def prever_arquivo():
    """Prevê os municípios de um arquivo enviado e os salva na lista."""
    modelo_atual = modelos_service.escolher_modelo(request.form.get("modelo"))
    arquivo = request.files.get("arquivo")
    if arquivo is None or arquivo.filename == "":
        flash("Escolha um arquivo para prever.", "danger")
        return redirect(url_for("predicao.index", modelo=modelo_atual))

    try:
        lido = dados_service.ler_arquivo(arquivo)
        municipios = predicao_service.preparar_arquivo(lido)
        previstos = predicao_service.prever(municipios, modelo_atual)
    except ValueError as erro:
        flash(f"Não foi possível prever o arquivo: {erro}", "danger")
    else:
        predicao_service.salvar_predicoes(previstos)
        mensagem = f"{len(previstos)} municípios previstos."
        ignorados = len(lido) - len(previstos)
        if ignorados:
            mensagem += f" {ignorados} linhas ignoradas por falta de dados ou UF inválida."
        flash(mensagem, "success")
    return redirect(url_for("predicao.index", modelo=modelo_atual))


@predicao_bp.post("/predicao/limpar")
def limpar():
    """Apaga a lista de municípios previstos."""
    modelo_atual = modelos_service.escolher_modelo(request.form.get("modelo"))
    predicao_service.limpar_predicoes()
    flash("Lista de municípios previstos apagada.", "success")
    return redirect(url_for("predicao.index", modelo=modelo_atual))


@predicao_bp.get("/predicao/baixar")
def baixar():
    """Baixa a lista de municípios previstos em CSV."""
    if not predicao_service.ARQUIVO_PREDICOES_SALVAS.exists():
        flash("Nenhum município previsto ainda.", "warning")
        return redirect(url_for("predicao.index"))
    return send_file(
        predicao_service.ARQUIVO_PREDICOES_SALVAS, as_attachment=True, download_name="municipios_previstos.csv",
    )
