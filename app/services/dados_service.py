from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parents[2] / "data"
PASTA_MOCK = PASTA_DADOS / "mock"
BASE_EXEMPLO = PASTA_MOCK / "municipios_2026.csv"
PASTA_UPLOADS = PASTA_DADOS / "uploads"
BASE_ENVIADA = PASTA_UPLOADS / "base_atual.csv"
NOME_BASE_ENVIADA = PASTA_UPLOADS / "nome_base.txt"
NOME_BASE_EXEMPLO = "municipios_2026.csv (exemplo)"

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


COLUNAS_TEXTO = ["sg_uf", "regiao", "nm_municipio", "vencedor"]
COLUNAS_NUMERO = [coluna for coluna in DICIONARIO_COLUNAS if coluna not in COLUNAS_TEXTO]
PARTIDOS = ["PT", "PL"]


def ler_arquivo(arquivo):
    """Lê o arquivo enviado (.csv, .json ou .xml) e devolve um DataFrame."""
    nome = arquivo.filename.lower()
    if nome.endswith(".csv"):
        leitor = pd.read_csv
    elif nome.endswith(".json"):
        leitor = pd.read_json
    elif nome.endswith(".xml"):
        leitor = pd.read_xml
    else:
        raise ValueError("Formato não suportado: envie .csv, .json ou .xml")
    try:
        return leitor(arquivo.stream)
    except Exception as erro:
        raise ValueError(f"Não foi possível ler o arquivo: {erro}") from erro


def validar_colunas(df, colunas):
    """Devolve a lista das colunas obrigatórias que faltam no DataFrame (vazia quando está tudo certo)."""
    return [coluna for coluna in colunas if coluna not in df.columns]


def limpar_base(df):
    """Limpa a base e devolve (base limpa, número de linhas removidas)."""
    df = df.copy()
    linhas_antes = len(df)

    for coluna in COLUNAS_TEXTO:
        df[coluna] = df[coluna].astype("string").str.strip().replace("", pd.NA)
    df["sg_uf"] = df["sg_uf"].str.upper()
    df["vencedor"] = df["vencedor"].str.upper()
    for coluna in COLUNAS_NUMERO:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df.dropna(subset=list(DICIONARIO_COLUNAS))
    df = df[df["vencedor"].isin(PARTIDOS)]
    df = df.drop_duplicates(subset="cd_municipio")

    # Depois do dropna não há valores faltando: volta para tipos simples
    for coluna in COLUNAS_TEXTO:
        df[coluna] = df[coluna].astype(str)
    df["ano"] = df["ano"].astype(int)
    df["cd_municipio"] = df["cd_municipio"].astype(int)
    return df, linhas_antes - len(df)


def salvar_base(df, nome_arquivo):
    """Grava a base limpa como base atual e guarda o nome original do arquivo enviado."""
    PASTA_UPLOADS.mkdir(parents=True, exist_ok=True)
    df.to_csv(BASE_ENVIADA, index=False)
    NOME_BASE_ENVIADA.write_text(nome_arquivo, encoding="utf-8")


def carregar_base_atual():
    """Devolve a base enviada, se existir; senão, a base de exemplo (dados fictícios) de 2026."""
    if BASE_ENVIADA.exists():
        return pd.read_csv(BASE_ENVIADA)
    return pd.read_csv(BASE_EXEMPLO)


def nome_base_atual():
    """Devolve o nome do arquivo enviado, ou o nome da base de exemplo."""
    if BASE_ENVIADA.exists() and NOME_BASE_ENVIADA.exists():
        return NOME_BASE_ENVIADA.read_text(encoding="utf-8")
    return NOME_BASE_EXEMPLO


def voltar_base_exemplo():
    """Apaga a base enviada para a aplicação voltar a usar a base de exemplo."""
    BASE_ENVIADA.unlink(missing_ok=True)
    NOME_BASE_ENVIADA.unlink(missing_ok=True)


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
