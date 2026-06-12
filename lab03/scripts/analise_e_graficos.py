#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analise de PRs e Geracao de Graficos para LAB03
Responde as 8 questoes de pesquisa sobre Code Review no GitHub
"""

import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr
from datetime import datetime
import warnings
import os
from pathlib import Path

warnings.filterwarnings('ignore')

# Configuracao de estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'

class AnalisadorPRs:
    def __init__(self, base_path="data/raw"):
        self.base_path = Path(base_path)
        self.dataset_json = self.base_path / "dataset_prs.json"
        self.df = None
        self.relatorio_data = {}
        
    def carregar_dados(self):
        """Carrega dados do JSON e prepara DataFrame"""
        print("[LOAD] Carregando dados...")
        
        if not self.dataset_json.exists():
            raise FileNotFoundError(f"Arquivo {self.dataset_json} não encontrado")
        
        # Carregar JSON em chunks para evitar memória
        with open(self.dataset_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Converter para DataFrame
        self.df = pd.DataFrame(data)
        
        # Filtrar PRs com status MERGED ou CLOSED
        self.df = self.df[self.df['state'].isin(['MERGED', 'CLOSED'])].copy()
        
        # Converter tipos de dados
        self.df['changed_files'] = pd.to_numeric(self.df['changed_files'], errors='coerce')
        self.df['additions'] = pd.to_numeric(self.df['additions'], errors='coerce')
        self.df['deletions'] = pd.to_numeric(self.df['deletions'], errors='coerce')
        self.df['body_length'] = pd.to_numeric(self.df['body_length'], errors='coerce')
        self.df['participants_count'] = pd.to_numeric(self.df['participants_count'], errors='coerce')
        self.df['comments_count'] = pd.to_numeric(self.df['comments_count'], errors='coerce')
        self.df['reviews_count'] = pd.to_numeric(self.df['reviews_count'], errors='coerce')
        self.df['review_duration_hours'] = pd.to_numeric(self.df['review_duration_hours'], errors='coerce')
        
        # Remover NaNs
        self.df = self.df.dropna(subset=[
            'changed_files', 'additions', 'deletions', 'body_length', 
            'participants_count', 'comments_count', 'reviews_count', 
            'review_duration_hours'
        ])
        
        # Filtrar: apenas PRs com pelo menos 1 review
        self.df = self.df[self.df['reviews_count'] >= 1].copy()
        
        # Filtrar: PRs revisados por pelo menos 1 hora
        self.df = self.df[self.df['review_duration_hours'] >= 1.0].copy()
        
        print(f"✅ Dados carregados: {len(self.df)} PRs após filtros")
        print(f"   - Campos: {list(self.df.columns)}")
        return self.df
    
    def estatisticas_descritivas(self):
        """Gera estatísticas descritivas dos dados"""
        print("\n📊 Estatísticas Descritivas:")
        
        metricas = {
            'Tamanho (arquivos)': 'changed_files',
            'Adições (linhas)': 'additions',
            'Deleções (linhas)': 'deletions',
            'Total linhas modificadas': 'total_changes',
            'Tempo análise (horas)': 'review_duration_hours',
            'Descrição (caracteres)': 'body_length',
            'Participantes': 'participants_count',
            'Comentários': 'comments_count',
            'Reviews': 'reviews_count'
        }
        
        # Calcular total de mudanças
        self.df['total_changes'] = self.df['additions'] + self.df['deletions']
        
        stats_dict = {}
        for nome, coluna in metricas.items():
            if coluna in self.df.columns:
                stats_dict[nome] = {
                    'Mediana': self.df[coluna].median(),
                    'Média': self.df[coluna].mean(),
                    'Mín': self.df[coluna].min(),
                    'Máx': self.df[coluna].max(),
                    'Q1': self.df[coluna].quantile(0.25),
                    'Q3': self.df[coluna].quantile(0.75)
                }
                print(f"\n{nome}:")
                print(f"  Mediana: {stats_dict[nome]['Mediana']:.2f}")
                print(f"  Média: {stats_dict[nome]['Média']:.2f}")
                print(f"  Intervalo: [{stats_dict[nome]['Mín']:.2f}, {stats_dict[nome]['Máx']:.2f}]")
        
        self.relatorio_data['estatisticas'] = stats_dict
        return stats_dict
    
    def correlacao_tamanho_status(self):
        """RQ01 + RQ05: Tamanho vs Status/Reviews"""
        print("\n🔍 Análise: Tamanho vs Status/Reviews")
        
        results = {}
        
        # Para cada métrica de tamanho
        metricas_tamanho = {
            'Arquivos mudados': 'changed_files',
            'Linhas adicionadas': 'additions',
            'Linhas removidas': 'deletions',
            'Total de mudanças': 'total_changes'
        }
        
        for nome, coluna in metricas_tamanho.items():
            # Correlação com status (MERGED=1, CLOSED=0)
            status_numeric = (self.df['state'] == 'MERGED').astype(int)
            corr, p_value = spearmanr(self.df[coluna], status_numeric)
            
            results[f"{nome} → Status"] = {
                'correlation': corr,
                'p_value': p_value,
                'significante': p_value < 0.05
            }
            
            # Correlação com número de reviews
            corr_rev, p_rev = spearmanr(self.df[coluna], self.df['reviews_count'])
            results[f"{nome} → Reviews"] = {
                'correlation': corr_rev,
                'p_value': p_rev,
                'significante': p_rev < 0.05
            }
        
        for teste, dados in results.items():
            sig = "✓" if dados['significante'] else "✗"
            print(f"  {sig} {teste}: r={dados['correlation']:.3f}, p={dados['p_value']:.4f}")
        
        self.relatorio_data['rq01_05'] = results
        return results
    
    def correlacao_tempo_analise(self):
        """RQ02 + RQ06: Tempo de análise vs Status/Reviews"""
        print("\n🔍 Análise: Tempo de Análise vs Status/Reviews")
        
        results = {}
        
        # Correlação com status
        status_numeric = (self.df['state'] == 'MERGED').astype(int)
        corr, p_value = spearmanr(self.df['review_duration_hours'], status_numeric)
        
        results['Tempo → Status'] = {
            'correlation': corr,
            'p_value': p_value,
            'significante': p_value < 0.05
        }
        
        # Correlação com número de reviews
        corr_rev, p_rev = spearmanr(self.df['review_duration_hours'], self.df['reviews_count'])
        results['Tempo → Reviews'] = {
            'correlation': corr_rev,
            'p_value': p_rev,
            'significante': p_rev < 0.05
        }
        
        for teste, dados in results.items():
            sig = "✓" if dados['significante'] else "✗"
            print(f"  {sig} {teste}: r={dados['correlation']:.3f}, p={dados['p_value']:.4f}")
        
        self.relatorio_data['rq02_06'] = results
        return results
    
    def correlacao_descricao(self):
        """RQ03 + RQ07: Descrição vs Status/Reviews"""
        print("\n🔍 Análise: Descrição vs Status/Reviews")
        
        results = {}
        
        # Correlação com status
        status_numeric = (self.df['state'] == 'MERGED').astype(int)
        corr, p_value = spearmanr(self.df['body_length'], status_numeric)
        
        results['Descrição → Status'] = {
            'correlation': corr,
            'p_value': p_value,
            'significante': p_value < 0.05
        }
        
        # Correlação com número de reviews
        corr_rev, p_rev = spearmanr(self.df['body_length'], self.df['reviews_count'])
        results['Descrição → Reviews'] = {
            'correlation': corr_rev,
            'p_value': p_rev,
            'significante': p_rev < 0.05
        }
        
        for teste, dados in results.items():
            sig = "✓" if dados['significante'] else "✗"
            print(f"  {sig} {teste}: r={dados['correlation']:.3f}, p={dados['p_value']:.4f}")
        
        self.relatorio_data['rq03_07'] = results
        return results
    
    def correlacao_interacoes(self):
        """RQ04 + RQ08: Interações vs Status/Reviews"""
        print("\n🔍 Análise: Interações vs Status/Reviews")
        
        results = {}
        
        metricas_interacao = {
            'Participantes': 'participants_count',
            'Comentários': 'comments_count'
        }
        
        status_numeric = (self.df['state'] == 'MERGED').astype(int)
        
        for nome, coluna in metricas_interacao.items():
            # Correlação com status
            corr, p_value = spearmanr(self.df[coluna], status_numeric)
            results[f"{nome} → Status"] = {
                'correlation': corr,
                'p_value': p_value,
                'significante': p_value < 0.05
            }
            
            # Correlação com número de reviews
            corr_rev, p_rev = spearmanr(self.df[coluna], self.df['reviews_count'])
            results[f"{nome} → Reviews"] = {
                'correlation': corr_rev,
                'p_value': p_rev,
                'significante': p_rev < 0.05
            }
        
        for teste, dados in results.items():
            sig = "✓" if dados['significante'] else "✗"
            print(f"  {sig} {teste}: r={dados['correlation']:.3f}, p={dados['p_value']:.4f}")
        
        self.relatorio_data['rq04_08'] = results
        return results
    
    def gerar_graficos(self, output_dir="graficos"):
        """Gera todos os gráficos para responder as questões"""
        print("\n📈 Gerando gráficos...")
        
        Path(output_dir).mkdir(exist_ok=True)
        
        # RQ01: Tamanho vs Status
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('RQ01 - Tamanho vs Feedback Final (Status do PR)', fontsize=14, fontweight='bold')
        
        merged = self.df[self.df['state'] == 'MERGED']
        closed = self.df[self.df['state'] == 'CLOSED']
        
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
        axes[1, 1].set_title('Total de Mudanças (Add + Del)')
        axes[1, 1].set_ylabel('Quantidade')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ01_tamanho_vs_status.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # RQ02: Tempo de análise vs Status
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle('RQ02 - Tempo de Análise vs Feedback Final (Status do PR)', fontsize=14, fontweight='bold')
        
        ax.boxplot([merged['review_duration_hours'], closed['review_duration_hours']], labels=['MERGED', 'CLOSED'])
        ax.set_title('Tempo entre Criação e Merge/Close (em horas)')
        ax.set_ylabel('Horas')
        ax.set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ02_tempo_vs_status.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # RQ03: Descrição vs Status
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle('RQ03 - Descrição vs Feedback Final (Status do PR)', fontsize=14, fontweight='bold')
        
        ax.boxplot([merged['body_length'], closed['body_length']], labels=['MERGED', 'CLOSED'])
        ax.set_title('Comprimento da Descrição (caracteres)')
        ax.set_ylabel('Caracteres')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ03_descricao_vs_status.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # RQ04: Interações vs Status
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('RQ04 - Interações vs Feedback Final (Status do PR)', fontsize=14, fontweight='bold')
        
        axes[0].boxplot([merged['participants_count'], closed['participants_count']], labels=['MERGED', 'CLOSED'])
        axes[0].set_title('Número de Participantes')
        axes[0].set_ylabel('Quantidade')
        
        axes[1].boxplot([merged['comments_count'], closed['comments_count']], labels=['MERGED', 'CLOSED'])
        axes[1].set_title('Número de Comentários')
        axes[1].set_ylabel('Quantidade')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ04_interacoes_vs_status.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # RQ05: Tamanho vs Número de Reviews
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('RQ05 - Tamanho vs Número de Revisões', fontsize=14, fontweight='bold')
        
        axes[0, 0].scatter(self.df['changed_files'], self.df['reviews_count'], alpha=0.5)
        axes[0, 0].set_title('Arquivos Modificados vs Reviews')
        axes[0, 0].set_xlabel('Arquivos')
        axes[0, 0].set_ylabel('Número de Reviews')
        
        axes[0, 1].scatter(self.df['additions'], self.df['reviews_count'], alpha=0.5)
        axes[0, 1].set_title('Linhas Adicionadas vs Reviews')
        axes[0, 1].set_xlabel('Linhas Adicionadas')
        axes[0, 1].set_ylabel('Número de Reviews')
        
        axes[1, 0].scatter(self.df['deletions'], self.df['reviews_count'], alpha=0.5)
        axes[1, 0].set_title('Linhas Removidas vs Reviews')
        axes[1, 0].set_xlabel('Linhas Removidas')
        axes[1, 0].set_ylabel('Número de Reviews')
        
        axes[1, 1].scatter(self.df['total_changes'], self.df['reviews_count'], alpha=0.5)
        axes[1, 1].set_title('Total de Mudanças vs Reviews')
        axes[1, 1].set_xlabel('Total de Mudanças')
        axes[1, 1].set_ylabel('Número de Reviews')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ05_tamanho_vs_reviews.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # RQ06: Tempo de análise vs Número de Reviews
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle('RQ06 - Tempo de Análise vs Número de Revisões', fontsize=14, fontweight='bold')
        
        ax.scatter(self.df['review_duration_hours'], self.df['reviews_count'], alpha=0.5)
        ax.set_xlabel('Tempo de Análise (horas)')
        ax.set_ylabel('Número de Reviews')
        ax.set_xscale('log')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ06_tempo_vs_reviews.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # RQ07: Descrição vs Número de Reviews
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle('RQ07 - Descrição vs Número de Revisões', fontsize=14, fontweight='bold')
        
        ax.scatter(self.df['body_length'], self.df['reviews_count'], alpha=0.5)
        ax.set_xlabel('Comprimento da Descrição (caracteres)')
        ax.set_ylabel('Número de Reviews')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ07_descricao_vs_reviews.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # RQ08: Interações vs Número de Reviews
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('RQ08 - Interações vs Número de Revisões', fontsize=14, fontweight='bold')
        
        axes[0].scatter(self.df['participants_count'], self.df['reviews_count'], alpha=0.5)
        axes[0].set_xlabel('Número de Participantes')
        axes[0].set_ylabel('Número de Reviews')
        
        axes[1].scatter(self.df['comments_count'], self.df['reviews_count'], alpha=0.5)
        axes[1].set_xlabel('Número de Comentários')
        axes[1].set_ylabel('Número de Reviews')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/RQ08_interacoes_vs_reviews.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Gráficos salvos em '{output_dir}/'")
        return output_dir
    
    def salvar_relatorio_json(self, output_path="relatorio_analise.json"):
        """Salva dados do relatório em JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.relatorio_data, f, indent=2, default=str)
        print(f"✅ Relatório JSON salvo em '{output_path}'")

def main():
    print("=" * 60)
    print("ANÁLISE DE CODE REVIEW - LAB03")
    print("=" * 60)
    
    try:
        analisador = AnalisadorPRs()
        
        # Carregar dados
        analisador.carregar_dados()
        
        # Estatísticas
        analisador.estatisticas_descritivas()
        
        # Análises de correlação
        analisador.correlacao_tamanho_status()
        analisador.correlacao_tempo_analise()
        analisador.correlacao_descricao()
        analisador.correlacao_interacoes()
        
        # Gerar gráficos
        analisador.gerar_graficos()
        
        # Salvar relatório
        analisador.salvar_relatorio_json()
        
        print("\n" + "=" * 60)
        print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
