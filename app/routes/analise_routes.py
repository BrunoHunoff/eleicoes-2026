from flask import Blueprint, render_template, request

from app.services import analise_service, dados_service

analise_bp = Blueprint("analise", __name__)

# Variável e partido do histograma e da dispersão quando o filtro não informa um valor válido
VARIAVEL_PADRAO = "pib_per_capita"
PARTIDO_PADRAO = "PT"


@analise_bp.get("/analise")
def index():
    """Página Análise: aplica os filtros da URL e monta indicadores, gráficos e mapas."""
    df = dados_service.carregar_base_atual()
    ufs_da_base = sorted(df["sg_uf"].unique())

    # Valores inválidos na URL são ignorados
    regiao = request.args.get("regiao", "")
    if regiao not in dados_service.REGIOES:
        regiao = ""
    uf = request.args.get("uf", "")
    if uf not in ufs_da_base:
        uf = ""
    variavel = request.args.get("variavel", "")
    if variavel not in dados_service.COLUNAS_NUMERICAS:
        variavel = VARIAVEL_PADRAO
    partido = request.args.get("partido", "")
    if partido not in dados_service.PARTIDOS:
        partido = PARTIDO_PADRAO
    mapa_atual = "estados" if request.args.get("mapa") == "estados" else "municipios"

    filtrado = analise_service.filtrar(df, regiao, uf)
    # Com uma região escolhida, a lista de UFs mostra só as UFs dela
    ufs = sorted(analise_service.filtrar(df, regiao, "")["sg_uf"].unique())

    # Com 0 municípios os gráficos quebram: nesse caso o template mostra só o aviso
    graficos = {}
    if not filtrado.empty:
        if mapa_atual == "estados":
            mapa = analise_service.mapa_estados(filtrado)
        else:
            mapa = analise_service.mapa_municipios(filtrado)
        graficos = {
            "indicadores": analise_service.calcular_indicadores(filtrado),
            "barras": analise_service.grafico_barras_vencedores(filtrado),
            "pizza": analise_service.grafico_pizza_vencedores(filtrado),
            "histograma": analise_service.grafico_histograma(filtrado, variavel),
            "dispersao": analise_service.grafico_dispersao(filtrado, variavel, partido),
            "mapa": mapa,
            "correlacao": analise_service.mapa_calor_correlacao(filtrado),
        }

    return render_template(
        "analise.html",
        nome_base=dados_service.nome_base_atual(),
        base_enviada=dados_service.BASE_ENVIADA.exists(),
        total_municipios=len(df),
        municipios_filtro=len(filtrado),
        cores_partidos=analise_service.CORES_PARTIDOS,
        regioes=dados_service.REGIOES,
        ufs=ufs,
        variaveis=dados_service.COLUNAS_NUMERICAS,
        partidos=dados_service.PARTIDOS,
        rotulos=dados_service.ROTULOS,
        regiao_atual=regiao,
        uf_atual=uf,
        variavel_atual=variavel,
        partido_atual=partido,
        mapa_atual=mapa_atual,
        **graficos,
    )
