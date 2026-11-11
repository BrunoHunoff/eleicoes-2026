import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px

from app.services import dados_service
from app.services.analise_service import (
    ALTURA_GRAFICO, ALTURA_MAPA, CENTRO_BRASIL, CORES_PARTIDOS, ORDEM_CATEGORIAS, ROTULOS_GRAFICOS,
    contar_municipios, figura_para_html,
)
from app.services.dados_service import PASTA_DADOS, ROTULOS, carregar_base_atual
from app.services.modelos_service import (
    ARQUIVO_PREDICOES_TESTE, caminho_modelo, carregar_resultados, probabilidade_pt,
)

PASTA_PREDICOES = Path(__file__).resolve().parents[2] / "data" / "predicoes"
ARQUIVO_PREDICOES_SALVAS = PASTA_PREDICOES / "salvas.csv"
# Contorno dos 27 estados (malha do IBGE); cada estado é identificado pelo código IBGE da UF
CONTORNO_ESTADOS = PASTA_DADOS / "geo" / "estados.json"

# Dados do município guardados na lista de previstos, sem nenhuma coluna de resultado
COLUNAS_MUNICIPIO = ["cd_municipio", "nm_municipio", "sg_uf", "regiao", "latitude", "longitude", "qt_eleitores"]
COLUNAS_SALVAS = COLUNAS_MUNICIPIO + ["modelo", "previsto_em", "previsto", "prob_pt"]
COLUNAS_OBRIGATORIAS = ["nm_municipio", "sg_uf"]

# sigla: (código IBGE da UF, região)
UFS = {
    "RO": ("11", "Norte"), "AC": ("12", "Norte"), "AM": ("13", "Norte"), "RR": ("14", "Norte"),
    "PA": ("15", "Norte"), "AP": ("16", "Norte"), "TO": ("17", "Norte"),
    "MA": ("21", "Nordeste"), "PI": ("22", "Nordeste"), "CE": ("23", "Nordeste"), "RN": ("24", "Nordeste"),
    "PB": ("25", "Nordeste"), "PE": ("26", "Nordeste"), "AL": ("27", "Nordeste"), "SE": ("28", "Nordeste"),
    "BA": ("29", "Nordeste"),
    "MG": ("31", "Sudeste"), "ES": ("32", "Sudeste"), "RJ": ("33", "Sudeste"), "SP": ("35", "Sudeste"),
    "PR": ("41", "Sul"), "SC": ("42", "Sul"), "RS": ("43", "Sul"),
    "MS": ("50", "Centro-Oeste"), "MT": ("51", "Centro-Oeste"), "GO": ("52", "Centro-Oeste"),
    "DF": ("53", "Centro-Oeste"),
}
CODIGOS_UF = {sigla: codigo for sigla, (codigo, _) in UFS.items()}
REGIOES_UF = {sigla: regiao for sigla, (_, regiao) in UFS.items()}

CORES_RESULTADO = {"Acertou": "#198754", "Errou": "#fd7e14"}
# Escala do mapa: azul do PL (probabilidade do PT = 0), cinza (empate) e vermelho do PT (probabilidade do PT = 1)
ESCALA_PROBABILIDADE = [CORES_PARTIDOS["PL"], "#b0b0b0", CORES_PARTIDOS["PT"]]
BARRA_DE_CORES = {
    "title": "Previsto",
    "tickvals": [0, 0.25, 0.5, 0.75, 1],
    "ticktext": ["PL 100%", "PL 75%", "50%", "PT 75%", "PT 100%"],
}

ORDEM_PREDICAO = {
    **ORDEM_CATEGORIAS,
    "previsto": ["PT", "PL"],
    "partido": ["PT", "PL"],
    "resultado": ["Acertou", "Errou"],
    "tipo": ["Real", "Previsto"],
}
ROTULOS_PREDICAO = {
    **ROTULOS_GRAFICOS,
    "previsto": "Previsto",
    "partido": "Partido",
    "tipo": "Tipo",
    "resultado": "Resultado",
    "prob_previsto": "Probabilidade do partido previsto",
    "pct_votos_previsto": "Votos reais no partido previsto (%)",
    "favorito": "Favorito",
    "prob_favorito": "Probabilidade média do favorito",
}


def carregar_modelo(chave):
    """Carrega o pipeline treinado do modelo escolhido; se ainda não houve treino, treina antes."""
    if not caminho_modelo(chave).exists():
        carregar_resultados()
    return joblib.load(caminho_modelo(chave))


def prever(df, chave):
    """Devolve o DataFrame com o partido previsto, a probabilidade do PT, o modelo usado e a data da predição."""
    modelo = carregar_modelo(chave)
    variaveis = carregar_resultados()["variaveis"]
    df = df.copy()
    df["previsto"] = modelo.predict(df[variaveis])
    df["prob_pt"] = probabilidade_pt(modelo, df[variaveis]).round(3)
    df["modelo"] = chave
    df["previsto_em"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return df


def completar_colunas(df):
    """Cria as colunas opcionais que faltarem: a região vem da UF e as outras ficam vazias."""
    df = df.copy()
    if "regiao" not in df.columns:
        df["regiao"] = df["sg_uf"].map(REGIOES_UF)
    for coluna in COLUNAS_MUNICIPIO:
        if coluna not in df.columns:
            df[coluna] = np.nan
    return df


def montar_municipio(formulario):
    """Monta a linha de um município digitado no formulário, com os indicadores convertidos para número."""
    nome = formulario.get("nm_municipio", "").strip()
    uf = formulario.get("sg_uf")
    if not nome:
        raise ValueError("Informe o nome do município.")
    if uf not in UFS:
        raise ValueError("Escolha uma UF válida.")

    municipio = {"nm_municipio": nome, "sg_uf": uf}
    for coluna in carregar_resultados()["variaveis"]:
        try:
            municipio[coluna] = float(formulario.get(coluna, ""))
        except ValueError:
            raise ValueError(f"{ROTULOS[coluna]} precisa ser um número.") from None
    return completar_colunas(pd.DataFrame([municipio]))


def preparar_arquivo(df):
    """Confere as colunas do arquivo e mantém só os municípios com nome, UF válida e todos os indicadores."""
    variaveis = carregar_resultados()["variaveis"]
    faltando = dados_service.validar_colunas(df, variaveis + COLUNAS_OBRIGATORIAS)
    if faltando:
        raise ValueError("faltam as colunas " + ", ".join(faltando) + ".")

    df = df.copy()
    df["sg_uf"] = df["sg_uf"].str.strip().str.upper()
    df = df.dropna(subset=variaveis + COLUNAS_OBRIGATORIAS)
    df = df[df["sg_uf"].isin(UFS)]
    if df.empty:
        raise ValueError("nenhum município do arquivo tem nome, UF válida e todos os indicadores.")
    return completar_colunas(df)


def carregar_predicoes_salvas():
    """Lê a lista de municípios previstos; se ela ainda não existe, devolve uma lista vazia."""
    if not ARQUIVO_PREDICOES_SALVAS.exists():
        return pd.DataFrame(columns=COLUNAS_SALVAS)
    return pd.read_csv(ARQUIVO_PREDICOES_SALVAS)


def salvar_predicoes(novas):
    """Junta as predições novas à lista salva; o mesmo município (nome + UF) previsto de novo é atualizado."""
    salvas = pd.concat([carregar_predicoes_salvas(), novas[COLUNAS_SALVAS]])
    salvas = salvas.drop_duplicates(["nm_municipio", "sg_uf"], keep="last")
    PASTA_PREDICOES.mkdir(parents=True, exist_ok=True)
    salvas.to_csv(ARQUIVO_PREDICOES_SALVAS, index=False)


def limpar_predicoes():
    """Apaga a lista de municípios previstos."""
    ARQUIVO_PREDICOES_SALVAS.unlink(missing_ok=True)


def adicionar_prob_previsto(df):
    """Cria a coluna com a probabilidade do partido previsto (a do PT ou a do PL)."""
    df = df.copy()
    df["prob_previsto"] = np.where(df["previsto"] == "PT", df["prob_pt"], 1 - df["prob_pt"])
    return df


def ultima_predicao(salvas):
    """A predição mais recente (última linha da lista salva), ou None se a lista está vazia."""
    if salvas.empty:
        return None
    return adicionar_prob_previsto(salvas).iloc[-1].to_dict()


def calcular_valores_iniciais(variaveis):
    """Mediana de cada variável na base atual, usada como valor inicial do formulário de um município."""
    return carregar_base_atual()[variaveis].median().round(2).to_dict()


def formatar_lista(salvas):
    """Lista para a tabela: data no padrão brasileiro e municípios ordenados por UF e nome."""
    df = salvas.copy()
    df["previsto_em"] = pd.to_datetime(df["previsto_em"]).dt.strftime("%d/%m/%Y %H:%M")
    return df.sort_values(["sg_uf", "nm_municipio"])


def montar_painel_lista(salvas, mapa):
    """Tabelas, gráficos e mapa da lista de municípios previstos; None quando a lista está vazia."""
    if salvas.empty:
        return None
    salvas = adicionar_prob_previsto(salvas)
    por_uf = resumir_por_grupo(salvas, "sg_uf")
    return {
        "por_regiao": resumir_por_grupo(salvas, "regiao").to_dict("records"),
        "por_uf": por_uf.to_dict("records"),
        "municipios": formatar_lista(salvas).to_dict("records"),
        "grafico_previstos_regiao": grafico_previstos_por_regiao(salvas),
        "grafico_probabilidade_uf": grafico_probabilidade_por_uf(por_uf),
        "mapa": mapa_por_estado(salvas) if mapa == "estados" else mapa_por_municipio(salvas),
    }


def carregar_predicoes_teste(modelo):
    """Predições do modelo nos municípios de teste do último treino, junto com o resultado real de cada um."""
    predicoes = pd.read_csv(ARQUIVO_PREDICOES_TESTE)
    predicoes = predicoes[predicoes["modelo"] == modelo]
    df = adicionar_prob_previsto(predicoes.merge(carregar_base_atual(), on="cd_municipio"))
    df["pct_votos_previsto"] = np.where(df["previsto"] == "PT", df["pct_votos_pt"], df["pct_votos_pl"])
    df["resultado"] = np.where(df["previsto"] == df["vencedor"], "Acertou", "Errou")
    return df


def montar_real_previsto(modelo):
    """Cards, tabela, gráficos e mapa do real × previsto; None se o teste não está na base atual."""
    teste = carregar_predicoes_teste(modelo)
    if teste.empty:
        return None
    return {
        "acertos": resumir_acertos(teste),
        "acertos_por_regiao": acertos_por_regiao(teste).to_dict("records"),
        "grafico_real_previsto": grafico_real_previsto(teste),
        "grafico_probabilidade_votos": grafico_probabilidade_votos(teste),
        "mapa_acertos": mapa_acertos(teste),
    }


def resumir_previstos(df):
    """Números dos cards: municípios previstos e quantos foram previstos para cada partido."""
    return {
        "municipios": len(df),
        "previstos_pt": int((df["previsto"] == "PT").sum()),
        "previstos_pl": int((df["previsto"] == "PL").sum()),
    }


def resumir_por_grupo(df, coluna):
    """Agrupa as predições por região ou UF: municípios, probabilidade média e eleitorado de cada partido."""
    df = df.copy()
    df["previsto_pt"] = df["previsto"] == "PT"
    df["eleitores_previsto_pt"] = np.where(df["previsto_pt"], df["qt_eleitores"], 0)

    # Conta pelo nome: municípios digitados não têm código IBGE
    grupos = df.groupby(coluna).agg(
        municipios=("nm_municipio", "count"),
        previstos_pt=("previsto_pt", "sum"),
        prob_media_pt=("prob_pt", "mean"),
        eleitores=("qt_eleitores", "sum"),
        eleitores_previsto_pt=("eleitores_previsto_pt", "sum"),
    ).reset_index()

    grupos["previstos_pl"] = grupos["municipios"] - grupos["previstos_pt"]
    grupos["prob_media_pl"] = 1 - grupos["prob_media_pt"]
    grupos["pct_eleitorado_pt"] = grupos["eleitores_previsto_pt"] / grupos["eleitores"]
    grupos["pct_eleitorado_pl"] = 1 - grupos["pct_eleitorado_pt"]
    return grupos.sort_values("prob_media_pt", ascending=False)


def resumir_acertos(df):
    """Números dos cards da comparação: municípios de teste, acertos e acurácia."""
    acertos = int((df["resultado"] == "Acertou").sum())
    return {"municipios": len(df), "acertos": acertos, "acuracia": acertos / len(df)}


def acertos_por_regiao(df):
    """Municípios de teste, acertos e acurácia em cada região, da maior para a menor acurácia."""
    df = df.copy()
    df["acertou"] = df["resultado"] == "Acertou"
    grupos = df.groupby("regiao").agg(
        municipios=("cd_municipio", "count"),
        acertos=("acertou", "sum"),
        acuracia=("acertou", "mean"),
    ).reset_index()
    return grupos.sort_values("acuracia", ascending=False)


def grafico_previstos_por_regiao(df):
    """Barras agrupadas com o número de municípios previstos para cada partido em cada região."""
    fig = px.bar(
        contar_municipios(df, ["regiao", "previsto"]), x="regiao", y="municipios", color="previsto",
        barmode="group", text_auto=True, color_discrete_map=CORES_PARTIDOS,
        category_orders=ORDEM_PREDICAO, labels=ROTULOS_PREDICAO, height=ALTURA_GRAFICO,
    )
    return figura_para_html(fig)


def grafico_probabilidade_por_uf(por_uf):
    """Barras empilhadas com a probabilidade média de cada partido em cada UF; a linha tracejada marca 50%."""
    probabilidades = por_uf.rename(columns={"prob_media_pt": "PT", "prob_media_pl": "PL"})
    fig = px.bar(
        probabilidades, x="sg_uf", y=["PT", "PL"], color_discrete_map=CORES_PARTIDOS,
        labels=ROTULOS_PREDICAO, height=ALTURA_GRAFICO,
    )
    fig.add_hline(y=0.5, line_dash="dash")
    fig.update_yaxes(title="Probabilidade média", tickformat=".0%", hoverformat=".1%", range=[0, 1])
    fig.update_layout(legend_title_text="Partido")
    return figura_para_html(fig)


def mapa_por_municipio(df):
    """Mapa com um ponto por município, colorido pelo partido previsto e pela probabilidade."""
    # Municípios digitados sem latitude e longitude ficam fora do mapa
    df = df.dropna(subset=["latitude", "longitude"])
    fig = px.scatter_map(
        df, lat="latitude", lon="longitude", color="prob_pt", range_color=[0, 1],
        color_continuous_scale=ESCALA_PROBABILIDADE, hover_name="nm_municipio",
        hover_data={
            "sg_uf": True, "previsto": True, "prob_previsto": ":.0%",
            "prob_pt": False, "latitude": False, "longitude": False,
        },
        labels=ROTULOS_PREDICAO, map_style="carto-positron", zoom=3, center=CENTRO_BRASIL, height=ALTURA_MAPA,
    )
    fig.update_traces(marker={"size": 10})
    fig.update_coloraxes(colorbar=BARRA_DE_CORES)
    return figura_para_html(fig)


def mapa_por_estado(df):
    """Mapa com cada estado pintado pela probabilidade média dos seus municípios previstos."""
    df = df.copy()
    # O código do estado vem da sigla da UF, porque municípios digitados não têm código IBGE
    df["cd_uf"] = df["sg_uf"].map(CODIGOS_UF)

    estados = df.groupby(["cd_uf", "sg_uf"]).agg(
        municipios=("nm_municipio", "count"),
        prob_media_pt=("prob_pt", "mean"),
    ).reset_index()
    estados["favorito"] = np.where(estados["prob_media_pt"] >= 0.5, "PT", "PL")
    estados["prob_favorito"] = np.where(
        estados["favorito"] == "PT", estados["prob_media_pt"], 1 - estados["prob_media_pt"],
    )

    with CONTORNO_ESTADOS.open(encoding="utf-8") as arquivo:
        contorno = json.load(arquivo)

    fig = px.choropleth_map(
        estados, geojson=contorno, featureidkey="properties.codarea", locations="cd_uf",
        color="prob_media_pt", range_color=[0, 1], color_continuous_scale=ESCALA_PROBABILIDADE, opacity=0.8,
        hover_name="sg_uf",
        hover_data={
            "municipios": True, "favorito": True, "prob_favorito": ":.0%", "cd_uf": False, "prob_media_pt": False,
        },
        labels=ROTULOS_PREDICAO, map_style="carto-positron", zoom=3, center=CENTRO_BRASIL, height=ALTURA_MAPA,
    )
    fig.update_coloraxes(colorbar=BARRA_DE_CORES)
    return figura_para_html(fig)


def grafico_real_previsto(df):
    """Barras com os municípios vencidos por partido em cada região: lisas = real, listradas = previsto."""
    real = contar_municipios(df, ["regiao", "vencedor"]).rename(columns={"vencedor": "partido"})
    real["tipo"] = "Real"
    previsto = contar_municipios(df, ["regiao", "previsto"]).rename(columns={"previsto": "partido"})
    previsto["tipo"] = "Previsto"

    fig = px.bar(
        pd.concat([real, previsto]), x="regiao", y="municipios", color="partido", pattern_shape="tipo",
        barmode="group", color_discrete_map=CORES_PARTIDOS, pattern_shape_map={"Real": "", "Previsto": "/"},
        category_orders=ORDEM_PREDICAO, labels=ROTULOS_PREDICAO, height=ALTURA_GRAFICO,
    )
    return figura_para_html(fig)


def grafico_probabilidade_votos(df):
    """Dispersão da probabilidade do partido previsto com os votos reais que ele teve; abaixo de 50% é erro."""
    fig = px.scatter(
        df, x="pct_votos_previsto", y="prob_previsto", color="resultado", color_discrete_map=CORES_RESULTADO,
        hover_name="nm_municipio", hover_data={"sg_uf": True, "previsto": True},
        category_orders=ORDEM_PREDICAO, labels=ROTULOS_PREDICAO, height=ALTURA_GRAFICO,
    )
    fig.add_vline(x=50, line_dash="dash")
    fig.update_yaxes(tickformat=".0%", hoverformat=".1%")
    return figura_para_html(fig)


def mapa_acertos(df):
    """Mapa com um ponto por município: verde quando o modelo acertou o vencedor e laranja quando errou."""
    fig = px.scatter_map(
        df, lat="latitude", lon="longitude", color="resultado", color_discrete_map=CORES_RESULTADO,
        hover_name="nm_municipio",
        hover_data={
            "sg_uf": True, "vencedor": True, "previsto": True, "prob_previsto": ":.0%",
            "latitude": False, "longitude": False,
        },
        category_orders=ORDEM_PREDICAO, labels=ROTULOS_PREDICAO,
        map_style="carto-positron", zoom=3, center=CENTRO_BRASIL, height=ALTURA_MAPA,
    )
    fig.update_traces(marker={"size": 10})
    return figura_para_html(fig)
