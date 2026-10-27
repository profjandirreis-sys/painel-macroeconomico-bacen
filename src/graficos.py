"""Os 5 gráficos Plotly do Data App, organizados em abas (st.tabs).

1. Política monetária: Selic Meta e IPCA 12M (linhas) + Juro Real Ex-Post (barras)
2. Dólar PTAX com a linha da média do período filtrado
3. Dispersão Dólar × IPCA 12M (cor = ano, tamanho = Selic)
4. IBC-Br dessazonalizado
5. Heatmap de correlação de Pearson com valores anotados

Todos os gráficos são construídos com Plotly Express (px.bar, px.line, px.scatter,
px.imshow), usam a base já filtrada e estão em português (títulos, eixos, legendas,
tooltips e separador decimal com vírgula).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # usado só para a anotação de tipo (go.Figure)
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
LINHAS_POLITICA = {"selic_meta": "Selic Meta", "ipca_12m": "IPCA 12 meses"}


def grafico_politica_monetaria(df: pd.DataFrame, indicadores: list) -> go.Figure:
    # Linhas (px.line) em formato longo: uma linha por indicador
    colunas = [c for c in LINHAS_POLITICA if c in indicadores]
    longo = df.melt(id_vars="data", value_vars=colunas, var_name="indicador", value_name="valor")
    longo["indicador"] = longo["indicador"].map(LINHAS_POLITICA)
    linhas = px.line(
        longo, x="data", y="valor", color="indicador",
        color_discrete_map={"Selic Meta": AZUL, "IPCA 12 meses": LARANJA},
    )
    linhas.update_traces(line_width=2.5)
    linhas.update_traces(line_shape="hv", hovertemplate="%{y:.2f}% a.a.", selector=dict(name="Selic Meta"))
    linhas.update_traces(hovertemplate="%{y:.2f}%", selector=dict(name="IPCA 12 meses"))

    # Barras do juro real (px.bar), só quando Selic e IPCA estão selecionados
    if {"selic_meta", "ipca_12m"} <= set(indicadores):
        fig = px.bar(df, x="data", y="juro_real_ex_post", opacity=0.55,
                     color_discrete_sequence=[VERDE_AGUA])
        fig.update_traces(name="Juro Real Ex-Post", showlegend=True, hovertemplate="%{y:.2f}% a.a.")
        fig.add_traces(linhas.data)  # barras atrás, linhas na frente
    else:
        fig = linhas

    fig.update_xaxes(tickformat=FORMATO_MES, hoverformat=FORMATO_MES)
    fig.update_layout(bargap=0.15)
    return _layout(fig, "Selic, inflação e juro real", "% (taxa)")


# ---------------- 2. Dólar PTAX ----------------
def grafico_dolar(df: pd.DataFrame) -> go.Figure:
    media = df["dolar_ptax"].mean()
    fig = px.line(df, x="data", y="dolar_ptax", markers=True, color_discrete_sequence=[AZUL])
    fig.update_traces(
        name="Dólar PTAX (média do mês)", line_width=2.5,
        marker=dict(size=6, line=dict(color="white", width=1)),
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
    base = df.assign(
        ano_texto=df["ano"].astype(str),
        mes_texto=df["data"].dt.strftime(FORMATO_MES),
    )
    # cor fixa por ano (não muda com o filtro): 2019 = azul claro ... 2023 = azul escuro
    anos = sorted(base["ano"].unique())
    cores = {str(a): RAMPA_ANOS[(a - 2019) % len(RAMPA_ANOS)] for a in anos}
    fig = px.scatter(
        base, x="dolar_ptax", y="ipca_12m",
        color="ano_texto", size="selic_meta", size_max=24,  # bolha maior = Selic mais alta
        color_discrete_map=cores, category_orders={"ano_texto": [str(a) for a in anos]},
        custom_data=["mes_texto", "selic_meta"],
    )
    fig.update_traces(
        marker=dict(sizemin=6, line=dict(color="white", width=1.5), opacity=0.9),
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
    fig = px.line(df, x="data", y="ibc_br", color_discrete_sequence=[AZUL])
    fig.update_traces(
        name="IBC-Br dessazonalizado", line_width=2.5,
        fill="tozeroy", fillcolor="rgba(42,120,214,0.08)",
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
    fig = px.imshow(
        matriz, zmin=-1, zmax=1, aspect="auto",
        color_continuous_scale=ESCALA_CORRELACAO,
    )
    fig.update_traces(
        text=texto.values, texttemplate="%{text}", textfont=dict(size=15),
        xgap=2, ygap=2,
        hovertemplate="%{y} × %{x}<br>Correlação: %{text}<extra></extra>",
    )
    _layout(fig, "Correlação de Pearson entre os indicadores", "", "")
    fig.update_layout(
        hovermode="closest", height=480,
        coloraxis_colorbar=dict(title="r", tickvals=[-1, -0.5, 0, 0.5, 1], ticktext=["−1", "−0,5", "0", "0,5", "1"]),
    )
    fig.update_yaxes(showgrid=False)  # px.imshow já coloca a 1ª linha no topo
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
