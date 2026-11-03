from pathlib import Path

import pandas as pd

PASTA_MOCK = Path(__file__).resolve().parents[2] / "data" / "mock"
BASE_EXEMPLO = PASTA_MOCK / "municipios_2026.csv"

REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

# coluna: (rótulo, descrição, fonte)
DICIONARIO_COLUNAS = {
    "ano": ("Ano", "Ano da eleição", "TSE"),
    "sg_uf": ("UF", "Sigla da unidade da federação", "TSE"),
    "regiao": ("Região", "Região do país", "IBGE"),
    "cd_municipio": ("Código do município", "Código IBGE do município", "IBGE"),
    "nm_municipio": ("Município", "Nome do município", "IBGE"),
    "latitude": ("Latitude", "Latitude da sede do município", "IBGE"),
    "longitude": ("Longitude", "Longitude da sede do município", "IBGE"),
    "qt_eleitores": ("Eleitores", "Eleitores aptos a votar", "TSE"),
    "populacao": ("População", "População residente (Censo 2022)", "IBGE"),
    "pib_per_capita": ("PIB per capita (R$)", "Produto interno bruto por habitante", "IBGE"),
    "pct_feminino": ("Eleitorado feminino (%)", "Percentual de mulheres no eleitorado", "TSE"),
    "pct_16_29": ("Eleitores de 16 a 29 anos (%)", "Percentual do eleitorado entre 16 e 29 anos", "TSE"),
    "pct_60_mais": ("Eleitores com 60 anos ou mais (%)", "Percentual do eleitorado com 60 anos ou mais", "TSE"),
    "pct_ensino_superior": ("Ensino superior completo (%)", "Percentual do eleitorado com ensino superior completo", "TSE"),
    "pct_ate_fundamental": ("Até o ensino fundamental (%)", "Percentual do eleitorado com no máximo o ensino fundamental", "TSE"),
    "pct_abstencao": ("Abstenção (%)", "Percentual de eleitores que não votaram no 2º turno", "TSE"),
    "pct_brancos_nulos": ("Brancos e nulos (%)", "Percentual de votos brancos e nulos no 2º turno", "TSE"),
    "pct_votos_pt": ("Votos no PT (%)", "Percentual dos votos válidos para o PT no 2º turno", "TSE"),
    "pct_votos_pl": ("Votos no PL (%)", "Percentual dos votos válidos para o PL no 2º turno", "TSE"),
    "vencedor": ("Vencedor", "Partido mais votado no município no 2º turno", "TSE"),
}

ROTULOS = {coluna: rotulo for coluna, (rotulo, _, _) in DICIONARIO_COLUNAS.items()}

# Indicadores numéricos usados em gráficos e modelos (sem códigos, coordenadas e ano)
COLUNAS_NUMERICAS = [
    "qt_eleitores", "populacao", "pib_per_capita", "pct_feminino", "pct_16_29", "pct_60_mais",
    "pct_ensino_superior", "pct_ate_fundamental", "pct_abstencao", "pct_brancos_nulos",
    "pct_votos_pt", "pct_votos_pl",
]


def carregar_base_atual():
    """Devolve a base em uso. Nesta etapa é sempre a base de exemplo (dados fictícios) de 2026."""
    return pd.read_csv(BASE_EXEMPLO)


def resumir_base(df):
    """Calcula os números exibidos nos cards de resumo da base."""
    return {
        "municipios": len(df),
        "colunas": df.shape[1],
        "ufs": df["sg_uf"].nunique(),
        "eleitores": int(df["qt_eleitores"].sum()),
        "anos": sorted(df["ano"].unique().tolist()),
    }


def listar_dicionario():
    """Lista as colunas esperadas com rótulo, descrição e fonte, para a tabela do dicionário de dados."""
    return [
        {"coluna": coluna, "rotulo": rotulo, "descricao": descricao, "fonte": fonte}
        for coluna, (rotulo, descricao, fonte) in DICIONARIO_COLUNAS.items()
    ]


def calcular_estatisticas(df):
    """Estatísticas descritivas dos indicadores numéricos (média, desvio, mínimo, mediana e máximo)."""
    estatisticas = df[COLUNAS_NUMERICAS].describe().T[["mean", "std", "min", "50%", "max"]]
    estatisticas.columns = ["media", "desvio", "minimo", "mediana", "maximo"]
    estatisticas.insert(0, "rotulo", [ROTULOS[coluna] for coluna in estatisticas.index])
    return estatisticas.round(2).to_dict("records")
