"""Gera as bases reais de municípios (2022 e 2026) a partir dos dados abertos do TSE e do IBGE.

Baixa os arquivos brutos em data/raw/ (fora do git), trata os dados com pandas e salva
data/reais/municipios_<ano>.csv com as mesmas colunas usadas pela aplicação.

Uso: python scripts/gerar_dataset.py
"""
import json
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
PASTA_BRUTOS = PASTA_DADOS / "raw"
PASTA_SAIDA = PASTA_DADOS / "reais"
ANOS = [2022, 2026]

URL_TSE = "https://cdn.tse.jus.br/estatistica/sead/odsele"
URL_SIDRA = "https://apisidra.ibge.gov.br/values/t"
ARQUIVOS_FIXOS = {
    "ibge_populacao_2022.json": f"{URL_SIDRA}/4714/n6/all/v/93/p/2022",
    "ibge_pib_municipios.json": f"{URL_SIDRA}/5938/n6/all/v/37/p/last",
    "municipios_coordenadas.csv": "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv",
    "municipios_tse_ibge.csv": (
        "https://raw.githubusercontent.com/betafcc/Municipios-Brasileiros-TSE/master/municipios_brasileiros_tse.csv"
    ),
}
ARQUIVOS_TSE = ["detalhe_votacao_munzona", "votacao_partido_munzona", "perfil_eleitorado"]

CARGO_PRESIDENTE = 1
SEGUNDO_TURNO = 2
UF_EXTERIOR = "ZZ"
GENERO_FEMININO = 4
ESCOLARIDADE_SUPERIOR_COMPLETO = 8
# Analfabeto, lê e escreve, fundamental incompleto e fundamental completo
ESCOLARIDADE_ATE_FUNDAMENTAL = [1, 2, 3, 4]
# O primeiro dígito do código IBGE do município é a região
REGIOES = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}

COLUNAS_DETALHE = [
    "NR_TURNO", "CD_CARGO", "SG_UF", "CD_MUNICIPIO",
    "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS",
]
COLUNAS_PARTIDO = ["NR_TURNO", "CD_CARGO", "SG_UF", "CD_MUNICIPIO", "SG_PARTIDO", "QT_VOTOS_NOMINAIS_VALIDOS"]
COLUNAS_PERFIL = ["CD_MUNICIPIO", "CD_GENERO", "CD_FAIXA_ETARIA", "CD_GRAU_ESCOLARIDADE", "QT_ELEITORES"]

COLUNAS_FINAIS = [
    "ano", "sg_uf", "regiao", "cd_municipio", "nm_municipio", "latitude", "longitude",
    "qt_eleitores", "populacao", "pib_per_capita", "pct_feminino", "pct_16_29", "pct_60_mais",
    "pct_ensino_superior", "pct_ate_fundamental", "pct_abstencao", "pct_brancos_nulos",
    "pct_votos_pt", "pct_votos_pl", "vencedor",
]


def baixar_arquivos():
    """Baixa os arquivos brutos que ainda não estão em data/raw/."""
    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
    arquivos = dict(ARQUIVOS_FIXOS)
    for ano in ANOS:
        for nome in ARQUIVOS_TSE:
            arquivos[f"{nome}_{ano}.zip"] = f"{URL_TSE}/{nome}/{nome}_{ano}.zip"

    for nome, url in arquivos.items():
        caminho = PASTA_BRUTOS / nome
        if not caminho.exists():
            print(f"Baixando {nome}...")
            urlretrieve(url, caminho)


def ler_csv_tse(nome_zip, colunas):
    """Lê o CSV nacional (_BRASIL) de dentro do zip do TSE, só com as colunas pedidas."""
    arquivo_zip = zipfile.ZipFile(PASTA_BRUTOS / nome_zip)
    nome_csv = [nome for nome in arquivo_zip.namelist() if nome.endswith("_BRASIL.csv")][0]
    # O TSE publica em latin-1 e separado por ponto e vírgula
    return pd.read_csv(arquivo_zip.open(nome_csv), sep=";", encoding="latin-1", usecols=colunas)


def filtrar_presidente_2turno(df):
    """Mantém só o 2º turno para presidente e remove as seções do exterior (UF "ZZ")."""
    filtro = (df["NR_TURNO"] == SEGUNDO_TURNO) & (df["CD_CARGO"] == CARGO_PRESIDENTE) & (df["SG_UF"] != UF_EXTERIOR)
    return df[filtro]


def resumir_participacao(ano):
    """Soma as zonas de cada município: eleitores aptos, abstenção e votos brancos e nulos."""
    df = filtrar_presidente_2turno(ler_csv_tse(f"detalhe_votacao_munzona_{ano}.zip", COLUNAS_DETALHE))
    participacao = df.groupby("CD_MUNICIPIO").agg(
        qt_eleitores=("QT_APTOS", "sum"),
        comparecimento=("QT_COMPARECIMENTO", "sum"),
        abstencoes=("QT_ABSTENCOES", "sum"),
        brancos=("QT_VOTOS_BRANCOS", "sum"),
        nulos=("QT_TOTAL_VOTOS_NULOS", "sum"),
    ).reset_index()

    participacao["pct_abstencao"] = participacao["abstencoes"] / participacao["qt_eleitores"] * 100
    brancos_nulos = participacao["brancos"] + participacao["nulos"]
    participacao["pct_brancos_nulos"] = brancos_nulos / participacao["comparecimento"] * 100
    return participacao.drop(columns=["comparecimento", "abstencoes", "brancos", "nulos"])


def resumir_votos(ano):
    """Calcula o % de votos válidos de PT e PL em cada município e o partido vencedor."""
    df = filtrar_presidente_2turno(ler_csv_tse(f"votacao_partido_munzona_{ano}.zip", COLUNAS_PARTIDO))
    df = df.copy()
    df["votos_pt"] = np.where(df["SG_PARTIDO"] == "PT", df["QT_VOTOS_NOMINAIS_VALIDOS"], 0)
    df["votos_pl"] = np.where(df["SG_PARTIDO"] == "PL", df["QT_VOTOS_NOMINAIS_VALIDOS"], 0)
    votos = df.groupby("CD_MUNICIPIO").agg(votos_pt=("votos_pt", "sum"), votos_pl=("votos_pl", "sum")).reset_index()

    validos = votos["votos_pt"] + votos["votos_pl"]
    votos["pct_votos_pt"] = votos["votos_pt"] / validos * 100
    votos["pct_votos_pl"] = votos["votos_pl"] / validos * 100
    votos["vencedor"] = np.where(votos["votos_pt"] > votos["votos_pl"], "PT", "PL")
    return votos.drop(columns=["votos_pt", "votos_pl"])


def resumir_perfil(ano):
    """Calcula o perfil do eleitorado de cada município: gênero, idade e escolaridade."""
    df = ler_csv_tse(f"perfil_eleitorado_{ano}.zip", COLUNAS_PERFIL)
    eleitores = df["QT_ELEITORES"]
    # Código da faixa etária: 2529 = 25 a 29 anos, então os dois primeiros dígitos são a idade inicial
    idade_inicial = df["CD_FAIXA_ETARIA"] // 100
    df["feminino"] = np.where(df["CD_GENERO"] == GENERO_FEMININO, eleitores, 0)
    df["de_16_a_29"] = np.where((idade_inicial >= 16) & (idade_inicial < 30), eleitores, 0)
    df["de_60_mais"] = np.where(idade_inicial >= 60, eleitores, 0)
    df["superior"] = np.where(df["CD_GRAU_ESCOLARIDADE"] == ESCOLARIDADE_SUPERIOR_COMPLETO, eleitores, 0)
    df["ate_fundamental"] = np.where(df["CD_GRAU_ESCOLARIDADE"].isin(ESCOLARIDADE_ATE_FUNDAMENTAL), eleitores, 0)

    # O exterior sai depois, no merge com a participação, que já não tem a UF "ZZ"
    perfil = df.groupby("CD_MUNICIPIO").agg(
        total=("QT_ELEITORES", "sum"),
        feminino=("feminino", "sum"),
        de_16_a_29=("de_16_a_29", "sum"),
        de_60_mais=("de_60_mais", "sum"),
        superior=("superior", "sum"),
        ate_fundamental=("ate_fundamental", "sum"),
    ).reset_index()

    perfil["pct_feminino"] = perfil["feminino"] / perfil["total"] * 100
    perfil["pct_16_29"] = perfil["de_16_a_29"] / perfil["total"] * 100
    perfil["pct_60_mais"] = perfil["de_60_mais"] / perfil["total"] * 100
    perfil["pct_ensino_superior"] = perfil["superior"] / perfil["total"] * 100
    perfil["pct_ate_fundamental"] = perfil["ate_fundamental"] / perfil["total"] * 100
    return perfil.drop(columns=["total", "feminino", "de_16_a_29", "de_60_mais", "superior", "ate_fundamental"])


def ler_sidra(nome_arquivo, nome_coluna):
    """Lê um JSON da API SIDRA do IBGE e devolve o código do município e o valor numérico."""
    with (PASTA_BRUTOS / nome_arquivo).open(encoding="utf-8") as arquivo:
        linhas = json.load(arquivo)
    # A primeira linha do SIDRA é o cabeçalho com a descrição das colunas
    df = pd.DataFrame(linhas[1:])[["D1C", "V"]]
    df.columns = ["cd_municipio", nome_coluna]
    df["cd_municipio"] = df["cd_municipio"].astype(int)
    # Valores sem informação vêm como "-" ou "...": viram NaN e são tratados depois
    df[nome_coluna] = pd.to_numeric(df[nome_coluna], errors="coerce")
    return df


def montar_municipios_ibge():
    """Junta código TSE, código IBGE, nome, coordenadas, população e PIB per capita de cada município."""
    codigos = pd.read_csv(PASTA_BRUTOS / "municipios_tse_ibge.csv", usecols=["codigo_tse", "uf", "codigo_ibge"])
    codigos.columns = ["CD_MUNICIPIO", "sg_uf", "cd_municipio"]

    coordenadas = pd.read_csv(
        PASTA_BRUTOS / "municipios_coordenadas.csv", usecols=["codigo_ibge", "nome", "latitude", "longitude"],
    )
    coordenadas.columns = ["cd_municipio", "nm_municipio", "latitude", "longitude"]

    populacao = ler_sidra("ibge_populacao_2022.json", "populacao")
    pib = ler_sidra("ibge_pib_municipios.json", "pib_mil_reais")

    municipios = codigos.merge(coordenadas, on="cd_municipio", how="left")
    municipios = municipios.merge(populacao, on="cd_municipio", how="left")
    municipios = municipios.merge(pib, on="cd_municipio", how="left")
    # O SIDRA informa o PIB em mil reais
    municipios["pib_per_capita"] = municipios["pib_mil_reais"] * 1000 / municipios["populacao"]
    municipios["regiao"] = (municipios["cd_municipio"] // 1_000_000).map(REGIOES)
    return municipios.drop(columns=["pib_mil_reais"])


def montar_base(ano, municipios):
    """Junta as fontes de um ano, trata ausentes e duplicados e devolve a base no formato da aplicação."""
    print(f"\n===== {ano} =====")
    df = resumir_participacao(ano)
    df = df.merge(resumir_votos(ano), on="CD_MUNICIPIO", how="left")
    df = df.merge(resumir_perfil(ano), on="CD_MUNICIPIO", how="left")
    df = df.merge(municipios, on="CD_MUNICIPIO", how="left")
    df["ano"] = ano
    df = df[COLUNAS_FINAIS]
    print("Formato antes da limpeza:", df.shape)

    print("\nNulos por coluna:")
    print(df.isnull().sum())
    print("\nDuplicados:", df.duplicated().sum())
    # Poucos nulos (município sem código IBGE): remover a linha é mais simples que imputar, como na aula de regressão
    df = df.drop_duplicates().dropna()
    print("Formato após limpeza:", df.shape)

    df["cd_municipio"] = df["cd_municipio"].astype(int)
    df["qt_eleitores"] = df["qt_eleitores"].astype(int)
    df["populacao"] = df["populacao"].astype(int)
    colunas_decimais = ["pib_per_capita"] + [coluna for coluna in COLUNAS_FINAIS if coluna.startswith("pct_")]
    df[colunas_decimais] = df[colunas_decimais].round(2)

    print("\nMunicípios vencidos por partido:")
    print(df["vencedor"].value_counts().to_string())
    return df.sort_values(["sg_uf", "nm_municipio"])


def main():
    """Baixa os arquivos brutos e gera as bases reais de 2022 e 2026."""
    baixar_arquivos()
    municipios = montar_municipios_ibge()
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    for ano in ANOS:
        base = montar_base(ano, municipios)
        caminho = PASTA_SAIDA / f"municipios_{ano}.csv"
        base.to_csv(caminho, index=False)
        print(f"\nSalvo: {caminho.relative_to(PASTA_DADOS.parent)} ({len(base)} municípios)")


if __name__ == "__main__":
    main()
