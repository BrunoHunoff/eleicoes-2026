import json

import numpy as np
import pandas as pd
import plotly.express as px

from app.services.analise_service import (
    ALTURA_GRAFICO, ALTURA_MAPA, CENTRO_BRASIL, CORES_PARTIDOS, ORDEM_CATEGORIAS, ROTULOS_GRAFICOS,
    contar_municipios, figura_para_html,
)
from app.services.dados_service import PASTA_MOCK, carregar_base_atual

PREDICOES_SALVAS_MOCK = PASTA_MOCK / "predicoes_salvas.csv"
PREDICOES_TESTE_MOCK = PASTA_MOCK / "predicoes_teste.csv"
# Contorno dos 27 estados (malha do IBGE); cada estado é identificado pelo código IBGE da UF
CONTORNO_ESTADOS = PASTA_MOCK.parent / "geo" / "estados.json"

# A lista de municípios previstos só usa os dados do município, sem nenhuma coluna de resultado
COLUNAS_MUNICIPIO = ["cd_municipio", "nm_municipio", "sg_uf", "regiao", "latitude", "longitude", "qt_eleitores"]

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


def carregar_predicoes_salvas_mock():
    """Lista fictícia de municípios já previstos, junto com os dados de cada município."""
    salvas = pd.read_csv(PREDICOES_SALVAS_MOCK)
    salvas["previsto_em"] = pd.to_datetime(salvas["previsto_em"]).dt.strftime("%d/%m/%Y %H:%M")
    salvas["prob_previsto"] = np.where(salvas["previsto"] == "PT", salvas["prob_pt"], 1 - salvas["prob_pt"])
    df = salvas.merge(carregar_base_atual()[COLUNAS_MUNICIPIO], on="cd_municipio")
    return df.sort_values(["sg_uf", "nm_municipio"])


def carregar_predicoes_teste_mock(modelo):
    """Predições fictícias do modelo para os municípios de teste, junto com o resultado real de cada um."""
    predicoes = pd.read_csv(PREDICOES_TESTE_MOCK)
    predicoes = predicoes[predicoes["modelo"] == modelo]
    df = predicoes.merge(carregar_base_atual(), on="cd_municipio")

    previsto_pt = df["previsto"] == "PT"
    df["prob_previsto"] = np.where(previsto_pt, df["prob_pt"], 1 - df["prob_pt"])
    df["pct_votos_previsto"] = np.where(previsto_pt, df["pct_votos_pt"], df["pct_votos_pl"])
    df["resultado"] = np.where(df["previsto"] == df["vencedor"], "Acertou", "Errou")
    return df


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

    grupos = df.groupby(coluna).agg(
        municipios=("cd_municipio", "count"),
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
    # Os dois primeiros dígitos do código IBGE do município são o código IBGE do estado
    df["cd_uf"] = (df["cd_municipio"] // 100_000).astype(str)

    estados = df.groupby(["cd_uf", "sg_uf"]).agg(
        municipios=("cd_municipio", "count"),
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
        hover_data={"municipios": True, "favorito": True, "prob_favorito": ":.0%", "cd_uf": False, "prob_media_pt": False},
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
