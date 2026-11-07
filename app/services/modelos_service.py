import json
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from app.services.dados_service import ROTULOS
from app.utils import figura_para_base64, formatar_numero

PASTA_MOCK = Path(__file__).resolve().parents[2] / "data" / "mock"
RESULTADOS_MOCK = PASTA_MOCK / "resultados_modelos.json"

MODELOS_DISPONIVEIS = {"arvore": "Árvore de Decisão", "knn": "KNN", "logistica": "Regressão Logística"}
MODELO_PADRAO = "arvore"

# Acima de 5 pontos percentuais entre treino e teste, o modelo pode estar decorando os dados de treino
LIMITE_OVERFITTING = 0.05


def carregar_resultados_mock():
    """Lê os resultados ilustrativos dos modelos (JSON fixo: nesta etapa não há treino)."""
    with RESULTADOS_MOCK.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def escolher_modelo(chave):
    """Devolve a chave do modelo pedido, ou a do modelo padrão quando ela não existe."""
    return chave if chave in MODELOS_DISPONIVEIS else MODELO_PADRAO


def calcular_metricas(modelo, baseline):
    """Métricas dos cards: acurácias, diferença treino × teste, F1 macro e ganho sobre o baseline."""
    diferenca = round(modelo["acuracia_treino"] - modelo["acuracia_teste"], 4)
    return {
        "acuracia_treino": modelo["acuracia_treino"],
        "acuracia_teste": modelo["acuracia_teste"],
        "diferenca_treino_teste": diferenca,
        "possivel_overfitting": diferenca > LIMITE_OVERFITTING,
        "f1_macro": modelo["f1_macro"],
        "ganho_baseline": round(modelo["acuracia_teste"] - baseline["acuracia_teste"], 4),
    }


def resumir_treino(resultados, modelo):
    """Dados do resumo do treino: base, data/hora, tamanho do teste e parâmetros do modelo."""
    treinado_em = datetime.strptime(resultados["treinado_em"], "%Y-%m-%d %H:%M")
    return {
        "base": resultados["base"],
        "treinado_em": treinado_em.strftime("%d/%m/%Y %H:%M"),
        "tamanho_teste": resultados["tamanho_teste"],
        "municipios_teste": sum(sum(linha) for linha in modelo["matriz_confusao"]),
        "parametros": modelo["parametros"],
    }


def montar_comparacao(resultados):
    """Linhas da tabela de comparação (três modelos e baseline), marcando a maior acurácia de teste."""
    linhas = [
        {
            "chave": chave,
            "nome": modelo["nome"],
            "acuracia_treino": modelo["acuracia_treino"],
            "acuracia_teste": modelo["acuracia_teste"],
            "f1_macro": modelo["f1_macro"],
        }
        for chave, modelo in resultados["modelos"].items()
    ]
    # O baseline só tem acurácia de teste: ele não aprende nada no treino
    linhas.append({
        "chave": None,
        "nome": resultados["baseline"]["nome"],
        "acuracia_treino": None,
        "acuracia_teste": resultados["baseline"]["acuracia_teste"],
        "f1_macro": None,
    })
    maior_acuracia = max(linha["acuracia_teste"] for linha in linhas)
    for linha in linhas:
        linha["melhor"] = linha["acuracia_teste"] == maior_acuracia
    return linhas


def grafico_matriz_confusao(matriz, classes):
    """Heatmap da matriz de confusão (linhas = classe real, colunas = classe prevista), em base64."""
    fig, ax = plt.subplots(figsize=(4.5, 3.6))
    sns.heatmap(
        matriz, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=classes, yticklabels=classes, annot_kws={"fontsize": 14}, ax=ax,
    )
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Real")
    ax.tick_params(axis="y", rotation=0)
    return figura_para_base64(fig)


def grafico_importancia(importancias):
    """Barras horizontais com a importância de cada variável (rótulos legíveis), em base64."""
    ordenadas = sorted(importancias.items(), key=lambda item: item[1], reverse=True)
    # Rótulos longos quebrados em linhas para o gráfico continuar legível na tela do celular
    rotulos = [textwrap.fill(ROTULOS[coluna], 20) for coluna, _ in ordenadas]
    valores = [valor for _, valor in ordenadas]

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    sns.barplot(x=valores, y=rotulos, color="#0d6efd", ax=ax)
    ax.bar_label(ax.containers[0], labels=[formatar_numero(valor, 2) for valor in valores], padding=3)
    ax.set_xticks([])
    ax.margins(x=0.12)
    ax.set_xlabel("Importância")
    ax.set_ylabel("")
    return figura_para_base64(fig)
