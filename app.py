"""Painel Macroeconômico BACEN – Data App em Streamlit (em construção)."""

import streamlit as st

from src.dados import carregar_dados
from src.filtros import INDICADORES, aplicar_filtros, renderizar_sidebar

st.set_page_config(page_title="Painel Macroeconômico BACEN", page_icon="📈", layout="wide")

st.title("Painel Macroeconômico BACEN")
st.caption("Selic, IPCA, Dólar PTAX e IBC-Br · 2019–2023 · Fonte: SGS/Banco Central do Brasil")

dados, origem, aviso = carregar_dados()

if aviso:
    st.warning(aviso)

# ---------------- Filtros (sidebar) ----------------
periodo, anos, indicadores = renderizar_sidebar(dados)
filtrados = aplicar_filtros(dados, periodo, anos)

st.sidebar.divider()
st.sidebar.caption(f"📂 Origem dos dados: **{origem}**")

# ---------------- Validações dos filtros ----------------
if not indicadores:
    st.warning("Selecione pelo menos um indicador na barra lateral.")
    st.stop()

if filtrados.empty:
    st.warning("Nenhum mês corresponde aos filtros escolhidos. Ajuste o período ou os anos, ou clique em **Resetar filtros**.")
    st.stop()

st.caption(
    f"🗓️ {filtrados['data'].min():%m/%Y} a {filtrados['data'].max():%m/%Y} · "
    f"{len(filtrados)} de {len(dados)} meses selecionados"
)

st.info("Aplicação em construção. Prévia dos dados filtrados:")
colunas = ["data"] + indicadores
st.dataframe(
    filtrados[colunas].rename(columns=INDICADORES),
    width="stretch",
    hide_index=True,
    column_config={"data": st.column_config.DateColumn("Mês", format="MM/YYYY")},
)
