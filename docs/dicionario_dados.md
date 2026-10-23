# Dicionário de Dados

Base final usada pelo Data App: `data/processed/macro_indicadores.csv`

- **Granularidade:** 1 linha por mês
- **Período:** janeiro/2019 a dezembro/2023 (60 linhas)
- **Fonte:** Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil
- **Geração:** `python -m src.pipeline` (extração → limpeza → indicadores)

## Colunas originais (vindas do SGS)

| Coluna | Tipo | Unidade | Descrição financeira | Origem / regra de cálculo | Faixa no período |
|---|---|---|---|---|---|
| `data` | datetime | – | Mês de referência (sempre o 1º dia do mês) | Datas do SGS (dd/mm/aaaa) convertidas para datetime e agrupadas por mês | 2019-01-01 a 2023-12-01 |
| `ano` | int | – | Ano de referência | Extraído de `data` | 2019 a 2023 |
| `mes` | int | – | Mês de referência (1 a 12) | Extraído de `data` | 1 a 12 |
| `selic_meta` | float | % a.a. | Taxa Selic Meta definida pelo Copom: principal instrumento de política monetária | SGS 432 (diária). Valor vigente no **último dia** do mês | 2,00 a 13,75 |
| `ipca_mensal` | float | % | Variação mensal do IPCA, o índice oficial de inflação ao consumidor | SGS 433 (mensal), sem alteração | −0,68 a 1,62 |
| `ipca_12m` | float | % | IPCA acumulado nos últimos 12 meses; usado para comparar com a meta de inflação | SGS 13522 (mensal), sem alteração | 1,88 a 12,13 |
| `dolar_ptax` | float | R$ por US$ | Taxa de câmbio PTAX de venda: referência oficial do dólar comercial | SGS 1 (dias úteis). **Média** das cotações do mês, 4 casas decimais | 3,7236 a 5,6514 |
| `ibc_br` | float | índice | Índice de Atividade Econômica do Banco Central, dessazonalizado; considerado uma "prévia" do PIB | SGS 24364 (mensal), sem alteração | 82,96 a 104,90 |

## Colunas derivadas (calculadas no ETL)

| Coluna | Tipo | Unidade | Descrição financeira | Regra de cálculo | Faixa no período |
|---|---|---|---|---|---|
| `juro_real_ex_post` | float | % a.a. | Juro real efetivamente obtido: quanto a Selic ficou acima (ou abaixo) da inflação passada | Equação de Fisher: `((1 + selic_meta/100) / (1 + ipca_12m/100) − 1) × 100`, 2 casas | −4,35 a 10,27 |
| `dolar_media_periodo` | float | R$ por US$ | Média do dólar PTAX em todo o quinquênio, usada como linha de referência | Média de `dolar_ptax` nos 60 meses | 4,9311 (constante) |
| `dolar_acima_media` | bool | – | Indica se o câmbio do mês ficou acima da média do quinquênio | `dolar_ptax > dolar_media_periodo` | True em 39 meses |
| `dolar_var_12m` | float | % | Variação do dólar em relação ao mesmo mês do ano anterior (choques cambiais) | `(dolar_ptax / dolar_ptax 12 meses antes − 1) × 100` | −14,46 a 41,03 |
| `ibc_br_var_12m` | float | % | Crescimento da atividade econômica em 12 meses | `(ibc_br / ibc_br 12 meses antes − 1) × 100` | −13,37 a 16,11 |
| `selic_variacao_pp` | float | pontos percentuais | Mudança da Selic Meta em relação ao mês anterior | `selic_meta − selic_meta do mês anterior` (0 no primeiro mês) | −0,75 a 1,50 |
| `ciclo_monetario` | texto | – | Fase da política monetária no mês | `Alta` se a Selic subiu, `Corte` se caiu, `Estável` se não mudou | Alta 12, Corte 13, Estável 35 |

## Tratamentos aplicados

- **Datas:** convertidas de texto `dd/mm/aaaa` para `datetime`; meses padronizados no 1º dia.
- **Valores:** convertidos de texto para `float`, com troca de vírgula decimal por ponto quando necessário.
- **Encoding:** leitura e gravação em UTF-8 explícito.
- **Nulos e duplicados:** verificados em todas as séries brutas; nenhum foi encontrado. A base final é validada automaticamente (60 meses, sem nulos e sem duplicados nas colunas originais).
- **Nulos esperados:** `dolar_var_12m` e `ibc_br_var_12m` ficam vazias nos 12 meses de 2019, porque não existe o mesmo mês do ano anterior dentro do período analisado.
