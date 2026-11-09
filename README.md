# Crescimento Populacional Brasileiro — Entrega individual

## Conteúdo
- `etl_estatisticas.py`: módulo de extração, validação, transformação e geração de estatísticas.
- `dados/populacao_uf_original.csv`: dados de entrada das 27 UFs.
- `dados/populacao_uf_tratada.csv`: base estadual limpa, com participação e ranking.
- `dados/populacao_brasil_historica_original.csv`: série nacional histórica.
- `dados/populacao_brasil_historica_tratada.csv`: série histórica com variações.
- `dados/base_ibge_tratada.xlsx`: planilha organizada em abas.
- `dados/estatisticas_uf_2025.json`: resultados estatísticos calculados.
- `analise_descritiva.docx` e `.txt`: interpretação dos resultados.
- `dashboard.py`: dashboard opcional em Streamlit.

## Fonte
IBGE — Estimativas da População 2025, data de referência de 1º de julho de 2025:
https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/estimativa_dou_2025.pdf

O arquivo oficial informa a população do Brasil e das 27 unidades da Federação.
A base estadual deste projeto contém apenas população total por UF. Portanto,
não há filtros por sexo ou faixa etária: essas dimensões exigiriam outra base
do IBGE com dados desagregados correspondentes.

A série histórica nacional reúne Censos Demográficos (2000, 2010 e 2022) e
estimativas (2024 e 2025). Como são modalidades distintas, o tipo de
levantamento é identificado em cada registro. A série não deve ser tratada
como se todos os pontos fossem censos.

## Instalação
```bash
pip install streamlit pandas numpy
```

## Executar ETL
Na pasta do projeto:
```bash
python etl_estatisticas.py
```

## Executar dashboard
```bash
 python -m streamlit run dashboard.py
```

## Metodologia estatística
As métricas de dispersão e os outliers são calculados sobre as 27 UFs
(população estadual estimada em 2025). O desvio padrão é populacional
(`ddof=0`), pois o conjunto inclui todas as unidades da Federação.
Os quartis são calculados pelo método padrão de interpolação linear do Pandas.
A moda é indicada como inexistente quando todos os valores são distintos.
