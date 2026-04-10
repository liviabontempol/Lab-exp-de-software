import os
import csv
import math
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

ARQUIVO_CSV = "repos_java_quality.csv"
REPO_DESTAQUE = "Snailclimb/JavaGuide"

LABELS = {
    "estrelas": "Popularidade (estrelas)",
    "idade_anos": "Maturidade (idade em anos)",
    "releases": "Atividade (releases)",
    "total_classes": "Total de classes",
    "loc_total": "LOC total",
    "loc_media": "LOC médio",
    "loc_mediana": "LOC mediano",
    "total_methods": "Total de métodos",
    "cbo_media": "CBO (média)",
    "cbo_mediana": "CBO (mediana)",
    "cbo_desvio": "CBO (desvio)",
    "dit_media": "DIT (média)",
    "dit_mediana": "DIT (mediana)",
    "dit_desvio": "DIT (desvio)",
    "lcom_media": "LCOM (média)",
    "lcom_mediana": "LCOM (mediana)",
    "lcom_desvio": "LCOM (desvio)",
}

PROCESSO_KEYS = [
    "estrelas",
    "idade_anos",
    "releases",
    "loc_total",
    "loc_media",
    "loc_mediana",
    "total_classes",
    "total_methods",
]

QUALIDADE_KEYS = [
    "cbo_mediana",
    "dit_mediana",
    "lcom_mediana",
]


def to_float(x):
    try:
        if x is None or x == "":
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def load_rows(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    filtradas = []
    for r in rows:
        nova = dict(r)
        for col in PROCESSO_KEYS + [
            "cbo_media", "cbo_mediana", "cbo_desvio",
            "dit_media", "dit_mediana", "dit_desvio",
            "lcom_media", "lcom_mediana", "lcom_desvio",
        ]:
            if col in nova:
                nova[col] = to_float(nova.get(col))
        filtradas.append(nova)

    return filtradas


def series(rows, key):
    return [r[key] for r in rows if r.get(key) is not None]


def stats(values):
    if not values:
        return None, None, None

    media = sum(values) / len(values)
    ordenados = sorted(values)
    n = len(ordenados)

    if n % 2 == 1:
        mediana = ordenados[n // 2]
    else:
        mediana = (ordenados[n // 2 - 1] + ordenados[n // 2]) / 2

    if n == 1:
        desvio = 0.0
    else:
        var = sum((x - media) ** 2 for x in values) / (n - 1)
        desvio = math.sqrt(var)

    return media, mediana, desvio


def correlacao(rows, x_key, y_key):
    xs, ys = [], []

    for r in rows:
        x = r.get(x_key)
        y = r.get(y_key)
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)

    if len(xs) < 3:
        return {"ok": False, "n": len(xs), "motivo": "menos de 3 pares válidos"}

    if len(set(xs)) == 1:
        return {"ok": False, "n": len(xs), "motivo": f"{x_key} constante"}

    if len(set(ys)) == 1:
        return {"ok": False, "n": len(xs), "motivo": f"{y_key} constante"}

    p = pearsonr(xs, ys)
    s = spearmanr(xs, ys)

    return {
        "ok": True,
        "n": len(xs),
        "pearson_r": p.statistic,
        "pearson_p": p.pvalue,
        "spearman_rho": s.statistic,
        "spearman_p": s.pvalue,
    }


def encontrar_repo(rows, nome_repo):
    for r in rows:
        if r.get("nome") == nome_repo:
            return r
    return None


def mostrar_estatisticas(rows):
    print(f"\nTotal de repositórios válidos: {len(rows)}")

    print("\n=== Estatísticas descritivas ===")
    for col in PROCESSO_KEYS + [
        "cbo_media", "cbo_mediana", "cbo_desvio",
        "dit_media", "dit_mediana", "dit_desvio",
        "lcom_media", "lcom_mediana", "lcom_desvio",
    ]:
        vals = series(rows, col)
        media, mediana, desvio = stats(vals)
        if media is None:
            print(f"{col}: sem dados")
        else:
            print(
                f"{col}: média={media:.4f} | mediana={mediana:.4f} | desvio={desvio:.4f}"
            )


def mostrar_correlacoes(rows):
    print("\n=== Correlações ===")
    for x in PROCESSO_KEYS:
        for y in QUALIDADE_KEYS:
            res = correlacao(rows, x, y)
            if not res["ok"]:
                print(f"{x} x {y}: não foi possível calcular (n={res['n']}, motivo: {res['motivo']})")
            else:
                print(
                    f"{x} x {y} (n={res['n']}): "
                    f"Pearson r={res['pearson_r']:.4f} (p={res['pearson_p']:.4g}) | "
                    f"Spearman rho={res['spearman_rho']:.4f} (p={res['spearman_p']:.4g})"
                )


def grafico_barras_repo(repo):
    metricas = ["cbo_mediana", "dit_mediana", "lcom_mediana"]
    valores = [repo.get(m) for m in metricas]

    plt.figure(figsize=(8, 5))
    plt.bar([LABELS[m] for m in metricas], valores)
    plt.title(f"Métricas de qualidade - {repo['nome']}")
    plt.ylabel("Valor")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.show()


def histograma(rows, coluna, repo_destaque=None):
    valores = series(rows, coluna)
    if not valores:
        return

    plt.figure(figsize=(8, 5))
    plt.hist(valores, bins=15, edgecolor="black")
    plt.title(f"Distribuição de {LABELS.get(coluna, coluna)}")
    plt.xlabel(LABELS.get(coluna, coluna))
    plt.ylabel("Frequência")

    if repo_destaque and repo_destaque.get(coluna) is not None:
        valor = repo_destaque[coluna]
        plt.axvline(valor, linestyle="--", linewidth=2)
        plt.annotate(
            f"Destaque = {valor:.2f}",
            (valor, 1),
            textcoords="offset points",
            xytext=(8, 8),
        )

    plt.tight_layout()
    plt.show()


def boxplot(rows, coluna, repo_destaque=None):
    valores = series(rows, coluna)
    if not valores:
        return

    plt.figure(figsize=(8, 4))
    plt.boxplot(valores, vert=False)
    plt.title(f"Boxplot de {LABELS.get(coluna, coluna)}")
    plt.xlabel(LABELS.get(coluna, coluna))

    if repo_destaque and repo_destaque.get(coluna) is not None:
        plt.axvline(repo_destaque[coluna], linestyle="--", linewidth=2)

    plt.tight_layout()
    plt.show()


def dispersao(rows, x_key, y_key, repo_destaque=None):
    xs, ys = [], []
    for r in rows:
        x = r.get(x_key)
        y = r.get(y_key)
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)

    if not xs:
        return

    plt.figure(figsize=(8, 5))
    plt.scatter(xs, ys, alpha=0.65)

    if repo_destaque and repo_destaque.get(x_key) is not None and repo_destaque.get(y_key) is not None:
        dx = repo_destaque[x_key]
        dy = repo_destaque[y_key]
        plt.scatter([dx], [dy], s=140)
        plt.annotate(
            repo_destaque["nome"],
            (dx, dy),
            textcoords="offset points",
            xytext=(8, 8),
        )

    plt.title(f"{LABELS.get(x_key, x_key)} vs {LABELS.get(y_key, y_key)}")
    plt.xlabel(LABELS.get(x_key, x_key))
    plt.ylabel(LABELS.get(y_key, y_key))
    plt.tight_layout()
    plt.show()


def main():
    rows = load_rows(ARQUIVO_CSV)

    if not rows:
        raise RuntimeError("Nenhum repositório encontrado no CSV.")

    mostrar_estatisticas(rows)
    mostrar_correlacoes(rows)

    repo_destaque = encontrar_repo(rows, REPO_DESTAQUE)

    if repo_destaque:
        grafico_barras_repo(repo_destaque)

    for col in QUALIDADE_KEYS:
        histograma(rows, col, repo_destaque)

    for col in QUALIDADE_KEYS:
        boxplot(rows, col, repo_destaque)

    for x in PROCESSO_KEYS:
        for y in QUALIDADE_KEYS:
            dispersao(rows, x, y, repo_destaque)


if __name__ == "__main__":
    main()