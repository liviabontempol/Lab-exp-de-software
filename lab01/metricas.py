import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import ttest_1samp, pearsonr
import seaborn as sns
import matplotlib.pyplot as plt

# carregar dados
df = pd.read_csv("repositorios_populares_1000.csv")

print("Colunas disponíveis:")
print(df.columns)

def estatisticas(coluna):
    dados = df[coluna].dropna()

    media = np.mean(dados)
    mediana = np.median(dados)
    desvio = np.std(dados, ddof=1)

    intervalo = stats.t.interval(
        confidence=0.95,
        df=len(dados)-1,
        loc=media,
        scale=stats.sem(dados)
    )

    return media, mediana, desvio, intervalo

metricas = [
    "repo_age_days",
    "merged_pull_requests",
    "releases_total",
    "closed_issues_ratio"
]

for coluna in metricas:
    media, mediana, desvio, intervalo = estatisticas(coluna)

    print(f"\n===== {coluna} =====")
    print(f"Média: {float(media):.2f}")
    print(f"Mediana: {float(mediana):.2f}")
    print(f"Desvio padrão: {float(desvio):.2f}")
    print(f"Intervalo de confiança 95%: ({float(intervalo[0]):.2f}, {float(intervalo[1]):.2f})")

# -------------------------
# Teste estatístico (RQ06)
# -------------------------

dados = df["closed_issues_ratio"].dropna()

# teste bicaudal padrão
stat, p = ttest_1samp(dados, 0.8)

print("\nTeste t para taxa de issues fechadas")
print(f"t = {float(stat):.4f}")
print(f"p = {float(p):.6f}")

# -------------------------
# boxplot PRs
# -------------------------

plt.figure(figsize=(10, 5))
sns.boxplot(x=df["merged_pull_requests"])
plt.title("Distribuição de Pull Requests Aceitos")
plt.show()

# -------------------------
# ANÁLISE DE CORRELAÇÃO
# -------------------------

print("\n==============================")
print("ANÁLISE DE CORRELAÇÃO")
print("==============================")

def analisar_correlacao(coluna1, coluna2):
    dados = df[[coluna1, coluna2]].dropna()

    corr, p = pearsonr(dados[coluna1], dados[coluna2])

    print(f"\nCorrelação entre {coluna1} e {coluna2}")
    print(f"Coeficiente de Pearson: {float(corr):.3f}")
    print(f"Valor-p: {float(p):.6f}")

    plt.figure(figsize=(7, 5))
    sns.regplot(
        data=dados,
        x=coluna1,
        y=coluna2,
        scatter_kws={"alpha": 0.5}
    )
    plt.title(f"Correlação entre {coluna1} e {coluna2}")
    plt.show()

# estrelas vs PRs
analisar_correlacao("stargazers", "merged_pull_requests")

# idade vs estrelas
analisar_correlacao("repo_age_days", "stargazers")

# PRs vs releases
analisar_correlacao("merged_pull_requests", "releases_total")

# -------------------------
# MATRIZ DE CORRELAÇÃO
# -------------------------

plt.figure(figsize=(8, 6))
sns.heatmap(
    df[
        [
            "repo_age_days",
            "merged_pull_requests",
            "releases_total",
            "stargazers",
            "closed_issues_ratio"
        ]
    ].corr(),
    annot=True,
    cmap="coolwarm"
)
plt.title("Matriz de Correlação entre Métricas dos Repositórios")
plt.show()