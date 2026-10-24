"""Os 5 gráficos Plotly do Data App, organizados em abas (st.tabs).

1. Política monetária: Selic Meta e IPCA 12M (linhas) + Juro Real Ex-Post (barras)
2. Dólar PTAX com a linha da média do período filtrado
3. Dispersão Dólar × IPCA 12M (cor = ano, tamanho = Selic)
4. IBC-Br dessazonalizado
5. Heatmap de correlação de Pearson com valores anotados

Todos os gráficos usam a base já filtrada e estão em português
(títulos, eixos, legendas, tooltips e separador decimal com vírgula).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import storytelling as story
from src.indicadores import VARIAVEIS_CORRELACAO, matriz_correlacao

# ---------------- Paleta (validada para daltonismo) ----------------
AZUL = "#2a78d6"
LARANJA = "#eb6834"
VERDE_AGUA = "#1baf7a"
CINZA_MEDIA = "#52514e"
# Rampa ordinal de azul para os anos (claro = mais antigo, escuro = mais recente)
RAMPA_ANOS = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]
# Escala divergente da correlação: azul (−1) · cinza (0) · vermelho (+1)
ESCALA_CORRELACAO = [[0.0, "#1c5cab"], [0.5, "#f0efec"], [1.0, "#d03b3b"]]

TEXTO = "#1A1A1A"
TEXTO_SECUNDARIO = "#52514e"
GRADE = "#e6e5e1"
FORMATO_MES = "%m/%Y"


def _layout(fig: go.Figure, titulo: str, eixo_y: str, eixo_x: str = "Mês") -> go.Figure:
    """Estilo comum: fundo limpo, grade discreta, legenda em cima e números em pt-BR."""
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=17, color=TEXTO), x=0, xanchor="left"),
        separators=",.",
        template="plotly_white",
        font=dict(color=TEXTO_SECUNDARIO, size=13),
        height=440,
        margin=dict(l=10, r=10, t=70, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title_text=""),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_color=TEXTO),
        barcornerradius=4,
    )
    fig.update_xaxes(title_text=eixo_x, showgrid=False, linecolor=GRADE, ticks="outside", tickcolor=GRADE)
    fig.update_yaxes(title_text=eixo_y, gridcolor=GRADE, zerolinecolor="#b9b8b3")
    return fig


def com_lacunas(df: pd.DataFrame) -> pd.DataFrame:
    """Completa os meses que ficaram fora do filtro com valores vazios.

    Assim, se o usuário escolher anos não seguidos (ex.: 2020 e 2023), a linha
    é interrompida no intervalo, em vez de ligar 12/2020 direto a 01/2023.
    """
    return df.set_index("data").asfreq("MS").reset_index()


# ---------------- 1. Política monetária ----------------
def grafico_politica_monetaria(df: pd.DataFrame, indicadores: list) -> go.Figure:
    fig = go.Figure()
    if "selic_meta" in indicadores and "ipca_12m" in indicadores:
        fig.add_bar(
            x=df["data"], y=df["juro_real_ex_post"], name="Juro Real Ex-Post",
            marker_color=VERDE_AGUA, opacity=0.55,
            hovertemplate="%{y:.2f}% a.a.",
        )
    if "selic_meta" in indicadores:
        fig.add_scatter(
            x=df["data"], y=df["selic_meta"], name="Selic Meta", mode="lines",
            line=dict(color=AZUL, width=2.5, shape="hv"),
            hovertemplate="%{y:.2f}% a.a.",
        )
    if "ipca_12m" in indicadores:
        fig.add_scatter(
            x=df["data"], y=df["ipca_12m"], name="IPCA 12 meses", mode="lines",
            line=dict(color=LARANJA, width=2.5),
            hovertemplate="%{y:.2f}%",
        )
    fig.update_xaxes(tickformat=FORMATO_MES, hoverformat=FORMATO_MES)
    fig.update_layout(bargap=0.15)
    return _layout(fig, "Selic, inflação e juro real", "% (taxa)")


# ---------------- 2. Dólar PTAX ----------------
def grafico_dolar(df: pd.DataFrame) -> go.Figure:
    media = df["dolar_ptax"].mean()
    fig = go.Figure()
    fig.add_scatter(
        x=df["data"], y=df["dolar_ptax"], name="Dólar PTAX (média do mês)", mode="lines+markers",
        line=dict(color=AZUL, width=2.5), marker=dict(size=6, line=dict(color="white", width=1)),
        hovertemplate="R$ %{y:.4f}",
    )
    fig.add_hline(
        y=media, line=dict(color=CINZA_MEDIA, width=1.5, dash="dash"),
        annotation_text=f"Média do período: R$ {media:.4f}".replace(".", ","),
        annotation_position="top left", annotation_font_color=TEXTO_SECUNDARIO,
    )
    fig.update_xaxes(tickformat=FORMATO_MES, hoverformat=FORMATO_MES)
    fig.update_yaxes(tickprefix="R$ ", tickformat=".2f")
    return _layout(fig, "Dólar PTAX × média do período", "R$ por US$")


# ---------------- 3. Dispersão Dólar × IPCA ----------------
def grafico_dispersao(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    anos = sorted(df["ano"].unique())
    # tamanho da bolha proporcional à Selic (mesma escala para todos os anos)
    tamanho_max = df["selic_meta"].max()
    for ano in anos:
        parte = df[df["ano"] == ano]
        cor = RAMPA_ANOS[(ano - 2019) % len(RAMPA_ANOS)]  # cor fixa por ano: não muda com o filtro
        fig.add_scatter(
            x=parte["dolar_ptax"], y=parte["ipca_12m"], name=str(ano), mode="markers",
            marker=dict(
                color=cor, size=parte["selic_meta"], sizemode="area",
                sizeref=2.0 * tamanho_max / (34 ** 2), sizemin=6,
                line=dict(color="white", width=1.5), opacity=0.9,
            ),
            customdata=parte[["data", "selic_meta"]].assign(data=parte["data"].dt.strftime(FORMATO_MES)),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Dólar: R$ %{x:.4f}<br>IPCA 12M: %{y:.2f}%"
                "<br>Selic: %{customdata[1]:.2f}% a.a.<extra></extra>"
            ),
        )
    _layout(fig, "Dólar × inflação (tamanho da bolha = Selic)", "IPCA 12 meses (%)", "Dólar PTAX (R$)")
    # itemsizing constante: na legenda todas as bolinhas têm o mesmo tamanho (a cor é o que identifica o ano)
    fig.update_layout(
        hovermode="closest",
        legend=dict(title=dict(text="Ano:", side="left"), itemsizing="constant"),
    )
    fig.update_xaxes(tickprefix="R$ ", tickformat=".2f", showgrid=True, gridcolor=GRADE)
    return fig


# ---------------- 4. IBC-Br ----------------
def grafico_ibc_br(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(
        x=df["data"], y=df["ibc_br"], name="IBC-Br dessazonalizado", mode="lines",
        line=dict(color=AZUL, width=2.5), fill="tozeroy", fillcolor="rgba(42,120,214,0.08)",
        hovertemplate="%{y:.2f} pontos",
    )
    fig.update_xaxes(tickformat=FORMATO_MES, hoverformat=FORMATO_MES)
    minimo, maximo = df["ibc_br"].min(), df["ibc_br"].max()
    folga = max((maximo - minimo) * 0.15, 1)
    fig.update_yaxes(range=[minimo - folga, maximo + folga])
    return _layout(fig, "Atividade econômica (IBC-Br, prévia do PIB)", "Índice (pontos)")


# ---------------- 5. Heatmap de correlação ----------------
def variaveis_correlacao(indicadores: list) -> dict:
    """Variáveis da matriz: as selecionadas + juro real quando Selic e IPCA estão ativos."""
    escolhidas = set(indicadores)
    if {"selic_meta", "ipca_12m"} <= escolhidas:
        escolhidas.add("juro_real_ex_post")
    return {c: r for c, r in VARIAVEIS_CORRELACAO.items() if c in escolhidas}


def grafico_correlacao(df: pd.DataFrame, indicadores: list) -> go.Figure:
    matriz = matriz_correlacao(df, variaveis_correlacao(indicadores))
    texto = matriz.map(lambda v: "–" if pd.isna(v) else f"{v:.2f}".replace(".", ","))
    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=matriz.columns, y=matriz.index,
        zmin=-1, zmax=1, colorscale=ESCALA_CORRELACAO,
        text=texto.values, texttemplate="%{text}", textfont=dict(size=15),
        xgap=2, ygap=2,
        colorbar=dict(title="r", tickvals=[-1, -0.5, 0, 0.5, 1], ticktext=["−1", "−0,5", "0", "0,5", "1"]),
        hovertemplate="%{y} × %{x}<br>Correlação: %{text}<extra></extra>",
    ))
    _layout(fig, "Correlação de Pearson entre os indicadores", "", "")
    fig.update_layout(hovermode="closest", height=480)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="bottom", ticks="")
    return fig


# ---------------- Abas ----------------
def _precisa(texto: str) -> None:
    st.info(f"Para ver este gráfico, selecione {texto} nos filtros da barra lateral.")


def renderizar_graficos(df: pd.DataFrame, indicadores: list, completos: pd.DataFrame) -> None:
    """Abas de análise: em cada uma, a resposta à pergunta de negócio (Pirâmide Invertida)
    e, logo abaixo, os gráficos que servem de evidência.

    `df` = base filtrada (gráficos); `completos` = quinquênio inteiro (respostas).
    """
    st.subheader("📊 Análise gráfica")
    abas = st.tabs([
        "🏦 Política monetária",
        "💵 Dólar",
        "🔵 Dólar × Inflação",
        "🏭 Atividade (IBC-Br)",
        "🔗 Correlações",
    ])
    config = {"displaylogo": False, "locale": "pt-BR"}
    serie = com_lacunas(df)  # para os gráficos de linha ao longo do tempo

    with abas[0]:
        story.renderizar_resposta(story.resposta_selic(completos))
        if {"selic_meta", "ipca_12m"} & set(indicadores):
            st.plotly_chart(grafico_politica_monetaria(serie, indicadores), width="stretch", config=config)
            st.caption("O juro real (barras) é a Selic descontada a inflação de 12 meses: "
                       "abaixo de zero, a taxa básica não cobria a inflação.")
        else:
            _precisa("**Selic Meta** ou **IPCA 12 meses**")

    with abas[1]:
        story.renderizar_resposta(story.resposta_dolar(completos))
        if "dolar_ptax" in indicadores:
            st.plotly_chart(grafico_dolar(serie), width="stretch", config=config)
            st.caption("Linha tracejada: média do dólar nos meses selecionados.")
        else:
            _precisa("**Dólar PTAX**")

    with abas[2]:
        resposta, defasagens = story.resposta_cambio_inflacao(completos)
        story.renderizar_resposta(resposta)
        st.plotly_chart(story.grafico_defasagem(defasagens), width="stretch", config=config)
        st.caption("Cada barra compara a alta do dólar em 12 meses com o IPCA 12M k meses depois "
                   "(quinquênio completo). Barras vermelhas: andam juntos; azuis: em sentidos opostos.")
        if {"dolar_ptax", "ipca_12m"} <= set(indicadores):
            st.plotly_chart(grafico_dispersao(df), width="stretch", config=config)
            st.caption("Cada bolha é um mês. Cores mais escuras são anos mais recentes; "
                       "bolhas maiores indicam Selic mais alta.")
        else:
            _precisa("**Dólar PTAX** e **IPCA 12 meses**")

    with abas[3]:
        story.renderizar_resposta(story.resposta_atividade(completos)[0])
        if "ibc_br" in indicadores:
            st.plotly_chart(grafico_ibc_br(serie), width="stretch", config=config)
            st.caption("Índice dessazonalizado: retira os efeitos típicos de cada época do ano.")
        else:
            _precisa("**IBC-Br**")

    with abas[4]:
        story.renderizar_resposta(story.resposta_correlacoes(completos))
        if len(variaveis_correlacao(indicadores)) < 2:
            _precisa("pelo menos **dois indicadores**")
        elif len(df) < 3:
            st.info("Selecione pelo menos 3 meses para calcular as correlações.")
        else:
            st.plotly_chart(grafico_correlacao(df, indicadores), width="stretch", config=config)
            st.caption("Vermelho = andam juntos (r perto de +1); azul = andam em sentidos opostos "
                       "(r perto de −1); cinza = pouca relação linear. Correlação não implica causalidade.")
