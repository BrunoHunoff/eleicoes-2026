from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parents[1] / "data"
ENTRADA = PASTA_DADOS / "reais" / "municipios_2022.csv"
PASTA_SAIDA = PASTA_DADOS / "exemplos"
MUNICIPIOS_PARA_PREVER = 30


def gerar_exemplos():
    """Converte a base real de 2022 (csv) para .json e .xml, para testar o upload nos três formatos."""
    df = pd.read_csv(ENTRADA)
    PASTA_SAIDA.mkdir(exist_ok=True)
    df.to_json(PASTA_SAIDA / "municipios_2022.json", orient="records", force_ascii=False)
    df.to_xml(PASTA_SAIDA / "municipios_2022.xml", index=False)
    print(f"{len(df)} municípios gravados em {PASTA_SAIDA}")


def gerar_municipios_para_prever():
    """Sorteia municípios de 2022 sem as colunas de resultado, para testar a predição de vários municípios."""
    df = pd.read_csv(ENTRADA).sample(MUNICIPIOS_PARA_PREVER, random_state=42)
    df = df.drop(columns=["pct_votos_pt", "pct_votos_pl", "vencedor"])
    df.sort_values(["sg_uf", "nm_municipio"]).to_csv(PASTA_SAIDA / "municipios_para_prever.csv", index=False)
    print(f"{len(df)} municípios para prever gravados em {PASTA_SAIDA}")


if __name__ == "__main__":
    gerar_exemplos()
    gerar_municipios_para_prever()
