import os
from dotenv import load_dotenv

load_dotenv()

# API GitHub
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
API_TOKEN = os.getenv("API_TOKEN")

# Coleta dos repositórios Java
TOTAL_REPOS = 1000
REPOS_POR_PAGINA = 10
ESPERA_ENTRE_PAGINAS_SEG = 0.02
QUERY_STRING = "language:Java stars:>0 sort:stars-desc"

# Arquivos de saída da coleta (S01/S02)
REPOS_JSON = "repos_java_1000.json"
REPOS_CSV = "repos_java_1000.csv"

# CK + clone + tamanho
CK_JAR_PATH = os.getenv("CK_JAR_PATH", "ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar")
WORKDIR_CLONES = "clones_java"
WORKDIR_CK_OUTPUT = "ck_output"
QUALITY_CSV = "repos_java_quality.csv"

# Limites de execução do pipeline
# Para S01, pode rodar com LIMIT_REPOS=1. Para S02, LIMIT_REPOS=1000.
LIMIT_REPOS = int(os.getenv("LIMIT_REPOS", "1"))
