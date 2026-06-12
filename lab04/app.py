import streamlit as st
import pandas as pd
import gzip
import io
import plotly.express as px

# Configuração da página - TEM QUE SER A PRIMEIRA LINHA DO STREAMLIT
st.set_page_config(page_title="Dashboard Sociotécnico", layout="wide")

@st.cache_data
def carregar_dados():
    try:
        # Lê os arquivos de forma binária com buffer (otimizado para não estourar memória)
        with open('poc_analytical_dataset_part_aa', 'rb') as fa, \
             open('poc_analytical_dataset_part_ab', 'rb') as fb:
            merged_bytes = fa.read() + fb.read()
            
        with gzip.GzipFile(fileobj=io.BytesIO(merged_bytes), mode='rb') as gz:
            # Selecionando e tipando colunas estritamente necessárias para otimizar memória
            usecols = [
                'repository', 'language', 'first_review_latency_hours', 
                'core_peripheral', 'centrality_asymmetry', 'author_is_bot',
                'author_degree_cent', 'author_frequency', 'time_to_merge_hours',
                'loc_changed', 'is_weekend'
            ]
            dtypes = {
                'language': 'category',
                'core_peripheral': 'category',
                'first_review_latency_hours': 'float32',
                'centrality_asymmetry': 'float32',
                'author_degree_cent': 'float32',
                'author_frequency': 'float32',
                'time_to_merge_hours': 'float32',
                'loc_changed': 'float32'
            }
            df = pd.read_csv(gz, usecols=usecols, dtype=dtypes)
            
            # Tratamento do final de semana
            if 'is_weekend' in df.columns:
                df['Dia_da_Semana'] = df['is_weekend'].map({0: 'Dia Útil', 1: 'Final de Semana'}).astype('category')
            
        # Filtros básicos de limpeza
        if 'author_is_bot' in df.columns:
            df = df[df['author_is_bot'] == False]
        df = df.dropna(subset=['first_review_latency_hours', 'core_peripheral'])
        
        # Criação de classes de assimetria
        def classificar_assimetria(val):
            if pd.isna(val): return 'Indefinido'
            if val > 0.1: return 'Top-Down'
            elif val < -0.1: return 'Bottom-Up'
            else: return 'Neutra'
            
        df['Status_Relativo'] = df['centrality_asymmetry'].apply(classificar_assimetria).astype('category')
        df['Perfil_Autor'] = df['core_peripheral'].map({
            'Core': 'Central',
            'Peripheral': 'Periférico'
        }).astype('category')
        df['Assimetria_Centralidade'] = df['Status_Relativo'].map({
            'Top-Down': 'Revisor mais central',
            'Neutra': 'Equilibrada',
            'Bottom-Up': 'Autor mais central',
            'Indefinido': 'Indefinida'
        }).astype('category')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carrega os dados com cache
df = carregar_dados()

if df.empty:
    st.stop()

# ================= FILTROS LATERAIS (SIDEBAR) =================
st.sidebar.header("Filtros de Análise")

def criar_slider_intervalo(label, coluna, q_max=0.99, help_text=None):
    serie = df[coluna].dropna()
    minimo = float(max(0, serie.min()))
    maximo = float(serie.quantile(q_max))
    if maximo <= minimo:
        maximo = minimo + 1.0
    return st.sidebar.slider(
        label,
        min_value=minimo,
        max_value=maximo,
        value=(minimo, maximo),
        help=help_text
    )

st.sidebar.subheader("Escopo")

linguagens = sorted(df['language'].dropna().unique().tolist())
lang_selecionada = st.sidebar.multiselect(
    "Linguagens:", 
    options=linguagens,
    default=linguagens
)

repositorios_populares = df['repository'].value_counts().head(100).index.tolist()
repo_selecionados = st.sidebar.multiselect(
    "Repositórios específicos (opcional):",
    options=repositorios_populares,
    default=[],
    help="Deixe vazio para considerar todos. A lista mostra os 100 repositórios com mais PRs."
)

st.sidebar.subheader("Perfil social")

categorias = sorted(df['Perfil_Autor'].dropna().unique().tolist())
perfil_selecionado = st.sidebar.multiselect(
    "Perfil do Autor:", 
    options=categorias,
    default=categorias
)

assimetria_opcoes = sorted(df['Assimetria_Centralidade'].dropna().unique().tolist())
assimetria_selecionada = st.sidebar.multiselect(
    "Assimetria de centralidade:",
    options=assimetria_opcoes,
    default=assimetria_opcoes
)

if 'Dia_da_Semana' in df.columns:
    dias_opcoes = sorted(df['Dia_da_Semana'].dropna().unique().tolist())
    dias_selecionados = st.sidebar.multiselect(
        "Dia de envio:",
        options=dias_opcoes,
        default=dias_opcoes
    )
else:
    dias_selecionados = []

st.sidebar.subheader("Faixas numéricas")

lat_min, lat_max = criar_slider_intervalo(
    "Latência até 1ª revisão (horas):",
    'first_review_latency_hours',
    q_max=0.99,
    help_text="Use a faixa para cortar caudas muito longas ou focar em revisões rápidas/lentas."
)

merge_min, merge_max = criar_slider_intervalo(
    "Tempo até merge (horas):",
    'time_to_merge_hours',
    q_max=0.99
)

loc_min, loc_max = criar_slider_intervalo(
    "Tamanho do PR (linhas alteradas):",
    'loc_changed',
    q_max=0.98
)

freq_min, freq_max = criar_slider_intervalo(
    "Frequência prévia do autor:",
    'author_frequency',
    q_max=0.99
)

st.sidebar.markdown("---")
st.sidebar.info("**Dica:** Estes filtros atualizam todos os gráficos e KPIs simultaneamente.")

# ================= APLICAÇÃO DOS FILTROS =================
filtro_repositorio = True
if repo_selecionados:
    filtro_repositorio = df['repository'].isin(repo_selecionados)

filtro_dia = True
if 'Dia_da_Semana' in df.columns:
    filtro_dia = df['Dia_da_Semana'].isin(dias_selecionados)

df_filtrado = df[
    (df['language'].isin(lang_selecionada)) &
    (df['Perfil_Autor'].isin(perfil_selecionado)) &
    (df['Assimetria_Centralidade'].isin(assimetria_selecionada)) &
    (df['first_review_latency_hours'].between(lat_min, lat_max)) &
    (df['time_to_merge_hours'].between(merge_min, merge_max)) &
    (df['loc_changed'].between(loc_min, loc_max)) &
    (df['author_frequency'].between(freq_min, freq_max)) &
    filtro_repositorio &
    filtro_dia
]

# ================= HEADER / KPIS =================
st.title("Dashboard Sociotécnico: O Processo de Code Review")
st.markdown("Visualização interativa para investigar a influência da posição social do desenvolvedor.")

if df_filtrado.empty:
    st.warning("Nenhum Pull Request encontrado com a combinação atual de filtros.")
    st.stop()

# KPIs com estilo melhorado
kpi_1 = len(df_filtrado)
kpi_2 = df_filtrado['first_review_latency_hours'].median()
kpi_3 = df_filtrado['time_to_merge_hours'].median()
kpi_4 = df_filtrado['loc_changed'].median()
kpi_5 = df_filtrado['repository'].nunique()

col1, col2, col3, col4, col5 = st.columns(5)

st.markdown("""
<style>
.swia-kpi-card {
    font-family: 'Segoe UI Variable Display', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height: 132px;
    height: 132px;
    padding: 18px 14px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 14px 28px rgba(0,0,0,0.22);
    border: 1px solid rgba(255,255,255,0.20);
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 7px;
}
.swia-kpi-title {
    color: white;
    font-family: 'Segoe UI Variable Text', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
    margin: 0;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    line-height: 1.18;
    opacity: 0.96;
    text-shadow: 0 2px 8px rgba(0,0,0,0.22);
}
.swia-kpi-value {
    color: #fff2a8 !important;
    font-family: 'Segoe UI Variable Display', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 44px !important;
    line-height: 0.95 !important;
    margin: 0 !important;
    font-weight: 950 !important;
    letter-spacing: -1px;
    text-shadow: 0 4px 14px rgba(0,0,0,0.35);
}
.swia-kpi-unit {
    color: rgba(255,255,255,0.92);
    font-family: 'Segoe UI Variable Text', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
    margin: 4px 0 0 0;
    line-height: 1;
    font-weight: 800;
    opacity: 0.95;
}
</style>
""", unsafe_allow_html=True)

def mostrar_kpi(coluna, titulo, valor, gradiente, unidade=""):
    unidade_html = f'<p class="swia-kpi-unit">{unidade}</p>' if unidade else '<p class="swia-kpi-unit">&nbsp;</p>'
    with coluna:
        st.markdown(f"""
        <div class="swia-kpi-card" style="background: {gradiente};">
            <p class="swia-kpi-title">{titulo}</p>
            <p class="swia-kpi-value">{valor}</p>
            {unidade_html}
        </div>
        """, unsafe_allow_html=True)

mostrar_kpi(col1, "Total de PRs", f"{kpi_1:,}", "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
mostrar_kpi(col2, "Latência 1ª Revisão", f"{kpi_2:.2f}h", "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)")
mostrar_kpi(col3, "Tempo de Merge", f"{kpi_3:.2f}h", "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)")
mostrar_kpi(col4, "Tamanho Mediano", f"{kpi_4:.0f}", "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", "linhas")
mostrar_kpi(col5, "Repositórios", f"{kpi_5:,}", "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)")

st.markdown("---")

color_map = {'Central': '#27ae60', 'Periférico': '#c0392b'}
rotulos_graficos = {
    'language': 'Linguagem',
    'Perfil_Autor': 'Perfil do Autor',
    'Perfil': 'Perfil do Autor',
    'Quantidade': 'Quantidade',
    'first_review_latency_hours': 'Latência até 1ª Revisão (horas)',
    'Assimetria_Centralidade': 'Assimetria de Centralidade',
    'author_frequency': 'Frequência prévia do autor',
    'loc_changed': 'Linhas de código alteradas',
    'Dia_da_Semana': 'Dia de envio'
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
    fig.update_xaxes(
        gridcolor="#edf2f7",
        zerolinecolor="#d9e2ec",
        linecolor="#d9e2ec"
    )
    fig.update_yaxes(
        gridcolor="#edf2f7",
        zerolinecolor="#d9e2ec",
        linecolor="#d9e2ec"
    )
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

def traduzir_hover_pontos_linhas(fig, eixo_x, eixo_y):
    for trace in fig.data:
        nome = trace.name or ""
        nome_limpo = nome.split(",")[0].strip()
        if "lines" in (trace.mode or ""):
            trace.name = f"Linha de tendência - {nome_limpo}"
            trace.update(
                hovertemplate=(
                    f"Linha de tendência - {nome_limpo}<br>"
                    f"{eixo_x}: " + "%{x:.2f}<br>"
                    f"{eixo_y}: " + "%{y:.2f}h"
                    "<extra></extra>"
                )
            )
        else:
            trace.name = nome_limpo
            trace.update(
                hovertemplate=(
                    f"Perfil do Autor: {nome_limpo}<br>"
                    f"{eixo_x}: " + "%{x:.2f}<br>"
                    f"{eixo_y}: " + "%{y:.2f}h"
                    "<extra></extra>"
                )
            )
    return fig

# ================= CRIAÇÃO DAS ABAS (TABS) =================
tab_overview, tab_rq1, tab_rq2, tab_rq3, tab_extras = st.tabs([
    "Visão Geral",
    "RQ1: Centralidade vs Latência",
    "RQ2: Impacto dos Ecossistemas",
    "RQ3: Diferença de Poder e Experiência",
    "Variáveis de Controle"
])

# ================= ABA 1: OVERVIEW =================
with tab_overview:
    st.header("Visão Geral dos Dados")
    st.markdown("Este painel descreve a demografia dos Pull Requests analisados após a aplicação dos filtros laterais. Serve para checar como as linguagens estão balanceadas.")
    
    col_ov1, col_ov2 = st.columns(2)
    with col_ov1:
        fig_pie = px.pie(
            df_filtrado,
            names='language',
            title='Distribuição por Linguagem de Programação',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Prism,
            labels=rotulos_graficos
        )
        estilizar_grafico(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_ov2:
        df_perfil = df_filtrado['Perfil_Autor'].value_counts().reset_index()
        df_perfil.columns = ['Perfil', 'Quantidade']
        fig_pie2 = px.pie(
            df_perfil,
            names='Perfil',
            values='Quantidade',
            title='Distribuição de Autores (Central vs Periférico)',
            color='Perfil',
            color_discrete_map=color_map,
            hole=0.4,
            labels=rotulos_graficos
        )
        estilizar_grafico(fig_pie2)
        st.plotly_chart(fig_pie2, use_container_width=True)

# ================= ABA 2: RQ1 =================
with tab_rq1:
    st.header("RQ1: Qual a relação entre a centralidade do autor e o tempo de revisão?")
    st.markdown("A hipótese central do estudo é válida: o 'Privilégio da Centralidade' existe. Autores que fazem parte do centro da rede de co-revisão (**Central**) têm seus códigos revisados consideravelmente mais rápido do que os desenvolvedores satélites (**Periférico**).")
    
    df_bp_sample = df_filtrado.sample(min(len(df_filtrado), 10000), random_state=42)
    fig_bp = px.box(
        df_bp_sample,
        x='Perfil_Autor',
        y='first_review_latency_hours',
        color='Perfil_Autor',
        color_discrete_map=color_map,
        title="Boxplot de Latência por Perfil do Autor (Q1, Mediana, Q3 e Outliers)",
        points='outliers',
        log_y=True,
        labels=rotulos_graficos
    )
    fig_bp.update_traces(
        quartilemethod="exclusive",
        boxpoints='outliers',
        marker_outliercolor='rgba(31, 45, 61, 0.78)',
        marker_line_outliercolor='rgba(31, 45, 61, 0.95)',
        marker_line_outlierwidth=1
    )
    preencher_boxplot(fig_bp)
    destacar_quartis_boxplot(fig_bp, df_bp_sample, 'Perfil_Autor', 'first_review_latency_hours')
    traduzir_hover_boxplot(fig_bp)
    fig_bp.update_layout(
        yaxis_title="Horas até a 1ª Revisão (Log)",
        xaxis_title="Perfil Social do Desenvolvedor",
        showlegend=False
    )
    estilizar_grafico(fig_bp)
    st.plotly_chart(fig_bp, use_container_width=True)
    st.caption("Leitura do boxplot: a linha sólida dentro da caixa representa a mediana; a caixa preenchida vai de Q1 a Q3, e os pontos nas caudas são outliers.")
    
    st.info("**Insight:** O agrupamento acima evidencia que até mesmo no Quartil 3 (Q3), a latência do grupo Central se mantém espremida num patamar mais veloz. Na base total mapeada no artigo, as medianas diferem de 1.9h para 3.5h (+1.8x).")

# ================= ABA 3: RQ2 =================
with tab_rq2:
    st.header("RQ2: Existe variação do grau de privilégio entre diferentes ecossistemas?")
    st.markdown("Enquanto o padrão 'autores centrais são revisados mais rápidos' acontece em todas as linguagens, a intensidade desse efeito varia muito pelas diretrizes de cada comunidade. **TypeScript e Java** parecem valorizar muito autores com alta centralidade. Ecossistemas consolidados como **C#** mitigam sutilmente parte desse privilégio, oferecendo tempos não tão discrepantes para os chamados periféricos.")
    
    df_med_lang = df_filtrado.groupby(['language', 'Perfil_Autor'], observed=True)['first_review_latency_hours'].median().reset_index()
    fig_bar1 = px.bar(df_med_lang, x='language', y='first_review_latency_hours', 
                      color='Perfil_Autor', barmode='group', text_auto='.2f', 
                      title="Latência Mediana (Horas) Categórica Mapeada por Linguagem",
                      color_discrete_map=color_map, labels=rotulos_graficos)
    fig_bar1.update_layout(yaxis_title="Latência Mediana (Horas)", xaxis_title="Ecossistema / Linguagem")
    traduzir_hover_barras(fig_bar1, "Linguagem", "Latência Mediana")
    estilizar_grafico(fig_bar1)
    st.plotly_chart(fig_bar1, use_container_width=True)

# ================= ABA 4: RQ3 =================
with tab_rq3:
    st.header("RQ3: O papel da Assimetria de Poder e da Frequência de Contribuição")
    st.markdown("A revisão de código não é cega ao peso na rede. E o que acontece quando **o revisor é muito mais influente do que o autor** daquele código?")
    
    col_rq3_1, col_rq3_2 = st.columns(2)
    with col_rq3_1:
        st.subheader("O Peso da Assimetria Top-Down")
        st.markdown("Este gráfico compara a **mediana de horas até a primeira revisão** de acordo com a diferença de centralidade entre autor e revisor.")
        
        df_asym = df_filtrado[df_filtrado['Status_Relativo'] != 'Indefinido']
        df_med_asym = df_asym.groupby('Assimetria_Centralidade', observed=True)['first_review_latency_hours'].median().reset_index()

        ordem = {"Revisor mais central": 3, "Equilibrada": 2, "Autor mais central": 1}
        df_med_asym['ordem'] = df_med_asym['Assimetria_Centralidade'].map(ordem)
        df_med_asym = df_med_asym.sort_values('ordem')

        fig_bar2 = px.bar(df_med_asym, x='Assimetria_Centralidade', y='first_review_latency_hours', 
                          color='Assimetria_Centralidade', text_auto='.2f',
                          color_discrete_sequence=['#2980b9', '#f39c12', '#8e44ad'],
                          title="Latência mediana por assimetria de centralidade",
                          labels=rotulos_graficos)
        fig_bar2.update_layout(yaxis_title="Latência Mediana (Horas)", xaxis_title="", showlegend=False)
        traduzir_hover_barras(fig_bar2, "Assimetria de Centralidade", "Latência Mediana")
        estilizar_grafico(fig_bar2)
        st.plotly_chart(fig_bar2, use_container_width=True)
        st.caption("Leitura: barras mais altas indicam revisões mais lentas. Quando o revisor é mais central que o autor, a espera tende a aumentar.")
        
    with col_rq3_2:
        st.subheader("Experiência prévia: A Frequência Preditiva")
        st.markdown("Este gráfico cruza a **frequência prévia de contribuição do autor** com o **tempo até a primeira revisão**, separando autores centrais e periféricos.")
        
        # Reduzida a amostragem pra 2500 pra aliviar o OLS e evitar fragmentação do motor Numba
        df_sample = df_filtrado.sample(min(len(df_filtrado), 2500), random_state=42)
        fig_scatter = px.scatter(df_sample, x='author_frequency', y='first_review_latency_hours', 
                                 color='Perfil_Autor', color_discrete_map=color_map,
                                 opacity=0.5, log_y=True, log_x=True, trendline="ols",
                                 title="Frequência do autor vs tempo de revisão",
                                 labels=rotulos_graficos)
        fig_scatter.update_traces(marker=dict(size=4))
        fig_scatter.update_layout(yaxis_title="Tempo de Revisão (Escala Log Y)", xaxis_title="Frequência (Escala Log X)")
        traduzir_hover_pontos_linhas(fig_scatter, "Frequência prévia do autor", "Tempo de Revisão")
        estilizar_grafico(fig_scatter)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Leitura: cada ponto é um PR. A linha de tendência mostra se autores mais frequentes costumam receber revisão mais rápido.")

# ================= ABA 5: CONTROLE (EXTRAS) =================
with tab_extras:
    st.header("Variáveis de Controle e Vieses (Tamanho do PR e Dias da Semana)")
    st.markdown("Em estudos de MSR, existem variáveis comuns que podem confundir a análise. Será que os autores *Centrais* só entregam PRs menores e mais fáceis? Será que finais de semana distorcem radicalmente a espera? Vamos evidenciar.")
    
    col_ex1, col_ex2 = st.columns(2)
    
    with col_ex1:
        st.subheader("O 'Efeito Final de Semana'")
        st.markdown("Este gráfico compara a latência mediana entre PRs enviados em **dias úteis** e em **finais de semana**, separando autores centrais e periféricos.")
        if 'Dia_da_Semana' in df_filtrado.columns:
            df_weekend = df_filtrado.groupby(['Dia_da_Semana', 'Perfil_Autor'], observed=True)['first_review_latency_hours'].median().reset_index()
            fig_weekend = px.bar(df_weekend, x='Dia_da_Semana', y='first_review_latency_hours', 
                                 color='Perfil_Autor', barmode='group', text_auto='.2f',
                                 color_discrete_map=color_map,
                                 title="Latência mediana por dia de envio",
                                 labels=rotulos_graficos)
            fig_weekend.update_layout(yaxis_title="Latência Mediana (Horas)", xaxis_title="Dia de Envio")
            traduzir_hover_barras(fig_weekend, "Dia de Envio", "Latência Mediana")
            estilizar_grafico(fig_weekend)
            st.plotly_chart(fig_weekend, use_container_width=True)
            st.caption("Leitura: compare as barras por perfil para ver se o fim de semana aumenta a espera e se a diferença entre autores centrais e periféricos permanece.")
            st.info("PRs submetidos nos finais de semana sofrem uma penalidade de tempo considerável para ambos os grupos, porém as proporções do *privilégio Central* continuam quase idênticas perante seus pares.")
        else:
            st.warning("Variável de Final de Semana não mapeada perfeitamente na amostra atual.")
            
    with col_ex2:
        st.subheader("O Paradoxo do Tamanho do PR (Linhas Alteradas)")
        st.markdown("Este gráfico verifica se PRs maiores, medidos por **linhas de código alteradas**, explicam sozinhos o tempo de revisão.")
        
        df_sample_loc = df_filtrado.sample(min(len(df_filtrado), 2500), random_state=42)
        fig_loc = px.scatter(df_sample_loc, x='loc_changed', y='first_review_latency_hours', 
                             color='Perfil_Autor', color_discrete_map=color_map,
                             opacity=0.4, log_y=True, log_x=True, trendline="ols",
                             title="Tamanho do PR vs tempo de revisão",
                             labels=rotulos_graficos)
        fig_loc.update_traces(marker=dict(size=4))
        fig_loc.update_layout(yaxis_title="Tempo de Revisão (Log)", xaxis_title="Linhas de Código Alteradas (Log)")
        traduzir_hover_pontos_linhas(fig_loc, "Linhas de Código Alteradas", "Tempo de Revisão")
        estilizar_grafico(fig_loc)
        st.plotly_chart(fig_loc, use_container_width=True)
        st.caption("Leitura: cada ponto é um PR. A linha de tendência ajuda a comparar se o tamanho do PR afeta igualmente autores centrais e periféricos.")
