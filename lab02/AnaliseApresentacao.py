import os
import math
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr


ARQUIVO_CSV = "repos_java_quality.csv"
REPO_DESTAQUE = "spring-projects/spring-boot"


LABELS = {
    "stars": "Popularidade (estrelas)",
    "repo_age_years": "Maturidade (idade em anos)",
    "releases_total": "Atividade (total de releases)",
    "loc": "Tamanho (linhas de código - LOC)",
    "comment_lines": "Tamanho (linhas de comentários)",
    "cbo_mean": "CBO (média)",
    "cbo_median": "CBO (mediana)",
    "cbo_std": "CBO (desvio padrão)",
    "dit_mean": "DIT (média)",
    "dit_median": "DIT (mediana)",
    "dit_std": "DIT (desvio padrão)",
    "lcom_mean": "LCOM (média)",
    "lcom_median": "LCOM (mediana)",
    "lcom_std": "LCOM (desvio padrão)",
}


PROCESSO_KEYS = [
    "stars",
    "repo_age_years",
    "releases_total",
    "loc",
    "comment_lines",
]

QUALIDADE_KEYS = [
    "cbo_median",
    "dit_median",
    "lcom_median",
]

QUALIDADE_KEYS_COMPLETA = [
    "cbo_mean", "cbo_median", "cbo_std",
    "dit_mean", "dit_median", "dit_std",
    "lcom_mean", "lcom_median", "lcom_std",
]


def carregar_dados(caminho_csv: str) -> pd.DataFrame:
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")

    df = pd.read_csv(caminho_csv)

    if "status" not in df.columns:
        raise RuntimeError("A coluna 'status' não foi encontrada no CSV.")

    df = df[df["status"].astype(str).str.lower() == "ok"].copy()

    colunas_numericas = [
        "stars", "releases_total", "repo_age_years", "loc", "comment_lines",
        "cbo_mean", "cbo_median", "cbo_std",
        "dit_mean", "dit_median", "dit_std",
        "lcom_mean", "lcom_median", "lcom_std",
    ]

    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def estatisticas_descritivas(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    linhas = []

    for col in colunas:
        if col not in df.columns:
            continue

        serie = df[col].dropna()
        if len(serie) == 0:
            continue

        linhas.append({
            "metrica": col,
            "media": float(serie.mean()),
            "mediana": float(serie.median()),
            "desvio_padrao": float(serie.std(ddof=1)) if len(serie) > 1 else 0.0,
            "min": float(serie.min()),
            "max": float(serie.max()),
            "n": int(len(serie)),
        })

    return pd.DataFrame(linhas)


def correlacao(df: pd.DataFrame, x_col: str, y_col: str) -> dict:
    dados = df[[x_col, y_col]].dropna()

    if len(dados) < 3:
        return {
            "ok": False,
            "motivo": "menos de 3 pares válidos",
            "n": len(dados),
        }

    x = dados[x_col].values
    y = dados[y_col].values

    if len(set(x)) == 1:
        return {
            "ok": False,
            "motivo": f"{x_col} constante",
            "n": len(dados),
        }

    if len(set(y)) == 1:
        return {
            "ok": False,
            "motivo": f"{y_col} constante",
            "n": len(dados),
        }

    pearson = pearsonr(x, y)
    spearman = spearmanr(x, y)

    return {
        "ok": True,
        "n": len(dados),
        "pearson_r": float(pearson.statistic),
        "pearson_p": float(pearson.pvalue),
        "spearman_rho": float(spearman.statistic),
        "spearman_p": float(spearman.pvalue),
    }


def salvar_correlacoes_csv(df: pd.DataFrame, saida="correlacoes_lab02.csv") -> None:
    relatorio = []

    for x_col in PROCESSO_KEYS:
        for y_col in QUALIDADE_KEYS:
            if x_col not in df.columns or y_col not in df.columns:
                continue

            res = correlacao(df, x_col, y_col)
            if not res["ok"]:
                relatorio.append({
                    "metrica_processo": x_col,
                    "metrica_qualidade": y_col,
                    "n": res["n"],
                    "pearson_r": "",
                    "pearson_p": "",
                    "spearman_rho": "",
                    "spearman_p": "",
                    "status": "nao_calculado",
                    "motivo": res["motivo"],
                })
            else:
                relatorio.append({
                    "metrica_processo": x_col,
                    "metrica_qualidade": y_col,
                    "n": res["n"],
                    "pearson_r": round(res["pearson_r"], 6),
                    "pearson_p": round(res["pearson_p"], 8),
                    "spearman_rho": round(res["spearman_rho"], 6),
                    "spearman_p": round(res["spearman_p"], 8),
                    "status": "ok",
                    "motivo": "",
                })

    with open(saida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "metrica_processo",
                "metrica_qualidade",
                "n",
                "pearson_r",
                "pearson_p",
                "spearman_rho",
                "spearman_p",
                "status",
                "motivo",
            ],
        )
        writer.writeheader()
        writer.writerows(relatorio)

    print(f"\nArquivo salvo: {saida}")


def mostrar_estatisticas(df: pd.DataFrame) -> None:
    print("\n=== Estatísticas descritivas das métricas de processo ===")
    stats_processo = estatisticas_descritivas(df, PROCESSO_KEYS)
    if not stats_processo.empty:
        for _, row in stats_processo.iterrows():
            print(
                f"{row['metrica']}: média={row['media']:.4f} | "
                f"mediana={row['mediana']:.4f} | "
                f"desvio={row['desvio_padrao']:.4f} | n={int(row['n'])}"
            )

    print("\n=== Estatísticas descritivas das métricas de qualidade ===")
    stats_qualidade = estatisticas_descritivas(df, QUALIDADE_KEYS_COMPLETA)
    if not stats_qualidade.empty:
        for _, row in stats_qualidade.iterrows():
            print(
                f"{row['metrica']}: média={row['media']:.4f} | "
                f"mediana={row['mediana']:.4f} | "
                f"desvio={row['desvio_padrao']:.4f} | n={int(row['n'])}"
            )


def grafico_barras_repositorio_destaque(df: pd.DataFrame, repo_nome: str) -> None:
    destaque = df[df["nameWithOwner"] == repo_nome].copy()

    if destaque.empty:
        print(f"\n[AVISO] Repositório de destaque não encontrado: {repo_nome}")
        return

    destaque = destaque.iloc[0]

    metricas = ["cbo_median", "dit_median", "lcom_median"]
    valores = [destaque[m] for m in metricas if m in destaque.index]

    plt.figure(figsize=(8, 5))
    plt.bar(
        [LABELS[m] for m in metricas],
        valores
    )
    plt.title(f"Métricas de qualidade do repositório em destaque\n{repo_nome}")
    plt.ylabel("Valor")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.show()


def grafico_processo_vs_qualidade(df: pd.DataFrame, x_col: str, y_col: str, repo_nome: str) -> None:
    dados = df[[x_col, y_col, "nameWithOwner"]].dropna().copy()
    if dados.empty:
        return

    plt.figure(figsize=(8, 5))
    plt.scatter(dados[x_col], dados[y_col], alpha=0.65)

    destaque = dados[dados["nameWithOwner"] == repo_nome]
    if not destaque.empty:
        dx = destaque.iloc[0][x_col]
        dy = destaque.iloc[0][y_col]
        plt.scatter([dx], [dy], s=140)
        plt.annotate(
            repo_nome,
            (dx, dy),
            textcoords="offset points",
            xytext=(8, 8)
        )

    titulo = f"{LABELS.get(x_col, x_col)} vs {LABELS.get(y_col, y_col)}"
    plt.title(titulo)
    plt.xlabel(LABELS.get(x_col, x_col))
    plt.ylabel(LABELS.get(y_col, y_col))
    plt.tight_layout()
    plt.show()


def grafico_histograma(df: pd.DataFrame, coluna: str, repo_nome: str) -> None:
    serie = df[coluna].dropna()
    if serie.empty:
        return

    plt.figure(figsize=(8, 5))
    plt.hist(serie, bins=20, edgecolor="black")
    plt.title(f"Distribuição de {LABELS.get(coluna, coluna)}")
    plt.xlabel(LABELS.get(coluna, coluna))
    plt.ylabel("Frequência")

    destaque = df[df["nameWithOwner"] == repo_nome]
    if not destaque.empty and pd.notna(destaque.iloc[0][coluna]):
        valor = destaque.iloc[0][coluna]
        plt.axvline(valor, linestyle="--", linewidth=2)
        plt.annotate(
            f"Spring Boot = {valor:.2f}",
            (valor, 1),
            textcoords="offset points",
            xytext=(8, 8)
        )

    plt.tight_layout()
    plt.show()


def grafico_boxplot(df: pd.DataFrame, coluna: str, repo_nome: str) -> None:
    serie = df[coluna].dropna()
    if serie.empty:
        return

    plt.figure(figsize=(8, 4.5))
    plt.boxplot(serie, vert=False)
    plt.title(f"Boxplot de {LABELS.get(coluna, coluna)}")
    plt.xlabel(LABELS.get(coluna, coluna))

    destaque = df[df["nameWithOwner"] == repo_nome]
    if not destaque.empty and pd.notna(destaque.iloc[0][coluna]):
        valor = destaque.iloc[0][coluna]
        plt.axvline(valor, linestyle="--", linewidth=2)

    plt.tight_layout()
    plt.show()


def matriz_correlacao(df: pd.DataFrame) -> None:
    colunas = [
        "stars", "repo_age_years", "releases_total", "loc", "comment_lines",
        "cbo_median", "dit_median", "lcom_median"
    ]

    disponiveis = [c for c in colunas if c in df.columns]
    dados = df[disponiveis].dropna()

    if dados.empty or len(dados) < 2:
        print("\n[AVISO] Dados insuficientes para matriz de correlação.")
        return

    corr = dados.corr(numeric_only=True)

    plt.figure(figsize=(10, 8))
    plt.imshow(corr, interpolation="nearest", aspect="auto")
    plt.colorbar()
    plt.xticks(range(len(disponiveis)), [LABELS.get(c, c) for c in disponiveis], rotation=45, ha="right")
    plt.yticks(range(len(disponiveis)), [LABELS.get(c, c) for c in disponiveis])

    for i in range(len(disponiveis)):
        for j in range(len(disponiveis)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")

    plt.title("Matriz de correlação entre métricas")
    plt.tight_layout()
    plt.show()


def mostrar_resultados_correlacao(df: pd.DataFrame) -> None:
    print("\n=== Correlações das questões de pesquisa ===")
    for x_col in PROCESSO_KEYS:
        for y_col in QUALIDADE_KEYS:
            if x_col not in df.columns or y_col not in df.columns:
                continue

            res = correlacao(df, x_col, y_col)

            if not res["ok"]:
                print(
                    f"{x_col} x {y_col}: não foi possível calcular "
                    f"(n={res['n']}, motivo: {res['motivo']})"
                )
            else:
                print(
                    f"{x_col} x {y_col} (n={res['n']}): "
                    f"Pearson r={res['pearson_r']:.4f} (p={res['pearson_p']:.4g}) | "
                    f"Spearman rho={res['spearman_rho']:.4f} (p={res['spearman_p']:.4g})"
                )


def main():
    df = carregar_dados(ARQUIVO_CSV)

    if df.empty:
        raise RuntimeError("Nenhum repositório com status=ok foi encontrado no CSV.")

    print(f"Total de repositórios válidos: {len(df)}")

    mostrar_estatisticas(df)
    mostrar_resultados_correlacao(df)
    salvar_correlacoes_csv(df)

    # Gráfico do repositório em destaque
    grafico_barras_repositorio_destaque(df, REPO_DESTAQUE)

    # Histogramas das métricas de qualidade
    for col in ["cbo_median", "dit_median", "lcom_median"]:
        grafico_histograma(df, col, REPO_DESTAQUE)

    # Boxplots das métricas de qualidade
    for col in ["cbo_median", "dit_median", "lcom_median"]:
        grafico_boxplot(df, col, REPO_DESTAQUE)

    # Todas as relações processo x qualidade
    for x_col in PROCESSO_KEYS:
        for y_col in QUALIDADE_KEYS:
            grafico_processo_vs_qualidade(df, x_col, y_col, REPO_DESTAQUE)

    # Matriz de correlação geral
    matriz_correlacao(df)


if __name__ == "__main__":
    main()