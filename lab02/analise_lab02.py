import os
import csv
import math
from statistics import mean, median

import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

from config import QUALITY_CSV


def _to_float(x):
    try:
        if x == "" or x is None:
            return None
        return float(x)
    except (ValueError, TypeError):
        return None


def _load_rows(path):
    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r.get("status") == "ok"]


def _series(rows, key):
    return [_to_float(r.get(key)) for r in rows if _to_float(r.get(key)) is not None]


def _stats(values):
    if not values:
        return {"media": None, "mediana": None, "desvio": None}
    m = mean(values)
    md = median(values)
    if len(values) == 1:
        sd = 0.0
    else:
        var = sum((x - m) ** 2 for x in values) / (len(values) - 1)
        sd = math.sqrt(var)
    return {"media": m, "mediana": md, "desvio": sd}


def _corr(rows, x_key, y_key):
    xs, ys = [], []
    for r in rows:
        x = _to_float(r.get(x_key))
        y = _to_float(r.get(y_key))
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)
    if len(xs) < 3:
        return None
    p_pearson = pearsonr(xs, ys)
    p_spearman = spearmanr(xs, ys)
    return {
        "n": len(xs),
        "pearson_r": p_pearson.statistic,
        "pearson_p": p_pearson.pvalue,
        "spearman_rho": p_spearman.statistic,
        "spearman_p": p_spearman.pvalue,
        "x": xs,
        "y": ys,
    }


def _scatter(xs, ys, x_label, y_label, file_name):
    plt.figure(figsize=(8, 5))
    plt.scatter(xs, ys, alpha=0.55)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(f"{x_label} vs {y_label}")
    plt.tight_layout()
    plt.savefig(file_name, dpi=130)
    plt.close()


def main():
    if not os.path.exists(QUALITY_CSV):
        raise RuntimeError(f"Arquivo não encontrado: {QUALITY_CSV}. Rode pipeline_qualidade.py antes.")

    rows = _load_rows(QUALITY_CSV)
    if not rows:
        raise RuntimeError("Nenhum repositório com status=ok no CSV de qualidade.")

    qualidade_keys = ["cbo_median", "dit_median", "lcom_median"]
    processo_keys = {
        "stars": "Popularidade (estrelas)",
        "repo_age_years": "Maturidade (idade em anos)",
        "releases_total": "Atividade (releases)",
        "loc": "Tamanho (LOC)",
    }

    # Estatísticas descritivas por repositório (métricas de qualidade)
    print("\n=== Estatísticas descritivas das métricas de qualidade ===")
    for q in qualidade_keys:
        st = _stats(_series(rows, q))
        print(
            f"{q}: média={st['media']:.4f} | mediana={st['mediana']:.4f} | desvio={st['desvio']:.4f}"
        )

    # Correlações das RQs
    print("\n=== Correlações (Pearson e Spearman) ===")
    relatorio = []
    for p_key, p_label in processo_keys.items():
        for q_key in qualidade_keys:
            res = _corr(rows, p_key, q_key)
            if not res:
                continue
            print(
                f"{p_key} x {q_key} (n={res['n']}): "
                f"Pearson r={res['pearson_r']:.4f} (p={res['pearson_p']:.4g}) | "
                f"Spearman rho={res['spearman_rho']:.4f} (p={res['spearman_p']:.4g})"
            )
            relatorio.append(
                {
                    "rq_eixo_processo": p_key,
                    "metrica_qualidade": q_key,
                    "n": res["n"],
                    "pearson_r": round(res["pearson_r"], 6),
                    "pearson_p": round(res["pearson_p"], 8),
                    "spearman_rho": round(res["spearman_rho"], 6),
                    "spearman_p": round(res["spearman_p"], 8),
                }
            )
            chart_name = f"grafico_{p_key}_vs_{q_key}.png"
            _scatter(res["x"], res["y"], p_label, q_key, chart_name)

    out_csv = "correlacoes_lab02.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(relatorio[0].keys()))
        writer.writeheader()
        writer.writerows(relatorio)

    print(f"\nArquivo de correlações: {out_csv}")
    print("Gráficos salvos como grafico_<metrica_processo>_vs_<metrica_qualidade>.png")


if __name__ == "__main__":
    main()
