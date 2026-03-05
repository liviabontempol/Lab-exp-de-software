import os
from dotenv import load_dotenv

load_dotenv()

# Autenticação e Endpoints
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
API_TOKEN = os.getenv("API_TOKEN")

# Parâmetros de Performance e Coleta
REPOS_POR_PAGINA = 10 # Menor valor = mais estabilidade contra erro 502
ESPERA_ENTRE_PAGINAS_SEG = 0.02
TOTAL_REPOS_PESQUISA = 1000  # Centraliza o limite exigido pelo trabalho

# Nomes de Arquivos de Saída
ARQUIVO_CSV = "repositorios_populares_1000.csv"
ARQUIVO_JSON = "repositorios_populares.json"

# Configurações de análise (Opcional)
TOP_LANGUAGES_COUNT = 5 # Quantidade de linguagens no ranking da RQ 05