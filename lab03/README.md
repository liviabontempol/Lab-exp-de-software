# Lab 03 - Coleta de Repositórios e Pull Requests

Este laboratório implementa a seleção automática de repositórios do GitHub e a coleta de métricas de Pull Requests usando a API GraphQL. O foco é gerar datasets brutos em CSV que serão usados nos próximos laboratórios (análises estatísticas, gráficos e datasets processados).

## Objetivo do Lab03S01

- Selecionar automaticamente 200 repositórios populares.
- Coletar Pull Requests (MERGED/CLOSED) com reviews.
- Extrair métricas definidas no enunciado.
- Persistir dados em CSV.

## Arquitetura

```
lab03/
	data/
		raw/
			repositories.csv
			pull_requests.csv
	scripts/
		select_repos.py
		collect_prs.py
		run_all.py
	src/
		github/
			graphql_client.py
			queries.py
		config.py
		io_utils.py
		logging_utils.py
		models.py
		pr_collector.py
		repo_selection.py
	requirements.txt
```

### Principais componentes

- `src/github/graphql_client.py`: cliente GraphQL com tratamento de rate limit.
- `src/repo_selection.py`: seleção de repositórios por popularidade e PRs.
- `src/pr_collector.py`: coleta paginada de PRs e extração de métricas.
- `src/io_utils.py`: leitura e escrita de CSV.

## Como executar

1. Configure o token do GitHub em `.env` na raiz do projeto:

```
GITHUB_TOKEN=seu_token_aqui
```

2. Instale as dependências:

```
pip install -r lab03/requirements.txt
```

3. Execute a seleção de repositórios:

```
python lab03/scripts/select_repos.py
```

4. Execute a coleta de Pull Requests:

```
python lab03/scripts/collect_prs.py
```

5. (Opcional) Execute tudo em sequência:

```
python lab03/scripts/run_all.py
```

## Saídas

- `lab03/data/raw/repositories.csv`
- `lab03/data/raw/pull_requests.csv`

## Lab 04 - Dashboard BI

Para preparar os dados para Power BI/Tableau/Looker Studio:

```
python lab03/scripts/prepare_bi_dashboard.py
```

Arquivos gerados em `lab03/data/processed/bi`:

- `fact_repositories.csv`
- `kpi_repositories.csv`
- `dataset_characterization_by_language.csv`
- `fact_pull_requests.csv` (quando `pull_requests.csv` existir)
- `kpi_pull_requests.csv`
- `rq_review_time_by_language.csv`
- `rq_size_vs_review_time.csv`
- `rq_interactions_by_feedback.csv`
- `rq_time_series_monthly.csv`

Guia completo do laboratorio de BI:

- `lab03/docs/LAB04_DASHBOARD_BI.md`

## Próximos laboratórios

A estrutura foi desenhada para facilitar:

- análises estatísticas e correlações;
- geração de gráficos;
- criação de datasets processados.
