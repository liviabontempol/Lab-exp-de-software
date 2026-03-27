# Lab 02

Um estudo das características de qualidade de sistemas Java (CK)

## O que você precisa fazer (visão geral)

### Lab02S01 (começo)
1. Coletar a lista dos 1.000 repositórios Java mais populares do GitHub.
2. Automatizar clone + coleta de métricas de qualidade (CK) e métricas de tamanho (LOC/Comentários).
+   Por enquanto, neste sprint você precisa gerar o CSV de **pelo menos 1 repositório**.

### Lab02S02 (continuação)
1. Rodar a coleta (clone + CK) para todos os 1.000 repositórios.
2. Analisar correlação com as RQs e escrever o relatório final.

## Como coletar a lista dos 1.000 repositórios Java

O script `coletor_java.py` reaproveita a lógica de busca/paginação GraphQL criada no `lab01`.

1. Entre na pasta `lab02`:

```powershell
cd C:\Users\JOAOPEDRO\Documents\GitHub\Lab-exp-de-software\lab02
```

2. Crie um arquivo `.env` com:

```env
API_TOKEN=seu_token_aqui
```

3. Rode:

```powershell
python coletor_java.py
```

4. Ele vai gerar:

- `repos_java_1000.json` (dados brutos)
- `repos_java_1000.csv` (tabela com `stars`, `releases_total`, `repo_age_years`, etc.)

> Arquivos gerados servem de base para as métricas de popularidade, maturidade e atividade (as de “processo”).

## Próximo passo (antes de rodar CK)

Para completar o Lab02S01, me diga qual forma/instância do CK você vai usar (por exemplo, arquivo `.jar` do CK e o comando exato para gerar métricas CBO/DIT/LCOM).
Com isso eu monto o script de:
1. clonar 1 repositório (dado o `url` do CSV),
2. contar LOC/comentários,
3. executar o CK e consolidar `CBO`, `DIT`, `LCOM` em um CSV final para 1 repositório.
