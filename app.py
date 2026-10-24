"""Painel Macroeconômico BACEN – Data App em Streamlit (em construção)."""

import streamlit as st

from src.dados import carregar_dados
from src.exportacao import gerar_csv, nome_arquivo
from src.filtros import INDICADORES, aplicar_filtros, renderizar_sidebar
from src.graficos import renderizar_graficos
from src.kpis import renderizar_kpis

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

# ---------------- KPIs ----------------
renderizar_kpis(filtrados, indicadores)

# ---------------- Gráficos ----------------
st.divider()
renderizar_graficos(filtrados, indicadores)

# ---------------- Exportação e tabela ----------------
st.divider()
col_texto, col_botao = st.columns([3, 1], vertical_alignment="center")
col_texto.markdown(
    f"**💾 Exportar dados** · {len(filtrados)} meses filtrados, com todas as colunas da base "
    "(formato do Excel em português: separador `;` e vírgula decimal)."
)
col_botao.download_button(
    "⬇️ Baixar CSV",
    data=gerar_csv(filtrados),
    file_name=nome_arquivo(filtrados),
    mime="text/csv",
    type="primary",
    width="stretch",
    on_click="ignore",  # baixar não recarrega o app nem altera os filtros
)

with st.expander("📋 Ver os dados filtrados em tabela"):
    colunas = ["data"] + indicadores
    st.dataframe(
        filtrados[colunas].rename(columns=INDICADORES),
        width="stretch",
        hide_index=True,
        column_config={"data": st.column_config.DateColumn("Mês", format="MM/YYYY")},
    )
