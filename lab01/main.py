import os
import json
import csv
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Configuração
# -----------------------------------------------------------------------------
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# Quantidade de repositórios por requisição (menor = menos 502).
REPOS_POR_PAGINA = 10
# Pausa entre páginas (segundos), para não sobrecarregar a API.
ESPERA_ENTRE_PAGINAS_SEG = 0.02


def carregar_token() -> str:
    """Carrega o token do GitHub a partir do arquivo .env."""
    load_dotenv()
    token = os.getenv("API_TOKEN")
    if not token:
        raise RuntimeError(
            "Variável de ambiente API_TOKEN não encontrada. Verifique seu arquivo .env."
        )
    return token


def montar_query() -> str:
    """Retorna a query GraphQL para busca de repositórios (com paginação)."""
    return """
    query($queryString: String!, $first: Int!, $after: String) {
      search(query: $queryString, type: REPOSITORY, first: $first, after: $after) {
        repositoryCount
        pageInfo {
          hasNextPage
          endCursor
        }
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


def post_graphql_com_retry(
    headers: dict, payload: dict, max_tentativas: int = 6
) -> requests.Response:
    """Faz requisição POST à API GraphQL com retry em caso de 502/503/504 ou timeout."""
    espera = 1
    for tentativa in range(1, max_tentativas + 1):
        try:
            resp = requests.post(
                GITHUB_GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                return resp
            if resp.status_code in (502, 503, 504):
                print(
                    f"  [WARN] HTTP {resp.status_code} (tentativa {tentativa}/{max_tentativas}). "
                    f"Aguardando {espera}s..."
                )
                time.sleep(espera)
                espera = min(espera * 2, 20)
                continue
            raise RuntimeError(f"Falha GraphQL ({resp.status_code}): {resp.text}")
        except requests.exceptions.Timeout:
            print(
                f"  [WARN] Timeout (tentativa {tentativa}/{max_tentativas}). "
                f"Aguardando {espera}s..."
            )
            time.sleep(espera)
            espera = min(espera * 2, 20)
    raise RuntimeError(
        "Falha após múltiplas tentativas (502/timeout). Tente novamente mais tarde."
    )


def buscar_repositorios_paginado(
    total: int, por_pagina: int | None = None
) -> list[dict]:
    """
    Busca até `total` repositórios populares (ordenados por estrelas) com paginação.
    Usada tanto para os 100 (Lab01S01) quanto para os 1.000 (Lab01S02).
    Retorna lista de nós (dict) de cada repositório.
    """
    if por_pagina is None:
        por_pagina = REPOS_POR_PAGINA
    if total <= 0:
        raise ValueError("total deve ser positivo.")
    if por_pagina <= 0 or por_pagina > 100:
        raise ValueError("por_pagina deve estar entre 1 e 100.")

    token = carregar_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    query = montar_query()

    repositorios: list[dict] = []
    cursor: str | None = None
    pagina = 0

    while len(repositorios) < total:
        pagina += 1
        quantidade = min(por_pagina, total - len(repositorios))
        variables = {
            "queryString": "stars:>0 sort:stars-desc",
            "first": quantidade,
            "after": cursor,
        }

        response = post_graphql_com_retry(
            headers, {"query": query, "variables": variables}
        )
        data = response.json()

        if "errors" in data:
            raise RuntimeError(f"Erro(s) GraphQL: {data['errors']}")

        search_info = data.get("data", {}).get("search", {})
        edges = search_info.get("edges", [])

        for edge in edges:
            node = edge.get("node")
            if node:
                repositorios.append(node)

        page_info = search_info.get("pageInfo") or {}
        has_next = page_info.get("hasNextPage")
        cursor = page_info.get("endCursor")

        print(f"  Página {pagina}: {len(repositorios)}/{total} repositórios")

        if not has_next or not cursor or len(repositorios) >= total:
            break

        time.sleep(ESPERA_ENTRE_PAGINAS_SEG)

    return repositorios[:total]


def dados_graphql_de_lista(repositorios: list[dict]) -> dict:
    """Monta a estrutura no formato da resposta GraphQL (data.search.edges) a partir da lista de nós."""
    edges = [{"node": r} for r in repositorios]
    return {
        "data": {
            "search": {
                "repositoryCount": len(repositorios),
                "edges": edges,
            }
        }
    }


def salvar_json(dados: dict, caminho: str) -> None:
    """Salva o resultado no formato GraphQL em JSON."""
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def salvar_csv(repositorios: list[dict], caminho: str) -> None:
    """Salva as métricas das RQs em CSV."""
    colunas = [
        "nameWithOwner", "url", "createdAt", "updatedAt",
        "repo_age_days", "last_update_days_ago", "primaryLanguage",
        "issues_total", "closed_issues_total", "closed_issues_ratio",
        "merged_pull_requests", "releases_total", "stargazers", "forks",
    ]
    agora = datetime.now(timezone.utc)

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()

        for repo in repositorios:
            created_at = repo.get("createdAt")
            updated_at = repo.get("updatedAt")
            repo_age_days = ""
            last_update_days_ago = ""

            if created_at:
                try:
                    dt = datetime.strptime(
                        created_at.replace("Z", "+00:00")[:19],
                        "%Y-%m-%dT%H:%M:%S",
                    ).replace(tzinfo=timezone.utc)
                    repo_age_days = (agora - dt).days
                except (ValueError, TypeError):
                    pass
            if updated_at:
                try:
                    dt = datetime.strptime(
                        updated_at.replace("Z", "+00:00")[:19],
                        "%Y-%m-%dT%H:%M:%S",
                    ).replace(tzinfo=timezone.utc)
                    last_update_days_ago = (agora - dt).days
                except (ValueError, TypeError):
                    pass

            lang = (repo.get("primaryLanguage") or {}).get("name")
            issues_total = (repo.get("issues") or {}).get("totalCount", 0)
            closed_total = (repo.get("closedIssues") or {}).get("totalCount", 0)
            closed_ratio = ""
            if issues_total and issues_total > 0:
                closed_ratio = closed_total / issues_total

            writer.writerow({
                "nameWithOwner": repo.get("nameWithOwner"),
                "url": repo.get("url"),
                "createdAt": created_at,
                "updatedAt": updated_at,
                "repo_age_days": repo_age_days,
                "last_update_days_ago": last_update_days_ago,
                "primaryLanguage": lang,
                "issues_total": issues_total,
                "closed_issues_total": closed_total,
                "closed_issues_ratio": closed_ratio,
                "merged_pull_requests": (repo.get("pullRequests") or {}).get("totalCount", 0),
                "releases_total": (repo.get("releases") or {}).get("totalCount", 0),
                "stargazers": repo.get("stargazerCount", 0),
                "forks": repo.get("forkCount", 0),
            })


def mostrar_amostra(repositorios: list[dict], quantidade: int = 5) -> None:
    """Exibe no terminal uma amostra dos repositórios (nome, estrelas, linguagem)."""
    for idx, repo in enumerate(repositorios[:quantidade], start=1):
        nome = repo.get("nameWithOwner", "?")
        estrelas = repo.get("stargazerCount", 0)
        lang = (repo.get("primaryLanguage") or {}).get("name") or "—"
        print(f"  {idx}. {nome} — estrelas: {estrelas} — linguagem: {lang}")


def main() -> None:
    # Lab01S01: 100 repositórios (paginado), salva JSON e mostra amostra
    print("Lab01S01 — Buscando 100 repositórios populares (paginado)...")
    repos_100 = buscar_repositorios_paginado(100)
    dados_100 = dados_graphql_de_lista(repos_100)
    salvar_json(dados_100, "repositorios_populares.json")
    print(f"Total (100): {len(repos_100)} repositórios. Amostra (5 primeiros):")
    mostrar_amostra(repos_100, 5)

    # Lab01S02: 1.000 repositórios (paginado), salva CSV
    print("\nLab01S02 — Buscando 1.000 repositórios populares (paginado)...")
    repos_1000 = buscar_repositorios_paginado(1000)
    salvar_csv(repos_1000, "repositorios_populares_1000.csv")
    print(f"Total (1000): {len(repos_1000)} repositórios.")
    print("Arquivos gerados: repositorios_populares.json, repositorios_populares_1000.csv")


if __name__ == "__main__":
    main()
