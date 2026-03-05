import sys
import csv
from datetime import datetime, timezone
from config import ARQUIVO_CSV
from coletor import buscar_repositorios
# from analise import analisar_resultados
from visualizacao import analisar_visualizacao

def salvar_csv(repositorios: list[dict]):
    """
    Processa os dados coletados e calcula as métricas para todas as RQs:
    RQ 01: Idade do Repo
    RQ 02: PRs Mergeados
    RQ 03: Total de Releases
    RQ 04: Tempo até a última atualização
    RQ 05: Linguagem Primária
    RQ 06: Razão de Issues Fechadas
    """
    agora = datetime.now(timezone.utc)
    
    # Cabeçalho atualizado com as novas métricas
    colunas = [
        "nameWithOwner", "repo_age_days", "primaryLanguage",
        "merged_pull_requests", "releases_total", "stargazers",
        "last_update_days", "closed_issues_ratio"
    ]

    print(f"Salvando dados em {ARQUIVO_CSV}...")

    with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        
        for repo in repositorios:
            # --- RQ 01: Idade ---
            created_at = repo.get("createdAt", "")
            age_days = ""
            if created_at:
                try:
                    dt_cr = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    age_days = (agora - dt_cr).days
                except: pass

            # --- RQ 04: Tempo até última atualização ---
            updated_at = repo.get("updatedAt", "")
            last_update_days = ""
            if updated_at:
                try:
                    dt_up = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    last_update_days = (agora - dt_up).days
                except: pass

            # --- RQ 06: Razão de Issues Fechadas ---
            issues_info = repo.get("issues") or {}
            closed_info = repo.get("closedIssues") or {}
            
            total_issues = issues_info.get("totalCount", 0)
            closed_issues = closed_info.get("totalCount", 0)
            
            # Cálculo da razão (evitando divisão por zero)
            ratio = 0.0
            if total_issues > 0:
                ratio = closed_issues / total_issues

            writer.writerow({
                "nameWithOwner": repo.get("nameWithOwner"),
                "repo_age_days": age_days,
                "primaryLanguage": (repo.get("primaryLanguage") or {}).get("name") or "None",
                "merged_pull_requests": (repo.get("pullRequests") or {}).get("totalCount", 0),
                "releases_total": (repo.get("releases") or {}).get("totalCount", 0),
                "stargazers": repo.get("stargazerCount", 0),
                "last_update_days": last_update_days,
                "closed_issues_ratio": round(ratio, 4) # Arredondado para 4 casas
            })

def exibir_menu():
    print("\n" + "="*40)
    print("   MINERAÇÃO DE REPOSITÓRIOS GITHUB   ")
    print("="*40)
    print("[1] Coletar 1.000 Repositórios (API)")
    print("[2] Analisar Dados Locais (RQs 01 a 06)")
    print("[3] Fluxo Completo (Coletar + Analisar)")
    print("[0] Sair")
    print("="*40)

def main():
    while True:
        exibir_menu()
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            print("\nConectando à API do GitHub...")
            dados = buscar_repositorios(1000)
            if dados:
                salvar_csv(dados)
                print(f"\n[OK] Arquivo {ARQUIVO_CSV} gerado com sucesso.")

        elif opcao == "2":
            print("\nLendo arquivo CSV e gerando estatísticas...")
            analisar_visualizacao(ARQUIVO_CSV)

        elif opcao == "3":
            print("\nIniciando execução completa...")
            dados = buscar_repositorios(1000)
            if dados:
                salvar_csv(dados)
                analisar_visualizacao(ARQUIVO_CSV)

        elif opcao == "0":
            print("Encerrando programa. Até logo!")
            break

        else:
            print("\n[!] Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()