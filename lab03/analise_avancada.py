#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analise Avancada com Graficos Sofisticados - LAB03
Gera visualizacoes profissionais e analises estatisticas completas
"""

import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, shapiro, mannwhitneyu
from scipy import stats
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuracoes de estilo profissional
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

print("="*60)
print("ANALISE AVANCADA - CODE REVIEW NO GITHUB")
print("="*60)

# Carregar dados
print("\nCarregando dados...")
with open('data/raw/dataset_prs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extrair campos
records = []
for item in data:
    record = {
        'repository': item.get('repository'),
        'pr_number': item.get('pr_number'),
        'state': item.get('pr_state'),
        'changed_files': item.get('tamanho_dos_prs', {}).get('changed_files'),
        'additions': item.get('tamanho_dos_prs', {}).get('additions'),
        'deletions': item.get('tamanho_dos_prs', {}).get('deletions'),
        'total_changes': item.get('tamanho_dos_prs', {}).get('total_changes'),
        'review_duration_hours': item.get('tempo_de_analise_dos_prs', {}).get('hours'),
        'issue_comments': item.get('interacoes_nos_prs', {}).get('issue_comments'),
        'review_comments': item.get('interacoes_nos_prs', {}).get('review_comments'),
        'reviews': item.get('interacoes_nos_prs', {}).get('reviews'),
        'body_length': item.get('descricao_dos_prs', {}).get('body_length'),
        'numero_de_revisoes': item.get('numero_de_revisoes_realizadas'),
    }
    records.append(record)

df = pd.DataFrame(records)

# Converter tipos
numeric_cols = ['changed_files', 'additions', 'deletions', 'total_changes',
                'review_duration_hours', 'issue_comments', 'review_comments', 
                'reviews', 'body_length', 'numero_de_revisoes']

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Filtros
df = df.dropna(subset=numeric_cols)
df = df[df['state'].isin(['MERGED', 'CLOSED'])]
df = df[df['numero_de_revisoes'] >= 1]
df = df[df['review_duration_hours'] >= 1.0]

df['comments_count'] = df['issue_comments'] + df['review_comments']
df['status_binary'] = (df['state'] == 'MERGED').astype(int)

print(f"Total PRs: {len(df)}")
print(f"MERGED: {(df['state']=='MERGED').sum()}")
print(f"CLOSED: {(df['state']=='CLOSED').sum()}")

# Criar pasta para graficos
Path('graficos_avancados').mkdir(exist_ok=True)

# ============================================================================
# ANALISE ESTATISTICA COMPLETA
# ============================================================================

def calcular_stats(serie, nome):
    """Calcula estatisticas completas"""
    return {
        'metrica': nome,
        'media': serie.mean(),
        'mediana': serie.median(),
        'desvio': serie.std(),
        'min': serie.min(),
        'max': serie.max(),
        'q1': serie.quantile(0.25),
        'q3': serie.quantile(0.75),
        'iqr': serie.quantile(0.75) - serie.quantile(0.25),
        'skewness': serie.skew(),
        'kurtosis': serie.kurtosis(),
        'cv': (serie.std() / serie.mean()) if serie.mean() != 0 else 0
    }

metricas_analise = {
    'changed_files': 'Arquivos modificados',
    'additions': 'Linhas adicionadas',
    'deletions': 'Linhas removidas',
    'total_changes': 'Total de mudancas',
    'review_duration_hours': 'Tempo de analise (h)',
    'body_length': 'Comprimento descricao',
    'reviews': 'Numero de reviews',
    'comments_count': 'Numero comentarios',
}

stats_completas = {}
for col, nome in metricas_analise.items():
    stats_completas[nome] = calcular_stats(df[col], nome)

# Salvar stats
with open('graficos_avancados/stats_completas.json', 'w', encoding='utf-8') as f:
    # Converter numpy types para serializar
    stats_json = {}
    for k, v in stats_completas.items():
        stats_json[k] = {k2: float(v2) if k2 != 'metrica' else v2 for k2, v2 in v.items()}
    json.dump(stats_json, f, indent=2, ensure_ascii=False)

print("\n" + "="*60)
print("ESTATISTICAS DESCRITIVAS")
print("="*60)
for nome, stats_dict in stats_completas.items():
    print(f"\n{nome}:")
    print(f"  Media: {stats_dict['media']:.2f} | Mediana: {stats_dict['mediana']:.2f}")
    print(f"  Desvio: {stats_dict['desvio']:.2f} | IQR: {stats_dict['iqr']:.2f}")
    print(f"  Skewness: {stats_dict['skewness']:.2f} | Kurtosis: {stats_dict['kurtosis']:.2f}")
    print(f"  CV: {stats_dict['cv']:.2f}")

# ============================================================================
# GRAFICOS VIOLINO + BOX PLOT
# ============================================================================
print("\nGerando Violin Plots...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Distribuicoes por Status (MERGED vs CLOSED) - Violin Plots', 
             fontsize=16, fontweight='bold', y=0.995)

metricas_plot = [('additions', 'Linhas Adicionadas'), 
                 ('deletions', 'Linhas Removidas'),
                 ('review_duration_hours', 'Tempo de Analise (horas)'),
                 ('comments_count', 'Numero de Comentarios')]

for idx, (col, title) in enumerate(metricas_plot):
    ax = axes[idx//2, idx%2]
    
    # Violin plot
    parts = ax.violinplot([df[df['state']=='MERGED'][col].dropna(),
                            df[df['state']=='CLOSED'][col].dropna()],
                           positions=[1, 2], widths=0.7, 
                           showmeans=True, showmedians=True)
    
    # Customizar cores
    for pc in parts['bodies']:
        pc.set_facecolor('#3498db')
        pc.set_alpha(0.7)
    
    ax.set_xticks([1, 2])
    ax.set_xticklabels(['MERGED', 'CLOSED'])
    ax.set_ylabel(title, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Adicionar estatisticas
    median_merged = df[df['state']=='MERGED'][col].median()
    median_closed = df[df['state']=='CLOSED'][col].median()
    ax.text(0.02, 0.98, f'Merged median: {median_merged:.1f}\nClosed median: {median_closed:.1f}',
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('graficos_avancados/00_violin_plots_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Violin plots")

# ============================================================================
# SCATTER PLOTS COM REGRESSAO
# ============================================================================
print("Gerando Scatter Plots com Regressao...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Correlacoes com Status MERGED - Scatter + Regressao Logistica', 
             fontsize=16, fontweight='bold', y=0.995)

metricas_scatter = [('changed_files', 'Arquivos Modificados'),
                    ('additions', 'Linhas Adicionadas'),
                    ('review_duration_hours', 'Tempo de Analise (horas)'),
                    ('comments_count', 'Numero de Comentarios')]

for idx, (col, title) in enumerate(metricas_scatter):
    ax = axes[idx//2, idx%2]
    
    # Scatter com transparencia
    merged = df[df['state']=='MERGED']
    closed = df[df['state']=='CLOSED']
    
    ax.scatter(merged[col], [1]*len(merged), alpha=0.3, s=20, label='MERGED', color='#27ae60')
    ax.scatter(closed[col], [0]*len(closed), alpha=0.3, s=20, label='CLOSED', color='#e74c3c')
    
    # Regressao logistica
    from sklearn.linear_model import LogisticRegression
    X = df[col].values.reshape(-1, 1)
    y = df['status_binary'].values
    
    model = LogisticRegression()
    model.fit(X, y)
    
    x_range = np.linspace(X.min(), X.max(), 300).reshape(-1, 1)
    y_pred = model.predict_proba(x_range)[:, 1]
    
    ax.plot(x_range, y_pred, 'b-', linewidth=2.5, label='Prob(MERGED)')
    ax.fill_between(x_range.flatten(), y_pred, alpha=0.2, color='blue')
    
    ax.set_xlabel(title, fontsize=12, fontweight='bold')
    ax.set_ylabel('P(MERGED)', fontsize=12, fontweight='bold')
    ax.set_ylim(-0.1, 1.1)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('graficos_avancados/01_scatter_regressao_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Scatter plots com regressao")

# ============================================================================
# DISTRIBUICOES KDE
# ============================================================================
print("Gerando KDE Plots...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Distribuicoes de Densidade (KDE) por Status', 
             fontsize=16, fontweight='bold', y=0.995)

for idx, (col, title) in enumerate(metricas_plot):
    ax = axes[idx//2, idx%2]
    
    # KDE plots
    merged_data = df[df['state']=='MERGED'][col].dropna()
    closed_data = df[df['state']=='CLOSED'][col].dropna()
    
    merged_data.plot.kde(ax=ax, linewidth=2.5, label='MERGED', color='#27ae60')
    closed_data.plot.kde(ax=ax, linewidth=2.5, label='CLOSED', color='#e74c3c')
    
    ax.fill_between(merged_data.plot.kde().get_lines()[0].get_xdata(),
                    merged_data.plot.kde().get_lines()[0].get_ydata(),
                    alpha=0.2, color='#27ae60')
    
    ax.set_xlabel(title, fontsize=12, fontweight='bold')
    ax.set_ylabel('Densidade', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('graficos_avancados/02_kde_plots.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] KDE plots")

# ============================================================================
# CORRELACAO COM NUMERO DE REVIEWS
# ============================================================================
print("Gerando Scatter plots vs Numero de Reviews...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Relacao com Numero de Reviews - Scatter + Trend Line', 
             fontsize=16, fontweight='bold', y=0.995)

metricas_reviews = [('changed_files', 'Arquivos Modificados'),
                    ('additions', 'Linhas Adicionadas'),
                    ('review_duration_hours', 'Tempo de Analise (horas)'),
                    ('comments_count', 'Numero de Comentarios')]

for idx, (col, title) in enumerate(metricas_reviews):
    ax = axes[idx//2, idx%2]
    
    # Scatter
    ax.scatter(df[col], df['numero_de_revisoes'], alpha=0.4, s=30, color='#3498db')
    
    # Trend line (LOWESS)
    from scipy.signal import savgol_filter
    sorted_idx = np.argsort(df[col].values)
    x_sorted = df[col].values[sorted_idx]
    y_sorted = df['numero_de_revisoes'].values[sorted_idx]
    
    # Suavizar
    if len(x_sorted) > 10:
        window = min(51, len(x_sorted) - 1 if len(x_sorted) % 2 == 0 else len(x_sorted))
        if window >= 5:
            y_smooth = savgol_filter(y_sorted, window, 3)
            ax.plot(x_sorted, y_smooth, 'r-', linewidth=2.5, label='Trend')
    
    ax.set_xlabel(title, fontsize=12, fontweight='bold')
    ax.set_ylabel('Numero de Reviews', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold')
    
    # Calcular correlacao
    r, p = spearmanr(df[col].dropna(), df['numero_de_revisoes'].dropna())
    ax.text(0.02, 0.98, f'r={r:.3f}\np-value={p:.2e}',
            transform=ax.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7),
            fontweight='bold')
    
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('graficos_avancados/03_scatter_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Scatter plots reviews")

# ============================================================================
# HEATMAP DE CORRELACOES
# ============================================================================
print("Gerando Heatmap de Correlacoes...")

fig, ax = plt.subplots(figsize=(14, 10))

# Selecionar colunas para heatmap
cols_heatmap = ['changed_files', 'additions', 'deletions', 'review_duration_hours',
                'body_length', 'reviews', 'comments_count', 'numero_de_revisoes', 'status_binary']

df_corr = df[cols_heatmap].dropna()

# Calcular matriz de correlacao
corr_matrix = df_corr.corr(method='spearman')

# Labels customizados
labels = ['Arquivos', 'Adicoes', 'Delecoes', 'Tempo (h)', 
          'Desc. Length', 'Reviews', 'Comentarios', 'Num Reviews', 'MERGED']

# Heatmap
sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8},
            xticklabels=labels, yticklabels=labels, ax=ax,
            vmin=-1, vmax=1, annot_kws={'size': 10, 'weight': 'bold'})

ax.set_title('Matriz de Correlacao de Spearman - Todas as Metricas',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('graficos_avancados/04_heatmap_correlacoes.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Heatmap")

# ============================================================================
# BOX PLOTS COM OUTLIERS
# ============================================================================
print("Gerando Box Plots com Outliers...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Box Plots Comparativos (MERGED vs CLOSED) com Outliers Destacados', 
             fontsize=16, fontweight='bold', y=0.995)

for idx, (col, title) in enumerate(metricas_plot):
    ax = axes[idx//2, idx%2]
    
    data_to_plot = [df[df['state']=='MERGED'][col].dropna(),
                    df[df['state']=='CLOSED'][col].dropna()]
    
    bp = ax.boxplot(data_to_plot, labels=['MERGED', 'CLOSED'], patch_artist=True,
                    widths=0.6, showmeans=True, meanline=True)
    
    # Colorir boxes
    colors = ['#27ae60', '#e74c3c']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    # Customizar medias
    for mean in bp['means']:
        mean.set_color('darkblue')
        mean.set_linewidth(2)
    
    # Adicionar pontos outliers
    for i, data in enumerate(data_to_plot):
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        
        outliers = data[(data < lower) | (data > upper)]
        ax.scatter([i+1]*len(outliers), outliers, color='red', s=50, 
                  alpha=0.6, zorder=3, marker='^', label='Outliers' if i==0 else '')
    
    ax.set_ylabel(title, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('graficos_avancados/05_boxplots_outliers.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Box plots")

# ============================================================================
# ANALISE DE OUTLIERS
# ============================================================================
print("\n" + "="*60)
print("DETECCAO DE OUTLIERS (IQR Method)")
print("="*60)

outliers_info = {}
for col, nome in metricas_analise.items():
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    
    outliers = df[(df[col] < lower) | (df[col] > upper)]
    outlier_pct = (len(outliers) / len(df)) * 100
    
    outliers_info[nome] = {
        'count': int(len(outliers)),
        'percentage': float(outlier_pct),
        'lower_bound': float(lower),
        'upper_bound': float(upper)
    }
    
    print(f"\n{nome}:")
    print(f"  Outliers: {len(outliers)} ({outlier_pct:.2f}%)")
    print(f"  Limites: [{lower:.2f}, {upper:.2f}]")

# ============================================================================
# TESTES ESTATISTICOS AVANCADOS
# ============================================================================
print("\n" + "="*60)
print("TESTES ESTATISTICOS AVANCADOS")
print("="*60)

testes_resultados = {}
for col, nome in metricas_analise.items():
    merged_data = df[df['state']=='MERGED'][col].dropna()
    closed_data = df[df['state']=='CLOSED'][col].dropna()
    
    # Mann-Whitney U (teste nao-parametrico)
    statistic, p_value = mannwhitneyu(merged_data, closed_data)
    
    # Cohen's d (effect size)
    cohens_d = (merged_data.mean() - closed_data.mean()) / np.sqrt(((len(merged_data)-1)*merged_data.std()**2 + (len(closed_data)-1)*closed_data.std()**2) / (len(merged_data) + len(closed_data) - 2))
    
    testes_resultados[nome] = {
        'mannwhitneyu_stat': float(statistic),
        'p_value': float(p_value),
        'cohens_d': float(cohens_d),
        'effect_size_interpretation': 'pequeno' if abs(cohens_d) < 0.2 else 'medio' if abs(cohens_d) < 0.5 else 'grande'
    }
    
    print(f"\n{nome}:")
    print(f"  Mann-Whitney U: {statistic:.2f}, p={p_value:.2e}")
    print(f"  Cohen's d: {cohens_d:.4f} ({testes_resultados[nome]['effect_size_interpretation']})")

# Salvar testes
with open('graficos_avancados/testes_estatisticos.json', 'w', encoding='utf-8') as f:
    json.dump(testes_resultados, f, indent=2, ensure_ascii=False)

print("\n" + "="*60)
print("GRAFICOS SALVOS: graficos_avancados/")
print("="*60)
