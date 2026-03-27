import os
import csv
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# Configuração do experimento (Lab02S01 / Lab02S02)
TOTAL_REPOS = 1000
REPOS_POR_PAGINA = 10  # menor = mais estável contra 502
ESPERA_ENTRE_PAGINAS_SEG = 0.02

OUTPUT_CSV = "repos_java_1000.csv"
OUTPUT_JSON = "repos_java_1000.json"


def carregar_token() -> str:
    load_dotenv()
    token = os.getenv("API_TOKEN")
    if not token:
        raise RuntimeError("Variável de ambiente API_TOKEN não encontrada. Verifique o arquivo .env em lab02.")
    return token


def montar_query() -> str:
    # Busca top-1000 Java por estrelas.
    # Observação: GraphQL search usa qualifiers como no GitHub Search (ex.: language:Java).
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
              stargazerCount
              releases { totalCount }
              primaryLanguage { name }
            }
          }
        }
      }
    }
    """


def post_graphql_com_retry(headers: dict, payload: dict, max_tentativas: int = 6) -> requests.Response:
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

    raise RuntimeError("Falha após múltiplas tentativas (502/timeout). Tente novamente mais tarde.")


def buscar_repositorios_java(total: int = TOTAL_REPOS, por_pagina: int = REPOS_POR_PAGINA) -> list[dict]:
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
    repos: list[dict] = []
    cursor: str | None = None

    pagina = 0
    while len(repos) < total:
        pagina += 1
        quantidade = min(por_pagina, total - len(repos))

        variables = {
            "queryString": "language:Java stars:>0 sort:stars-desc",
            "first": quantidade,
            "after": cursor,
        }

        response = post_graphql_com_retry(headers, {"query": query, "variables": variables})
        data = response.json()

        if "errors" in data:
            raise RuntimeError(f"Erro(s) GraphQL: {data['errors']}")

        search_info = data.get("data", {}).get("search", {})
        edges = search_info.get("edges", [])

        for edge in edges:
            node = edge.get("node")
            if node:
                repos.append(node)

        page_info = search_info.get("pageInfo") or {}
        has_next = page_info.get("hasNextPage")
        cursor = page_info.get("endCursor")

        print(f"  Página {pagina}: {len(repos)}/{total}")

        if not has_next or not cursor or len(repos) >= total:
            break

        time.sleep(ESPERA_ENTRE_PAGINAS_SEG)

    return repos[:total]


def salvar_csv(repos: list[dict], caminho: str = OUTPUT_CSV) -> None:
    agora = datetime.now(timezone.utc)

    fieldnames = [
        "nameWithOwner",
        "url",
        "createdAt",
        "updatedAt",
        "stars",
        "releases_total",
        "repo_age_years",
        "primaryLanguage",
    ]

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for repo in repos:
            created_at = repo.get("createdAt")
            repo_age_years = ""

            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                repo_age_years = (agora - dt).days / 365.0

            lang = (repo.get("primaryLanguage") or {}).get("name")

            writer.writerow(
                {
                    "nameWithOwner": repo.get("nameWithOwner"),
                    "url": repo.get("url"),
                    "createdAt": created_at,
                    "updatedAt": repo.get("updatedAt"),
                    "stars": repo.get("stargazerCount", 0),
                    "releases_total": (repo.get("releases") or {}).get("totalCount", 0),
                    "repo_age_years": repo_age_years,
                    "primaryLanguage": lang or "Java",
                }
            )


def salvar_json(repos: list[dict], caminho: str = OUTPUT_JSON) -> None:
    import json

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)


def main() -> None:
    print("Lab02S01 — Coletando top-1000 repositórios Java (GraphQL)...")
    repos = buscar_repositorios_java(total=TOTAL_REPOS, por_pagina=REPOS_POR_PAGINA)
    salvar_json(repos)
    salvar_csv(repos)
    print(f"OK. Gerados: {OUTPUT_JSON} e {OUTPUT_CSV} ({len(repos)} repos).")


if __name__ == "__main__":
    main()

