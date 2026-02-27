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

## Próximos passos

- Implementar o código para calcular, a partir de `repositorios_populares.json`, as métricas correspondentes a cada RQ.  
- Gerar tabelas/gráficos resumindo os resultados e responder cada RQ no relatório final.
