"""Filtros da barra lateral do Data App.

As escolhas ficam guardadas em st.session_state (chaves que começam com "filtro_"),
então permanecem iguais quando o usuário interage com outras partes do app.
O botão "Resetar filtros" devolve tudo ao padrão: período completo, todos os anos
e todos os indicadores.
"""

import pandas as pd
import streamlit as st

# Indicadores principais do painel (coluna da base: rótulo exibido)
INDICADORES = {
    "selic_meta": "Selic Meta (% a.a.)",
    "ipca_12m": "IPCA acumulado 12 meses (%)",
    "dolar_ptax": "Dólar PTAX (R$)",
    "ibc_br": "IBC-Br (índice)",
}

CHAVE_PERIODO = "filtro_periodo"
CHAVE_ANOS = "filtro_anos"
CHAVE_INDICADORES = "filtro_indicadores"


def _meses(dados: pd.DataFrame) -> list:
    return list(dados["data"].sort_values().dt.date.unique())


def _valores_padrao(dados: pd.DataFrame) -> dict:
    meses = _meses(dados)
    return {
        CHAVE_PERIODO: (meses[0], meses[-1]),
        CHAVE_ANOS: sorted(dados["ano"].unique().tolist()),
        CHAVE_INDICADORES: list(INDICADORES),
    }


def inicializar_estado(dados: pd.DataFrame) -> None:
    """Cria os filtros no session_state só na primeira execução da sessão."""
    for chave, valor in _valores_padrao(dados).items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def resetar_filtros(dados: pd.DataFrame) -> None:
    """Callback do botão: volta todos os filtros ao valor padrão."""
    for chave, valor in _valores_padrao(dados).items():
        st.session_state[chave] = valor


def aplicar_filtros(dados: pd.DataFrame, periodo: tuple, anos: list) -> pd.DataFrame:
    """Mantém só os meses dentro do período E dos anos escolhidos."""
    inicio, fim = (pd.Timestamp(d) for d in periodo)
    filtro = dados["data"].between(inicio, fim) & dados["ano"].isin(anos)
    return dados.loc[filtro].reset_index(drop=True)
