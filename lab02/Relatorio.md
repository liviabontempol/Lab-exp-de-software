LABORATÓRIO 02
Características de qualidade em repositórios populares Java

João Pedro Campos
Lívia Bontempo Leite


Pontifícia Universidade Católica de Minas Gerais
Engenharia de Software
Laboratório de Experimentação de Software



Belo Horizonte
2026






Estrutura de Documento de Experimento

1. Introdução

1.1 Contextualização

No desenvolvimento colaborativo de software open-source, diferentes mantenedores e colaboradores atuam continuamente em partes distintas do código. Esse cenário favorece evolução funcional e velocidade de entrega, mas também aumenta o risco de degradação de atributos internos de qualidade, como acoplamento, coesão e organização estrutural.

No contexto de Engenharia de Software baseada em evidências, métricas estáticas e métricas de processo permitem analisar, de forma objetiva, se características do ciclo de desenvolvimento estão associadas à qualidade interna dos sistemas.

1.2 Problema Foco do Experimento

O problema central deste experimento é verificar, em repositórios Java populares do GitHub, se atributos do processo de desenvolvimento (popularidade, maturidade, atividade e tamanho) apresentam relação com métricas de qualidade interna do código (CBO, DIT e LCOM).

1.3 Questões-problema ou Questões-Pesquisa

As questões de pesquisa investigadas foram:

RQ01: Qual a relação entre a popularidade dos repositórios e suas características de qualidade?

RQ02: Qual a relação entre a maturidade dos repositórios e suas características de qualidade?

RQ03: Qual a relação entre a atividade dos repositórios e suas características de qualidade?

RQ04: Qual a relação entre o tamanho dos repositórios e suas características de qualidade?


1.4 Hipótese(s)

Com base no problema e nas questões de pesquisa, a(s) hipótese(s) formulada(s) para este experimento é(são):

Hipótese Principal:

Repositórios Java populares que apresentam maior maturidade e manutenção contínua tendem a exibir melhores características de qualidade interna, observadas por valores mais estáveis de CBO, DIT e LCOM.

Hipóteses Secundárias:

H1: Repositórios com maior número de estrelas tendem a apresentar menor falta de coesão (LCOM mais baixo).

H2: Repositórios mais antigos tendem a apresentar maior acoplamento médio (CBO), devido à evolução histórica do código.

H3: Repositórios com maior número de releases tendem a apresentar métricas de qualidade mais estáveis, em razão de ciclos de manutenção contínuos.

H4: Repositórios maiores (mais LOC e comentários) tendem a apresentar maior dispersão nas métricas de qualidade.

H5: Em projetos com alta popularidade, a profundidade média de herança (DIT) tende a permanecer baixa ou moderada por práticas de simplicidade arquitetural.

H6: O aumento isolado do tamanho do projeto não implica necessariamente pior qualidade interna.


1.5 Objetivo (principal e específicos)

Objetivo Principal:

Analisar a relação entre atributos do processo de desenvolvimento e métricas de qualidade interna em repositórios Java populares no GitHub.


Objetivos Específicos:

1. Coletar metadados de processo para os 1.000 repositórios Java mais populares (estrelas, releases e idade).

2. Medir atributos de tamanho e qualidade interna em repositórios da amostra por meio de automação (clone, contagem de LOC/comentários e análise com CK).

3. Sumarizar os dados de qualidade por repositório com média, mediana e desvio padrão.

4. Discutir os resultados obtidos em relação às quatro questões de pesquisa propostas.


2. Metodologia

2.1 Passo a passo do experimento

1. Definição da amostra: seleção dos 1.000 repositórios Java mais populares no GitHub.

2. Coleta de dados de processo via GitHub GraphQL: geração dos arquivos de saída com metadados dos repositórios.

3. Preparação da automação de qualidade: implementação de script para clone, cálculo de tamanho e execução do CK.

4. Medição inicial (sprint atual): execução completa para 1 repositório, com consolidação das métricas em CSV.

5. Sumarização estatística: cálculo de média, mediana e desvio padrão para variáveis de processo (1.000 repositórios) e de qualidade (repositório medido).

6. Interpretação dos resultados frente às RQs e hipóteses.


2.2 Métricas e suas Unidades

As métricas utilizadas para medir o sucesso ou o resultado do experimento, juntamente com suas unidades de medida, são:

| Métrica | Unidade | Descrição |
|---|---|---|
| Idade do repositório | Anos (e derivável em dias) | Tempo entre a criação do repositório e a data de coleta. No projeto, foi utilizada a variável `repo_age_years` e pode ser convertida para dias. |
| Pull Requests aceitos | Quantidade | Número total de pull requests aceitos (merged). **Não coletado nesta etapa do projeto**. |
| Número de Releases | Quantidade | Total de versões lançadas oficialmente (`releases_total`). |
| Dias desde a última atualização | Dias | Tempo entre a última atualização e a data de coleta. **Não consolidado nesta etapa**. |
| Linguagem de Programação Primária | Percentual / Categoria | Linguagem predominante no repositório. No experimento atual, a amostra foi filtrada para Java. |
| Razão de Issues Fechadas | Percentual | Proporção entre issues fechadas e totais. **Não coletado nesta etapa do projeto**. |
| Popularidade (estrelas) | Quantidade | Total de estrelas do repositório (`stars`). |
| LOC (linhas de código) | Quantidade | Número de linhas de código Java não vazias (`loc_total`). |
| Linhas de comentários | Quantidade | Número de linhas classificadas como comentário (`comment_lines`). |
| CBO | Valor numérico | Acoplamento entre objetos por classe, sumarizado por média, mediana e desvio padrão no repositório. |
| DIT | Valor numérico | Profundidade da árvore de herança por classe, sumarizada por média, mediana e desvio padrão no repositório. |
| LCOM | Valor numérico | Falta de coesão entre métodos por classe, sumarizada por média, mediana e desvio padrão no repositório. |


3. Visualização dos Resultados

Nesta etapa, os resultados foram organizados em tabelas estatísticas a partir dos dados coletados:

Conjunto de 1.000 repositórios (métricas de processo):

1. Stars: média = 9810,53; mediana = 5904,00; desvio padrão = 11977,80; mínimo = 3474; máximo = 154816.

2. Releases: média = 41,32; mediana = 11,00; desvio padrão = 89,56; mínimo = 0; máximo = 1000.

3. Idade (anos): média = 10,14; mediana = 10,31; desvio padrão = 3,18; mínimo = 0,55; máximo = 17,48.

Repositório com medição de qualidade concluída (krahets/hello-algo):

1. Popularidade: 125036 estrelas (percentil aproximado 99,9 na amostra).

2. Atividade: 10 releases (percentil aproximado 49,4).

3. Maturidade: 3,43 anos (percentil aproximado 4,1).

4. Tamanho: 425 arquivos Java; 28705 LOC; 8665 linhas de comentários.

5. Qualidade CK:

- CBO: média = 1,8744; mediana = 2,0; desvio padrão = 1,5126.

- DIT: média = 1,0; mediana = 1,0; desvio padrão = 0,0.

- LCOM: média = 0,0695; mediana = 0,0; desvio padrão = 0,1768.


4. Discussão dos Resultados

4.1 Confrontar Questões-Pesquisa

RQ01 (Popularidade x Qualidade):

O repositório analisado apresenta alta popularidade e métricas estruturais controladas (LCOM baixo, DIT baixo, CBO moderado), sugerindo indício favorável de relação positiva. Contudo, a inferência estatística ainda é limitada por haver apenas um repositório com qualidade consolidada nesta fase.

RQ02 (Maturidade x Qualidade):

O repositório analisado é relativamente novo e, ainda assim, apresenta métricas estáveis. Isso indica que menor maturidade temporal não implica necessariamente pior qualidade.

RQ03 (Atividade x Qualidade):

Com atividade mediana e métricas de qualidade adequadas, observou-se indício de que atividade intermediária pode coexistir com boa organização estrutural.

RQ04 (Tamanho x Qualidade):

Mesmo com tamanho relevante (28705 LOC), o repositório manteve bons indicadores estruturais, reforçando que tamanho isolado não explica degradação da qualidade.


4.2 Confrontar Hipóteses

H1: Parcialmente suportada no estudo de caso.

H2: Não validada nesta fase (amostra de qualidade insuficiente para comparação de maturidade).

H3: Parcialmente suportada no estudo de caso.

H4: Não validada nesta fase (necessária amostra maior de repositórios com CK).

H5: Suportada no estudo de caso (DIT médio = 1,0).

H6: Suportada no estudo de caso.


4.3 Insights

Os resultados do experimento fornecem os seguintes insights importantes para a área de estudo:

Insight 1:

A distribuição de popularidade e atividade na amostra de 1.000 repositórios é fortemente assimétrica, indicando que análises futuras devem priorizar correlação não paramétrica (ex.: Spearman).


Insight 2:

No repositório analisado, DIT raso e LCOM baixo sugerem arquitetura com baixa profundidade de herança e boa coesão, mesmo em projeto de grande visibilidade.


Insight 3:

A automação construída no projeto viabiliza escalar a coleta para os próximos ciclos, permitindo transformar os indícios atuais em evidências estatísticas robustas ao ampliar a base de repositórios com métricas CK consolidadas.
