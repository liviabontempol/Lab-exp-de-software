import pandas as pd
import glob
import gzip
import plotly.express as px
import os
import io

print("Agrupando partições binárias e lendo o Dataset Analítico...")
# Como os arquivos part_aa e part_ab são uma divisão bruta de um único arquivo GZIP, 
# precisamos concatená-los binariamente antes de descompactar.
with open('poc_analytical_dataset_part_aa', 'rb') as fa, \
     open('poc_analytical_dataset_part_ab', 'rb') as fb:
    merged_bytes = fa.read() + fb.read()

# Lendo o CSV já descompactado em memória
with gzip.GzipFile(fileobj=io.BytesIO(merged_bytes), mode='rb') as gz:
    df = pd.read_csv(gz)

print("Limpando e formatando dados para o Dashboard...")
# Filtra contas de bot para limpar a análise puramente sociotécnica (humana)
if 'author_is_bot' in df.columns:
    df = df[df['author_is_bot'] == False]

# Remove entradas onde não haja dados definidos para as variáveis chave
df = df.dropna(subset=['first_review_latency_hours', 'core_peripheral'])

# Paleta de cores oficial do dashboard para destacar os 2 grupos principais
color_map = {'Core': '#27ae60', 'Peripheral': '#c0392b'}

print("Gerando gráficos interativos com Plotly...")

# --- CALCULOS DE KPI ---
total_prs = len(df)
median_latency = df['first_review_latency_hours'].median()
avg_latency = df['first_review_latency_hours'].mean()
total_repos = df['repository'].nunique()

# --- GRAFICO 1: Distribuição Geral ---
fig_lang = px.pie(df, names='language', title='Distribuição de Pull Requests por Linguagem', 
                  hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
fig_lang.update_layout(margin=dict(t=50, b=20, l=10, r=10))

# --- GRAFICO 2: Violino/Boxplot Core vs Peripheral (Escala Log) ---
fig_core_per = px.box(df, x='core_peripheral', y='first_review_latency_hours', color='core_peripheral',
                      title='Latência de Revisão: Core vs Peripheral (Escala Log - Cauda Longa)',
                      color_discrete_map=color_map, log_y=True)
fig_core_per.update_layout(yaxis_title='Latência (Horas)', xaxis_title='Perfil Social do Autor', showlegend=False, 
                           margin=dict(t=50, b=20, l=10, r=10))

# --- GRAFICO 3: Impacto por Ecossistema ---
# Agregar as medianas por linguagem antes de jogar no bar chart
df_med_lang = df.groupby(['language', 'core_peripheral'])['first_review_latency_hours'].median().reset_index()
fig_lang_comp = px.bar(df_med_lang, x='language', y='first_review_latency_hours', color='core_peripheral', 
                       barmode='group', text_auto='.2f', color_discrete_map=color_map,
                       title='Latência Mediana (Horas) por Linguagem: Comportamento Transversal')
fig_lang_comp.update_layout(yaxis_title='Mediana de Espera até 1ª Revisão (Horas)', xaxis_title='Linguagem', 
                            legend_title='Categoria do Autor', margin=dict(t=50, b=20, l=10, r=10))

# --- GRAFICO 4: Assimetria (Dinâmica Pessoal Revisor vs Autor) ---
def classificar_assimetria(val):
    if pd.isna(val): return 'Indefinido'
    if val > 0.1: return 'Top-Down (Revisor muito mais influente)'
    elif val < -0.1: return 'Bottom-Up (Autor muito mais influente)'
    else: return 'Neutra (Mesmo Patamar)'
    
df['Status_Relativo'] = df['centrality_asymmetry'].apply(classificar_assimetria)
df_asym = df[df['Status_Relativo'] != 'Indefinido']
df_med_asym = df_asym.groupby('Status_Relativo')['first_review_latency_hours'].median().reset_index()

# Ordenar logicamente as opções
df_med_asym['ordem'] = df_med_asym['Status_Relativo'].map(
    {"Top-Down (Revisor muito mais influente)": 3, "Neutra (Mesmo Patamar)": 2, "Bottom-Up (Autor muito mais influente)": 1})
df_med_asym = df_med_asym.sort_values('ordem')

fig_asym = px.bar(df_med_asym, x='Status_Relativo', y='first_review_latency_hours', color='Status_Relativo', 
                  text_auto='.2f', title='Efeito da Assimetria Top-Down (Revisor Central joga latência para cima)',
                  color_discrete_sequence=['#2980b9', '#f39c12', '#8e44ad'])
fig_asym.update_layout(yaxis_title='Latência Mediana (Horas)', xaxis_title='Dinâmica de Centralidade Revisor-Autor', 
                       showlegend=False, margin=dict(t=50, b=20, l=10, r=10))

print("Montando o esqueleto HTML do Dashboard...")



# TEMPLATE HTML ESTILIZADO 
html_template = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Socio-Technical Dashboard: Code Review Latency</title>
    <!-- Importa a biblioteca do Plotly para gerar a interatividade dos gráficos -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {{
            --bg-color: #f4f6f9;
            --card-bg: #ffffff;
            --text-main: #2c3e50;
            --text-muted: #7f8c8d;
            --border: #e9ecef;
            --primary: #3498db;
            --rad: 12px;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px 40px;
        }}
        .header {{ text-align: center; margin-bottom: 40px; padding-top: 20px; }}
        .header h1 {{ font-size: 2.2em; margin-bottom: 8px; color: #1a252f; }}
        .header p {{ font-size: 1.1em; color: var(--text-muted); margin: 0; }}
        
        .kpi-container {{ 
            display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 40px; justify-content: space-between;
        }}
        .kpi-card {{
            flex: 1; min-width: 180px; background-color: var(--card-bg); border-radius: var(--rad); 
            padding: 25px 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.03); 
            border: 1px solid var(--border); transition: transform 0.2s;
        }}
        .kpi-card:hover {{ transform: translateY(-5px); }}
        .kpi-card h3 {{ margin: 0; color: #95a5a6; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }}
        .kpi-value {{ margin: 15px 0 0 0; font-size: 2.5em; font-weight: 700; color: var(--primary); }}
        
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }}
        .chart-card {{ 
            background-color: var(--card-bg); border-radius: var(--rad); padding: 25px; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.03); border: 1px solid var(--border); overflow: hidden;
        }}
        .full-width {{ grid-column: 1 / -1; }}
        .desc-text {{ text-align: center; color: var(--text-muted); font-size: 0.95em; font-style: italic; margin-bottom: 20px; padding: 0 40px; }}

        @media (max-width: 1000px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dashboard Sociotécnico: Processo de Code Review 🔍</h1>
        <p>A influência da posição social do desenvolvedor na latência das avaliações (GitHub)</p>
    </div>

    <div class="kpi-container">
        <div class="kpi-card"><h3>Total de Requiçiões Mapeadas</h3><p class="kpi-value">{total_prs:,}</p></div>
        <div class="kpi-card"><h3>Latência Mediana (Geral)</h3><p class="kpi-value">{median_latency:.2f}h</p></div>
        <div class="kpi-card"><h3>Latência Média (Geral)</h3><p class="kpi-value">{avg_latency:.2f}h</p></div>
        <div class="kpi-card"><h3>Projetos / Repositórios</h3><p class="kpi-value">{total_repos:,}</p></div>
    </div>

    <div class="grid">
        <!-- Linha 1 -->
        <div class="chart-card">
            {fig_lang.to_html(full_html=False, include_plotlyjs=False)}
        </div>
        <div class="chart-card">
            <p class="desc-text">Como os dados são muito assimétricos (cauda longa com valores imensos), o eixo Y logarítmico revela melhor onde a massa dos dados se encontra. Autores <b>Core</b> tem boxplots expressivamente mais "baixos".</p>
            {fig_core_per.to_html(full_html=False, include_plotlyjs=False)}
        </div>
        
        <!-- Linha 2 -->
        <div class="chart-card full-width">
            <p class="desc-text">O gráfico abaixo evidencia o "Privilégio da Centralidade": o tempo mediano cai consideravelmente se o autor pertence ao coração do repósitório, independente de ecossistema, embora C# atenue sutilmente a diferença.</p>
            {fig_lang_comp.to_html(full_html=False, include_plotlyjs=False)}
        </div>

        <!-- Linha 3 -->
        <div class="chart-card full-width">
            <p class="desc-text">A <b>Dinâmica de Poder</b> importa: quando o revisor é muito mais central (influente) que o autor da submissão (<b>Top-Down</b>), o processo tende a ser mais rigoroso e lento do que uma revisão entre pares de status semelhante.</p>
            {fig_asym.to_html(full_html=False, include_plotlyjs=False)}
        </div>
    </div>
</body>
</html>
"""

# Salva o arquivo no diretorio
with open('dashboard_interativo.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("✅ SUCESSO! Dashboard gerado perfeitamente no arquivo: 'dashboard_interativo.html'")
