from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parents[1] / "data"
ENTRADA = PASTA_DADOS / "mock" / "municipios_2022.csv"
PASTA_SAIDA = PASTA_DADOS / "exemplos"


def gerar_exemplos():
    """Converte a base de 2022 (csv) para .json e .xml, para testar o upload nos três formatos."""
    df = pd.read_csv(ENTRADA)
    PASTA_SAIDA.mkdir(exist_ok=True)
    df.to_json(PASTA_SAIDA / "municipios_2022.json", orient="records", force_ascii=False)
    df.to_xml(PASTA_SAIDA / "municipios_2022.xml", index=False)
    print(f"{len(df)} municípios gravados em {PASTA_SAIDA}")


if __name__ == "__main__":
    gerar_exemplos()
