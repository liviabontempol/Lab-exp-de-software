#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10

# Carregar dados
print("Carregando dados...")
with open('data/raw/dataset_prs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data)
print(f"Total de PRs: {len(df)}")

# Converter tipos
cols = ['changed_files', 'additions', 'deletions', 'body_length', 
        'participants_count', 'comments_count', 'reviews_count', 'review_duration_hours']
for col in cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Filtrar
df = df[df['state'].isin(['MERGED', 'CLOSED'])].dropna(subset=cols)
df = df[df['reviews_count'] >= 1]
df = df[df['review_duration_hours'] >= 1.0]

df['total_changes'] = df['additions'] + df['deletions']

print(f"PRs apos filtros: {len(df)}")

# Estatisticas
print("\nEstatisticas Descritivas:")
for col in cols:
    print(f"{col}: Mediana={df[col].median():.2f}, Media={df[col].mean():.2f}")

# Criar graficos
Path('graficos').mkdir(exist_ok=True)

# RQ01
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('RQ01 - Tamanho vs Status', fontweight='bold')
merged = df[df['state'] == 'MERGED']
closed = df[df['state'] == 'CLOSED']

axes[0, 0].boxplot([merged['changed_files'], closed['changed_files']], labels=['MERGED', 'CLOSED'])
axes[0, 0].set_title('Arquivos Modificados')

axes[0, 1].boxplot([merged['additions'], closed['additions']], labels=['MERGED', 'CLOSED'])
axes[0, 1].set_title('Linhas Adicionadas')

axes[1, 0].boxplot([merged['deletions'], closed['deletions']], labels=['MERGED', 'CLOSED'])
axes[1, 0].set_title('Linhas Removidas')

axes[1, 1].boxplot([merged['total_changes'], closed['total_changes']], labels=['MERGED', 'CLOSED'])
axes[1, 1].set_title('Total de Mudancas')

plt.tight_layout()
plt.savefig('graficos/RQ01_tamanho_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ01 OK")

# RQ02
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ02 - Tempo de Analise vs Status', fontweight='bold')
ax.boxplot([merged['review_duration_hours'], closed['review_duration_hours']], labels=['MERGED', 'CLOSED'])
ax.set_ylabel('Horas')
ax.set_yscale('log')
plt.tight_layout()
plt.savefig('graficos/RQ02_tempo_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ02 OK")

# RQ03
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ03 - Descricao vs Status', fontweight='bold')
ax.boxplot([merged['body_length'], closed['body_length']], labels=['MERGED', 'CLOSED'])
ax.set_ylabel('Caracteres')
plt.tight_layout()
plt.savefig('graficos/RQ03_descricao_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ03 OK")

# RQ04
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('RQ04 - Interacoes vs Status', fontweight='bold')
axes[0].boxplot([merged['participants_count'], closed['participants_count']], labels=['MERGED', 'CLOSED'])
axes[0].set_title('Participantes')
axes[1].boxplot([merged['comments_count'], closed['comments_count']], labels=['MERGED', 'CLOSED'])
axes[1].set_title('Comentarios')
plt.tight_layout()
plt.savefig('graficos/RQ04_interacoes_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ04 OK")

# RQ05
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('RQ05 - Tamanho vs Reviews', fontweight='bold')
axes[0, 0].scatter(df['changed_files'], df['reviews_count'], alpha=0.5)
axes[0, 0].set_title('Arquivos vs Reviews')
axes[0, 1].scatter(df['additions'], df['reviews_count'], alpha=0.5)
axes[0, 1].set_title('Adicoes vs Reviews')
axes[1, 0].scatter(df['deletions'], df['reviews_count'], alpha=0.5)
axes[1, 0].set_title('Delecoes vs Reviews')
axes[1, 1].scatter(df['total_changes'], df['reviews_count'], alpha=0.5)
axes[1, 1].set_title('Total Mudancas vs Reviews')
plt.tight_layout()
plt.savefig('graficos/RQ05_tamanho_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ05 OK")

# RQ06
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ06 - Tempo de Analise vs Reviews', fontweight='bold')
ax.scatter(df['review_duration_hours'], df['reviews_count'], alpha=0.5)
ax.set_xlabel('Tempo (horas)')
ax.set_ylabel('Reviews')
ax.set_xscale('log')
plt.tight_layout()
plt.savefig('graficos/RQ06_tempo_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ06 OK")

# RQ07
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ07 - Descricao vs Reviews', fontweight='bold')
ax.scatter(df['body_length'], df['reviews_count'], alpha=0.5)
ax.set_xlabel('Caracteres')
ax.set_ylabel('Reviews')
plt.tight_layout()
plt.savefig('graficos/RQ07_descricao_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ07 OK")

# RQ08
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('RQ08 - Interacoes vs Reviews', fontweight='bold')
axes[0].scatter(df['participants_count'], df['reviews_count'], alpha=0.5)
axes[0].set_title('Participantes vs Reviews')
axes[1].scatter(df['comments_count'], df['reviews_count'], alpha=0.5)
axes[1].set_title('Comentarios vs Reviews')
plt.tight_layout()
plt.savefig('graficos/RQ08_interacoes_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("RQ08 OK")

# Calcular correlacoes
print("\nCorrelacoes (Spearman):")
status_numeric = (df['state'] == 'MERGED').astype(int)

metricas = {
    'changed_files': 'Arquivos',
    'additions': 'Adicoes',
    'deletions': 'Delecoes',
    'total_changes': 'Total Mudancas',
    'review_duration_hours': 'Tempo',
    'body_length': 'Descricao',
    'participants_count': 'Participantes',
    'comments_count': 'Comentarios'
}

resultados = {}
for col, nome in metricas.items():
    r_status, p_status = spearmanr(df[col], status_numeric)
    r_review, p_review = spearmanr(df[col], df['reviews_count'])
    resultados[nome] = {
        'vs_status': {'r': r_status, 'p': p_status},
        'vs_reviews': {'r': r_review, 'p': p_review}
    }
    print(f"{nome}:")
    print(f"  vs Status: r={r_status:.4f}, p={p_status:.4f}")
    print(f"  vs Reviews: r={r_review:.4f}, p={p_review:.4f}")

# Salvar resultados
with open('relatorio_analise.json', 'w') as f:
    json.dump(resultados, f, indent=2)

print("\nGraficos salvos em graficos/")
print("Relatorio JSON salvo: relatorio_analise.json")
