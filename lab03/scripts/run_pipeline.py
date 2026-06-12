#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Master - Executa toda análise de LAB03
1. Análise de dados e gráficos
2. Geração de PDF com resultados
"""

import subprocess
import sys
from pathlib import Path

def instalar_dependencias():
    """Instala dependências necessárias"""
    print("📦 Verificando dependências...")
    
    pacotes_necessarios = [
        'pandas',
        'numpy',
        'matplotlib',
        'seaborn',
        'scipy',
        'reportlab'
    ]
    
    for pacote in pacotes_necessarios:
        try:
            __import__(pacote)
            print(f"  ✅ {pacote} já instalado")
        except ImportError:
            print(f"  📥 Instalando {pacote}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pacote, "-q"])
            print(f"  ✅ {pacote} instalado")

def executar_analise():
    """Executa análise de dados"""
    print("\n" + "=" * 60)
    print("ETAPA 1: ANÁLISE DE DADOS E GRÁFICOS")
    print("=" * 60)
    
    script_path = Path(__file__).parent / "analise_e_graficos.py"
    
    if script_path.exists():
        resultado = subprocess.run([sys.executable, str(script_path)], cwd=Path(__file__).parent.parent)
        return resultado.returncode == 0
    else:
        print(f"❌ Script não encontrado: {script_path}")
        return False

def gerar_pdf():
    """Gera PDF com resultados"""
    print("\n" + "=" * 60)
    print("ETAPA 2: GERAÇÃO DE RELATÓRIO PDF")
    print("=" * 60)
    
    script_path = Path(__file__).parent / "gerar_pdf.py"
    
    if script_path.exists():
        resultado = subprocess.run([sys.executable, str(script_path)], cwd=Path(__file__).parent.parent)
        return resultado.returncode == 0
    else:
        print(f"❌ Script não encontrado: {script_path}")
        return False

def main():
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║     LAB03 - PIPELINE DE ANÁLISE COMPLETO                       ║")
    print("║  Geração de Gráficos e Relatório PDF - Code Review no GitHub  ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    # Instalar dependências
    instalar_dependencias()
    
    # Executar análise
    if not executar_analise():
        print("\n❌ Erro na etapa de análise")
        return 1
    
    # Gerar PDF
    if not gerar_pdf():
        print("\n❌ Erro na geração do PDF")
        return 1
    
    print("\n" + "╔════════════════════════════════════════════════════════════════╗")
    print("║                  ✅ PIPELINE CONCLUÍDO COM SUCESSO!              ║")
    print("║                                                                  ║")
    print("║  Saídas geradas:                                                ║")
    print("║  • Gráficos: graficos/RQ0[1-8]_*.png                           ║")
    print("║  • Relatório JSON: relatorio_analise.json                       ║")
    print("║  • Relatório PDF: relatorio_lab03.pdf                           ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
