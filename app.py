"""Painel Macroeconômico BACEN – Data App em Streamlit (em construção)."""

import streamlit as st

from src.dados import carregar_dados

st.set_page_config(page_title="Painel Macroeconômico BACEN", page_icon="📈", layout="wide")

st.title("Painel Macroeconômico BACEN")
st.caption("Selic, IPCA, Dólar PTAX e IBC-Br · 2019–2023 · Fonte: SGS/Banco Central do Brasil")

dados, origem, aviso = carregar_dados()

if aviso:
    st.warning(aviso)

st.sidebar.caption(f"📂 Origem dos dados: **{origem}**")
st.sidebar.caption(
    f"🗓️ Período: {dados['data'].min():%m/%Y} a {dados['data'].max():%m/%Y} · {len(dados)} meses"
)

st.info("Aplicação em construção. Prévia da base carregada:")
st.dataframe(dados.tail(12), width="stretch", hide_index=True)
