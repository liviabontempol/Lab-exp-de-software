# Lab 01 - Características de Repositórios Populares

## Objetivo

Este laboratório investiga se **repositórios populares do GitHub** apresentam certas características relacionadas a maturidade, colaboração e manutenção contínua.

As seguintes *Research Questions (RQs)* são respondidas a partir de métricas extraídas da API do GitHub (GraphQL):

- **RQ01. Sistemas populares são maduros/antigos?**  
  - **Métrica**: idade do repositório (calculada a partir do campo `createdAt`).

- **RQ02. Sistemas populares recebem muita contribuição externa?**  
  - **Métrica**: total de *pull requests* aceitas (`pullRequests(states: MERGED).totalCount`).

- **RQ03. Sistemas populares lançam releases com frequência?**  
  - **Métrica**: total de *releases* (`releases.totalCount`).

- **RQ04. Sistemas populares são atualizados com frequência?**  
  - **Métrica**: tempo até a última atualização (calculado a partir do campo `updatedAt`).

- **RQ05. Sistemas populares são escritos nas linguagens mais populares?**  
  - **Métrica**: linguagem primária (`primaryLanguage.name`) de cada repositório.

- **RQ06. Sistemas populares possuem um alto percentual de issues fechadas?**  
  - **Métrica**: razão entre número de *issues* fechadas (`closedIssues.totalCount`) e total de *issues* (`issues.totalCount`).

## Coleta automática de dados (API GitHub GraphQL)

A coleta dos dados é feita automaticamente pelo script `main.py` usando a **API GraphQL do GitHub**, que busca os **100 repositórios mais populares** (ordenados por estrelas).

### Dependências

- Python 3.10+  
- Bibliotecas Python:
  - `requests`
  - `python-dotenv`

Instalação das dependências (em um ambiente virtual):

```bash
pip install requests python-dotenv
```

### Configuração do token de acesso

1. Gerar um **Personal Access Token (PAT)** no GitHub com permissão de acesso a repositórios públicos.  
2. Criar um arquivo `.env` dentro da pasta `lab01` com o seguinte conteúdo:

```env
API_TOKEN=seu_token_aqui
```

> Atenção: o arquivo `.env` é ignorado pelo Git (listado em `.gitignore`) e não deve ser versionado em repositórios públicos.

### Execução da coleta

Dentro da pasta `lab01`:

```bash
python main.py
```

O script irá:

- Autenticar na API do GitHub usando o token do arquivo `.env`.  
- Fazer uma consulta GraphQL para buscar até **100 repositórios populares**.  
- Salvar o resultado bruto da consulta no arquivo `repositorios_populares.json`, que será utilizado posteriormente para calcular as métricas das RQs.

## Como rodar o projeto em Python

### 1. Criar e ativar o ambiente virtual (recomendado)
Dentro da pasta `lab01`:

```bash
python -m venv .venv
```

No PowerShell (Windows):

```bash
.venv\Scripts\Activate.ps1
```

Se aparecer erro de execução de script:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Instalar dependências

Com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
```

Se não quiser usar `requirements.txt`, instale manualmente:

```bash
pip install requests python-dotenv matplotlib
```

### 3. Configurar o token do GitHub

Crie (ou edite) o arquivo `.env` dentro de `lab01`:

```env
API_TOKEN=seu_token_aqui
```

Certifique-se de que o token tem permissão para ler repositórios públicos.

### 4. Coletar os dados (1.000 repositórios)

O fluxo principal usa os arquivos `config.py` e `coletor.py`:

```bash
python coletor.py
```

Isso irá:

- Autenticar na API GraphQL do GitHub.
- Paginar até `TOTAL_REPOS_PESQUISA` repositórios (configurado em `config.py`, padrão 1000).
- Salvar:
  - `repositorios_populares.json` (dados brutos).
  - `repositorios_populares_1000.csv` (dados tabulares para análise).

> Opcionalmente, para testar apenas a consulta base (100 repositórios), você pode usar `main.py` ou `teste_graphql.py`.

### 5. Gerar estatísticas (medianas para as RQs)

Para calcular as medianas das métricas (idade, PRs, releases, tempo desde última atualização, razão de issues fechadas e ranking de linguagens):

```bash
python analise.py
```

Isso lê o CSV definido em `ARQUIVO_CSV` no `config.py` e imprime um resumo no terminal, já organizado por RQ.

### 6. Gerar gráficos e relatório HTML

Para gerar visualizações e um relatório pronto em HTML:

```bash
python visualizacao.py
```

Esse comando irá:

- Gerar gráficos (histogramas e gráfico de barras) para RQ01–RQ06.
- Salvar um relatório visual em:
  - `relatorio_visualizacao.html` (abrir no navegador).
- Salvar um resumo em JSON:
  - `visualizacao.json` (medianas e contagem de linguagens).

Com esses passos, você executa todo o pipeline do laboratório: **coleta → análise → visualização → relatório**.

