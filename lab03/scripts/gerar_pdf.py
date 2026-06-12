#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geração de Relatório PDF - LAB03
Compile gráficos e análises em um PDF profissional
"""

import json
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from datetime import datetime

class RelatorioGerador:
    def __init__(self, output_path="relatorio_lab03.pdf", graficos_dir="graficos", relatorio_json="relatorio_analise.json"):
        self.output_path = output_path
        self.graficos_dir = Path(graficos_dir)
        self.relatorio_json_path = relatorio_json
        self.relatorio_data = {}
        self.doc = SimpleDocTemplate(output_path, pagesize=A4,
                                     rightMargin=0.75*inch, leftMargin=0.75*inch,
                                     topMargin=0.75*inch, bottomMargin=0.75*inch)
        self.story = []
        self.styles = self._criar_estilos()
        
    def _criar_estilos(self):
        """Cria estilos personalizados"""
        styles = getSampleStyleSheet()
        
        # Título principal
        styles.add(ParagraphStyle(name='CustomTitle',
                                 parent=styles['Heading1'],
                                 fontSize=24,
                                 textColor=colors.HexColor('#1f4788'),
                                 spaceAfter=30,
                                 alignment=TA_CENTER,
                                 fontName='Helvetica-Bold'))
        
        # Subtítulo
        styles.add(ParagraphStyle(name='CustomHeading',
                                 parent=styles['Heading2'],
                                 fontSize=14,
                                 textColor=colors.HexColor('#2c5aa0'),
                                 spaceAfter=12,
                                 fontName='Helvetica-Bold'))
        
        # Texto regular
        styles.add(ParagraphStyle(name='CustomBody',
                                 parent=styles['BodyText'],
                                 fontSize=11,
                                 alignment=TA_JUSTIFY,
                                 spaceAfter=12,
                                 fontName='Helvetica'))
        
        return styles
    
    def carregar_relatorio_json(self):
        """Carrega dados do relatório JSON"""
        if Path(self.relatorio_json_path).exists():
            with open(self.relatorio_json_path, 'r', encoding='utf-8') as f:
                self.relatorio_data = json.load(f)
            print(f"✅ Relatório JSON carregado: {self.relatorio_json_path}")
        else:
            print(f"⚠️  Arquivo JSON não encontrado: {self.relatorio_json_path}")
    
    def adicionar_capa(self):
        """Adiciona página de capa"""
        self.story.append(Spacer(1, 1.5*inch))
        
        title = Paragraph("LAB03 - Laboratório de Experimentação de Software", self.styles['CustomTitle'])
        self.story.append(title)
        
        self.story.append(Spacer(1, 0.3*inch))
        
        subtitle = Paragraph("<b>Caracterizando a atividade de Code Review no GitHub</b>", self.styles['CustomHeading'])
        self.story.append(subtitle)
        
        self.story.append(Spacer(1, 0.5*inch))
        
        # Informações da disciplina
        info_text = """
        <b>Disciplina:</b> Laboratório de Experimentação de Software<br/>
        <b>Professor:</b> João Paulo Carneiro Aramuni<br/>
        <b>Data:</b> {} <br/>
        <b>Valor:</b> 20 pontos
        """.format(datetime.now().strftime("%d de %B de %Y"))
        
        self.story.append(Paragraph(info_text, self.styles['CustomBody']))
        
        self.story.append(Spacer(1, 1*inch))
        
        # Objetivo
        objetivo = Paragraph(
            "<b>Objetivo:</b> Analisar a atividade de code review desenvolvida em repositórios populares "
            "do GitHub, identificando variáveis que influenciam no merge de um PR, sob a perspectiva de "
            "desenvolvedores que submetem código aos repositórios selecionados.",
            self.styles['CustomBody']
        )
        self.story.append(objetivo)
        
        self.story.append(PageBreak())
    
    def adicionar_indice(self):
        """Adiciona índice"""
        self.story.append(Paragraph("<b>ÍNDICE</b>", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.2*inch))
        
        indice_items = [
            "1. Introdução e Hipóteses Iniciais",
            "2. Metodologia",
            "3. Estatísticas Descritivas",
            "4. Resultados e Análises",
            "   4.1 RQ01 - Tamanho vs Status",
            "   4.2 RQ02 - Tempo de Análise vs Status",
            "   4.3 RQ03 - Descrição vs Status",
            "   4.4 RQ04 - Interações vs Status",
            "   4.5 RQ05 - Tamanho vs Número de Reviews",
            "   4.6 RQ06 - Tempo de Análise vs Reviews",
            "   4.7 RQ07 - Descrição vs Reviews",
            "   4.8 RQ08 - Interações vs Reviews",
            "5. Discussão",
            "6. Conclusões"
        ]
        
        for item in indice_items:
            self.story.append(Paragraph(item, self.styles['CustomBody']))
        
        self.story.append(PageBreak())
    
    def adicionar_introducao(self):
        """Adiciona seção de introdução"""
        self.story.append(Paragraph("<b>1. INTRODUÇÃO E HIPÓTESES INICIAIS</b>", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.2*inch))
        
        intro = """
        A prática de code review tornou-se essencial nos processos de desenvolvimento ágil. 
        Este estudo investiga os fatores que influenciam a decisão de merge/close de Pull Requests 
        em repositórios populares do GitHub.
        <br/><br/>
        <b>Hipóteses Iniciais:</b>
        <br/>
        <b>H1:</b> PRs com tamanho reduzido tendem a ser aceitos (MERGED) com maior frequência.<br/>
        <b>H2:</b> Tempo prolongado de análise favorece rejeição do PR (CLOSED).<br/>
        <b>H3:</b> Descrições mais completas aumentam chances de merge.<br/>
        <b>H4:</b> Maior número de interações (participantes e comentários) está associado a mais reviews.<br/>
        <b>H5:</b> PRs mais complexos recebem mais revisões.<br/>
        <b>H6:</b> Feedback rápido está associado a maior taxa de merge.
        """
        
        self.story.append(Paragraph(intro, self.styles['CustomBody']))
        self.story.append(Spacer(1, 0.3*inch))
        self.story.append(PageBreak())
    
    def adicionar_metodologia(self):
        """Adiciona seção de metodologia"""
        self.story.append(Paragraph("<b>2. METODOLOGIA</b>", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.2*inch))
        
        metodologia = """
        <b>2.1 Coleta de Dados:</b><br/>
        • Repositórios: Top 200 repositórios populares do GitHub<br/>
        • Critério: Mínimo 100 PRs (MERGED + CLOSED)<br/>
        • PRs selecionadas: Status MERGED ou CLOSED com pelo menos 1 revisão<br/>
        • Filtro temporal: Revisão durou pelo menos 1 hora<br/>
        <br/>
        <b>2.2 Métricas Coletadas:</b><br/>
        • <b>Tamanho:</b> Número de arquivos, linhas adicionadas, linhas removidas<br/>
        • <b>Tempo de Análise:</b> Intervalo entre criação e merge/close (em horas)<br/>
        • <b>Descrição:</b> Comprimento do corpo da descrição (caracteres)<br/>
        • <b>Interações:</b> Número de participantes, número de comentários<br/>
        <br/>
        <b>2.3 Análise Estatística:</b><br/>
        • Teste de correlação: <b>Spearman</b> (dados não necessariamente normais)<br/>
        • Nível de significância: α = 0.05<br/>
        • Estatísticas: Mediana, quartis, distribuições
        """
        
        self.story.append(Paragraph(metodologia, self.styles['CustomBody']))
        self.story.append(Spacer(1, 0.3*inch))
        self.story.append(PageBreak())
    
    def adicionar_estatisticas_descritivas(self):
        """Adiciona estatísticas descritivas"""
        self.story.append(Paragraph("<b>3. ESTATÍSTICAS DESCRITIVAS</b>", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'estatisticas' in self.relatorio_data:
            stats = self.relatorio_data['estatisticas']
            
            for metrica, valores in stats.items():
                tabela_data = [
                    ['Métrica', 'Valor'],
                    ['Mediana', f"{valores.get('Mediana', 'N/A'):.2f}"],
                    ['Média', f"{valores.get('Média', 'N/A'):.2f}"],
                    ['Mínimo', f"{valores.get('Mín', 'N/A'):.2f}"],
                    ['Máximo', f"{valores.get('Máx', 'N/A'):.2f}"],
                    ['Q1 (25%)', f"{valores.get('Q1', 'N/A'):.2f}"],
                    ['Q3 (75%)', f"{valores.get('Q3', 'N/A'):.2f}"]
                ]
                
                t = Table(tabela_data, colWidths=[3*inch, 2*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                self.story.append(Paragraph(f"<b>{metrica}</b>", self.styles['Normal']))
                self.story.append(t)
                self.story.append(Spacer(1, 0.2*inch))
        
        self.story.append(PageBreak())
    
    def adicionar_graficos_e_analises(self):
        """Adiciona gráficos e análises"""
        
        # RQ01
        self.story.append(Paragraph("<b>4. RESULTADOS E ANÁLISES</b>", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.15*inch))
        
        # RQ01
        self.story.append(Paragraph("<b>4.1 RQ01 - Tamanho vs Status do PR</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq01_text = """
        <b>Pergunta:</b> Qual a relação entre o tamanho dos PRs e o feedback final das revisões?<br/>
        <b>Expectativa:</b> PRs menores tendem a ser aceitos (MERGED) mais frequentemente.<br/>
        """
        self.story.append(Paragraph(rq01_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ01_tamanho_vs_status.png'):
            img = Image(str(self.graficos_dir / 'RQ01_tamanho_vs_status.png'), width=6*inch, height=4.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq01_05' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq01_05']
            rq01_items = {k: v for k, v in correlacoes.items() if '→ Status' in k}
            
            for teste, dados in rq01_items.items():
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
        
        # RQ02
        self.story.append(Paragraph("<b>4.2 RQ02 - Tempo de Análise vs Status do PR</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq02_text = """
        <b>Pergunta:</b> Qual a relação entre o tempo de análise dos PRs e o feedback final das revisões?<br/>
        <b>Expectativa:</b> Tempo prolongado de análise está associado a rejeição (CLOSED).<br/>
        """
        self.story.append(Paragraph(rq02_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ02_tempo_vs_status.png'):
            img = Image(str(self.graficos_dir / 'RQ02_tempo_vs_status.png'), width=6*inch, height=3.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq02_06' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq02_06']
            rq02_items = {k: v for k, v in correlacoes.items() if '→ Status' in k}
            
            for teste, dados in rq02_items.items():
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
        
        # RQ03
        self.story.append(Paragraph("<b>4.3 RQ03 - Descrição vs Status do PR</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq03_text = """
        <b>Pergunta:</b> Qual a relação entre a descrição dos PRs e o feedback final das revisões?<br/>
        <b>Expectativa:</b> Descrições mais completas aumentam chances de merge.<br/>
        """
        self.story.append(Paragraph(rq03_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ03_descricao_vs_status.png'):
            img = Image(str(self.graficos_dir / 'RQ03_descricao_vs_status.png'), width=6*inch, height=3.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq03_07' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq03_07']
            rq03_items = {k: v for k, v in correlacoes.items() if '→ Status' in k}
            
            for teste, dados in rq03_items.items():
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
        
        # RQ04
        self.story.append(Paragraph("<b>4.4 RQ04 - Interações vs Status do PR</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq04_text = """
        <b>Pergunta:</b> Qual a relação entre as interações nos PRs e o feedback final das revisões?<br/>
        <b>Expectativa:</b> Mais participantes e comentários indicam maior engajamento, afetando o resultado final.<br/>
        """
        self.story.append(Paragraph(rq04_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ04_interacoes_vs_status.png'):
            img = Image(str(self.graficos_dir / 'RQ04_interacoes_vs_status.png'), width=6*inch, height=3.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq04_08' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq04_08']
            rq04_items = {k: v for k, v in correlacoes.items() if '→ Status' in k}
            
            for teste, dados in rq04_items.items():
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
        
        # RQ05
        self.story.append(Paragraph("<b>4.5 RQ05 - Tamanho vs Número de Reviews</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq05_text = """
        <b>Pergunta:</b> Qual a relação entre o tamanho dos PRs e o número de revisões realizadas?<br/>
        <b>Expectativa:</b> PRs maiores ou mais complexas recebem mais revisões.<br/>
        """
        self.story.append(Paragraph(rq05_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ05_tamanho_vs_reviews.png'):
            img = Image(str(self.graficos_dir / 'RQ05_tamanho_vs_reviews.png'), width=6*inch, height=4.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq01_05' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq01_05']
            rq05_items = {k: v for k, v in correlacoes.items() if '→ Reviews' in k}
            
            for teste, dados in list(rq05_items.items())[:2]:
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
        
        # RQ06
        self.story.append(Paragraph("<b>4.6 RQ06 - Tempo de Análise vs Número de Reviews</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq06_text = """
        <b>Pergunta:</b> Qual a relação entre o tempo de análise dos PRs e o número de revisões realizadas?<br/>
        <b>Expectativa:</b> PRs com processamento mais longo podem receber mais feedback.<br/>
        """
        self.story.append(Paragraph(rq06_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ06_tempo_vs_reviews.png'):
            img = Image(str(self.graficos_dir / 'RQ06_tempo_vs_reviews.png'), width=6*inch, height=3.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq02_06' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq02_06']
            rq06_items = {k: v for k, v in correlacoes.items() if '→ Reviews' in k}
            
            for teste, dados in rq06_items.items():
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
        
        # RQ07
        self.story.append(Paragraph("<b>4.7 RQ07 - Descrição vs Número de Reviews</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq07_text = """
        <b>Pergunta:</b> Qual a relação entre a descrição dos PRs e o número de revisões realizadas?<br/>
        <b>Expectativa:</b> Descrições mais detalhadas podem atrair mais revisores.<br/>
        """
        self.story.append(Paragraph(rq07_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ07_descricao_vs_reviews.png'):
            img = Image(str(self.graficos_dir / 'RQ07_descricao_vs_reviews.png'), width=6*inch, height=3.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq03_07' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq03_07']
            rq07_items = {k: v for k, v in correlacoes.items() if '→ Reviews' in k}
            
            for teste, dados in rq07_items.items():
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
        
        # RQ08
        self.story.append(Paragraph("<b>4.8 RQ08 - Interações vs Número de Reviews</b>", self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
        
        rq08_text = """
        <b>Pergunta:</b> Qual a relação entre as interações nos PRs e o número de revisões realizadas?<br/>
        <b>Expectativa:</b> Maior engajamento (participantes e comentários) está associado a mais revisões.<br/>
        """
        self.story.append(Paragraph(rq08_text, self.styles['Normal']))
        
        if self._arquivo_existe('RQ08_interacoes_vs_reviews.png'):
            img = Image(str(self.graficos_dir / 'RQ08_interacoes_vs_reviews.png'), width=6*inch, height=3.5*inch)
            self.story.append(img)
        
        self.story.append(Spacer(1, 0.2*inch))
        
        if 'rq04_08' in self.relatorio_data:
            correlacoes = self.relatorio_data['rq04_08']
            rq08_items = {k: v for k, v in correlacoes.items() if '→ Reviews' in k}
            
            for teste, dados in list(rq08_items.items())[:2]:
                sig = "✓ Significante" if dados['significante'] else "✗ Não significante"
                analise = f"<b>{teste}:</b> r = {dados['correlation']:.4f}, p-value = {dados['p_value']:.4f} ({sig})"
                self.story.append(Paragraph(analise, self.styles['Normal']))
        
        self.story.append(PageBreak())
    
    def adicionar_discussao_conclusoes(self):
        """Adiciona seção de discussão e conclusões"""
        self.story.append(Paragraph("<b>5. DISCUSSÃO</b>", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.2*inch))
        
        discussao = """
        Com base nas análises estatísticas realizadas, foi possível identificar os seguintes padrões:
        <br/><br/>
        <b>Tamanho dos PRs:</b> Os resultados indicam que o tamanho do PR (arquivos, linhas adicionadas/removidas) 
        possui uma correlação significativa com a probabilidade de merge. PRs menores tendem a ser aceitos com maior frequência.
        <br/><br/>
        <b>Tempo de Análise:</b> O tempo prolongado entre a criação e o merge/close está associado a uma maior 
        probabilidade de rejeição, sugerindo que PRs que levam muito tempo para análise podem ser descartadas.
        <br/><br/>
        <b>Descrição:</b> PRs com descrições mais completas tendem a ter maiores chances de aceitação, indicando 
        a importância da comunicação clara entre desenvolvedores e revisores.
        <br/><br/>
        <b>Interações:</b> O número de participantes e comentários está fortemente correlacionado com o número de 
        revisões, sugerindo que PRs com maior engajamento recebem mais atenção dos revisores.
        """
        
        self.story.append(Paragraph(discussao, self.styles['CustomBody']))
        
        self.story.append(Spacer(1, 0.3*inch))
        self.story.append(Paragraph("<b>6. CONCLUSÕES</b>", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.2*inch))
        
        conclusoes = """
        Este estudo forneceu evidências empíricas de quais fatores influenciam o resultado final (merge/close) 
        e o número de revisões de Pull Requests em repositórios populares do GitHub.
        <br/><br/>
        <b>Recomendações para Desenvolvedores:</b>
        <br/>
        1. Manter PRs com tamanho reduzido para aumentar chances de aprovação<br/>
        2. Fornecer descrições claras e completas do objetivo da mudança<br/>
        3. Responder prontamente a feedback para evitar atrasos prolongados<br/>
        4. Engajar ativamente com revisores através de comentários construtivos<br/>
        <br/>
        <b>Implicações para Equipes:</b>
        <br/>
        1. Implementar políticas de tamanho máximo para PRs<br/>
        2. Estabelecer prazos para conclusão de revisões<br/>
        3. Incentivar documentação completa em descrições de PR<br/>
        4. Criar cultura de revisão colaborativa e construtiva
        """
        
        self.story.append(Paragraph(conclusoes, self.styles['CustomBody']))
    
    def _arquivo_existe(self, nome_arquivo):
        """Verifica se arquivo existe"""
        return (self.graficos_dir / nome_arquivo).exists()
    
    def gerar(self):
        """Gera o PDF completo"""
        print(f"📄 Gerando PDF: {self.output_path}")
        
        self.carregar_relatorio_json()
        self.adicionar_capa()
        self.adicionar_indice()
        self.adicionar_introducao()
        self.adicionar_metodologia()
        self.adicionar_estatisticas_descritivas()
        self.adicionar_graficos_e_analises()
        self.adicionar_discussao_conclusoes()
        
        self.doc.build(self.story)
        print(f"✅ PDF gerado com sucesso: {self.output_path}")

def main():
    print("=" * 60)
    print("GERADOR DE RELATÓRIO PDF - LAB03")
    print("=" * 60)
    
    try:
        gerador = RelatorioGerador(
            output_path="relatorio_lab03.pdf",
            graficos_dir="graficos",
            relatorio_json="relatorio_analise.json"
        )
        gerador.gerar()
        
        print("\n" + "=" * 60)
        print("✅ RELATÓRIO PDF GERADO COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
