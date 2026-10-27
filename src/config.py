"""Configurações centrais do projeto: caminhos relativos, período e séries do SGS/BACEN."""

from pathlib import Path

# Caminhos sempre relativos à raiz do projeto (funciona em qualquer computador e no Streamlit Cloud)
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"
PASTA_BRUTOS = PASTA_DADOS / "raw"
PASTA_TRATADOS = PASTA_DADOS / "processed"
ARQUIVO_BASE = PASTA_TRATADOS / "macro_mensal.csv"
ARQUIVO_INDICADORES = PASTA_TRATADOS / "macro_indicadores.csv"

# Período obrigatório da Linha 3 do enunciado
DATA_INICIAL = "01/01/2019"
DATA_FINAL = "31/12/2023"

# Séries oficiais do SGS (código: nome da coluna)
SERIES_SGS = {
    432: "selic_meta",       # Meta Selic definida pelo Copom (% a.a.)
    433: "ipca_mensal",      # IPCA – variação mensal (%)
    13522: "ipca_12m",       # IPCA – acumulado em 12 meses (%)
    1: "dolar_ptax",         # Dólar comercial PTAX – venda (R$)
    24364: "ibc_br",         # IBC-Br dessazonalizado (índice)
}

URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
