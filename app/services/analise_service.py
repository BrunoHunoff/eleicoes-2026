import plotly.express as px

from app.services.dados_service import REGIOES, ROTULOS

# Cores fixas: cada partido tem a mesma cor em todos os gráficos
CORES_PARTIDOS = {"PT": "#c4122d", "PL": "#1d4e9e"}

# Mesma ordem de partidos e regiões em todas as legendas e eixos
ORDEM_CATEGORIAS = {"vencedor": list(CORES_PARTIDOS), "regiao": REGIOES}

# Rótulos legíveis nos eixos, legendas e hovers (inclui a contagem de municípios dos gráficos agregados)
ROTULOS_GRAFICOS = {**ROTULOS, "municipios": "Municípios"}

ALTURA_GRAFICO = 400


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
    fig.update_traces(
        hovertemplate=f"{ROTULOS_GRAFICOS[coluna]}=%{{x}}<br>Municípios=%{{y}}<extra>%{{fullData.name}}</extra>",
    )
    return figura_para_html(fig)
