"""Gera as predições fictícias (mock): as dos municípios de teste e a lista de municípios já previstos."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

PASTA_MOCK = Path(__file__).resolve().parent.parent / "data" / "mock"
SEMENTE = 42

# Rodadas de predição fictícias que formam a lista salva: (modelo, data e hora, quantidade de municípios)
RODADAS_SALVAS = [("logistica", "2026-11-05 10:30", 120), ("arvore", "2026-11-06 16:00", 30)]


def calcular_prob_pt(municipios, rng):
    """Probabilidade fictícia do PT: quanto maior a vantagem de votos, mais certeza; nos erros, perto de 50%."""
    quantidade = len(municipios)
    vantagem = (municipios["pct_votos_pt"] - 50).abs()
    certeza = (0.5 + vantagem / 40 + rng.normal(0, 0.05, quantidade)).clip(0.51, 0.99)

    errou = municipios["previsto"] != municipios["vencedor"]
    certeza = np.where(errou, rng.uniform(0.51, 0.75, quantidade), certeza)

    prob_pt = np.where(municipios["previsto"] == "PT", certeza, 1 - certeza)
    return prob_pt.round(3)


def sortear_teste(base, suporte):
    """Sorteia os municípios de teste com a mesma quantidade de PT e PL do relatório dos modelos."""
    vencidos_pt = base[base["vencedor"] == "PT"].sample(suporte["PT"], random_state=SEMENTE)
    vencidos_pl = base[base["vencedor"] == "PL"].sample(suporte["PL"], random_state=SEMENTE)
    return pd.concat([vencidos_pt, vencidos_pl])


def prever_teste(teste, matriz, rng):
    """Reproduz a matriz de confusão do modelo, colocando os erros nos municípios mais disputados."""
    teste = teste.copy()
    teste["previsto"] = teste["vencedor"]

    disputa = (teste["pct_votos_pt"] - 50).abs() + rng.normal(0, 3, len(teste))
    erros_pt = disputa[teste["vencedor"] == "PT"].nsmallest(matriz[0][1]).index
    erros_pl = disputa[teste["vencedor"] == "PL"].nsmallest(matriz[1][0]).index
    teste.loc[erros_pt, "previsto"] = "PL"
    teste.loc[erros_pl, "previsto"] = "PT"

    teste["prob_pt"] = calcular_prob_pt(teste, rng)
    return teste[["cd_municipio", "previsto", "prob_pt"]]


def gerar_predicoes_salvas(base, rng):
    """Simula a lista de municípios já previstos; quem foi previsto duas vezes fica só com a mais recente."""
    rodadas = []
    for modelo, previsto_em, quantidade in RODADAS_SALVAS:
        rodada = base.sample(quantidade, random_state=rng)
        rodada["previsto"] = rodada["vencedor"]
        rodada["prob_pt"] = calcular_prob_pt(rodada, rng)
        rodada["modelo"] = modelo
        rodada["previsto_em"] = previsto_em
        rodadas.append(rodada)

    salvas = pd.concat(rodadas).drop_duplicates("cd_municipio", keep="last")
    return salvas[["cd_municipio", "modelo", "previsto_em", "previsto", "prob_pt"]]


def main():
    rng = np.random.default_rng(SEMENTE)
    base = pd.read_csv(PASTA_MOCK / "municipios_2026.csv")
    with (PASTA_MOCK / "resultados_modelos.json").open(encoding="utf-8") as arquivo:
        resultados = json.load(arquivo)

    relatorio = resultados["modelos"]["arvore"]["relatorio"]
    teste = sortear_teste(base, {"PT": relatorio["PT"]["suporte"], "PL": relatorio["PL"]["suporte"]})

    predicoes = []
    for chave, modelo in resultados["modelos"].items():
        predicao = prever_teste(teste, modelo["matriz_confusao"], rng)
        predicao["modelo"] = chave
        predicoes.append(predicao)

    caminho = PASTA_MOCK / "predicoes_teste.csv"
    pd.concat(predicoes)[["modelo", "cd_municipio", "previsto", "prob_pt"]].to_csv(caminho, index=False)
    print(f"{caminho.name}: {len(teste)} municípios de teste × {len(predicoes)} modelos")

    salvas = gerar_predicoes_salvas(base, rng)
    caminho = PASTA_MOCK / "predicoes_salvas.csv"
    salvas.to_csv(caminho, index=False)
    print(f"{caminho.name}: {len(salvas)} municípios previstos")


if __name__ == "__main__":
    main()
