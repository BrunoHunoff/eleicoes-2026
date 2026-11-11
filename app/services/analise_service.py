import json

import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

from app.services.dados_service import COLUNAS_NUMERICAS, PASTA_DADOS, REGIOES, ROTULOS
from app.utils import figura_para_base64

# Cores fixas: cada partido tem a mesma cor em todos os gráficos
CORES_PARTIDOS = {"PT": "#c4122d", "PL": "#1d4e9e"}

# Paleta das regiões sem vermelho e azul fortes, para não confundir região com partido
CORES_REGIOES = dict(zip(REGIOES, px.colors.qualitative.Dark2))

# Mesma ordem de partidos e regiões em todas as legendas e eixos
ORDEM_CATEGORIAS = {"vencedor": list(CORES_PARTIDOS), "regiao": REGIOES}

# Rótulos legíveis nos eixos, legendas e hovers (inclui a contagem de municípios dos gráficos agregados)
ROTULOS_GRAFICOS = {**ROTULOS, "municipios": "Municípios"}

# Contorno dos 27 estados (malha do IBGE) e escala do mapa por estado: azul do PL, cinza (empate) e vermelho do PT
CONTORNO_ESTADOS = PASTA_DADOS / "geo" / "estados.json"
ESCALA_VOTOS = [CORES_PARTIDOS["PL"], "#b0b0b0", CORES_PARTIDOS["PT"]]
BARRA_DE_CORES_VOTOS = {
    "title": "Votos",
    "tickvals": [0, 25, 50, 75, 100],
    "ticktext": ["PL 100%", "PL 75%", "50%", "PT 75%", "PT 100%"],
}

ALTURA_GRAFICO = 400
ALTURA_MAPA = 550
CENTRO_BRASIL = {"lat": -14.2, "lon": -51.9}


def figura_para_html(fig):
    """Aplica o visual comum aos gráficos do Plotly e devolve o HTML do gráfico, sem o plotly.js."""
    fig.update_layout(
        template="plotly_white",
        # Vírgula como separador decimal e ponto como separador de milhar (padrão brasileiro)
        separators=",.",
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        # Legenda acima do gráfico: na lateral ela ocupa boa parte da largura na tela do celular
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def filtrar(df, regiao, uf):
    """Mantém só os municípios da região e da UF escolhidas (texto vazio = todas)."""
    if regiao:
        df = df[df["regiao"] == regiao]
    if uf:
        df = df[df["sg_uf"] == uf]
    return df


def calcular_indicadores(df):
    """Números dos cards: municípios, eleitores, abstenção média e municípios vencidos por partido."""
    vitorias = df["vencedor"].value_counts()
    return {
        "municipios": len(df),
        "eleitores": int(df["qt_eleitores"].sum()),
        "abstencao_media": float(df["pct_abstencao"].mean()),
        "vitorias_pt": int(vitorias.get("PT", 0)),
        "vitorias_pl": int(vitorias.get("PL", 0)),
    }


def contar_municipios(df, colunas):
    """Conta os municípios de cada combinação das colunas informadas (ex.: vencedor por região)."""
    return df.groupby(colunas).size().reset_index(name="municipios")


def grafico_barras_vencedores(df):
    """Barras agrupadas com o número de municípios vencidos por cada partido em cada região."""
    fig = px.bar(
        contar_municipios(df, ["regiao", "vencedor"]), x="regiao", y="municipios", color="vencedor",
        barmode="group", text_auto=True, color_discrete_map=CORES_PARTIDOS,
        category_orders=ORDEM_CATEGORIAS, labels=ROTULOS_GRAFICOS, height=ALTURA_GRAFICO,
    )
    return figura_para_html(fig)


def grafico_pizza_vencedores(df):
    """Pizza com a proporção de municípios vencidos por cada partido."""
    fig = px.pie(
        contar_municipios(df, ["vencedor"]), names="vencedor", values="municipios", color="vencedor",
        color_discrete_map=CORES_PARTIDOS, category_orders=ORDEM_CATEGORIAS, labels=ROTULOS_GRAFICOS,
        height=ALTURA_GRAFICO,
    )
    fig.update_traces(textinfo="label+percent")
    return figura_para_html(fig)


def grafico_histograma(df, coluna):
    """Histograma da coluna escolhida, sobrepondo os municípios vencidos por cada partido."""
    fig = px.histogram(
        df, x=coluna, color="vencedor", barmode="overlay", opacity=0.65, nbins=30,
        color_discrete_map=CORES_PARTIDOS, category_orders=ORDEM_CATEGORIAS, labels=ROTULOS_GRAFICOS,
        height=ALTURA_GRAFICO,
    )
    fig.update_layout(yaxis_title="Municípios")
    # O labels não renomeia o "count" do hover do histograma, por isso o texto do hover é montado aqui
    fig.update_traces(hovertemplate=ROTULOS_GRAFICOS[coluna] + "=%{x}<br>Municípios=%{y}")
    return figura_para_html(fig)


def grafico_dispersao(df, coluna, partido):
    """Dispersão da coluna escolhida (eixo x) com o % de votos do partido escolhido (eixo y), um ponto por município."""
    fig = px.scatter(
        df, x=coluna, y="pct_votos_" + partido.lower(), color="regiao", opacity=0.7,
        hover_name="nm_municipio", hover_data={"sg_uf": True},
        color_discrete_map=CORES_REGIOES, category_orders=ORDEM_CATEGORIAS, labels=ROTULOS_GRAFICOS,
        height=ALTURA_GRAFICO,
    )
    return figura_para_html(fig)


def mapa_municipios(df):
    """Mapa com um ponto por município: cor pelo partido vencedor e tamanho pelo número de eleitores."""
    fig = px.scatter_map(
        df, lat="latitude", lon="longitude", color="vencedor", size="qt_eleitores",
        hover_name="nm_municipio",
        hover_data={
            "sg_uf": True, "pct_votos_pt": ":.1f", "pct_votos_pl": ":.1f", "qt_eleitores": ":,",
            "latitude": False, "longitude": False,
        },
        color_discrete_map=CORES_PARTIDOS, category_orders=ORDEM_CATEGORIAS, labels=ROTULOS_GRAFICOS,
        map_style="carto-positron", zoom=3, center=CENTRO_BRASIL, height=ALTURA_MAPA,
    )
    return figura_para_html(fig)


def mapa_estados(df):
    """Mapa com cada estado pintado pelo % de votos no PT, ponderado pelo eleitorado dos municípios."""
    df = df.copy()
    # Os 2 primeiros dígitos do código do município são o código do estado
    df["cd_uf"] = df["cd_municipio"].astype(str).str[:2]
    # Ponderar pelo eleitorado: uma cidade grande pesa mais que uma pequena
    df["votos_pt"] = df["pct_votos_pt"] * df["qt_eleitores"]
    df["votos_pl"] = df["pct_votos_pl"] * df["qt_eleitores"]

    estados = df.groupby(["cd_uf", "sg_uf"]).agg(
        municipios=("cd_municipio", "count"),
        eleitores=("qt_eleitores", "sum"),
        votos_pt=("votos_pt", "sum"),
        votos_pl=("votos_pl", "sum"),
    ).reset_index()
    estados["pct_votos_pt"] = estados["votos_pt"] / estados["eleitores"]
    estados["pct_votos_pl"] = estados["votos_pl"] / estados["eleitores"]

    with CONTORNO_ESTADOS.open(encoding="utf-8") as arquivo:
        contorno = json.load(arquivo)

    fig = px.choropleth_map(
        estados, geojson=contorno, featureidkey="properties.codarea", locations="cd_uf",
        color="pct_votos_pt", range_color=[0, 100], color_continuous_scale=ESCALA_VOTOS, opacity=0.8,
        hover_name="sg_uf",
        hover_data={"municipios": True, "pct_votos_pt": ":.1f", "pct_votos_pl": ":.1f", "cd_uf": False},
        labels=ROTULOS_GRAFICOS, map_style="carto-positron", zoom=3, center=CENTRO_BRASIL, height=ALTURA_MAPA,
    )
    fig.update_coloraxes(colorbar=BARRA_DE_CORES_VOTOS)
    return figura_para_html(fig)


def mapa_calor_correlacao(df):
    """Mapa de calor (seaborn) da correlação entre os indicadores numéricos, em base64."""
    correlacao = df[COLUNAS_NUMERICAS].corr()
    rotulos = [ROTULOS[coluna] for coluna in COLUNAS_NUMERICAS]

    fig, ax = plt.subplots(figsize=(11, 8))
    # vmin/vmax fixos: o branco fica sempre no zero e as cores são comparáveis entre bases diferentes
    sns.heatmap(
        correlacao, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1,
        xticklabels=rotulos, yticklabels=rotulos, ax=ax,
    )
    ax.set_xticklabels(rotulos, rotation=45, ha="right")
    return figura_para_base64(fig)
