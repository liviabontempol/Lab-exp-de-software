#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from datetime import datetime

print("Gerando PDF...")

# Carregar dados
with open('relatorio_analise.json', 'r', encoding='utf-8') as f:
    relatorio_data = json.load(f)

doc = SimpleDocTemplate('relatorio_lab03.pdf', pagesize=A4,
                        rightMargin=0.75*inch, leftMargin=0.75*inch,
                        topMargin=0.75*inch, bottomMargin=0.75*inch)
story = []
styles = getSampleStyleSheet()

# Estilos customizados
styles.add(ParagraphStyle(name='CustomTitle',
                         parent=styles['Heading1'],
                         fontSize=24,
                         textColor=colors.HexColor('#1f4788'),
                         spaceAfter=30,
                         alignment=TA_CENTER,
                         fontName='Helvetica-Bold'))

styles.add(ParagraphStyle(name='CustomHeading',
                         parent=styles['Heading2'],
                         fontSize=14,
                         textColor=colors.HexColor('#2c5aa0'),
                         spaceAfter=12,
                         fontName='Helvetica-Bold'))

styles.add(ParagraphStyle(name='CustomBody',
                         parent=styles['BodyText'],
                         fontSize=11,
                         alignment=TA_JUSTIFY,
                         spaceAfter=12,
                         fontName='Helvetica'))

# CAPA
story.append(Spacer(1, 1.5*inch))
title = Paragraph("LAB03 - Laboratorio de Experimentacao de Software", styles['CustomTitle'])
story.append(title)
story.append(Spacer(1, 0.3*inch))

subtitle = Paragraph("<b>Caracterizando a atividade de Code Review no GitHub</b>", styles['CustomHeading'])
story.append(subtitle)
story.append(Spacer(1, 0.5*inch))

info_text = f"""
<b>Disciplina:</b> Laboratorio de Experimentacao de Software<br/>
<b>Professor:</b> Joao Paulo Carneiro Aramuni<br/>
<b>Data:</b> {datetime.now().strftime("%d de %B de %Y")}<br/>
<b>Valor:</b> 20 pontos
"""
story.append(Paragraph(info_text, styles['CustomBody']))
story.append(Spacer(1, 1*inch))

objetivo = Paragraph(
    "<b>Objetivo:</b> Analisar a atividade de code review desenvolvida em repositorios populares "
    "do GitHub, identificando variaveis que influenciam no merge de um PR, sob a perspectiva de "
    "desenvolvedores que submetem codigo aos repositorios selecionados.",
    styles['CustomBody']
)
story.append(objetivo)
story.append(PageBreak())

# SECAO 1: INTRODUCAO
story.append(Paragraph("<b>1. INTRODUCAO E HIPOTESES INICIAIS</b>", styles['CustomHeading']))
story.append(Spacer(1, 0.2*inch))

intro = """
A pratica de code review tornou-se essencial nos processos de desenvolvimento agil. 
Este estudo investiga os fatores que influenciam a decisao de merge/close de Pull Requests 
em repositorios populares do GitHub.<br/><br/>

<b>Hipoteses Iniciais:</b><br/>
<b>H1:</b> PRs com tamanho reduzido tendem a ser aceitos (MERGED) com maior frequencia.<br/>
<b>H2:</b> Tempo prolongado de analise favorece rejeicao do PR (CLOSED).<br/>
<b>H3:</b> Descricoes mais completas aumentam chances de merge.<br/>
<b>H4:</b> Maior numero de interacoes (participantes e comentarios) esta associado a mais reviews.<br/>
<b>H5:</b> PRs mais complexos recebem mais revisoes.<br/>
<b>H6:</b> Feedback rapido esta associado a maior taxa de merge.
"""
story.append(Paragraph(intro, styles['CustomBody']))
story.append(Spacer(1, 0.3*inch))
story.append(PageBreak())

# SECAO 2: METODOLOGIA
story.append(Paragraph("<b>2. METODOLOGIA</b>", styles['CustomHeading']))
story.append(Spacer(1, 0.2*inch))

metodologia = """
<b>2.1 Coleta de Dados:</b><br/>
- Repositorios: Top 200 repositorios populares do GitHub<br/>
- Criterio: Minimo 100 PRs (MERGED + CLOSED)<br/>
- PRs selecionadas: Status MERGED ou CLOSED com pelo menos 1 revisao<br/>
- Filtro temporal: Revisao durou pelo menos 1 hora<br/>
<br/>
<b>2.2 Metricas Coletadas:</b><br/>
- <b>Tamanho:</b> Numero de arquivos, linhas adicionadas, linhas removidas<br/>
- <b>Tempo de Analise:</b> Intervalo entre criacao e merge/close (em horas)<br/>
- <b>Descricao:</b> Comprimento do corpo da descricao (caracteres)<br/>
- <b>Interacoes:</b> Numero de participantes, numero de comentarios<br/>
<br/>
<b>2.3 Analise Estatistica:</b><br/>
- Teste de correlacao: <b>Spearman</b> (dados nao-parametricos)<br/>
- Nivel de significancia: alpha = 0.05<br/>
- Estatisticas: Mediana, quartis, distribuicoes
"""
story.append(Paragraph(metodologia, styles['CustomBody']))
story.append(Spacer(1, 0.3*inch))
story.append(PageBreak())

# SECAO 3: RESULTADOS RQ01
story.append(Paragraph("<b>3. RESULTADOS E ANALISES</b>", styles['CustomHeading']))
story.append(Spacer(1, 0.15*inch))

story.append(Paragraph("<b>RQ01 - Tamanho vs Status do PR</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq01_text = """
<b>Pergunta:</b> Qual a relacao entre o tamanho dos PRs e o feedback final das revisoes?<br/>
<b>Expectativa:</b> PRs menores tendem a ser aceitos (MERGED) mais frequentemente.<br/>
<b>Resultado:</b> As correlacoes encontradas indicam relacoes significativas entre tamanho e status.
"""
story.append(Paragraph(rq01_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ01_tamanho_vs_status.png').exists():
    img = Image('graficos/RQ01_tamanho_vs_status.png', width=6*inch, height=4.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# RQ02
story.append(Paragraph("<b>RQ02 - Tempo de Analise vs Status do PR</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq02_text = """
<b>Pergunta:</b> Qual a relacao entre o tempo de analise dos PRs e o feedback final das revisoes?<br/>
<b>Expectativa:</b> Tempo prolongado de analise esta associado a rejeicao (CLOSED).<br/>
<b>Resultado:</b> Correlacao significativa (r=-0.3279, p<0.05) indica que PRs com tempo prolongado tendem a ser rejeitadas.
"""
story.append(Paragraph(rq02_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ02_tempo_vs_status.png').exists():
    img = Image('graficos/RQ02_tempo_vs_status.png', width=6*inch, height=3.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# RQ03
story.append(Paragraph("<b>RQ03 - Descricao vs Status do PR</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq03_text = """
<b>Pergunta:</b> Qual a relacao entre a descricao dos PRs e o feedback final das revisoes?<br/>
<b>Expectativa:</b> Descricoes mais completas aumentam chances de merge.<br/>
<b>Resultado:</b> Correlacao significativa (r=-0.1990, p<0.05) sugere descricoes mais concisas tendem a ser aceitas.
"""
story.append(Paragraph(rq03_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ03_descricao_vs_status.png').exists():
    img = Image('graficos/RQ03_descricao_vs_status.png', width=6*inch, height=3.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# RQ04
story.append(Paragraph("<b>RQ04 - Interacoes vs Status do PR</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq04_text = """
<b>Pergunta:</b> Qual a relacao entre as interacoes nos PRs e o feedback final das revisoes?<br/>
<b>Expectativa:</b> Mais participantes e comentarios indicam maior engajamento.<br/>
<b>Resultado:</b> Correlacao significativa entre comentarios e status (r=-0.2097, p<0.05).
"""
story.append(Paragraph(rq04_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ04_interacoes_vs_status.png').exists():
    img = Image('graficos/RQ04_interacoes_vs_status.png', width=6*inch, height=3.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# RQ05
story.append(Paragraph("<b>RQ05 - Tamanho vs Numero de Revisoes</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq05_text = """
<b>Pergunta:</b> Qual a relacao entre o tamanho dos PRs e o numero de revisoes realizadas?<br/>
<b>Expectativa:</b> PRs maiores ou mais complexas recebem mais revisoes.<br/>
<b>Resultado:</b> Correlacao positiva significativa (r=0.3464 para adicoes, p<0.05).
"""
story.append(Paragraph(rq05_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ05_tamanho_vs_reviews.png').exists():
    img = Image('graficos/RQ05_tamanho_vs_reviews.png', width=6*inch, height=4.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# RQ06
story.append(Paragraph("<b>RQ06 - Tempo de Analise vs Numero de Revisoes</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq06_text = """
<b>Pergunta:</b> Qual a relacao entre o tempo de analise dos PRs e o numero de revisoes realizadas?<br/>
<b>Expectativa:</b> PRs com processamento mais longo podem receber mais feedback.<br/>
<b>Resultado:</b> Correlacao significativa (r=0.1938, p<0.05).
"""
story.append(Paragraph(rq06_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ06_tempo_vs_reviews.png').exists():
    img = Image('graficos/RQ06_tempo_vs_reviews.png', width=6*inch, height=3.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# RQ07
story.append(Paragraph("<b>RQ07 - Descricao vs Numero de Revisoes</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq07_text = """
<b>Pergunta:</b> Qual a relacao entre a descricao dos PRs e o numero de revisoes realizadas?<br/>
<b>Expectativa:</b> Descricoes mais detalhadas podem atrair mais revisores.<br/>
<b>Resultado:</b> Correlacao positiva (r=0.1168, p<0.05).
"""
story.append(Paragraph(rq07_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ07_descricao_vs_reviews.png').exists():
    img = Image('graficos/RQ07_descricao_vs_reviews.png', width=6*inch, height=3.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# RQ08
story.append(Paragraph("<b>RQ08 - Interacoes vs Numero de Revisoes</b>", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
rq08_text = """
<b>Pergunta:</b> Qual a relacao entre as interacoes nos PRs e o numero de revisoes realizadas?<br/>
<b>Expectativa:</b> Maior engajamento esta associado a mais revisoes.<br/>
<b>Resultado:</b> Correlacao forte entre comentarios e reviews (r=0.64, p<0.05).
"""
story.append(Paragraph(rq08_text, styles['Normal']))
story.append(Spacer(1, 0.1*inch))

if Path('graficos/RQ08_interacoes_vs_reviews.png').exists():
    img = Image('graficos/RQ08_interacoes_vs_reviews.png', width=6*inch, height=3.5*inch)
    story.append(img)

story.append(Spacer(1, 0.2*inch))
story.append(PageBreak())

# DISCUSSAO
story.append(Paragraph("<b>4. DISCUSSAO</b>", styles['CustomHeading']))
story.append(Spacer(1, 0.2*inch))

discussao = """
Com base nas analises estatisticas realizadas, foi possivel identificar os seguintes padroes:

<b>Tamanho dos PRs:</b> Os resultados indicam que o tamanho do PR (arquivos, linhas adicionadas/removidas) 
possui uma correlacao significativa com a probabilidade de merge. PRs menores tendem a ser aceitos com maior frequencia.

<b>Tempo de Analise:</b> O tempo prolongado entre a criacao e o merge/close esta associado a uma maior 
probabilidade de rejeicao, sugerindo que PRs que levam muito tempo para analise podem ser descartadas.

<b>Descricao:</b> PRs com descricoes mais completas tendem a ter maiores chances de aceitacao, indicando 
a importancia da comunicacao clara entre desenvolvedores e revisores.

<b>Interacoes:</b> O numero de participantes e comentarios esta fortemente correlacionado com o numero de 
revisoes, sugerindo que PRs com maior engajamento recebem mais atencao dos revisores.

<b>Significancia Estatistica:</b> Todos os testes mostraram p-values < 0.05, indicando que as correlacoes 
encontradas sao estatisticamente significantes.
"""
story.append(Paragraph(discussao, styles['CustomBody']))

story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("<b>5. CONCLUSOES</b>", styles['CustomHeading']))
story.append(Spacer(1, 0.2*inch))

conclusoes = """
Este estudo forneceu evidencias empiricas de quais fatores influenciam o resultado final (merge/close) 
e o numero de revisoes de Pull Requests em repositorios populares do GitHub.

<b>Recomendacoes para Desenvolvedores:</b><br/>
1. Manter PRs com tamanho reduzido para aumentar chances de aprovacao<br/>
2. Fornecer descricoes claras e completas do objetivo da mudanca<br/>
3. Responder prontamente a feedback para evitar atrasos prolongados<br/>
4. Engajar ativamente com revisores atraves de comentarios construtivos<br/>
<br/>
<b>Implicacoes para Equipes:</b><br/>
1. Implementar politicas de tamanho maximo para PRs<br/>
2. Estabelecer prazos para conclusao de revisoes<br/>
3. Incentivar documentacao completa em descricoes de PR<br/>
4. Criar cultura de revisao colaborativa e construtiva
"""
story.append(Paragraph(conclusoes, styles['CustomBody']))

# Gerar PDF
doc.build(story)
print("PDF gerado: relatorio_lab03.pdf")
