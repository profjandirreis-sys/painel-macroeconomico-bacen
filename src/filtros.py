"""Filtros da barra lateral do Data App.

Cada filtro tem uma chave própria em st.session_state (ex.: "filtro_anos_0").
O Streamlit guarda ali a escolha do usuário, que permanece igual quando ele interage
com outras partes do app.

O botão "Resetar filtros" aumenta a versão das chaves ("filtro_anos_1", ...): os
componentes são recriados com os valores padrão – período completo, todos os anos
e todos os indicadores.

Obs.: o valor padrão é passado no próprio componente (value/default). É isso que faz o
select_slider funcionar como intervalo (duas pontas) em todas as execuções.
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
CHAVE_VERSAO = "filtros_versao"  # aumenta 1 a cada clique em "Resetar filtros"


def _meses(dados: pd.DataFrame) -> list:
    return list(dados["data"].sort_values().dt.date.unique())


def _anos(dados: pd.DataFrame) -> list:
    return sorted(dados["ano"].unique().tolist())


def _valores_padrao(dados: pd.DataFrame) -> dict:
    meses = _meses(dados)
    return {
        CHAVE_PERIODO: (meses[0], meses[-1]),
        CHAVE_ANOS: _anos(dados),
        CHAVE_INDICADORES: list(INDICADORES),
    }


def _chave(nome: str) -> str:
    """Chave do componente no session_state, ex.: "filtro_anos_0"."""
    return f"{nome}_{st.session_state.get(CHAVE_VERSAO, 0)}"


def resetar_filtros() -> None:
    """Callback do botão: troca a versão das chaves dos filtros.

    Com chaves novas, o Streamlit recria cada componente do zero com o valor padrão,
    tanto nos dados quanto na tela. As escolhas antigas deixam de ser usadas e são
    descartadas automaticamente.
    """
    st.session_state[CHAVE_VERSAO] = st.session_state.get(CHAVE_VERSAO, 0) + 1


def renderizar_sidebar(dados: pd.DataFrame) -> tuple[tuple, list, list]:
    """Desenha os filtros na barra lateral e devolve (período, anos, indicadores)."""
    meses = _meses(dados)
    padrao = _valores_padrao(dados)

    st.sidebar.header("🔎 Filtros")
    periodo = st.sidebar.select_slider(
        "Período",
        options=meses,
        value=padrao[CHAVE_PERIODO],
        key=_chave(CHAVE_PERIODO),
        format_func=lambda d: d.strftime("%m/%Y"),
        help="Arraste as pontas para escolher o mês inicial e o mês final.",
    )
    anos = st.sidebar.multiselect(
        "Anos",
        options=_anos(dados),
        default=padrao[CHAVE_ANOS],
        key=_chave(CHAVE_ANOS),
        placeholder="Selecione os anos",
        help="Mostra apenas os anos marcados (dentro do período escolhido).",
    )
    indicadores = st.sidebar.multiselect(
        "Indicadores",
        options=list(INDICADORES),
        default=padrao[CHAVE_INDICADORES],
        key=_chave(CHAVE_INDICADORES),
        placeholder="Selecione os indicadores",
        format_func=INDICADORES.get,
        help="Escolha quais indicadores aparecem nos KPIs e gráficos.",
    )
    st.sidebar.button(
        "🔄 Resetar filtros", on_click=resetar_filtros, width="stretch"
    )

    return periodo, anos, indicadores


def aplicar_filtros(dados: pd.DataFrame, periodo: tuple, anos: list) -> pd.DataFrame:
    """Mantém só os meses dentro do período E dos anos escolhidos."""
    inicio, fim = (pd.Timestamp(d) for d in periodo)
    filtro = dados["data"].between(inicio, fim) & dados["ano"].isin(anos)
    return dados.loc[filtro].reset_index(drop=True)
