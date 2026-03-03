import csv
import statistics
from config import ARQUIVO_CSV 

def analisar_resultados(caminho_csv: str):
    idades, prs, releases, updates, ratios = [], [], [], [], []
    linguagens = {}

    try:
        with open(caminho_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Verificamos se a chave existe E se tem valor antes de converter
                if row.get('repo_age_days'):
                    idades.append(int(row['repo_age_days']))
                if row.get('merged_pull_requests'):
                    prs.append(int(row['merged_pull_requests']))
                if row.get('releases_total'):
                    releases.append(int(row['releases_total']))
                if row.get('last_update_days'):
                    updates.append(int(row['last_update_days']))
                if row.get('closed_issues_ratio'):
                    ratios.append(float(row['closed_issues_ratio']))
                
                lang = row.get('primaryLanguage') or "Não Informada"
                linguagens[lang] = linguagens.get(lang, 0) + 1

        print("\n" + "="*60)
        print("          RELATÓRIO FINAL: ANÁLISE DE SISTEMAS POPULARES")
        print("="*60)
        
        # Função auxiliar para evitar o erro de lista vazia
        def imprimir_mediana(label, lista, sufixo=""):
            if lista:
                print(f"{label}: Mediana = {statistics.median(lista):.2f}{sufixo}")
            else:
                print(f"{label}: [SEM DADOS NO CSV]")

        imprimir_mediana("RQ 01 (Idade)", idades, " dias")
        imprimir_mediana("RQ 02 (PRs Mergeados)", prs)
        imprimir_mediana("RQ 03 (Total Releases)", releases)
        imprimir_mediana("RQ 04 (Tempo de Atualização)", updates, " dias")
        
        if ratios:
            print(f"RQ 06 (Razão Issues Fechadas): Mediana = {statistics.median(ratios)*100:.2f}%")
        else:
            print("RQ 06 (Razão Issues Fechadas): [SEM DADOS NO CSV]")
        
        print("\nRQ 05: Top 5 Linguagens Mais Populares")
        ranking = sorted(linguagens.items(), key=lambda x: x[1], reverse=True)
        for i, (lang, total) in enumerate(ranking[:5], 1):
            print(f"  {i}. {lang}: {total} repositórios")
            
        print("="*60)

    except FileNotFoundError:
        print(f"ERRO: O arquivo '{caminho_csv}' não existe.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    analisar_resultados(ARQUIVO_CSV)