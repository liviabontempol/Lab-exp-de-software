# Lab 04 - Dashboard BI (Power BI / Tableau / Looker Studio)

Este guia implementa o laboratorio de BI a partir dos dados do Lab03.

## 1. Objetivo

Construir um dashboard autoexplicativo com duas partes:
1. Caracterizacao do dataset completo e de subgrupos.
2. Respostas visuais para cada RQ (GQM), com metricas e medidas de tendencia central adequadas.

## 2. Preparacao dos Dados

Execute na raiz do projeto:

```powershell
python scripts/prepare_bi_dashboard.py
```

Arquivos gerados em `data/processed/bi`:
- `fact_repositories.csv`
- `kpi_repositories.csv`
- `dataset_characterization_by_language.csv`
- `fact_pull_requests.csv` (quando existir `data/raw/pull_requests.csv`)
- `kpi_pull_requests.csv`
- `rq_review_time_by_language.csv`
- `rq_size_vs_review_time.csv`
- `rq_interactions_by_feedback.csv`
- `rq_time_series_monthly.csv`

## 3. Especificacao do Dashboard

## 3.1 Pagina A - Caracterizacao do Dataset

Objetivo: descrever claramente os objetos de estudo e subgrupos.

Visuais recomendados:
1. Cards de KPI:
- Total de repositorios
- Total de linguagens
- Media e mediana de estrelas
- Media e mediana de total de PRs por repositorio

2. Grafico de barras (por linguagem):
- Eixo X: `language`
- Eixo Y: `repositories`
- Complementar com tooltip: `avg_stars`, `median_stars`, `avg_total_prs`, `median_total_prs`

3. Tabela de apoio:
- `language`, `repositories`, `avg_stars`, `median_stars`, `avg_total_prs`, `median_total_prs`

Importante:
- Mostrar dataset total e os subgrupos (linguagens).
- Se houver outro particionamento no trabalho (periodo/ano), adicionar filtros e cards para cada faixa.

## 3.2 Pagina B - Questoes de Pesquisa (RQs)

Cada bloco deve conter:
1. Enunciado da pergunta (texto visivel no dashboard)
2. Visualizacao principal
3. Medida usada (media, mediana, quartis)

RQ sugeridas com base no dataset de PRs:

RQ1. O tempo de analise dos PRs varia entre linguagens?
- Fonte: `rq_review_time_by_language.csv`
- Visual: barras + erro (P25/P75)
- Medida principal: mediana de `review_duration_hours`

RQ2. PRs maiores demandam mais tempo de analise?
- Fonte: `rq_size_vs_review_time.csv`
- Visual: barras por `size_bucket`
- Medidas: mediana de `total_changes`, mediana de `review_duration_hours`

RQ3. Como interacoes e revisoes se relacionam ao feedback final?
- Fonte: `rq_interactions_by_feedback.csv`
- Visual: barras agrupadas por `final_review_state`
- Medidas: mediana de `total_interactions`, mediana de `reviews`

RQ4. Ha tendencia temporal no processo de revisao?
- Fonte: `rq_time_series_monthly.csv`
- Visual: linha temporal por `created_year_month`
- Medidas: mediana de `review_duration_hours`, `total_changes`

Boas praticas:
- Preferir mediana para distribuicoes assimetricas.
- Nomear eixos de forma explicita (ex.: "Tempo de analise (horas, mediana)").
- Padronizar unidades (horas, contagem).

## 4. Modelo de Storytelling no Dashboard

Sugestao de ordem dos elementos:
1. Contexto e objetivo do estudo
2. Caracterizacao do dataset
3. RQ1
4. RQ2
5. RQ3
6. RQ4
7. Sintese final (insights chave)

## 5. Entregas Parciais (Sprints)

Sprint 1:
- Pagina de caracterizacao pronta
- Dicionario de dados (curto)
- Estrutura visual inicial do dashboard

Sprint 2:
- RQ1 e RQ2 implementadas
- Ajustes de labels, unidades e legenda
- Validacao de medidas de tendencia central

Sprint 3:
- RQ3 e RQ4 implementadas
- Dashboard autoexplicativo completo
- Revisao visual final para apresentacao

## 6. Apresentacao em Aula

Checklist de apresentacao:
1. Mostrar a pagina de caracterizacao completa
2. Mostrar cada RQ com seu enunciado e grafico correspondente
3. Explicar qual medida estatistica foi usada e por que
4. Apontar 2-3 insights observados
5. Demonstrar filtros por linguagem/periodo (se aplicavel)

## 7. Relatorio Final (Artigo TIS6)

Insercao recomendada:
- Secao 3 (Metodologia): graficos de caracterizacao do dataset
- Secao 4 (Resultados): graficos por RQ

Para cada figura no artigo:
1. Citar no texto ("Figura X mostra...")
2. Explicar o que esta sendo medido
3. Destacar interpretacao (insight)

Entregavel final:
- Dashboard exportado em PDF
- Artigo atualizado com figuras e discussoes

## 8. Dica de Implementacao no Power BI

Medidas DAX uteis (se importar `fact_pull_requests.csv`):

```DAX
PRs = COUNTROWS(fact_pull_requests)

Mediana_Tempo_Analise = MEDIAN(fact_pull_requests[review_duration_hours])

Media_Tempo_Analise = AVERAGE(fact_pull_requests[review_duration_hours])

Mediana_Tamanho_PR = MEDIAN(fact_pull_requests[total_changes])

Mediana_Interacoes = MEDIAN(fact_pull_requests[total_interactions])
```

Se `fact_pull_requests.csv` ainda nao existir, execute antes:

```powershell
python scripts/collect_prs.py
python scripts/prepare_bi_dashboard.py
```
