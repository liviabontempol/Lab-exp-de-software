import os
import csv
import math
import matplotlib.pyplot as plt


ARQUIVO_CSV = "repos_java_quality.csv"
PASTA_SAIDA = "graficos_png"
REPO_DESTAQUE = "Snailclimb/JavaGuide"

LABELS = {
    "estrelas": "Popularidade (estrelas)",
    "idade_anos": "Maturidade (idade em anos)",
    "releases": "Atividade (releases)",
    "total_classes": "Total de classes",
    "loc_total": "LOC total",
    "loc_media": "LOC medio por classe",
    "loc_mediana": "LOC mediano por classe",
    "total_methods": "Total de metodos",
    "cbo_media": "CBO media",
    "cbo_mediana": "CBO mediana",
    "cbo_desvio": "CBO desvio",
    "dit_media": "DIT media",
    "dit_mediana": "DIT mediana",
    "dit_desvio": "DIT desvio",
    "lcom_media": "LCOM media",
    "lcom_mediana": "LCOM mediana",
    "lcom_desvio": "LCOM desvio",
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

QUALIDADE_COMPLETA = [
    "cbo_media", "cbo_mediana", "cbo_desvio",
    "dit_media", "dit_mediana", "dit_desvio",
    "lcom_media", "lcom_mediana", "lcom_desvio",
]


def to_float(x):
    try:
        if x is None or x == "":
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def slug(txt: str) -> str:
    return (
        txt.lower()
        .replace("/", "_")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("-", "_")
        .replace("__", "_")
    )


def load_rows(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    tratadas = []
    for r in rows:
        nova = dict(r)

        for col in PROCESSO_KEYS + QUALIDADE_COMPLETA:
            if col in nova:
                nova[col] = to_float(nova.get(col))

        tratadas.append(nova)

    return tratadas


def series(rows, key):
    return [r[key] for r in rows if r.get(key) is not None]


def encontrar_repo(rows, nome_repo):
    for r in rows:
        if r.get("nome") == nome_repo:
            return r
    return None


def salvar_histograma(rows, coluna, repo_destaque=None):
    valores = series(rows, coluna)
    if not valores:
        return

    plt.figure(figsize=(8, 5))
    plt.hist(valores, bins=15, edgecolor="black")
    plt.title(f"Distribuicao de {LABELS.get(coluna, coluna)}")
    plt.xlabel(LABELS.get(coluna, coluna))
    plt.ylabel("Frequencia")

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
    nome_arquivo = f"histograma_{slug(coluna)}.png"
    plt.savefig(os.path.join(PASTA_SAIDA, nome_arquivo), dpi=150)
    plt.close()


def salvar_boxplot(rows, coluna, repo_destaque=None):
    valores = series(rows, coluna)
    if not valores:
        return

    plt.figure(figsize=(8, 4.5))
    plt.boxplot(valores, vert=False)
    plt.title(f"Boxplot de {LABELS.get(coluna, coluna)}")
    plt.xlabel(LABELS.get(coluna, coluna))

    if repo_destaque and repo_destaque.get(coluna) is not None:
        valor = repo_destaque[coluna]
        plt.axvline(valor, linestyle="--", linewidth=2)

    plt.tight_layout()
    nome_arquivo = f"boxplot_{slug(coluna)}.png"
    plt.savefig(os.path.join(PASTA_SAIDA, nome_arquivo), dpi=150)
    plt.close()


def salvar_barras_repo(repo):
    metricas = ["cbo_mediana", "dit_mediana", "lcom_mediana"]
    valores = [repo.get(m) for m in metricas]

    plt.figure(figsize=(8, 5))
    plt.bar([LABELS[m] for m in metricas], valores)
    plt.title(f"Metricas de qualidade - {repo['nome']}")
    plt.ylabel("Valor")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    nome_arquivo = f"barras_repositorio_destaque_{slug(repo['nome'])}.png"
    plt.savefig(os.path.join(PASTA_SAIDA, nome_arquivo), dpi=150)
    plt.close()


def salvar_dispersao(rows, x_key, y_key, repo_destaque=None):
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

    nome_arquivo = f"relacao_{slug(x_key)}_vs_{slug(y_key)}.png"
    plt.savefig(os.path.join(PASTA_SAIDA, nome_arquivo), dpi=150)
    plt.close()


def salvar_matriz_correlacao(rows):
    colunas = PROCESSO_KEYS + QUALIDADE_KEYS

    dados = []
    for r in rows:
        linha = []
        ok = True
        for c in colunas:
            v = r.get(c)
            if v is None:
                ok = False
                break
            linha.append(v)
        if ok:
            dados.append(linha)

    if len(dados) < 2:
        return

    # correlação manual
    n = len(colunas)
    matriz = [[0.0 for _ in range(n)] for _ in range(n)]

    for i in range(n):
        xi = [linha[i] for linha in dados]
        mi = sum(xi) / len(xi)
        sdi = math.sqrt(sum((x - mi) ** 2 for x in xi) / (len(xi) - 1)) if len(xi) > 1 else 0.0

        for j in range(n):
            xj = [linha[j] for linha in dados]
            mj = sum(xj) / len(xj)
            sdj = math.sqrt(sum((x - mj) ** 2 for x in xj) / (len(xj) - 1)) if len(xj) > 1 else 0.0

            if sdi == 0 or sdj == 0:
                matriz[i][j] = 0.0
            else:
                cov = sum((a - mi) * (b - mj) for a, b in zip(xi, xj)) / (len(dados) - 1)
                matriz[i][j] = cov / (sdi * sdj)

    plt.figure(figsize=(11, 8))
    plt.imshow(matriz, interpolation="nearest", aspect="auto")
    plt.colorbar()
    plt.xticks(range(n), [LABELS.get(c, c) for c in colunas], rotation=45, ha="right")
    plt.yticks(range(n), [LABELS.get(c, c) for c in colunas])

    for i in range(n):
        for j in range(n):
            plt.text(j, i, f"{matriz[i][j]:.2f}", ha="center", va="center")

    plt.title("Matriz de correlacao entre metricas")
    plt.tight_layout()
    plt.savefig(os.path.join(PASTA_SAIDA, "matriz_correlacao_metricas.png"), dpi=150)
    plt.close()


def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    rows = load_rows(ARQUIVO_CSV)
    if not rows:
        raise RuntimeError("Nenhum dado encontrado no CSV.")

    repo_destaque = encontrar_repo(rows, REPO_DESTAQUE)

    # gráfico do repositório em destaque
    if repo_destaque:
        salvar_barras_repo(repo_destaque)

    # histogramas e boxplots de qualidade
    for col in QUALIDADE_KEYS:
        salvar_histograma(rows, col, repo_destaque)
        salvar_boxplot(rows, col, repo_destaque)

    # gráficos das relações pedidas
    for x in PROCESSO_KEYS:
        for y in QUALIDADE_KEYS:
            salvar_dispersao(rows, x, y, repo_destaque)

    # matriz de correlação
    salvar_matriz_correlacao(rows)

    print(f"Graficos gerados em: {PASTA_SAIDA}")


if __name__ == "__main__":
    main()