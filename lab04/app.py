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
                df['DiadaSemana'] = df['is_weekend'].map({0: 'Dia Útil', 1: 'Final de Semana'}).astype('category')
            
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

# Filtro de Linguagem
linguagens = sorted(df['language'].dropna().unique().tolist())
lang_selecionada = st.sidebar.multiselect(
    "Filtrar por Linguagens:", 
    options=linguagens,
    default=linguagens
)

# Filtro de Categoria (Core/Peripheral)
categorias = df['core_peripheral'].unique().tolist()
cat_selecionada = st.sidebar.multiselect(
    "Perfil do Autor:", 
    options=categorias,
    default=categorias
)

# Filtro Slider de Latência Limite (Para tirar outliers extremos se o usuário quiser)
max_latency = st.sidebar.slider(
    "Ocultar Outliers (Latência Máxima em Hrs):", 
    min_value=1.0, 
    max_value=float(df['first_review_latency_hours'].quantile(0.99) + 100), 
    value=float(df['first_review_latency_hours'].quantile(0.98)),
    help="Use isto para melhorar a visualização cortando caudas muito longas."
)

st.sidebar.markdown("---")
st.sidebar.info("**Dica:** Estes filtros atualizam todos os gráficos e KPIs simultaneamente.")

# ================= APLICAÇÃO DOS FILTROS =================
df_filtrado = df[
    (df['language'].isin(lang_selecionada)) &
    (df['core_peripheral'].isin(cat_selecionada)) &
    (df['first_review_latency_hours'] <= max_latency)
]

# ================= HEADER / KPIS =================
st.title("Dashboard Sociotécnico: O Processo de Code Review")
st.markdown("Visualização interativa para investigar a influência da posição social do desenvolvedor.")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de PRs Filtrados", f"{len(df_filtrado):,}")
col2.metric("Latência 1ª Revisão (Mediana)", f"{df_filtrado['first_review_latency_hours'].median():.2f}h")
col3.metric("Tempo de Merge (Mediana)", f"{df_filtrado['time_to_merge_hours'].median():.2f}h")
col4.metric("Tamanho Médio (LoC)", f"{df_filtrado['loc_changed'].median():.0f} linhas")
col5.metric("Projetos / Repositórios", f"{df_filtrado['repository'].nunique():,}")

st.markdown("---")

color_map = {'Core': '#27ae60', 'Peripheral': '#c0392b'}

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
        fig_pie = px.pie(df_filtrado, names='language', title='Distribuição por Linguagem de Programação', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_ov2:
        df_perfil = df_filtrado['core_peripheral'].value_counts().reset_index()
        df_perfil.columns = ['Perfil', 'Quantidade']
        fig_pie2 = px.pie(df_perfil, names='Perfil', values='Quantidade', title='Distribuição de Autores (Core vs Peripheral)', color='Perfil', color_discrete_map=color_map, hole=0.4)
        st.plotly_chart(fig_pie2, use_container_width=True)

# ================= ABA 2: RQ1 =================
with tab_rq1:
    st.header("RQ1: Qual a relação entre a centralidade do autor e o tempo de revisão?")
    st.markdown("A hipótese central do estudo é válida: o 'Privilégio da Centralidade' existe. Autores que fazem parte do centro da rede de co-revisão (**Core**) têm seus códigos revisados consideravelmente mais rápido do que os desenvolvedores satélites (**Peripheral**).")
    
    # Amostra muito pequena apenas para o cálculo relâmpago do plotly. 
    # Isso evita travamento na serialização WebGL do json Plotly para arrays gigantscos
    df_bp_sample = df_filtrado.sample(min(len(df_filtrado), 10000), random_state=42)
    
    # Renderização estatística
    fig_bp = px.box(df_bp_sample, x='core_peripheral', y='first_review_latency_hours', 
                    color='core_peripheral', color_discrete_map=color_map, 
                    title="Boxplot de Latência: Autores Core esperam drasticamente menos (Note a escala Y logarítmica)",
                    log_y=True) # Eixo Y em Log
    
    # IMPORTANTE: A sintaxe correta no Plotly Express atual para ocultar outliers é boxpoints = False
    fig_bp.update_traces(quartilemethod="exclusive", boxpoints=False) 
    fig_bp.update_layout(yaxis_title="Horas até a 1ª Revisão (Log)", xaxis_title="Perfil Social do Desenvolvedor")
    st.plotly_chart(fig_bp, use_container_width=True)
    
    st.info("**Insight:** O agrupamento acima evidencia que até mesmo no Quartil 3 (Q3), a latência do grupo Core se mantém espremida num patamar mais veloz. Na base total mapeada no artigo, as medianas diferem de 1.9h para 3.5h (+1.8x).")

# ================= ABA 3: RQ2 =================
with tab_rq2:
    st.header("RQ2: Existe variação do grau de privilégio entre diferentes ecossistemas?")
    st.markdown("Enquanto o padrão 'Autores Core são revisados mais rápidos' acontece em todas as linguagens, a intensidade desse efeito varia muito pelas diretrizes de cada comunidade. **TypeScript e Java** parecem valorizar muito autores com alta centralidade. Ecossistemas consolidados como **C#** mitigam sutilmente parte desse privilégio, oferecendo tempos não tão discrepantes para os chamados periféricos.")
    
    df_med_lang = df_filtrado.groupby(['language', 'core_peripheral'], observed=True)['first_review_latency_hours'].median().reset_index()
    fig_bar1 = px.bar(df_med_lang, x='language', y='first_review_latency_hours', 
                      color='core_peripheral', barmode='group', text_auto='.2f', 
                      title="Latência Mediana (Horas) Categórica Mapeada por Linguagem",
                      color_discrete_map=color_map)
    fig_bar1.update_layout(yaxis_title="Latência Mediana (Horas)", xaxis_title="Ecossistema / Linguagem")
    st.plotly_chart(fig_bar1, use_container_width=True)

# ================= ABA 4: RQ3 =================
with tab_rq3:
    st.header("RQ3: O papel da Assimetria de Poder e da Frequência de Contribuição")
    st.markdown("A revisão de código não é cega ao peso na rede. E o que acontece quando **o revisor é muito mais influente do que o autor** daquele código?")
    
    col_rq3_1, col_rq3_2 = st.columns(2)
    with col_rq3_1:
        st.subheader("O Peso da Assimetria Top-Down")
        st.markdown("Revisões do tipo *Top-Down* (Revisor Central inspecionando autor Periférico) demoram significativamente mais. Quando os *peers* têm centralidades equiparáveis (Neutra/Bottom-Up), a análise é acelerada.")
        
        df_asym = df_filtrado[df_filtrado['Status_Relativo'] != 'Indefinido']
        df_med_asym = df_asym.groupby('Status_Relativo', observed=True)['first_review_latency_hours'].median().reset_index()

        ordem = {"Top-Down": 3, "Neutra": 2, "Bottom-Up": 1}
        df_med_asym['ordem'] = df_med_asym['Status_Relativo'].map(ordem)
        df_med_asym = df_med_asym.sort_values('ordem')

        fig_bar2 = px.bar(df_med_asym, x='Status_Relativo', y='first_review_latency_hours', 
                          color='Status_Relativo', text_auto='.2f',
                          color_discrete_sequence=['#2980b9', '#f39c12', '#8e44ad'])
        fig_bar2.update_layout(yaxis_title="Latência Mediana (Horas)", xaxis_title="", showlegend=False)
        st.plotly_chart(fig_bar2, use_container_width=True)
        
    with col_rq3_2:
        st.subheader("Experiência prévia: A Frequência Preditiva")
        st.markdown("A métrica mais forte atrelada puramente ao autor para derrubar o tempo de revisão é o quão freneticamente ele atua naquele repositório. Observe a clara curva de Regressão Linear desabando no quadro (Amostragem).")
        
        # Reduzida a amostragem pra 2500 pra aliviar o OLS e evitar fragmentação do motor Numba
        df_sample = df_filtrado.sample(min(len(df_filtrado), 2500), random_state=42)
        fig_scatter = px.scatter(df_sample, x='author_frequency', y='first_review_latency_hours', 
                                 color='core_peripheral', color_discrete_map=color_map,
                                 opacity=0.5, log_y=True, log_x=True, trendline="ols")
        fig_scatter.update_traces(marker=dict(size=4))
        fig_scatter.update_layout(yaxis_title="Tempo de Revisão (Escala Log Y)", xaxis_title="Frequência (Escala Log X)")
        st.plotly_chart(fig_scatter, use_container_width=True)

# ================= ABA 5: CONTROLE (EXTRAS) =================
with tab_extras:
    st.header("Variáveis de Controle e Vieses (Tamanho do PR e Dias da Semana)")
    st.markdown("Em estudos de MSR, existem variáveis comuns que podem confundir a análise. Será que os Autores *Core* só entregam PRs menores e mais fáceis? Será que finais de semana distorcem radicalmente a espera? Vamos evidenciar.")
    
    col_ex1, col_ex2 = st.columns(2)
    
    with col_ex1:
        st.subheader("O 'Efeito Final de Semana'")
        if 'DiadaSemana' in df_filtrado.columns:
            df_weekend = df_filtrado.groupby(['DiadaSemana', 'core_peripheral'], observed=True)['first_review_latency_hours'].median().reset_index()
            fig_weekend = px.bar(df_weekend, x='DiadaSemana', y='first_review_latency_hours', 
                                 color='core_peripheral', barmode='group', text_auto='.2f',
                                 color_discrete_map=color_map)
            fig_weekend.update_layout(yaxis_title="Latência Mediana (Horas)", xaxis_title="Dia de Envio")
            st.plotly_chart(fig_weekend, use_container_width=True)
            st.info("PRs submetidos nos finais de semana sofrem uma penalidade de tempo considerável para ambos os grupos, porém as proporções do *privilégio Core* continuam quase idênticas perante seus pares.")
        else:
            st.warning("Variável de Final de Semana não mapeada perfeitamente na amostra atual.")
            
    with col_ex2:
        st.subheader("O Paradoxo do Tamanho do PR (Linhas Alteradas)")
        st.markdown("Mesmo com PRs enormes, o autor Core fura a fila.")
        
        df_sample_loc = df_filtrado.sample(min(len(df_filtrado), 2500), random_state=42)
        fig_loc = px.scatter(df_sample_loc, x='loc_changed', y='first_review_latency_hours', 
                             color='core_peripheral', color_discrete_map=color_map,
                             opacity=0.4, log_y=True, log_x=True, trendline="ols")
        fig_loc.update_traces(marker=dict(size=4))
        fig_loc.update_layout(yaxis_title="Tempo de Revisão (Log)", xaxis_title="Linhas de Código Alteradas (Log)")
        st.plotly_chart(fig_loc, use_container_width=True)
