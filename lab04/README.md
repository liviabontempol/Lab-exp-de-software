# Lab 04 - Dashboard Sociotécnico Interativo

## Descrição

Dashboard interativo desenvolvido com **Streamlit** que analisa dados sociotécnicos de pull requests de repositórios públicos. O dashboard fornece visualizações e métricas sobre:

- Distribuição de PRs por linguagem de programação
- Comparação de latência de revisão entre autores Core e Peripheral
- Análise de impacto por ecossistema
- KPIs (Key Performance Indicators) de review time e interações

## Dados

O dashboard utiliza dados processados em formato GZIP comprimido, divididos em duas partes:
- `poc_analytical_dataset_part_aa` 
- `poc_analytical_dataset_part_ab`

Estes arquivos são concatenados binariamente e descompactados para análise em memória.

## Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## Como Executar

### 1. Instalar Dependências

Execute o seguinte comando no diretório do lab04:

```bash
pip install -r requirements.txt
```

Isso instalará:
- **streamlit**: Framework para criar aplicações web de dados
- **pandas**: Manipulação e análise de dados
- **plotly**: Visualizações interativas

### 2. Executar o Dashboard

```bash
streamlit run app.py
```

O dashboard será aberto automaticamente no seu navegador padrão em `http://localhost:8501`

### 3. Explorar o Dashboard

Uma vez aberto, você poderá:

- **Filtrar por Linguagens**: Selecione quais linguagens de programação deseja incluir na análise
- **Filtrar por Perfil**: Escolha entre autores Core (centrais) e Peripheral (periféricos)
- **Ajustar Outliers**: Use o slider para limpar dados extremos e melhorar visualizações

### Recursos do Dashboard

- **Visualizações Dinâmicas**: Gráficos interativos que atualizam em tempo real com seus filtros
- **Otimização de Memória**: Leitura inteligente de colunas e tipos de dados para grandes datasets
- **Cache de Dados**: Primeiro carregamento pode levar alguns segundos, mas é cacheado para consultas futuras

## Estrutura de Arquivos

```
lab04/
├── app.py                              # App principal do Streamlit
├── gerar_dashboard.py                  # Script para gerar visualizações
├── requirements.txt                    # Dependências do projeto
├── poc_analytical_dataset_part_aa      # Dados (parte 1)
├── poc_analytical_dataset_part_ab      # Dados (parte 2)
├── poc_prs_*.* (outros arquivos de dados)
└── figures/                            # Diretório para figuras/outputs
```

## Troubleshooting

### Erro ao carregar dados
- Verifique se os arquivos `poc_analytical_dataset_part_aa` e `poc_analytical_dataset_part_ab` estão presentes
- Verifique se há espaço em disco suficiente para descompactar os dados

### Streamlit não inicia
- Certifique-se de que está no diretório correto (`lab04/`)
- Verifique se todas as dependências foram instaladas: `pip list`
- Tente limpar o cache: `streamlit cache clear`

### Lentidão ao carregar dados
- Reduza o número de linguagens selecionadas no filtro
- Use o slider de outliers para reduzir o volume de dados processados

## Notas Adicionais

- O dashboard filtra automaticamente pull requests de bots
- Dados com valores indefinidos nas variáveis-chave são removidos
- A classificação de assimetria segue a seguinte lógica:
  - **Top-Down**: centrality_asymmetry > 0.1 (influência vem de cima para baixo)
  - **Bottom-Up**: centrality_asymmetry < -0.1 (influência vem de baixo para cima)
  - **Neutra**: Valores entre -0.1 e 0.1
