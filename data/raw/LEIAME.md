# Dados brutos – SGS/Banco Central do Brasil

Arquivos gerados pela etapa de extração (`python -m src.extracao`), sem nenhuma alteração em relação à API.

- **Fonte:** API pública do Sistema Gerenciador de Séries Temporais (SGS) – `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`
- **Período consultado:** 01/01/2019 a 31/12/2023
- **Data da extração:** 23/10/2026
- **Formato:** CSV com as colunas `data` (dd/mm/aaaa) e `valor` (ponto como separador decimal)

| Arquivo | Código SGS | Série | Periodicidade | Registros |
|---|---|---|---|---|
| sgs_432.csv | 432 | Taxa Selic Meta (% a.a.) | Diária (dias corridos) | 1.826 |
| sgs_433.csv | 433 | IPCA – variação mensal (%) | Mensal | 60 |
| sgs_13522.csv | 13522 | IPCA – acumulado em 12 meses (%) | Mensal | 60 |
| sgs_1.csv | 1 | Dólar comercial PTAX – venda (R$) | Diária (dias úteis) | 1.255 |
| sgs_24364.csv | 24364 | IBC-Br dessazonalizado (índice) | Mensal | 60 |

Licença: dados públicos do Banco Central do Brasil, de livre utilização com citação da fonte.
