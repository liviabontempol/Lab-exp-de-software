# Lab 02 - Qualidade de sistemas Java

Este laboratório investiga a relação entre métricas de processo dos repositórios Java no GitHub e métricas de qualidade interna obtidas com CK (CBO, DIT e LCOM).

## RQs do laboratório

- RQ01: relação entre popularidade (estrelas) e qualidade.
- RQ02: relação entre maturidade (idade) e qualidade.
- RQ03: relação entre atividade (releases) e qualidade.
- RQ04: relação entre tamanho (LOC e comentários) e qualidade.

## Estrutura dos scripts

- `coletor_java.py`: coleta os top-1000 repositórios Java (GraphQL) e gera:
  - `repos_java_1000.json`
  - `repos_java_1000.csv`
- `pipeline_qualidade.py`: clona repositórios, conta LOC/comentários, executa CK e agrega CBO/DIT/LCOM por repositório.
- `analise_lab02.py`: calcula estatísticas descritivas, correlações (Pearson/Spearman) e gera gráficos.
- `config.py`: centraliza configurações (token, caminho do CK, limite de repositórios etc.).

## Pré-requisitos

- Python 3.10+
- Java (para executar o CK jar)
- Git no PATH
- Token GitHub em `.env`
- CK jar baixado localmente

Dependências Python:

```powershell
pip install requests python-dotenv matplotlib scipy
```

## Configuração

1. Crie `lab02/.env`:

```env
API_TOKEN=seu_token_github
CK_JAR_PATH=C:\caminho\para\ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
LIMIT_REPOS=1
```

`LIMIT_REPOS`:
- `1` para entregar Lab02S01 rapidamente (teste em 1 repositório).
- `1000` para Lab02S02/final.

2. Ajuste parâmetros opcionais em `config.py` se necessário.

## Execução completa

Dentro de `lab02`:

### 1) Coletar lista dos repositórios Java

```powershell
python coletor_java.py
```

### 2) Rodar clone + LOC/comentários + CK + sumarização por repositório

```powershell
python pipeline_qualidade.py
```

Saída principal:
- `repos_java_quality.csv`

Esse arquivo contém, por repositório:
- processo: `stars`, `releases_total`, `repo_age_years`, `loc`, `comment_lines`
- qualidade CK sumarizada: `cbo_*`, `dit_*`, `lcom_*`
- status/erro para diagnosticar falhas

### 3) Rodar análise e gráficos das RQs

```powershell
python analise_lab02.py
```

Saídas:
- `correlacoes_lab02.csv` (Pearson e Spearman por combinação processo x qualidade)
- `grafico_<metrica_processo>_vs_<metrica_qualidade>.png`

## Entrega sugerida

### Lab02S01
- `repos_java_1000.csv`
- `repos_java_quality.csv` com `LIMIT_REPOS=1` (pelo menos 1 repositório processado)

### Lab02S02 / final
- `repos_java_quality.csv` para toda a amostra (ou o máximo possível)
- `correlacoes_lab02.csv`
- gráficos gerados
- relatório final com hipóteses, metodologia, resultados e discussão

## O que você precisa fazer (visão geral)

### Lab02S01 (começo)
1. Coletar a lista dos 1.000 repositórios Java mais populares do GitHub.
2. Automatizar clone + coleta de métricas de qualidade (CK) e métricas de tamanho (LOC/Comentários).
+   Por enquanto, neste sprint você precisa gerar o CSV de **pelo menos 1 repositório**.

### Lab02S02 (continuação)
1. Rodar a coleta (clone + CK) para todos os 1.000 repositórios.
2. Analisar correlação com as RQs e escrever o relatório final.

## Como coletar a lista dos 1.000 repositórios Java

O script `coletor_java.py` reaproveita a lógica de busca/paginação GraphQL criada no `lab01`.

1. Entre na pasta `lab02`:

```powershell
cd C:\Users\JOAOPEDRO\Documents\GitHub\Lab-exp-de-software\lab02
```

2. Crie um arquivo `.env` com:

```env
API_TOKEN=seu_token_aqui
```

3. Rode:

```powershell
python coletor_java.py
```

4. Ele vai gerar:

- `repos_java_1000.json` (dados brutos)
- `repos_java_1000.csv` (tabela com `stars`, `releases_total`, `repo_age_years`, etc.)

> Arquivos gerados servem de base para as métricas de popularidade, maturidade e atividade (as de “processo”).

## Próximo passo (antes de rodar CK)

Para completar o Lab02S01, me diga qual forma/instância do CK você vai usar (por exemplo, arquivo `.jar` do CK e o comando exato para gerar métricas CBO/DIT/LCOM).
Com isso eu monto o script de:
1. clonar 1 repositório (dado o `url` do CSV),
2. contar LOC/comentários,
3. executar o CK e consolidar `CBO`, `DIT`, `LCOM` em um CSV final para 1 repositório.
