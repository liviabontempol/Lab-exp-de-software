import csv
import json
import statistics
import base64
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from config import ARQUIVO_CSV

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    MATPLOTLIB_DISPONIVEL = True
except ImportError:
    MATPLOTLIB_DISPONIVEL = False


def _to_int(value: str) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        number = int(value)
        return number if number >= 0 else None
    except (TypeError, ValueError):
        return None


def _to_float(value: str) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_rows(csv_path: str) -> List[Dict]:
    rows: List[Dict] = []
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for raw in reader:
            ratio = _to_float(raw.get("closed_issues_ratio"))
            row = {
                "name": raw.get("nameWithOwner", ""),
                "age_days": _to_int(raw.get("repo_age_days")),
                "merged_prs": _to_int(raw.get("merged_pull_requests")),
                "releases": _to_int(raw.get("releases_total")),
                "last_update_days": _to_int(raw.get("last_update_days")),
                "closed_issues_ratio": ratio if ratio is not None and 0.0 <= ratio <= 1.0 else None,
                "language": raw.get("primaryLanguage") or "Não Informada",
            }
            rows.append(row)
    return rows


def _series(rows: List[Dict], key: str) -> List[float]:
    return [row[key] for row in rows if row.get(key) is not None]


def _language_breakdown(rows: List[Dict]) -> Dict[str, int]:
    ranking: Dict[str, int] = {}
    for row in rows:
        lang = row["language"]
        ranking[lang] = ranking.get(lang, 0) + 1
    return ranking


def _print_terminal_report(medianas: Dict[str, float], languages: Dict[str, int], total_repos: int):
    print("\n" + "=" * 80)
    print(" " * 20 + "ANÁLISE DE REPOSITÓRIOS POPULARES")
    print("=" * 80)
    print(f"\nTotal de repositórios analisados: {total_repos}")
    
    print("\n" + "-" * 80)
    print("SUMARIZAÇÃO DOS DADOS (VALORES MEDIANOS)")
    print("-" * 80)
    
    print(f"\n• RQ01 - Idade dos repositórios")
    if medianas.get("age_days") is not None:
        print(f"  Mediana: {medianas['age_days']:.0f} dias ({medianas['age_days']/365:.1f} anos)")
    else:
        print("  [Sem dados]")
    
    print(f"\n• RQ02 - Total de pull requests aceitos")
    if medianas.get("merged_prs") is not None:
        print(f"  Mediana: {medianas['merged_prs']:.0f} PRs")
    else:
        print("  [Sem dados]")
    
    print(f"\n• RQ03 - Total de releases")
    if medianas.get("releases") is not None:
        print(f"  Mediana: {medianas['releases']:.0f} releases")
    else:
        print("  [Sem dados]")
    
    print(f"\n• RQ04 - Tempo desde a última atualização")
    if medianas.get("last_update_days") is not None:
        print(f"  Mediana: {medianas['last_update_days']:.0f} dias")
    else:
        print("  [Sem dados]")
    
    print(f"\n• RQ06 - Razão de issues fechadas")
    if medianas.get("closed_issues_ratio") is not None:
        print(f"  Mediana: {medianas['closed_issues_ratio']*100:.1f}%")
    else:
        print("  [Sem dados]")
    
    print("\n" + "-" * 80)
    print("RQ05 - LINGUAGENS DE PROGRAMAÇÃO MAIS POPULARES")
    print("-" * 80)
    
    total = sum(languages.values())
    ranking = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    
    print("\nTop 10 linguagens:")
    for i, (lang, count) in enumerate(ranking[:10], 1):
        pct = (count / total) * 100 if total else 0
        print(f"  {i:2d}. {lang:25s} {count:4d} repos ({pct:5.1f}%)")
    
    print("=" * 80 + "\n")


def _generate_chart_base64(rows: List[Dict], languages: Dict[str, int], medianas: Dict[str, float]) -> Dict[str, str]:
    if not MATPLOTLIB_DISPONIVEL:
        return {}
    
    charts = {}
    
    # RQ01 - histograma de idade
    ages = _series(rows, "age_days")
    if ages:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(ages, bins=30, color="#3b82f6", edgecolor="black", alpha=0.75)
        ax.axvline(medianas.get("age_days", 0), color="red", linestyle="--", linewidth=2, 
                   label=f"Mediana: {medianas.get('age_days', 0):.0f} dias")
        ax.set_title("RQ01 - Distribuição da Idade dos Repositórios", fontsize=14, fontweight="bold")
        ax.set_xlabel("Idade (dias)")
        ax.set_ylabel("Frequência")
        ax.legend()
        ax.grid(alpha=0.3)
        
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        charts["idade"] = base64.b64encode(buffer.read()).decode()
        plt.close()
    
    # RQ02 - histograma de PRs
    prs = _series(rows, "merged_prs")
    if prs:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(prs, bins=30, color="#3b82f6", edgecolor="black", alpha=0.75)
        ax.axvline(medianas.get("merged_prs", 0), color="red", linestyle="--", linewidth=2,
                   label=f"Mediana: {medianas.get('merged_prs', 0):.0f} PRs")
        ax.set_title("RQ02 - Distribuição de Pull Requests Aceitos", fontsize=14, fontweight="bold")
        ax.set_xlabel("Número de PRs Mergeados")
        ax.set_ylabel("Frequência")
        ax.legend()
        ax.grid(alpha=0.3)
        
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        charts["prs"] = base64.b64encode(buffer.read()).decode()
        plt.close()
    
    # RQ03 - histograma de releases
    releases = _series(rows, "releases")
    if releases:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(releases, bins=30, color="#3b82f6", edgecolor="black", alpha=0.75)
        ax.axvline(medianas.get("releases", 0), color="red", linestyle="--", linewidth=2,
                   label=f"Mediana: {medianas.get('releases', 0):.0f} releases")
        ax.set_title("RQ03 - Distribuição de Releases", fontsize=14, fontweight="bold")
        ax.set_xlabel("Número de Releases")
        ax.set_ylabel("Frequência")
        ax.legend()
        ax.grid(alpha=0.3)
        
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        charts["releases"] = base64.b64encode(buffer.read()).decode()
        plt.close()
    
    # RQ05 - gráfico de barras de linguagens
    if languages:
        top_langs = sorted(languages.items(), key=lambda i: i[1], reverse=True)[:10]
        labels = [lang for lang, _ in top_langs]
        values = [count for _, count in top_langs]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(labels[::-1], values[::-1], color="#3b82f6")
        ax.set_title("RQ05 - Top 10 Linguagens de Programação", fontsize=14, fontweight="bold")
        ax.set_xlabel("Número de Repositórios")
        ax.grid(axis='x', alpha=0.3)
        
        # Adiciona valores nas barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, f'{int(width)}',
                   ha='left', va='center', fontsize=9, fontweight='bold')
        
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        charts["linguagens"] = base64.b64encode(buffer.read()).decode()
        plt.close()
    
    # RQ06 - Distribuição de issues fechadas
    ratios = _series(rows, "closed_issues_ratio")
    if ratios:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist([r * 100 for r in ratios], bins=25, color="#3b82f6", edgecolor="black", alpha=0.75)
        ax.axvline(medianas.get("closed_issues_ratio", 0) * 100, color="red", linestyle="--", linewidth=2,
                   label=f"Mediana: {medianas.get('closed_issues_ratio', 0)*100:.1f}%")
        ax.set_title("RQ06 - Distribuição da Razão de Issues Fechadas", fontsize=14, fontweight="bold")
        ax.set_xlabel("Percentual de Issues Fechadas (%)")
        ax.set_ylabel("Frequência")
        ax.legend()
        ax.grid(alpha=0.3)
        
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        charts["issues"] = base64.b64encode(buffer.read()).decode()
        plt.close()
    
    return charts


def _save_html(medianas: Dict[str, float], languages: Dict[str, int], total_repos: int, charts: Dict[str, str]):
    ranking = sorted(languages.items(), key=lambda i: i[1], reverse=True)
    total = sum(languages.values())

    lang_rows = []
    for i, (lang, count) in enumerate(ranking[:15], 1):
        pct = (count / total) * 100 if total else 0
        lang_rows.append(f"<tr><td>{i}</td><td>{lang}</td><td>{count}</td><td>{pct:.1f}%</td></tr>")

    charts_html = ""
    if MATPLOTLIB_DISPONIVEL and charts:
        if "idade" in charts:
            charts_html += f"""
    <div class="chart-container">
      <img src="data:image/png;base64,{charts['idade']}" alt="Gráfico RQ01">
    </div>
"""
        
        if "prs" in charts:
            charts_html += f"""
    <div class="chart-container">
      <img src="data:image/png;base64,{charts['prs']}" alt="Gráfico RQ02">
    </div>
"""
        
        if "releases" in charts:
            charts_html += f"""
    <div class="chart-container">
      <img src="data:image/png;base64,{charts['releases']}" alt="Gráfico RQ03">
    </div>
"""
        
        if "linguagens" in charts:
            charts_html += f"""
    <div class="chart-container">
      <img src="data:image/png;base64,{charts['linguagens']}" alt="Gráfico RQ05">
    </div>
"""
        
        if "issues" in charts:
            charts_html += f"""
    <div class="chart-container">
      <img src="data:image/png;base64,{charts['issues']}" alt="Gráfico RQ06">
    </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Análise de Repositórios Populares - GitHub</title>
  </head>
<body>
  <div class="container">
    <h1>Análise de Repositórios Populares do GitHub</h1>
    
    <div class="summary">
      <p><strong>Objetivo:</strong> Estudo das principais características de sistemas open-source populares</p>
      <p><strong>Amostra:</strong> <span class="badge">{total_repos} repositórios</span></p>
      <p><strong>Método:</strong> Análise por valores medianos e contagem por categoria</p>
    </div>

    <h2> Sumarização dos Dados (Valores Medianos)</h2>
    
    <div class="metric">
      <strong>RQ01 - Sistemas populares são maduros/antigos?</strong>
      <div class="metric-value">{medianas.get('age_days', 0):.0f} dias ({medianas.get('age_days', 0)/365:.1f} anos)</div>
      <p style="margin-top: 8px; color: #6b7280;">Métrica: Idade do repositório (mediana)</p>
    </div>

    <div class="metric">
      <strong>RQ02 - Sistemas populares recebem muita contribuição externa?</strong>
      <div class="metric-value">{medianas.get('merged_prs', 0):.0f} pull requests</div>
      <p style="margin-top: 8px; color: #6b7280;">Métrica: Total de PRs aceitos (mediana)</p>
    </div>

    <div class="metric">
      <strong>RQ03 - Sistemas populares lançam releases com frequência?</strong>
      <div class="metric-value">{medianas.get('releases', 0):.0f} releases</div>
      <p style="margin-top: 8px; color: #6b7280;">Métrica: Total de releases (mediana)</p>
    </div>

    <div class="metric">
      <strong>RQ04 - Sistemas populares são atualizados com frequência?</strong>
      <div class="metric-value">{medianas.get('last_update_days', 0):.0f} dias</div>
      <p style="margin-top: 8px; color: #6b7280;">Métrica: Tempo desde última atualização (mediana)</p>
    </div>

    <div class="metric">
      <strong>RQ06 - Sistemas populares possuem alto percentual de issues fechadas?</strong>
      <div class="metric-value">{medianas.get('closed_issues_ratio', 0)*100:.1f}%</div>
      <p style="margin-top: 8px; color: #6b7280;">Métrica: Razão de issues fechadas (mediana)</p>
    </div>

    <h2>Visualizações Gráficas</h2>
    {charts_html}

    <h2>RQ05 - Linguagens de Programação Mais Populares</h2>
    <p style="margin-bottom: 15px; color: #6b7280;">Contagem por categoria (linguagem primária do repositório)</p>
    <table>
      <tr><th>#</th><th>Linguagem</th><th>Repositórios</th><th>Percentual</th></tr>
      {''.join(lang_rows)}
    </table>

    <div class="footer">
      <p><strong>Lab de Experimentação em Software</strong></p>
      <p>Relatório gerado automaticamente - Análise de 1.000 repositórios mais populares do GitHub</p>
    </div>
  </div>
</body>
</html>
"""

    with open("relatorio_visualizacao.html", "w", encoding="utf-8") as file:
        file.write(html)

    print("✓ Relatório HTML salvo em: relatorio_visualizacao.html")


def _save_json(medianas: Dict[str, float], languages: Dict[str, int]):
    payload = {
        "medianas": medianas,
        "linguagens": languages,
    }
    with open("visualizacao.json", "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    print("✓ Dados JSON salvos em: visualizacao.json")


def analisar_visualizacao(caminho_csv: str):
    try:
        rows = _load_rows(caminho_csv)
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {caminho_csv}")
        return
    except Exception as exc:
        print(f"Erro ao ler CSV: {exc}")
        return

    if not rows:
        print("Não há dados no CSV para análise.")
        return

    medianas = {}
    
    ages = _series(rows, "age_days")
    if ages:
        medianas["age_days"] = statistics.median(ages)
    
    prs = _series(rows, "merged_prs")
    if prs:
        medianas["merged_prs"] = statistics.median(prs)
    
    releases = _series(rows, "releases")
    if releases:
        medianas["releases"] = statistics.median(releases)
    
    updates = _series(rows, "last_update_days")
    if updates:
        medianas["last_update_days"] = statistics.median(updates)
    
    ratios = _series(rows, "closed_issues_ratio")
    if ratios:
        medianas["closed_issues_ratio"] = statistics.median(ratios)

    # Contagem por categoria (linguagens)
    languages = _language_breakdown(rows)

    # Exibe relatório
    _print_terminal_report(medianas, languages, len(rows))
    
    # Gera gráficos como base64
    charts = _generate_chart_base64(rows, languages, medianas)
    if charts:
        print(f"✓ {len(charts)} gráficos gerados e embutidos no HTML")
    
    # saidas
    _save_html(medianas, languages, len(rows), charts)
    _save_json(medianas, languages)


def main():
    analisar_visualizacao(ARQUIVO_CSV)


if __name__ == "__main__":
    main()
