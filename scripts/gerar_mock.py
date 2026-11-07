"""Gera as bases fictícias (mock) de 2022 e 2026, com as colunas da base real e valores sorteados."""
from pathlib import Path

import numpy as np
import pandas as pd

PASTA_SAIDA = Path(__file__).resolve().parent.parent / "data" / "mock"
QUANTIDADE_MUNICIPIOS = 1000
SEMENTE = 42

COLUNAS = [
    "ano", "sg_uf", "regiao", "cd_municipio", "nm_municipio", "latitude", "longitude",
    "qt_eleitores", "populacao", "pib_per_capita", "pct_feminino", "pct_16_29", "pct_60_mais",
    "pct_ensino_superior", "pct_ate_fundamental", "pct_abstencao", "pct_brancos_nulos",
    "pct_votos_pt", "pct_votos_pl", "vencedor",
]

# UF: (código IBGE, região, latitude e longitude do centro, espalhamento em graus, nº real de municípios)
UFS = {
    "RO": (11, "Norte", -10.9, -62.8, 2.0, 52),
    "AC": (12, "Norte", -9.0, -70.5, 1.5, 22),
    "AM": (13, "Norte", -4.2, -64.6, 4.0, 62),
    "RR": (14, "Norte", 2.0, -61.4, 1.5, 15),
    "PA": (15, "Norte", -4.0, -52.5, 3.5, 144),
    "AP": (16, "Norte", 1.4, -51.8, 1.0, 16),
    "TO": (17, "Norte", -10.2, -48.3, 2.0, 139),
    "MA": (21, "Nordeste", -5.0, -45.3, 2.5, 217),
    "PI": (22, "Nordeste", -7.7, -42.7, 2.0, 224),
    "CE": (23, "Nordeste", -5.3, -39.5, 1.5, 184),
    "RN": (24, "Nordeste", -5.8, -36.6, 0.8, 167),
    "PB": (25, "Nordeste", -7.2, -36.7, 0.8, 223),
    "PE": (26, "Nordeste", -8.4, -37.9, 1.2, 185),
    "AL": (27, "Nordeste", -9.6, -36.6, 0.6, 102),
    "SE": (28, "Nordeste", -10.6, -37.4, 0.5, 75),
    "BA": (29, "Nordeste", -12.5, -41.7, 2.5, 417),
    "MG": (31, "Sudeste", -18.5, -44.5, 2.5, 853),
    "ES": (32, "Sudeste", -19.6, -40.6, 0.8, 78),
    "RJ": (33, "Sudeste", -22.3, -42.6, 0.8, 92),
    "SP": (35, "Sudeste", -22.2, -48.7, 1.8, 645),
    "PR": (41, "Sul", -24.6, -51.6, 1.5, 399),
    "SC": (42, "Sul", -27.2, -50.4, 1.0, 295),
    "RS": (43, "Sul", -29.7, -53.2, 1.8, 497),
    "MS": (50, "Centro-Oeste", -20.5, -54.8, 2.0, 79),
    "MT": (51, "Centro-Oeste", -12.9, -55.9, 3.0, 141),
    "GO": (52, "Centro-Oeste", -15.9, -49.6, 2.0, 246),
    "DF": (53, "Centro-Oeste", -15.8, -47.9, 0.2, 1),
}

# Perfil médio de cada região: os municípios são sorteados em torno desses valores
PERFIL_REGIOES = pd.DataFrame(
    {
        "pib_per_capita": [22000, 15000, 50000, 38000, 45000],
        "pct_16_29": [27, 24, 23, 20, 19],
        "pct_60_mais": [15, 20, 19, 24, 26],
        "pct_ensino_superior": [6, 6, 10, 11, 11],
        "pct_ate_fundamental": [58, 62, 50, 48, 50],
        "pct_abstencao": [22, 19, 21, 20, 17],
        "efeito_voto_pt": [0.2, 0.55, -0.3, -0.05, -0.3],
    },
    index=["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
)

# Diferenças fictícias de cada ano em relação ao perfil sorteado, para as bases não ficarem idênticas
AJUSTES_POR_ANO = {
    2022: {"pct_16_29": 0.0, "pct_60_mais": 0.0, "pct_ensino_superior": 0.0,
           "pct_ate_fundamental": 0.0, "pct_abstencao": 0.0, "eleitorado": 1.00, "voto_pt": 0.05},
    2026: {"pct_16_29": -0.8, "pct_60_mais": 1.5, "pct_ensino_superior": 1.0,
           "pct_ate_fundamental": -2.0, "pct_abstencao": 1.0, "eleitorado": 1.03, "voto_pt": -0.05},
}


def sortear_municipios(rng, quantidade):
    """Sorteia os municípios com as características que mudam pouco entre eleições."""
    ufs = pd.DataFrame.from_dict(
        UFS, orient="index",
        columns=["codigo_uf", "regiao", "lat_centro", "lon_centro", "espalhamento", "qt_real"],
    )
    pesos = ufs["qt_real"] / ufs["qt_real"].sum()
    siglas = rng.choice(ufs.index, size=quantidade, p=pesos)

    municipios = ufs.loc[siglas].reset_index(names="sg_uf")
    municipios = municipios.sort_values("codigo_uf", kind="stable").reset_index(drop=True)

    sequencia_na_uf = municipios.groupby("sg_uf").cumcount() + 1
    municipios["cd_municipio"] = municipios["codigo_uf"] * 100_000 + sequencia_na_uf
    municipios["nm_municipio"] = [f"Município {numero:04d}" for numero in range(1, quantidade + 1)]

    meio_espalhamento = municipios["espalhamento"] / 2
    municipios["latitude"] = municipios["lat_centro"] + rng.normal(0, 1, quantidade) * meio_espalhamento
    municipios["longitude"] = municipios["lon_centro"] + rng.normal(0, 1, quantidade) * meio_espalhamento

    perfil = PERFIL_REGIOES.loc[municipios["regiao"]].reset_index(drop=True)

    # População com cauda longa: muitos municípios pequenos e poucos muito grandes
    municipios["populacao"] = np.exp(rng.normal(np.log(11_000), 1.0, quantidade)).clip(800, 2_500_000).round()
    municipios["pib_per_capita"] = perfil["pib_per_capita"] * np.exp(rng.normal(0, 0.4, quantidade))

    # Quanto o município é mais rico (>0) ou mais pobre (<0) que a média da sua região
    riqueza_relativa = np.log(municipios["pib_per_capita"] / perfil["pib_per_capita"])

    municipios["pct_feminino"] = rng.normal(51.5, 1.2, quantidade)
    municipios["pct_16_29"] = perfil["pct_16_29"] + rng.normal(0, 2.5, quantidade)
    municipios["pct_60_mais"] = perfil["pct_60_mais"] + rng.normal(0, 3, quantidade)
    municipios["pct_ensino_superior"] = (
        perfil["pct_ensino_superior"] + 4 * riqueza_relativa + rng.normal(0, 2, quantidade)
    )
    municipios["pct_ate_fundamental"] = (
        perfil["pct_ate_fundamental"]
        - 1.2 * (municipios["pct_ensino_superior"] - perfil["pct_ensino_superior"])
        + rng.normal(0, 5, quantidade)
    )
    municipios["pct_abstencao"] = perfil["pct_abstencao"] + rng.normal(0, 3, quantidade)
    municipios["pct_brancos_nulos"] = rng.normal(4.5, 1.2, quantidade)

    # Inclinação política própria do município, que se mantém de uma eleição para outra
    municipios["tendencia_local"] = rng.normal(0, 0.55, quantidade)

    return municipios


def calcular_pct_votos_pt(base, efeito_ano, rng):
    """Combina o perfil do município em uma pontuação e a converte em % de votos com a função logística."""
    pontuacao = (
        base["regiao"].map(PERFIL_REGIOES["efeito_voto_pt"])
        + efeito_ano
        - 0.4 * np.log(base["pib_per_capita"] / 30_000)
        + 0.03 * (base["pct_ate_fundamental"] - 50)
        - 0.03 * (base["pct_ensino_superior"] - 10)
        + 0.05 * (base["pct_feminino"] - 51.5)
        + 0.03 * (base["pct_16_29"] - 22)
        + base["tendencia_local"]
        + rng.normal(0, 0.2, len(base))
    )
    return 100 / (1 + np.exp(-pontuacao))


def gerar_eleicao(municipios, ano, rng):
    """Monta a base de uma eleição: aplica os ajustes do ano e calcula participação e votos."""
    ajustes = AJUSTES_POR_ANO[ano]
    quantidade = len(municipios)
    base = municipios.copy()
    base["ano"] = ano

    # Pequeno ruído por ano: o mesmo município muda pouco de uma eleição para a outra
    for coluna in ["pct_16_29", "pct_60_mais", "pct_ensino_superior", "pct_ate_fundamental"]:
        base[coluna] = base[coluna] + ajustes[coluna] + rng.normal(0, 0.3, quantidade)
    base["pct_abstencao"] = base["pct_abstencao"] + ajustes["pct_abstencao"] + rng.normal(0, 1.0, quantidade)
    base["pct_brancos_nulos"] = base["pct_brancos_nulos"] + rng.normal(0, 0.5, quantidade)

    limites = {
        "pct_feminino": (47, 55), "pct_16_29": (10, 40), "pct_60_mais": (8, 40),
        "pct_ensino_superior": (1, 40), "pct_ate_fundamental": (15, 85),
        "pct_abstencao": (8, 40), "pct_brancos_nulos": (1, 12),
    }
    for coluna, (minimo, maximo) in limites.items():
        base[coluna] = base[coluna].clip(minimo, maximo)

    proporcao_eleitores = rng.uniform(0.68, 0.80, quantidade)
    base["qt_eleitores"] = (base["populacao"] * proporcao_eleitores * ajustes["eleitorado"]).round()

    base["pct_votos_pt"] = calcular_pct_votos_pt(base, ajustes["voto_pt"], rng)
    base["pct_votos_pl"] = 100 - base["pct_votos_pt"]
    base["vencedor"] = np.where(base["pct_votos_pt"] > 50, "PT", "PL")

    return formatar(base)


def formatar(base):
    """Ordena as colunas, define os tipos e arredonda os valores como na base real."""
    base = base[COLUNAS].copy()
    for coluna in ["ano", "cd_municipio", "qt_eleitores", "populacao"]:
        base[coluna] = base[coluna].astype(int)
    base[["latitude", "longitude"]] = base[["latitude", "longitude"]].round(4)
    colunas_decimais = ["pib_per_capita"] + [coluna for coluna in COLUNAS if coluna.startswith("pct_")]
    base[colunas_decimais] = base[colunas_decimais].round(2)
    return base


def main():
    rng = np.random.default_rng(SEMENTE)
    municipios = sortear_municipios(rng, QUANTIDADE_MUNICIPIOS)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    for ano in AJUSTES_POR_ANO:
        base = gerar_eleicao(municipios, ano, rng)
        caminho = PASTA_SAIDA / f"municipios_{ano}.csv"
        base.to_csv(caminho, index=False)
        print(f"{caminho.name}: {len(base)} municípios, vencedor {base['vencedor'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
