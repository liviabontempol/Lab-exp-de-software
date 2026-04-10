# Lab 02 - Um estudo das características de qualidade de sistemas Java

Este projeto responde às RQs do Lab02 relacionando métricas de processo (GitHub) com métricas de qualidade interna (CK): `CBO`, `DIT` e `LCOM`.

## Objetivo das RQs

- `RQ01`: relação entre popularidade (`stars`) e qualidade.
- `RQ02`: relação entre maturidade (`repo_age_years`) e qualidade.
- `RQ03`: relação entre atividade (`releases_total`) e qualidade.
- `RQ04`: relação entre tamanho (`loc`, `comment_lines`) e qualidade.

## Arquivos principais

- `coletor_java.py`: coleta top-1000 repositórios Java via GraphQL.
- `pipeline_qualidade.py`: clone + métricas de tamanho + execução do CK + sumarização por repositório.
- `analise_lab02.py`: estatísticas e correlações (Pearson/Spearman) + gráficos.
- `config.py`: parâmetros centralizados.

## Pré-requisitos

- Python 3.10+
- Git instalado e no PATH
- Java instalado e no PATH (JDK 8+; recomendado 17+)
- CK `.jar` baixado localmente

Dependências Python:

```powershell
pip install requests python-dotenv matplotlib scipy
```

## Configuração de ambiente

### 1) Java no Windows (obrigatório para CK)

Se o terminal mostrar `java não é reconhecido`, configure:

- `JAVA_HOME = C:\Program Files\Java\jdk-21.0.10`
- no `Path`, adicione `%JAVA_HOME%\bin`

Teste:

```powershell
java -version
javac -version
```

### 2) Arquivo `.env` em `lab02`

Crie/edite `lab02/.env`:

```env
API_TOKEN=seu_token_github
CK_JAR_PATH=C:\Users\SEU_USUARIO\Downloads\ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
LIMIT_REPOS=1
```

Observações:
- `LIMIT_REPOS=1` para Lab02S01 (teste inicial e entrega parcial).
- `LIMIT_REPOS=1000` para Lab02S02/final.

## Como rodar (ordem correta)

Entre na pasta `lab02`:

```powershell
cd C:\Users\JOAOPEDRO\Documents\GitHub\Lab-exp-de-software\lab02
```

### Passo 1 - Coletar os 1000 repositórios Java

```powershell
python coletor_java.py
```

Saídas:
- `repos_java_1000.json`
- `repos_java_1000.csv`

### Passo 2 - Rodar qualidade (clone + CK + sumarização)

```powershell
python pipeline_qualidade.py
```

Saída:
- `repos_java_quality.csv`

Esse CSV já vem sumarizado por repositório com:
- Processo: `stars`, `releases_total`, `repo_age_years`, `loc`, `comment_lines`
- Qualidade: `cbo_mean/median/std`, `dit_mean/median/std`, `lcom_mean/median/std`
- Diagnóstico: `status`, `erro`

### Passo 3 - Rodar análise estatística e gráficos

```powershell
python analise_lab02.py
```

Saídas:
- `correlacoes_lab02.csv` (Pearson e Spearman para as combinações processo x qualidade)
- `grafico_<metrica_processo>_vs_<metrica_qualidade>.png`

## Como fizemos neste projeto

1. **Coleta de processo** com GraphQL do GitHub filtrando `language:Java` e ordenando por estrelas.
2. **Paginação** para atingir o top-1000 repositórios.
3. **Métricas de tamanho** calculadas localmente após clone (`LOC` e linhas de comentário).
4. **Métricas de qualidade** extraídas com CK em nível de classe.
5. **Sumarização por repositório** de `CBO`, `DIT`, `LCOM` por média, mediana e desvio.
6. **Análise final** com correlação (Pearson/Spearman) e gráficos para responder RQ01-RQ04.

## Solução de problemas comuns

- **`401 Bad credentials` em `coletor_java.py`**
  - Token inválido/expirado no `.env`. Gere um novo PAT e reinicie o terminal.

- **`java não é reconhecido`**
  - Java não está no PATH. Configure `JAVA_HOME` e `%JAVA_HOME%\bin`.

- **`Nenhum repositório com status=ok` em `analise_lab02.py`**
  - O `pipeline_qualidade.py` falhou para todos os repositórios. Verifique coluna `erro` em `repos_java_quality.csv`.

- **Erro de clone: pasta já existe**
  - Apague `clones_java` e `ck_output` e rode o pipeline novamente.

## Entregáveis esperados

### Lab02S01
- `repos_java_1000.csv`
- `repos_java_quality.csv` com pelo menos 1 repositório com `status=ok`

### Lab02S02 / Final
- `repos_java_quality.csv` (amostra completa ou máxima possível)
- `correlacoes_lab02.csv`
- gráficos `grafico_*.png`
- relatório final com hipóteses, metodologia, resultados e discussão
