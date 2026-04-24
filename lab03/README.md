# Lab 03 - Características de Repositórios Populares com Alto Engajamento em Pull Requests

## Objetivo

Este laboratório investiga se **repositórios populares do GitHub com alto engajamento em pull requests** (mínimo 100 PRs mescladas) apresentam certas características relacionadas a maturidade, colaboração e manutenção contínua.

As seguintes *Research Questions (RQs)* são respondidas a partir de métricas extraídas da API do GitHub (GraphQL):

- **RQ01. Sistemas populares com alto engajamento em PRs são maduros/antigos?**  
  - **Métrica**: idade do repositório (calculada a partir do campo `createdAt`).

- **RQ02. Sistemas populares com alto engajamento em PRs recebem muita contribuição externa?**  
  - **Métrica**: total de *pull requests* aceitas (`pullRequests(states: MERGED).totalCount`).

- **RQ03. Sistemas populares com alto engajamento em PRs lançam releases com frequência?**  
  - **Métrica**: total de *releases* (`releases.totalCount`).

- **RQ04. Sistemas populares com alto engajamento em PRs são atualizados com frequência?**  
  - **Métrica**: tempo até a última atualização (calculado a partir do campo `updatedAt`).

- **RQ05. Sistemas populares com alto engajamento em PRs são escritos nas linguagens mais populares?**  
  - **Métrica**: linguagem primária (`primaryLanguage.name`) de cada repositório.

- **RQ06. Sistemas populares com alto engajamento em PRs possuem um alto percentual de issues fechadas?**  
  - **Métrica**: razão entre número de *issues* fechadas (`closedIssues.totalCount`) e total de *issues* (`issues.totalCount`).

## Coleta automática de dados (API GitHub GraphQL)

A coleta dos dados é feita automaticamente pelo script `main.py` usando a **API GraphQL do GitHub**, que busca os **200 repositórios mais populares** (ordenados por estrelas) que possuem **pelo menos 100 pull requests mescladas**.

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
2. Criar um arquivo `.env` dentro da pasta `lab03` com o seguinte conteúdo:

```env
API_TOKEN=seu_token_aqui
```
