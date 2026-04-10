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

### Ambiente virtual Python (recomendado)

Na pasta do projeto (ou na raiz do repositório), crie e ative o `.venv` para isolar as dependências.

**Criar o ambiente virtual** (uma vez):

```powershell
cd C:\Users\JOAOPEDRO\Documents\GitHub\Lab-exp-de-software\lab02
python -m venv .venv
```

**Ativar no PowerShell (Windows):**

```powershell
.venv\Scripts\Activate.ps1
```

Se aparecer erro de política de execução:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois de ativar, o prompt deve mostrar `(`.venv`)` no início da linha.

**Instalar dependências** (com o venv ativado):

```powershell
pip install requests python-dotenv matplotlib scipy
```

**Sair do ambiente virtual** (quando terminar):

```powershell
deactivate
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
CK_JAR_PATH=C:\Users\SEU_USUARIO\Desktop\ck-master\target\ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar
LIMIT_REPOS=1
```

**Importante — qual JAR do CK usar**

Após `mvn clean package` no repositório do CK, na pasta `target/` existem vários `.jar`. O único que serve para `java -jar` é o **fat jar** cujo nome termina em **`jar-with-dependencies.jar`**.

- **Não use** `ck-*-javadoc.jar` (erro: `no main manifest attribute`).
- **Não use** `ck-*-sources.jar`.
- **Use** `ck-*-jar-with-dependencies.jar` (ex.: `ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar`).

Observações:
- `LIMIT_REPOS=1` para Lab02S01 (teste inicial e entrega parcial).
- `LIMIT_REPOS=1000` para Lab02S02/final.

## Como rodar (ordem correta)

Entre na pasta `lab02` e **ative o ambiente virtual** (`.venv`) conforme a seção acima.

```powershell
cd C:\Users\JOAOPEDRO\Documents\GitHub\Lab-exp-de-software\lab02
.venv\Scripts\Activate.ps1
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

- **`Colunas CBO/DIT/LCOM não encontradas` ou `class.csv sem linhas`**
  - O primeiro repositório da lista (`Snailclimb/JavaGuide`) é em grande parte **conteúdo de estudo** (Markdown etc.), com **pouco ou nenhum código Java** analisável. O CK pode gerar `class.csv` só com cabeçalho.
  - **Solução**: no `.env`, use `LIMIT_REPOS=1` mas **pule manualmente** esse repo alterando o `repos_java_1000.csv` (remova a primeira linha de dados) **ou** aumente `LIMIT_REPOS` e processe vários até achar um com Java real; ou edite o CSV para colocar no topo um projeto Maven/Gradle com `src/main/java`.

- **`401 Bad credentials` em `coletor_java.py`**
  - Token inválido/expirado no `.env`. Gere um novo PAT e reinicie o terminal.

- **`java não é reconhecido`**
  - Java não está no PATH. Configure `JAVA_HOME` e `%JAVA_HOME%\bin`.

- **`Nenhum repositório com status=ok` em `analise_lab02.py`**
  - O `pipeline_qualidade.py` falhou para todos os repositórios. Verifique coluna `erro` em `repos_java_quality.csv`.

- **Erro de clone: pasta já existe**
  - Apague `clones_java` e `ck_output` e rode o pipeline novamente.

- **`Filename too long` / `unable to create file ...` no clone (Windows)**
  - Repositórios grandes (ex.: Spring Boot) têm caminhos muito longos. O script já usa `git -c core.longpaths=true clone`.
  - Se ainda falhar, rode uma vez no seu usuário:
    ```powershell
    git config --global core.longpaths true
    ```
  - No Windows 10/11, em **Política de grupo** ou **Editor de Registro**, também existe a opção “Habilitar caminhos longos” (opcional).

## Entregáveis esperados

### Lab02S01
- `repos_java_1000.csv`
- `repos_java_quality.csv` com pelo menos 1 repositório com `status=ok`

### Lab02S02 / Final
- `repos_java_quality.csv` (amostra completa ou máxima possível)
- `correlacoes_lab02.csv`
- gráficos `grafico_*.png`
- relatório final com hipóteses, metodologia, resultados e discussão
