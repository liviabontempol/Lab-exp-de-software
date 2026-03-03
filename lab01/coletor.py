import time
import requests
from config import GITHUB_GRAPHQL_URL, API_TOKEN, REPOS_POR_PAGINA, ESPERA_ENTRE_PAGINAS_SEG

def montar_query() -> str:
    """Retorna a query GraphQL com todos os campos necessários para as RQs."""
    return """
    query($queryString: String!, $first: Int!, $after: String) {
      search(query: $queryString, type: REPOSITORY, first: $first, after: $after) {
        pageInfo { hasNextPage endCursor }
        edges {
          node {
            ... on Repository {
              nameWithOwner 
              url 
              createdAt 
              updatedAt
              primaryLanguage { name }
              issues { totalCount }
              closedIssues: issues(states: CLOSED) { totalCount }
              pullRequests(states: MERGED) { totalCount }
              releases { totalCount }
              stargazerCount 
              forkCount
            }
          }
        }
      }
    }
    """

def buscar_repositorios(total: int) -> list[dict]:
    if not API_TOKEN:
        raise RuntimeError("API_TOKEN não encontrado. Verifique seu arquivo .env")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    query = montar_query()
    repositorios = []
    cursor = None
    tentativas_erro = 0
    max_tentativas = 5

    while len(repositorios) < total:
        quantidade = min(REPOS_POR_PAGINA, total - len(repositorios))
        variables = {
            "queryString": "stars:>0 sort:stars-desc",
            "first": quantidade,
            "after": cursor,
        }

        try:
            response = requests.post(
                GITHUB_GRAPHQL_URL, 
                json={"query": query, "variables": variables}, 
                headers=headers, 
                timeout=30
            )

            # Tratamento de Erros de Rede/API
            if response.status_code != 200:
                tentativas_erro += 1
                espera = tentativas_erro * 10 # Espera 10s, 20s, 30s...
                print(f"\n[!] Erro {response.status_code}. Tentativa {tentativas_erro}/{max_tentativas}. "
                      f"Aguardando {espera}s...")
                
                if tentativas_erro >= max_tentativas:
                    print("Critico: Limite de tentativas atingido. Salvando o que foi coletado até agora.")
                    break
                
                time.sleep(espera)
                continue

            data = response.json()
            
            # Verifica se há erros retornados pelo GraphQL (ex: query malformada)
            if "errors" in data:
                print(f"\n[ERRO GraphQL]: {data['errors'][0].get('message')}")
                break

            search_info = data.get("data", {}).get("search", {})
            edges = search_info.get("edges", [])

            for edge in edges:
                node = edge.get("node")
                if node:
                    repositorios.append(node)

            # Paginação
            page_info = search_info.get("pageInfo", {})
            if not page_info.get("hasNextPage") or len(repositorios) >= total:
                break
            
            cursor = page_info.get("endCursor")
            tentativas_erro = 0 # Reseta erros se a página foi baixada com sucesso
            
            print(f"-> Coletados: {len(repositorios)}/{total}...", end="\r")
            time.sleep(ESPERA_ENTRE_PAGINAS_SEG)

        except requests.exceptions.RequestException as e:
            print(f"\n[Falha de Conexão]: {e}. Tentando novamente em 10s...")
            time.sleep(10)

    print(f"\n[FIM] Coleta concluída com {len(repositorios)} repositórios.")
    return repositorios