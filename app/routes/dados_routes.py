from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from app.services import dados_service

dados_bp = Blueprint("dados", __name__)

LINHAS_AMOSTRA = 10


@dados_bp.get("/dados")
def index():
    """Página Dados: resumo, dicionário, amostra e estatísticas da base atual."""
    df = dados_service.carregar_base_atual()
    amostra = df.head(LINHAS_AMOSTRA)
    return render_template(
        "dados.html",
        nome_base=dados_service.nome_base_atual(),
        base_enviada=dados_service.BASE_ENVIADA.exists(),
        resumo=dados_service.resumir_base(df),
        dicionario=dados_service.listar_dicionario(),
        estatisticas=dados_service.calcular_estatisticas(df),
        colunas_amostra=amostra.columns.tolist(),
        linhas_amostra=amostra.values.tolist(),
    )


@dados_bp.post("/dados/enviar")
def enviar():
    """Lê, valida, limpa e salva a base enviada no formulário."""
    arquivo = request.files.get("arquivo")
    if arquivo is None or arquivo.filename == "":
        flash("Escolha um arquivo para enviar.", "danger")
        return redirect(url_for("dados.index"))

    try:
        df = dados_service.ler_arquivo(arquivo)
    except ValueError as erro:
        flash(str(erro), "danger")
        return redirect(url_for("dados.index"))

    faltando = dados_service.validar_colunas(df, list(dados_service.DICIONARIO_COLUNAS))
    if faltando:
        flash("Colunas faltando no arquivo: " + ", ".join(faltando), "danger")
        return redirect(url_for("dados.index"))

    df, removidas = dados_service.limpar_base(df)
    if df.empty:
        flash("A base ficou vazia depois da limpeza: confira os valores do arquivo.", "danger")
        return redirect(url_for("dados.index"))

    dados_service.salvar_base(df, arquivo.filename)
    flash(
        f"Base {arquivo.filename} enviada: {len(df)} municípios ({removidas} linhas removidas na limpeza). "
        "Clique em Re-treinar na página Modelos.",
        "success",
    )
    return redirect(url_for("dados.index"))


@dados_bp.post("/dados/voltar-exemplo")
def voltar_exemplo():
    """Apaga a base enviada e volta para a base padrão."""
    dados_service.voltar_base_exemplo()
    flash("Voltou para a base padrão. Clique em Re-treinar na página Modelos.", "success")
    return redirect(url_for("dados.index"))


@dados_bp.app_errorhandler(RequestEntityTooLarge)
def arquivo_grande_demais(erro):
    """Arquivo acima do limite de 16 MB: avisa na página Dados em vez de mostrar tela de erro."""
    flash("Arquivo grande demais: o limite é 16 MB.", "danger")
    return redirect(url_for("dados.index"))
