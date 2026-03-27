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

# Mapeia nomes técnicos das colunas para rótulos amigáveis em português
LABELS = {
    "repo_age_days": "Idade do repositório (dias)",
    "merged_pull_requests": "Pull requests aceitos",
    "releases_total": "Total de releases",
    "closed_issues_ratio": "Taxa de issues fechadas",
    "stargazers": "Estrelas (stargazers)",
}


def estatisticas(coluna):
    dados = df[coluna].dropna()

    media = np.mean(dados)
    mediana = np.median(dados)
    desvio = np.std(dados, ddof=1)

    intervalo = stats.t.interval(
        confidence=0.95,
        df=len(dados) - 1,
        loc=media,
        scale=stats.sem(dados),
    )

    return media, mediana, desvio, intervalo


metricas = [
    "repo_age_days",
    "merged_pull_requests",
    "releases_total",
    "closed_issues_ratio",
]

for coluna in metricas:
    media, mediana, desvio, intervalo = estatisticas(coluna)
    label = LABELS.get(coluna, coluna)

    print(f"\n===== {label} =====")
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

print("\nTeste t para taxa de issues fechadas (média vs 0.8)")
print(f"t = {float(stat):.4f}")
print(f"p = {float(p):.6f}")

# -------------------------
# boxplot PRs
# -------------------------

plt.figure(figsize=(10, 5))
sns.boxplot(x=df["merged_pull_requests"])
plt.title("Distribuição de Pull Requests Aceitos")
plt.xlabel(LABELS["merged_pull_requests"])
plt.tight_layout()
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

    label1 = LABELS.get(coluna1, coluna1)
    label2 = LABELS.get(coluna2, coluna2)

    print(f"\nCorrelação entre {label1} e {label2}")
    print(f"Coeficiente de Pearson: {float(corr):.3f}")
    print(f"Valor-p: {float(p):.6f}")

    plt.figure(figsize=(7, 5))
    sns.regplot(
        data=dados,
        x=coluna1,
        y=coluna2,
        scatter_kws={"alpha": 0.5},
    )
    plt.xlabel(label1)
    plt.ylabel(label2)
    plt.title(f"Correlação entre {label1} e {label2}")
    plt.tight_layout()
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

cols = [
    "repo_age_days",
    "merged_pull_requests",
    "releases_total",
    "stargazers",
    "closed_issues_ratio",
]

plt.figure(figsize=(9, 7))
ax = sns.heatmap(
    df[cols].corr(),
    annot=True,
    cmap="coolwarm",
    xticklabels=[LABELS.get(c, c) for c in cols],
    yticklabels=[LABELS.get(c, c) for c in cols],
)
plt.title("Matriz de Correlação entre Métricas dos Repositórios")

# Gira os rótulos do eixo X para não ficarem cortados
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)

# Ajusta espaçamento para que legenda/labels não sejam \"comidos\"
plt.tight_layout()

plt.show()