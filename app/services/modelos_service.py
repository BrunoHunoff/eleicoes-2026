import json
import textwrap
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from app.services import dados_service
from app.services.dados_service import ROTULOS
from app.utils import figura_para_base64, formatar_numero

PASTA_MODELOS = Path(__file__).resolve().parents[2] / "data" / "modelos"
ARQUIVO_RESULTADOS = PASTA_MODELOS / "resultados.json"
ARQUIVO_PREDICOES_TESTE = PASTA_MODELOS / "predicoes_teste.csv"

MODELOS_DISPONIVEIS = {"arvore": "Árvore de Decisão", "knn": "KNN", "logistica": "Regressão Logística"}
MODELO_PADRAO = "arvore"

COLUNA_ALVO = "vencedor"
CLASSES = ["PT", "PL"]

VARIAVEIS_CANDIDATAS = [
    "populacao", "pib_per_capita", "pct_feminino", "pct_16_29", "pct_60_mais",
    "pct_ensino_superior", "pct_ate_fundamental", "pct_abstencao", "pct_brancos_nulos",
]
# Sem abstenção e brancos/nulos: são do próprio 2º turno e só se sabem depois da votação
VARIAVEIS_PADRAO = [
    "populacao", "pib_per_capita", "pct_feminino", "pct_16_29", "pct_60_mais",
    "pct_ensino_superior", "pct_ate_fundamental",
]

PARAMETROS_PADRAO = {
    "arvore": {"max_depth": 5, "min_samples_split": 2},
    "knn": {"n_neighbors": 5, "weights": "uniform"},
    "logistica": {"C": 1.0},
}
TAMANHO_TESTE_PADRAO = 0.2
FOLDS_VALIDACAO = 5

# campo: (nome na mensagem de erro, mínimo, máximo); os mesmos limites do formulário
LIMITES = {
    "max_depth": ("Profundidade máxima", 1, 30),
    "min_samples_split": ("Mínimo de amostras para dividir", 2, 50),
    "n_neighbors": ("Número de vizinhos", 1, 50),
    "C": ("C", 0.01, 100),
    "tamanho_teste": ("Tamanho do teste", 10, 40),
}

# Acima de 5 pontos percentuais entre treino e teste, o modelo pode estar decorando os dados de treino
LIMITE_OVERFITTING = 0.05


def escolher_modelo(chave):
    """Devolve a chave do modelo pedido, ou a do modelo padrão quando ela não existe."""
    return chave if chave in MODELOS_DISPONIVEIS else MODELO_PADRAO


def caminho_modelo(chave):
    """Caminho do arquivo .joblib onde fica o pipeline treinado de um modelo."""
    return PASTA_MODELOS / f"{chave}.joblib"


def ler_numero(formulario, campo, tipo):
    """Converte um campo do formulário para número e confere se está dentro dos limites."""
    nome, minimo, maximo = LIMITES[campo]
    try:
        valor = tipo(formulario.get(campo, ""))
    except ValueError:
        raise ValueError(f"{nome} precisa ser um número.") from None
    if not minimo <= valor <= maximo:
        raise ValueError(f"{nome} precisa estar entre {minimo} e {maximo}.")
    return valor


def ler_configuracao(formulario):
    """Lê e valida o formulário de treino: parâmetros dos três modelos, variáveis e tamanho do teste."""
    marcadas = formulario.getlist("variaveis")
    variaveis = [coluna for coluna in VARIAVEIS_CANDIDATAS if coluna in marcadas]
    if not variaveis:
        raise ValueError("Escolha pelo menos uma variável preditora.")

    pesos = formulario.get("weights")
    if pesos not in ("uniform", "distance"):
        raise ValueError("Peso dos vizinhos inválido.")

    # Profundidade vazia = árvore sem limite de profundidade
    max_depth = ler_numero(formulario, "max_depth", int) if formulario.get("max_depth") else None
    parametros = {
        "arvore": {"max_depth": max_depth, "min_samples_split": ler_numero(formulario, "min_samples_split", int)},
        "knn": {"n_neighbors": ler_numero(formulario, "n_neighbors", int), "weights": pesos},
        "logistica": {"C": ler_numero(formulario, "C", float)},
    }
    tamanho_teste = ler_numero(formulario, "tamanho_teste", int) / 100
    return parametros, variaveis, tamanho_teste


def criar_classificador(chave, parametros):
    """Cria o classificador do scikit-learn com os parâmetros escolhidos."""
    if chave == "arvore":
        return DecisionTreeClassifier(
            max_depth=parametros["max_depth"], min_samples_split=parametros["min_samples_split"], random_state=42,
        )
    if chave == "knn":
        return KNeighborsClassifier(n_neighbors=parametros["n_neighbors"], weights=parametros["weights"])
    return LogisticRegression(C=parametros["C"], max_iter=1000)


def criar_pipeline(classificador):
    """Junta a padronização das variáveis e o classificador num único Pipeline."""
    # Variáveis na mesma escala: sem isso, a população dominaria as distâncias do KNN
    return Pipeline([("padronizar", StandardScaler()), ("modelo", classificador)])


def probabilidade_pt(pipeline, X):
    """Probabilidade do PT para cada linha de X."""
    # O scikit-learn ordena classes_ em ordem alfabética (PL, PT), então a coluna do PT é procurada pelo nome
    indice_pt = list(pipeline.classes_).index("PT")
    return pipeline.predict_proba(X)[:, indice_pt]


def calcular_importancia(chave, classificador, variaveis):
    """Importância de cada variável entre 0 e 1 (árvore e logística); o KNN não tem importância."""
    if chave == "arvore":
        valores = classificador.feature_importances_
    elif chave == "logistica":
        pesos = np.abs(classificador.coef_[0])
        valores = pesos / pesos.sum()
    else:
        return None
    return pd.Series(valores, index=variaveis).round(4).to_dict()


def converter_relatorio(relatorio):
    """Converte o classification_report do scikit-learn para precisao/recall/f1/suporte de cada partido."""
    convertido = {}
    for partido in CLASSES:
        linha = relatorio[partido]
        convertido[partido] = {
            "precisao": round(linha["precision"], 4),
            "recall": round(linha["recall"], 4),
            "f1": round(linha["f1-score"], 4),
            "suporte": int(linha["support"]),
        }
    return convertido


def validar_cruzado(modelo, X_treino, y_treino):
    """Acurácia média e desvio padrão na validação cruzada com 5 folds do treino, como na aula de regressão."""
    kfold = KFold(n_splits=FOLDS_VALIDACAO, shuffle=True, random_state=42)
    # Com o Pipeline, o StandardScaler é ajustado dentro de cada fold, sem vazar dados da parte de validação
    acuracias = cross_val_score(modelo, X_treino, y_treino, cv=kfold, scoring="accuracy")
    return round(acuracias.mean(), 4), round(acuracias.std(), 4)


def avaliar(chave, pipeline, X_treino, X_teste, y_treino, y_teste):
    """Calcula as métricas de um modelo já treinado, no formato usado pela página Modelos."""
    previsto = pipeline.predict(X_teste)
    relatorio = classification_report(y_teste, previsto, labels=CLASSES, output_dict=True, zero_division=0)
    validacao_media, validacao_desvio = validar_cruzado(pipeline, X_treino, y_treino)
    return {
        "nome": MODELOS_DISPONIVEIS[chave],
        "acuracia_treino": round(accuracy_score(y_treino, pipeline.predict(X_treino)), 4),
        "acuracia_teste": round(accuracy_score(y_teste, previsto), 4),
        "f1_macro": round(f1_score(y_teste, previsto, average="macro"), 4),
        "validacao_media": validacao_media,
        "validacao_desvio": validacao_desvio,
        "relatorio": converter_relatorio(relatorio),
        "matriz_confusao": confusion_matrix(y_teste, previsto, labels=CLASSES).tolist(),
        "importancia_variaveis": calcular_importancia(chave, pipeline.named_steps["modelo"], list(X_treino.columns)),
    }


def montar_predicoes_teste(chave, pipeline, X_teste, municipios):
    """Tabela com o partido previsto e a probabilidade do PT em cada município de teste."""
    return pd.DataFrame({
        "modelo": chave,
        "cd_municipio": municipios,
        "previsto": pipeline.predict(X_teste),
        "prob_pt": probabilidade_pt(pipeline, X_teste).round(3),
    })


def treinar_modelos(df, parametros, variaveis, tamanho_teste):
    """Treina os três modelos e o baseline com a mesma divisão treino/teste, salva tudo e devolve os resultados."""
    if df[COLUNA_ALVO].nunique() < 2:
        raise ValueError("a base precisa ter municípios vencidos pelo PT e pelo PL.")

    X = df[variaveis]
    y = df[COLUNA_ALVO]
    # stratify mantém a mesma proporção de PT e PL no treino e no teste
    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=tamanho_teste, stratify=y, random_state=42,
    )

    baseline = DummyClassifier(strategy="most_frequent").fit(X_treino, y_treino)
    baseline_media, baseline_desvio = validar_cruzado(baseline, X_treino, y_treino)
    resultados = {
        "base": dados_service.nome_base_atual(),
        "treinado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tamanho_teste": tamanho_teste,
        "classes": CLASSES,
        "variaveis": variaveis,
        "baseline": {
            "nome": "Baseline (classe mais frequente)",
            "acuracia_teste": round(baseline.score(X_teste, y_teste), 4),
            "validacao_media": baseline_media,
            "validacao_desvio": baseline_desvio,
        },
        "modelos": {},
    }

    PASTA_MODELOS.mkdir(parents=True, exist_ok=True)
    predicoes = []
    for chave in MODELOS_DISPONIVEIS:
        pipeline = criar_pipeline(criar_classificador(chave, parametros[chave]))
        pipeline.fit(X_treino, y_treino)
        joblib.dump(pipeline, caminho_modelo(chave))

        metricas = avaliar(chave, pipeline, X_treino, X_teste, y_treino, y_teste)
        metricas["parametros"] = parametros[chave]
        resultados["modelos"][chave] = metricas
        predicoes.append(montar_predicoes_teste(chave, pipeline, X_teste, df.loc[X_teste.index, "cd_municipio"]))

    pd.concat(predicoes).to_csv(ARQUIVO_PREDICOES_TESTE, index=False)
    with ARQUIVO_RESULTADOS.open("w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, ensure_ascii=False, indent=2)
    return resultados


def carregar_resultados():
    """Lê os resultados do último treino; se ainda não houve treino, treina com a configuração padrão."""
    if not ARQUIVO_RESULTADOS.exists():
        return treinar_modelos(
            dados_service.carregar_base_atual(), PARAMETROS_PADRAO, VARIAVEIS_PADRAO, TAMANHO_TESTE_PADRAO,
        )
    with ARQUIVO_RESULTADOS.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def retreinar():
    """Treina de novo com os parâmetros e as variáveis do último treino, usando a base atual."""
    resultados = carregar_resultados()
    parametros = {chave: modelo["parametros"] for chave, modelo in resultados["modelos"].items()}
    return treinar_modelos(
        dados_service.carregar_base_atual(), parametros, resultados["variaveis"], resultados["tamanho_teste"],
    )


def base_mudou(resultados):
    """Indica se a base atual é diferente da base usada no último treino."""
    return resultados["base"] != dados_service.nome_base_atual()


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
    """Dados do resumo do treino: base, data/hora, tamanho do teste, parâmetros e variáveis."""
    treinado_em = datetime.strptime(resultados["treinado_em"], "%Y-%m-%d %H:%M")
    return {
        "base": resultados["base"],
        "treinado_em": treinado_em.strftime("%d/%m/%Y %H:%M"),
        "tamanho_teste": resultados["tamanho_teste"],
        "municipios_teste": int(np.sum(modelo["matriz_confusao"])),
        "parametros": modelo["parametros"],
        "variaveis": [ROTULOS[coluna] for coluna in resultados["variaveis"]],
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
            # .get: um treino salvo antes da validação cruzada não tem esses campos
            "validacao_media": modelo.get("validacao_media"),
            "validacao_desvio": modelo.get("validacao_desvio"),
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
        "validacao_media": resultados["baseline"].get("validacao_media"),
        "validacao_desvio": resultados["baseline"].get("validacao_desvio"),
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
    ordenadas = pd.Series(importancias).sort_values(ascending=False)
    # Rótulos longos quebrados em linhas para o gráfico continuar legível na tela do celular
    rotulos = [textwrap.fill(ROTULOS[coluna], 20) for coluna in ordenadas.index]
    valores = ordenadas.tolist()

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    sns.barplot(x=valores, y=rotulos, color="#0d6efd", ax=ax)
    ax.bar_label(ax.containers[0], labels=[formatar_numero(valor, 2) for valor in valores], padding=3)
    ax.set_xticks([])
    ax.margins(x=0.12)
    ax.set_xlabel("Importância")
    ax.set_ylabel("")
    return figura_para_base64(fig)
