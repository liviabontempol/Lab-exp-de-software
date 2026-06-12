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
df['Perfil_Autor'] = df['core_peripheral'].map({
    'Core': 'Central',
    'Peripheral': 'Periférico'
})
color_map = {'Central': '#27ae60', 'Periférico': '#c0392b'}
rotulos_graficos = {
    'language': 'Linguagem',
    'Perfil_Autor': 'Perfil do Autor',
    'first_review_latency_hours': 'Latência até 1ª Revisão (horas)',
    'Assimetria_Centralidade': 'Assimetria de Centralidade'
}

def estilizar_grafico(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#243447", family="Segoe UI Variable Text, Inter, Segoe UI, Arial, sans-serif"),
        title_font=dict(color="#1f2d3d", size=18, family="Segoe UI Variable Display, Inter, Segoe UI, Arial, sans-serif"),
        margin=dict(t=65, b=50, l=55, r=35),
        legend=dict(
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0
        ),
        hoverlabel=dict(
            bgcolor="#1f2d3d",
            font_color="white"
        )
    )
    fig.update_xaxes(gridcolor="#edf2f7", zerolinecolor="#d9e2ec", linecolor="#d9e2ec")
    fig.update_yaxes(gridcolor="#edf2f7", zerolinecolor="#d9e2ec", linecolor="#d9e2ec")
    return fig

def preencher_boxplot(fig):
    cores = {
        'Central': ('rgba(39, 174, 96, 0.72)', '#145a32'),
        'Periférico': ('rgba(192, 57, 43, 0.68)', '#7b241c')
    }
    for trace in fig.data:
        preenchimento, linha = cores.get(trace.name, ('rgba(52, 152, 219, 0.65)', '#1b4f72'))
        trace.update(
            fillcolor=preenchimento,
            line=dict(color=linha, width=3),
            marker=dict(color=linha, opacity=0.55, size=4),
            whiskerwidth=0.7
        )
    return fig

def destacar_quartis_boxplot(fig, dados, coluna_grupo, coluna_valor):
    estatisticas = dados.groupby(coluna_grupo, observed=True)[coluna_valor].quantile([0.25, 0.5, 0.75]).unstack()
    for grupo, linha in estatisticas.iterrows():
        q1 = linha.get(0.25)
        mediana = linha.get(0.5)
        q3 = linha.get(0.75)
        if pd.isna(q1) or pd.isna(mediana) or pd.isna(q3):
            continue
        fig.add_annotation(
            x=grupo,
            y=mediana,
            text=f"Q1 {q1:.2f}h<br><b>Mediana {mediana:.2f}h</b><br>Q3 {q3:.2f}h",
            showarrow=False,
            font=dict(color="white", size=12, family="Segoe UI Variable Display, Inter, Segoe UI, sans-serif"),
            align="center",
            bgcolor="rgba(31, 45, 61, 0.90)",
            bordercolor="rgba(255, 255, 255, 0.90)",
            borderwidth=1,
            borderpad=6
        )
    return fig

def traduzir_hover_boxplot(fig):
    fig.update_traces(
        hovertemplate=(
            "Perfil do Autor: %{x}<br>"
            "Latência até 1ª Revisão: %{y:.2f}h"
            "<extra></extra>"
        )
    )
    return fig

def traduzir_hover_barras(fig, eixo_x, eixo_y):
    fig.update_traces(
        hovertemplate=(
            f"{eixo_x}: " + "%{x}<br>"
            f"{eixo_y}: " + "%{y:.2f}h"
            "<extra></extra>"
        )
    )
    return fig

print("Gerando gráficos interativos com Plotly...")

# --- CALCULOS DE KPI ---
total_prs = len(df)
median_latency = df['first_review_latency_hours'].median()
median_merge = df['time_to_merge_hours'].median() if 'time_to_merge_hours' in df.columns else 0
total_repos = df['repository'].nunique()

# --- GRAFICO 1: Distribuição Geral ---
fig_lang = px.pie(df, names='language', title='Distribuição de Pull Requests por Linguagem', 
                  hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism,
                  labels=rotulos_graficos)
fig_lang.update_layout(margin=dict(t=50, b=20, l=10, r=10))
estilizar_grafico(fig_lang)

# --- GRAFICO 2: Boxplot Core vs Peripheral (Escala Log) ---
fig_core_per = px.box(df, x='Perfil_Autor', y='first_review_latency_hours', color='Perfil_Autor',
                      title='Boxplot de Latência por Perfil do Autor (Q1, Mediana, Q3 e Outliers)',
                      points='outliers',
                      color_discrete_map=color_map, log_y=True,
                      labels=rotulos_graficos)
fig_core_per.update_traces(
    quartilemethod="exclusive",
    boxpoints='outliers',
    marker_outliercolor='rgba(31, 45, 61, 0.78)',
    marker_line_outliercolor='rgba(31, 45, 61, 0.95)',
    marker_line_outlierwidth=1
)
preencher_boxplot(fig_core_per)
destacar_quartis_boxplot(fig_core_per, df, 'Perfil_Autor', 'first_review_latency_hours')
traduzir_hover_boxplot(fig_core_per)
fig_core_per.update_layout(yaxis_title='Horas até a 1ª Revisão (Log)', xaxis_title='Perfil Social do Autor',
                           showlegend=False, margin=dict(t=50, b=20, l=10, r=10))
estilizar_grafico(fig_core_per)

# --- GRAFICO 3: Impacto por Ecossistema ---
# Agregar as medianas por linguagem antes de jogar no bar chart
df_med_lang = df.groupby(['language', 'Perfil_Autor'])['first_review_latency_hours'].median().reset_index()
fig_lang_comp = px.bar(df_med_lang, x='language', y='first_review_latency_hours', color='Perfil_Autor', 
                       barmode='group', text_auto='.2f', color_discrete_map=color_map,
                       title='Latência Mediana (Horas) por Linguagem: Comportamento Transversal',
                       labels=rotulos_graficos)
fig_lang_comp.update_layout(yaxis_title='Mediana de Espera até 1ª Revisão (Horas)', xaxis_title='Linguagem', 
                            legend_title='Categoria do Autor', margin=dict(t=50, b=20, l=10, r=10))
traduzir_hover_barras(fig_lang_comp, "Linguagem", "Latência Mediana")
estilizar_grafico(fig_lang_comp)

# --- GRAFICO 4: Assimetria (Dinâmica Pessoal Revisor vs Autor) ---
def classificar_assimetria(val):
    if pd.isna(val): return 'Indefinido'
    if val > 0.1: return 'Top-Down (Revisor muito mais influente)'
    elif val < -0.1: return 'Bottom-Up (Autor muito mais influente)'
    else: return 'Neutra (Mesmo Patamar)'
    
df['Assimetria_Centralidade'] = df['centrality_asymmetry'].apply(classificar_assimetria)
df_asym = df[df['Assimetria_Centralidade'] != 'Indefinido']
df_med_asym = df_asym.groupby('Assimetria_Centralidade')['first_review_latency_hours'].median().reset_index()

# Ordenar logicamente as opções
df_med_asym['ordem'] = df_med_asym['Assimetria_Centralidade'].map(
    {"Top-Down (Revisor muito mais influente)": 3, "Neutra (Mesmo Patamar)": 2, "Bottom-Up (Autor muito mais influente)": 1})
df_med_asym = df_med_asym.sort_values('ordem')

fig_asym = px.bar(df_med_asym, x='Assimetria_Centralidade', y='first_review_latency_hours', color='Assimetria_Centralidade', 
                  text_auto='.2f', title='Efeito da Assimetria Top-Down (Revisor Central joga latência para cima)',
                  color_discrete_sequence=['#2980b9', '#f39c12', '#8e44ad'],
                  labels=rotulos_graficos)
fig_asym.update_layout(yaxis_title='Latência Mediana (Horas)', xaxis_title='Dinâmica de Centralidade Revisor-Autor', 
                       showlegend=False, margin=dict(t=50, b=20, l=10, r=10))
traduzir_hover_barras(fig_asym, "Assimetria de Centralidade", "Latência Mediana")
estilizar_grafico(fig_asym)

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
            font-family: 'Segoe UI Variable Text', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
            font-family: 'Segoe UI Variable Display', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            flex: 1; min-width: 180px; background-color: var(--card-bg); border-radius: var(--rad); 
            min-height: 146px; padding: 24px 20px; text-align: center; box-shadow: 0 12px 26px rgba(31,45,61,0.12); 
            border: 1px solid var(--border); transition: transform 0.2s;
            display: flex; flex-direction: column; justify-content: center;
        }}
        .kpi-card:hover {{ transform: translateY(-5px); }}
        .kpi-card h3 {{ margin: 0; color: #5f7180; font-family: 'Segoe UI Variable Text', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 1.04em; font-weight: 850; text-transform: uppercase; letter-spacing: 0.7px; line-height: 1.18; }}
        .kpi-value {{ display: inline-block; min-width: 118px; margin: 12px auto 0 auto; padding: 8px 14px 9px 14px; border-radius: 9px; background: rgba(10,18,32,0.09); border: 1px solid rgba(52,70,92,0.10); box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 10px 22px rgba(31,45,61,0.08); font-family: 'Segoe UI Variable Display', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 3.45em; line-height: 0.95; font-weight: 950; letter-spacing: -1px; color: #155f9c; text-shadow: 0 3px 10px rgba(52,152,219,0.18); }}
        
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
        <div class="kpi-card"><h3>📊 Total de Requisições Mapeadas</h3><p class="kpi-value">{total_prs:,}</p></div>
        <div class="kpi-card"><h3>⏱️ Latência Mediana (Geral)</h3><p class="kpi-value">{median_latency:.2f}h</p></div>
        <div class="kpi-card"><h3>🔀 Tempo de Merge</h3><p class="kpi-value">{median_merge:.2f}h</p></div>
        <div class="kpi-card"><h3>🏢 Projetos / Repositórios</h3><p class="kpi-value">{total_repos:,}</p></div>
    </div>

    <div class="grid">
        <!-- Linha 1 -->
        <div class="chart-card">
            {fig_lang.to_html(full_html=False, include_plotlyjs=False)}
        </div>
        <div class="chart-card">
            <p class="desc-text">O boxplot mostra Q1, mediana, Q3 e outliers. A linha sólida dentro da caixa é a <b>mediana</b>; a caixa preenchida vai de Q1 a Q3.</p>
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

print("SUCESSO! Dashboard gerado perfeitamente no arquivo: 'dashboard_interativo.html'")
