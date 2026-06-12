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

print("Carregando dados...")
with open('data/raw/dataset_prs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total PRs brutos: {len(data)}")

# Extrair campos aninhados e criar DataFrame
records = []
for item in data:
    record = {
        'repository': item.get('repository'),
        'pr_number': item.get('pr_number'),
        'state': item.get('pr_state'),
        
        # Tamanho
        'changed_files': item.get('tamanho_dos_prs', {}).get('changed_files'),
        'additions': item.get('tamanho_dos_prs', {}).get('additions'),
        'deletions': item.get('tamanho_dos_prs', {}).get('deletions'),
        'total_changes': item.get('tamanho_dos_prs', {}).get('total_changes'),
        
        # Tempo de analise
        'review_duration_hours': item.get('tempo_de_analise_dos_prs', {}).get('hours'),
        'review_duration_seconds': item.get('tempo_de_analise_dos_prs', {}).get('seconds'),
        
        # Interacoes
        'issue_comments': item.get('interacoes_nos_prs', {}).get('issue_comments'),
        'review_comments': item.get('interacoes_nos_prs', {}).get('review_comments'),
        'reviews': item.get('interacoes_nos_prs', {}).get('reviews'),
        'total_interactions': item.get('interacoes_nos_prs', {}).get('total_interactions'),
        
        # Descricao
        'body_length': item.get('descricao_dos_prs', {}).get('body_length'),
        
        # Reviews e feedback
        'numero_de_revisoes': item.get('numero_de_revisoes_realizadas'),
        'final_state': item.get('feedback_final_das_revisoes', {}).get('final_state'),
    }
    records.append(record)

df = pd.DataFrame(records)
print(f"Campos: {list(df.columns)}")

# Converter tipos numericos
numeric_cols = ['changed_files', 'additions', 'deletions', 'total_changes',
                'review_duration_hours', 'review_duration_seconds',
                'issue_comments', 'review_comments', 'reviews', 'total_interactions',
                'body_length', 'numero_de_revisoes']

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Remover NaNs
df = df.dropna(subset=numeric_cols)

# Filtros conforme especificacao do lab
# 1. Status MERGED ou CLOSED
df = df[df['state'].isin(['MERGED', 'CLOSED'])]

# 2. Pelo menos uma revisao
df = df[df['numero_de_revisoes'] >= 1]

# 3. Revisao durou pelo menos 1 hora
df = df[df['review_duration_hours'] >= 1.0]

print(f"PRs apos filtros: {len(df)}")

# Calcular numer de participantes (simplificado: considerando reviews + comments)
df['participants_approx'] = df['reviews'] + (df['issue_comments'] > 0).astype(int)
df['comments_count'] = df['issue_comments'] + df['review_comments']

# Estatisticas
print("\n=== ESTATISTICAS DESCRITIVAS ===")
print("\nTamanho:")
for col in ['changed_files', 'additions', 'deletions', 'total_changes']:
    print(f"  {col}: Mediana={df[col].median():.2f}, Media={df[col].mean():.2f}")

print("\nTempo de Analise (horas):")
print(f"  Mediana={df['review_duration_hours'].median():.2f}, Media={df['review_duration_hours'].mean():.2f}")

print("\nDescricao:")
print(f"  body_length: Mediana={df['body_length'].median():.2f}, Media={df['body_length'].mean():.2f}")

print("\nInteracoes:")
for col in ['reviews', 'comments_count', 'total_interactions']:
    if col in df.columns:
        print(f"  {col}: Mediana={df[col].median():.2f}, Media={df[col].mean():.2f}")

# Criar graficos
Path('graficos').mkdir(exist_ok=True)

# RQ01
print("\nGerando graficos...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('RQ01 - Tamanho vs Status do PR', fontweight='bold')
merged = df[df['state'] == 'MERGED']
closed = df[df['state'] == 'CLOSED']

axes[0, 0].boxplot([merged['changed_files'], closed['changed_files']], labels=['MERGED', 'CLOSED'])
axes[0, 0].set_title('Arquivos Modificados')
axes[0, 0].set_ylabel('Quantidade')

axes[0, 1].boxplot([merged['additions'], closed['additions']], labels=['MERGED', 'CLOSED'])
axes[0, 1].set_title('Linhas Adicionadas')
axes[0, 1].set_ylabel('Quantidade')

axes[1, 0].boxplot([merged['deletions'], closed['deletions']], labels=['MERGED', 'CLOSED'])
axes[1, 0].set_title('Linhas Removidas')
axes[1, 0].set_ylabel('Quantidade')

axes[1, 1].boxplot([merged['total_changes'], closed['total_changes']], labels=['MERGED', 'CLOSED'])
axes[1, 1].set_title('Total de Mudancas')
axes[1, 1].set_ylabel('Quantidade')

plt.tight_layout()
plt.savefig('graficos/RQ01_tamanho_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ01")

# RQ02
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ02 - Tempo de Analise vs Status do PR', fontweight='bold')
ax.boxplot([merged['review_duration_hours'], closed['review_duration_hours']], labels=['MERGED', 'CLOSED'])
ax.set_ylabel('Horas')
ax.set_yscale('log')
ax.set_title('Intervalo entre Criacao e Merge/Close')
plt.tight_layout()
plt.savefig('graficos/RQ02_tempo_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ02")

# RQ03
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ03 - Descricao vs Status do PR', fontweight='bold')
ax.boxplot([merged['body_length'], closed['body_length']], labels=['MERGED', 'CLOSED'])
ax.set_ylabel('Caracteres')
ax.set_title('Comprimento da Descricao')
plt.tight_layout()
plt.savefig('graficos/RQ03_descricao_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ03")

# RQ04
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('RQ04 - Interacoes vs Status do PR', fontweight='bold')
axes[0].boxplot([merged['reviews'], closed['reviews']], labels=['MERGED', 'CLOSED'])
axes[0].set_title('Numero de Reviews')
axes[0].set_ylabel('Quantidade')
axes[1].boxplot([merged['comments_count'], closed['comments_count']], labels=['MERGED', 'CLOSED'])
axes[1].set_title('Numero de Comentarios')
axes[1].set_ylabel('Quantidade')
plt.tight_layout()
plt.savefig('graficos/RQ04_interacoes_vs_status.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ04")

# RQ05
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('RQ05 - Tamanho vs Numero de Revisoes', fontweight='bold')
axes[0, 0].scatter(df['changed_files'], df['numero_de_revisoes'], alpha=0.5)
axes[0, 0].set_title('Arquivos vs Reviews')
axes[0, 0].set_xlabel('Arquivos')
axes[0, 0].set_ylabel('Reviews')
axes[0, 1].scatter(df['additions'], df['numero_de_revisoes'], alpha=0.5)
axes[0, 1].set_title('Adicoes vs Reviews')
axes[0, 1].set_xlabel('Adicoes')
axes[0, 1].set_ylabel('Reviews')
axes[1, 0].scatter(df['deletions'], df['numero_de_revisoes'], alpha=0.5)
axes[1, 0].set_title('Delecoes vs Reviews')
axes[1, 0].set_xlabel('Delecoes')
axes[1, 0].set_ylabel('Reviews')
axes[1, 1].scatter(df['total_changes'], df['numero_de_revisoes'], alpha=0.5)
axes[1, 1].set_title('Total Mudancas vs Reviews')
axes[1, 1].set_xlabel('Total Mudancas')
axes[1, 1].set_ylabel('Reviews')
plt.tight_layout()
plt.savefig('graficos/RQ05_tamanho_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ05")

# RQ06
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ06 - Tempo de Analise vs Numero de Revisoes', fontweight='bold')
ax.scatter(df['review_duration_hours'], df['numero_de_revisoes'], alpha=0.5)
ax.set_xlabel('Tempo de Analise (horas)')
ax.set_ylabel('Numero de Reviews')
ax.set_xscale('log')
plt.tight_layout()
plt.savefig('graficos/RQ06_tempo_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ06")

# RQ07
fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle('RQ07 - Descricao vs Numero de Revisoes', fontweight='bold')
ax.scatter(df['body_length'], df['numero_de_revisoes'], alpha=0.5)
ax.set_xlabel('Comprimento da Descricao (caracteres)')
ax.set_ylabel('Numero de Reviews')
plt.tight_layout()
plt.savefig('graficos/RQ07_descricao_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ07")

# RQ08
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('RQ08 - Interacoes vs Numero de Revisoes', fontweight='bold')
axes[0].scatter(df['reviews'], df['numero_de_revisoes'], alpha=0.5)
axes[0].set_title('Numero de Reviews vs Reviews Totais')
axes[0].set_xlabel('Reviews')
axes[0].set_ylabel('Reviews')
axes[1].scatter(df['comments_count'], df['numero_de_revisoes'], alpha=0.5)
axes[1].set_title('Comentarios vs Reviews')
axes[1].set_xlabel('Comentarios')
axes[1].set_ylabel('Reviews')
plt.tight_layout()
plt.savefig('graficos/RQ08_interacoes_vs_reviews.png', dpi=300, bbox_inches='tight')
plt.close()
print("[OK] RQ08")

# Calcular correlacoes
print("\n=== CORRELACOES SPEARMAN ===")
status_numeric = (df['state'] == 'MERGED').astype(int)

metricas = {
    'changed_files': 'Arquivos modificados',
    'additions': 'Linhas adicionadas',
    'deletions': 'Linhas removidas',
    'total_changes': 'Total de mudancas',
    'review_duration_hours': 'Tempo de analise (horas)',
    'body_length': 'Comprimento descricao',
    'reviews': 'Reviews',
    'comments_count': 'Comentarios',
}

resultados = {}
for col, nome in metricas.items():
    r_status, p_status = spearmanr(df[col], status_numeric)
    r_review, p_review = spearmanr(df[col], df['numero_de_revisoes'])
    
    sig_status = "SIM" if p_status < 0.05 else "NAO"
    sig_review = "SIM" if p_review < 0.05 else "NAO"
    
    resultados[nome] = {
        'vs_status_merged': {'r': float(r_status), 'p': float(p_status), 'significante': p_status < 0.05},
        'vs_num_reviews': {'r': float(r_review), 'p': float(p_review), 'significante': p_review < 0.05}
    }
    
    print(f"\n{nome}:")
    print(f"  vs Status (MERGED): r={r_status:.4f}, p={p_status:.6f}, Significante={sig_status}")
    print(f"  vs Num Reviews: r={r_review:.4f}, p={p_review:.6f}, Significante={sig_review}")

# Salvar resultados
with open('relatorio_analise.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)

print("\n" + "="*50)
print("GRAFICOS SALVOS EM: graficos/")
print("RELATORIO JSON: relatorio_analise.json")
print("="*50)
