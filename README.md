# Eleições 2026: análise de dados e Machine Learning

Trabalho final da disciplina de **Tópicos Especiais em Software** (Prof. Rhafael Freitas da Costa).

Aplicação web em Python (Flask) para analisar o **2º turno presidencial (PT × PL) por município** e prever o partido vencedor com machine learning. O usuário envia uma base de municípios (.csv, .json ou .xml). A aplicação gera os gráficos e mapas automaticamente, treina classificadores configuráveis e faz predições para novos municípios.

---

## Sumário

1. [Funcionalidades](#funcionalidades)
2. [Tecnologias](#tecnologias)
3. [Como rodar](#como-rodar)
4. [Como usar (passo a passo)](#como-usar-passo-a-passo)
5. [Base de dados](#base-de-dados)
6. [Páginas da aplicação](#páginas-da-aplicação)
7. [Modelos e Predição](#modelos-e-predição)
8. [Estrutura do projeto](#estrutura-do-projeto)
9. [Como o código está organizado](#como-o-código-está-organizado)
10. [Decisões de projeto](#decisões-de-projeto)
11. [Divisão de tarefas](#divisão-de-tarefas)

---

## Funcionalidades

Cada requisito do enunciado e onde ele está na aplicação:

| Requisito do enunciado | Onde está |
|---|---|
| **Upload e flexibilidade dos dados**: arquivos .csv, .xml ou .json com as mesmas colunas, com gráficos gerados automaticamente | Página **Dados**: envio da base, validação das colunas e limpeza. Todas as páginas passam a usar a base enviada. |
| **Análise de dados e visualização**: gráficos básicos e interativos, incluindo mapas | Página **Análise**: cards, barras, pizza, histograma, dispersão, mapa dos municípios e mapa de calor da correlação, com filtros por região, UF e variável. |
| **Machine learning com personalização**: escolha do classificador e ajuste dos parâmetros | Página **Modelos**: Árvore de Decisão, KNN e Regressão Logística, com parâmetros, variáveis e tamanho do teste configuráveis. |
| **Treinamento dinâmico**: re-treinar quando entram dados novos | Botão **Re-treinar** na página Modelos. Um aviso aparece quando a base mudou desde o último treino. |
| **Predições personalizadas** | Página **Predição**: um município digitado ou vários por arquivo, com resultado por região, por UF, no mapa e comparado com o resultado real. |

---

## Tecnologias

- **Python 3** com **Flask**: servidor web, rotas e templates
- **pandas** e **NumPy**: leitura, limpeza e agrupamento dos dados
- **matplotlib** e **seaborn**: mapa de calor da correlação, matriz de confusão e importância das variáveis
- **Plotly**: gráficos e mapas interativos
- **scikit-learn**: modelos, divisão treino/teste e métricas
- **lxml**: leitura de arquivos .xml pelo pandas
- **Bootstrap 5**: layout das páginas

---

## Como rodar

Pré-requisito: **Python 3.11 ou mais novo** (o projeto foi desenvolvido com o 3.13).

```bash
# 1. Clonar o repositório
git clone https://github.com/BrunoHunoff/eleicoes-2026.git
cd eleicoes-2026

# 2. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Criar o arquivo de configuração
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS

# 5. Rodar
python run.py
```

Depois, abra **http://localhost:5001** no navegador. A porta é a 5001 porque, no macOS, a 5000 (padrão do Flask) é usada pelo AirPlay.

No primeiro acesso, a aplicação usa a **base padrão** (dados reais de 2026, já incluída em `data/reais/`) e treina os modelos sozinha. Não é preciso preparar nada antes.

**Para gerar as bases de novo a partir das fontes oficiais** (opcional; baixa cerca de 520 MB do TSE e do IBGE para `data/raw/`):

```bash
python scripts/gerar_dataset.py
```

---

## Como usar (passo a passo)

1. **Dados**: confira a base padrão (2026) ou envie outra (.csv, .json ou .xml). Para testar, envie `data/reais/municipios_2022.csv` (eleição de 2022) ou um dos arquivos de `data/exemplos/`.
2. **Análise**: explore os gráficos e use os filtros de região, UF e variável.
3. **Modelos**: escolha o classificador, ajuste os parâmetros e as variáveis e clique em **Treinar**. Compare as métricas dos três modelos. Se você enviou uma base nova, clique em **Re-treinar**.
4. **Predição**: escolha o modelo, preveja um município digitando os indicadores ou vários enviando um arquivo. Veja o resultado por região, por UF e no mapa, e compare o previsto com o real.

---

## Base de dados

Cada linha é **um município** em **uma eleição**. A aplicação aceita qualquer base com as colunas abaixo. É isso que permite trocar a base (outra eleição, dados atualizados) e ver tudo recalculado.

| Coluna | Descrição | Fonte |
|---|---|---|
| `ano` | Ano da eleição | TSE |
| `sg_uf` | Sigla da unidade da federação | TSE |
| `regiao` | Região do país | IBGE |
| `cd_municipio` | Código IBGE do município (os 2 primeiros dígitos são o código do estado) | IBGE |
| `nm_municipio` | Nome do município | IBGE |
| `latitude`, `longitude` | Coordenadas da sede do município | IBGE |
| `qt_eleitores` | Eleitores aptos a votar | TSE |
| `populacao` | População residente (Censo 2022) | IBGE |
| `pib_per_capita` | PIB por habitante (R$) | IBGE |
| `pct_feminino` | % de mulheres no eleitorado | TSE |
| `pct_16_29` | % do eleitorado entre 16 e 29 anos | TSE |
| `pct_60_mais` | % do eleitorado com 60 anos ou mais | TSE |
| `pct_ensino_superior` | % do eleitorado com ensino superior completo | TSE |
| `pct_ate_fundamental` | % do eleitorado com no máximo o ensino fundamental | TSE |
| `pct_abstencao` | % de eleitores que não votaram no 2º turno | TSE |
| `pct_brancos_nulos` | % de votos brancos e nulos no 2º turno | TSE |
| `pct_votos_pt`, `pct_votos_pl` | % dos votos válidos de cada partido no 2º turno | TSE |
| `vencedor` | Partido mais votado no município no 2º turno (PT ou PL) | TSE |

**Bases reais.** `data/reais/municipios_2022.csv` e `municipios_2026.csv` têm os **5.570 municípios** do Brasil, com os dados oficiais do 2º turno presidencial de cada ano (PT × PL nas duas eleições). A de 2026 é a base padrão da aplicação. Conferência: somando os municípios, o PT tem 50,9% dos votos válidos em 2022, o resultado oficial (sem as seções do exterior).

**Como a base foi montada (tratamento dos dados).** O script `scripts/gerar_dataset.py` baixa os arquivos brutos e trata tudo com pandas:
1. **Lê só as colunas necessárias** dos arquivos do TSE (`usecols`). O arquivo de votação tem 47 colunas e o de perfil do eleitorado, 27; as outras (datas de geração, códigos de eleição, raça, estado civil etc.) são descartadas.
2. **Filtra as linhas** com máscaras: só o 2º turno, só o cargo de presidente e sem as seções do exterior (UF `ZZ`).
3. **Agrupa por município** (`groupby(...).agg(...)`): os arquivos do TSE vêm por zona eleitoral, e um município pode ter várias zonas.
4. **Calcula os percentuais**: votos de PT e PL (`np.where` separa os votos de cada partido), abstenção, brancos e nulos, gênero, faixa etária e escolaridade. O perfil do eleitorado de 2026 tem 11 milhões de linhas (2,2 GB); com `usecols`, só 5 das 27 colunas são carregadas.
5. **Junta as fontes** com `merge`: votação + perfil (TSE) + código IBGE, nome, coordenadas, população e PIB (IBGE). O código de município do TSE é diferente do IBGE; a tabela de correspondência faz a ligação.
6. **Remove colunas auxiliares** (`drop`) usadas só nos cálculos, como os votos absolutos e as somas por grupo.
7. **Trata ausentes e duplicados** como na aula de regressão: `isnull().sum()`, `duplicated().sum()` e `drop_duplicates().dropna()`. Como os nulos são poucos, as linhas são removidas em vez de imputadas. Em 2026, um município criado depois da tabela de correspondência não tem código IBGE e é removido.
8. **Confere o alvo** (`value_counts()`): 2022 tem 3.123 municípios vencidos pelo PT e 2.447 pelo PL; 2026, 2.875 e 2.695.

O script imprime cada etapa (ausentes, duplicados, linhas removidas e contagem do alvo).

**Notebook do tratamento.** `notebooks/tratamento_dados.ipynb` mostra as etapas uma a uma, no formato das aulas: `head`, `info`, `describe`, filtro com máscara, remoção de colunas com `drop`, `isnull`, `duplicated`, `groupby`, `value_counts` e gráficos exploratórios (histograma, boxplot e mapa de calor da correlação). As saídas já estão salvas no arquivo. Para rodar de novo, gere os arquivos brutos com o script e instale o Jupyter (`pip install notebook`).

**Limpeza no envio.** Quando uma base é enviada, a aplicação:
- confere se todas as colunas existem (e avisa quais faltam);
- tira espaços dos textos e padroniza as siglas;
- converte as colunas numéricas;
- remove linhas com valores faltando, com `vencedor` diferente de PT ou PL e municípios repetidos.

A mensagem de confirmação informa quantas linhas foram removidas.

**Exemplos nos três formatos.** `data/exemplos/municipios_2022.json` e `municipios_2022.xml` têm a mesma base real de 2022 (`data/reais/municipios_2022.csv`) em .json e .xml. São gerados por `scripts/gerar_exemplos.py` e servem para testar o envio de cada formato.

**Fontes.**
- **TSE, [Portal de Dados Abertos](https://dadosabertos.tse.jus.br/)**: `detalhe_votacao_munzona` (eleitores aptos, abstenção, brancos e nulos), `votacao_partido_munzona` (votos por partido) e `perfil_eleitorado` (gênero, idade e escolaridade), de 2022 e 2026.
- **IBGE, [API SIDRA](https://apisidra.ibge.gov.br/)**: população do Censo 2022 (tabela 4714) e PIB dos municípios de 2023 (tabela 5938). O PIB per capita é o PIB de 2023 dividido pela população do Censo 2022.
- **Coordenadas** da sede de cada município: [kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros), com base no IBGE.
- **Correspondência entre código TSE e código IBGE**: [betafcc/Municipios-Brasileiros-TSE](https://github.com/betafcc/Municipios-Brasileiros-TSE).
- **Malha dos estados**: `data/geo/estados.json`, a malha oficial do IBGE (API de malhas, qualidade mínima), usada no mapa por estado.

---

## Páginas da aplicação

### Dados
Envio da base e visão geral:
- resumo (municípios, eleitores, UFs, colunas);
- dicionário de dados;
- amostra das primeiras linhas;
- estatísticas de cada indicador (média, desvio padrão, mínimo, mediana e máximo).

O envio aceita .csv, .json e .xml (até 16 MB). Se faltar coluna, o arquivo é recusado com a lista das que faltam. Depois a base é limpa e a mensagem informa quantos municípios ficaram e quantas linhas foram removidas. A base enviada fica em `data/uploads/`, e o aviso do topo mostra o nome do arquivo em uso.

O botão "Voltar para a base padrão" (só aparece quando existe base enviada) desfaz o envio.

### Análise
Análise descritiva dos dados que já existem, sem predição:
- cards com municípios, eleitores, abstenção média e municípios vencidos por partido;
- barras de municípios vencidos por região e pizza com a proporção;
- histograma da variável escolhida, separado por partido vencedor;
- dispersão da variável escolhida × % de votos do partido escolhido (PT ou PL);
- mapa dos municípios (cor = vencedor, tamanho = eleitores) ou mapa por estado (% de votos no PT, ponderado pelo eleitorado, com o % de cada partido no hover);
- mapa de calor da correlação entre os indicadores.

Os filtros de região e UF valem para a página inteira (cards, gráficos, mapa e correlação). A variável e o partido valem para o histograma e a dispersão. Valores inválidos na URL são ignorados, e um filtro sem nenhum município mostra um aviso no lugar dos gráficos.

### Modelos
Treino e avaliação dos classificadores (detalhes em [Modelos e Predição](#modelos-e-predição)):
- configuração: modelo, parâmetros, variáveis e tamanho do teste;
- métricas: acurácia de treino e de teste, diferença entre elas, F1 e ganho sobre o baseline;
- relatório por partido, matriz de confusão e importância das variáveis;
- comparação dos três modelos;
- botão Re-treinar.

### Predição
Uso do modelo treinado:
- **Um município**: nome, UF e indicadores.
- **Vários municípios**: arquivo com as mesmas colunas da base, menos as de resultado (votos e vencedor).
- **Municípios previstos**: todas as predições ficam salvas numa lista. Se um município for previsto de novo, a linha dele é atualizada em vez de duplicar. A partir da lista, a página mostra:
  - cards;
  - municípios previstos por região;
  - probabilidade média de cada partido por UF;
  - resumo por região e por UF;
  - mapa por município ou por estado.

  A lista pode ser baixada em CSV ou apagada.
- **Real × previsto**: como o modelo escolhido se saiu nos municípios de teste:
  - acertos e acurácia;
  - municípios vencidos por partido, real ao lado do previsto;
  - probabilidade × votos reais;
  - mapa de acertos e erros;
  - acertos por região.

---

## Modelos e Predição

**O problema.** Classificação binária: para cada município, prever se o vencedor do 2º turno é **PT** ou **PL** a partir do perfil do eleitorado e de indicadores socioeconômicos.

**Variáveis preditoras.** O padrão são 7 variáveis, todas conhecidas **antes** da eleição:
- `populacao`, `pib_per_capita` (IBGE);
- `pct_feminino`, `pct_16_29`, `pct_60_mais`, `pct_ensino_superior`, `pct_ate_fundamental` (perfil do eleitorado, TSE).

`pct_abstencao` e `pct_brancos_nulos` aparecem como opção, mas ficam **desmarcadas por padrão**: são do próprio 2º turno e só são conhecidas depois da votação. `pct_votos_pt`, `pct_votos_pl` e `vencedor` **nunca** entram como variável, porque são a própria resposta.

**Modelos e parâmetros.** Cada modelo fica num `Pipeline` com `StandardScaler`, que coloca as variáveis na mesma escala. Isso é importante para o KNN, que mede distâncias.

| Modelo | Parâmetros ajustáveis (faixa · padrão) |
|---|---|
| Árvore de Decisão | `max_depth`, profundidade máxima (1 a 30 ou vazio = sem limite · 5) e `min_samples_split`, mínimo de amostras para dividir um nó (2 a 50 · 2) |
| KNN | `n_neighbors`, número de vizinhos (1 a 50 · 5) e `weights`, vizinhos com peso igual ou pela distância (· `uniform`) |
| Regressão Logística | `C`, inverso da regularização: quanto menor, mais simples o modelo (0,01 a 100 · 1,0) |

**Treino e teste.** A base é dividida com `train_test_split` estratificado: a proporção de PT e PL é a mesma nos dois conjuntos. O tamanho do teste vai de 10% a 40% (padrão 20%). O botão **Treinar** treina os três modelos de uma vez, com a mesma divisão (`random_state=42`), então a comparação entre eles é justa. O formulário sempre mostra a configuração do último treino.

**Primeiro acesso.** Se ainda não existe nenhum treino, a aplicação treina sozinha com a configuração padrão (7 variáveis e os parâmetros da tabela). Assim as páginas Modelos e Predição nunca ficam sem modelo.

**Métricas.**
- **Acurácia de treino e de teste.** Uma diferença acima de 5 pontos percentuais indica possível *overfitting* (o modelo decorou o treino).
- **Validação cruzada (5 folds)** na tabela de comparação: `KFold(n_splits=5, shuffle=True, random_state=42)` e `cross_val_score` no conjunto de treino, com o Pipeline (o `StandardScaler` é ajustado dentro de cada fold), como na aula de regressão. Mostra a acurácia média ± desvio padrão. Com uma única divisão treino/teste, o resultado pode depender da sorte da divisão; a validação cruzada mostra se ele é estável e se a diferença entre os modelos é maior que o desvio.
- **Precisão, recall e F1** por partido, e o **F1 macro** (média dos dois).
- **Matriz de confusão**: real × previsto.
- **Importância das variáveis**:
  - Árvore: `feature_importances_`;
  - Regressão Logística: peso absoluto dos coeficientes;
  - KNN: não tem importância por variável.
- **Baseline**: um `DummyClassifier` que sempre chuta o partido mais frequente. Um modelo só é útil se ficar acima dele.

**Re-treino.** O botão **Re-treinar** treina de novo com os mesmos parâmetros e variáveis, usando a base atual. É o treinamento dinâmico do enunciado. Quando uma base nova é enviada, as páginas Modelos e Predição avisam que o treino está desatualizado.

**Predição.**
- O modelo devolve a **probabilidade** de cada partido. O previsto é o de maior probabilidade.
- *"72% de chance"* quer dizer que, entre municípios parecidos com esse, cerca de 7 em cada 10 votaram nesse partido. **É a melhor aposta com base no padrão, não uma certeza.**
- Nos agrupamentos por região e UF aparecem a probabilidade média e o **% do eleitorado** nos municípios previstos para cada partido. Uma cidade grande pesa mais que várias pequenas.

**Lista de municípios previstos.**
- **Um município**: nome, UF e as variáveis do último treino. Os valores iniciais do formulário são a mediana de cada variável na base atual. A região vem da UF. Como não tem latitude, longitude nem número de eleitores, o município aparece nas tabelas e no mapa por estado, mas não no mapa por município nem no % do eleitorado.
- **Vários municípios**: arquivo .csv, .json ou .xml com `nm_municipio`, `sg_uf` e as variáveis do último treino. As outras colunas são opcionais. Linhas sem algum desses dados ou com UF inválida são ignoradas, e a mensagem informa quantas.
- Cada predição guarda o município, o modelo usado, a data, o partido previsto e a probabilidade do PT. Se o mesmo município (nome + UF) for previsto de novo, a linha é **atualizada**, não repetida.
- A lista pode ser baixada em CSV (**Baixar CSV**) ou apagada (**Limpar lista**). Para testar o envio, use `data/exemplos/municipios_para_prever.csv` (30 municípios reais da base de 2022, sem as colunas de resultado).

**Por que a comparação real × previsto usa só os municípios de teste.** Os municípios usados no treino já foram "vistos" pelo modelo. Medir o acerto neles daria uma nota inflada, como fazer a prova com o gabarito.

**Arquivos gerados.** Essas pastas estão no `.gitignore`, porque a aplicação recria tudo sozinha.
- `data/modelos/`: `resultados.json` (métricas e configuração do último treino), um `.joblib` por modelo (`arvore`, `knn`, `logistica`) e `predicoes_teste.csv` (previsões nos municípios de teste, usadas no real × previsto).
- `data/predicoes/salvas.csv`: a lista de municípios previstos.
- `data/uploads/`: a base enviada.

---

## Estrutura do projeto

```
eleicoes-2026/
├── run.py                  # Ponto de entrada: cria o app e sobe o servidor na porta 5001
├── config.py               # Configurações do Flask (chave secreta, tamanho máximo de upload)
├── requirements.txt        # Dependências
├── .env.example            # Modelo do arquivo .env
├── app/
│   ├── __init__.py         # Cria o app Flask e registra as páginas (blueprints)
│   ├── utils.py            # Formatação de números (padrão brasileiro) e conversão de gráficos em imagem
│   ├── routes/             # Uma rota por página: lê a requisição, chama os services e devolve o HTML
│   │   ├── inicio_routes.py
│   │   ├── dados_routes.py
│   │   ├── analise_routes.py
│   │   ├── modelos_routes.py
│   │   └── predicao_routes.py
│   ├── services/           # Toda a lógica: dados, gráficos, treino e predição
│   │   ├── dados_service.py
│   │   ├── analise_service.py
│   │   ├── modelos_service.py
│   │   └── predicao_service.py
│   ├── templates/          # HTML (Jinja + Bootstrap 5); base.html tem o menu e as mensagens
│   └── static/css/         # Estilos próprios
├── data/
│   ├── reais/              # Bases reais de 2022 e 2026 (TSE + IBGE), geradas por scripts/gerar_dataset.py
│   ├── raw/                # Arquivos brutos do TSE e do IBGE (baixados pelo script, fora do git)
│   ├── exemplos/           # A base de 2022 em .json e .xml e municípios para testar a predição
│   ├── geo/                # Contorno dos estados (malha do IBGE) para o mapa por estado
│   ├── uploads/            # Base enviada pelo usuário (criada pela aplicação, fora do git)
│   ├── modelos/            # Modelos treinados e resultados (criada pela aplicação, fora do git)
│   └── predicoes/          # Lista de municípios previstos (criada pela aplicação, fora do git)
├── notebooks/
│   └── tratamento_dados.ipynb  # Tratamento dos dados passo a passo, no formato das aulas
└── scripts/
    ├── gerar_dataset.py    # Baixa e trata os dados do TSE e do IBGE e gera as bases reais
    └── gerar_exemplos.py   # Converte a base real de 2022 para .json e .xml e sorteia municípios para prever
```

---

## Como o código está organizado

O projeto separa as responsabilidades em três camadas:

```
Navegador ──► routes/ ──► services/ ──► (pandas, scikit-learn, Plotly)
                │
                └──► templates/ ──► HTML de volta para o navegador
```

- **`routes/`**: cada página é um *blueprint* do Flask. A rota só lê o que veio do navegador (filtros, formulário, arquivo), chama os services e devolve a página com `render_template`. Formulários que mudam algo (enviar base, treinar, prever) usam `POST`, mostram uma mensagem com `flash` e redirecionam de volta.
- **`services/`**: onde está a lógica.
  - **`dados_service`**: lê os arquivos (.csv, .json, .xml), valida as colunas, limpa e guarda a base atual. Também tem o dicionário de dados.
  - **`analise_service`**: filtros, indicadores e todos os gráficos da página Análise.
  - **`modelos_service`**: treino dos três modelos, métricas, gráficos da matriz de confusão e da importância, e re-treino.
  - **`predicao_service`**: carrega o modelo treinado, faz as predições, mantém a lista de municípios previstos, agrupa por região e UF e gera os mapas.
- **`templates/`**: o HTML de cada página. Os números aparecem no padrão brasileiro com o filtro `numero` (ex.: `1.234,5`).

**Gráficos.** Os interativos (barras, pizza, histograma, dispersão e mapas) usam Plotly e são convertidos para HTML pela função `figura_para_html`. Os estáticos (mapa de calor, matriz de confusão, importância) usam matplotlib/seaborn e viram imagem pela função `figura_para_base64`. As cores dos partidos são sempre as mesmas em todos os gráficos.

**Exemplo do caminho de uma requisição.** Ao clicar em **Treinar**:
1. o navegador envia o formulário;
2. `modelos_routes` lê os parâmetros e chama `modelos_service`;
3. o service carrega a base atual, separa treino e teste, treina os três modelos, calcula as métricas e salva tudo;
4. a rota redireciona para a página Modelos, que mostra os resultados novos.

---

## Decisões de projeto

- **Apresentação neutra.** Nenhum gráfico usa um partido só como referência: PT e PL aparecem lado a lado, ou aparece o partido previsto ou vencedor.
- **Variáveis só do que se sabe antes da eleição.** Os votos e o vencedor nunca são variáveis. Abstenção e brancos/nulos ficam fora do padrão.
- **Comparação justa.** Real × previsto só nos municípios de teste. Os três modelos usam a mesma divisão treino/teste.
- **Baseline.** Toda acurácia é comparada com a de um modelo que sempre chuta o partido mais frequente.
- **Agrupamento ponderado.** Por região e UF, além da média das probabilidades, aparece o % do eleitorado, porque uma cidade grande pesa mais que várias pequenas.
- **Mapa por estado com código IBGE.** Cada estado do contorno é identificado pelo código IBGE da UF. O código vem da sigla da UF (tabela `UFS` em `predicao_service`), e não do código do município, porque municípios digitados não têm código IBGE.
- **Código simples.** Funções curtas e comentários de no máximo uma linha, para que qualquer membro da equipe consiga explicar qualquer parte.

---

## Divisão de tarefas

| Membro | Responsabilidades |
|---|---|
| **Igor** | Estrutura do projeto Flask, front-end das páginas, aba Predição (layout, agrupamentos por região e UF, real × previsto) e mapa por estado |
| **Nicolas** | Upload e limpeza dos dados (.csv, .json, .xml), filtros da Análise (incluindo dispersão por partido e mapa por estado), arquivos de exemplo e README |
| **Bruno** | Bases reais (download e tratamento dos dados do TSE e do IBGE), treino dos modelos com scikit-learn, métricas, re-treino e predição real (um município, arquivo e lista salva) |

Apresentação do front-end: 04/11/2026. Entrega final: 11/11/2026.
