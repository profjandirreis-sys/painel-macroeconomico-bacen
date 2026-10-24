"""Storytelling do Data App: respostas às 5 perguntas de negócio da Linha 3.

Cada resposta segue a Pirâmide Invertida (Contexto → Insight → Ação) e é calculada
a partir da base completa de 2019–2023 (o quinquênio pedido no enunciado), para que
as conclusões não mudem conforme os filtros. Nenhum número é digitado à mão:
todos vêm dos dados, então o texto continua correto se a base for atualizada.

Regra metodológica: correlação não implica causalidade. Os textos descrevem
associações e coincidências temporais, nunca relações de causa comprovadas.
"""

from dataclasses import dataclass

import pandas as pd
import plotly.express as px
import streamlit as st

from src.indicadores import correlacao_defasada, matriz_correlacao, pares_mais_correlacionados
from src.kpis import formatar_numero as fmt


@dataclass
class Resposta:
    pergunta: str
    resumo: str      # a resposta em uma frase (topo da pirâmide)
    contexto: str
    insight: str
    acao: str


def _mes(data) -> str:
    return f"{pd.Timestamp(data):%m/%Y}"


def _intervalo(datas: pd.Series) -> str:
    return f"{_mes(datas.min())} a {_mes(datas.max())}"


# ---------------- Fases da política monetária ----------------
def fases_politica_monetaria(df: pd.DataFrame) -> pd.DataFrame:
    """Divide o período em fases: Alta, Corte e Manutenção (Selic parada entre movimentos).

    Uma fase de Alta vai do 1º ao último aumento seguido; os meses depois do último
    aumento, até a próxima mudança, são "Manutenção". O mesmo vale para os cortes.
    """
    base = df.sort_values("data").reset_index(drop=True)
    direcao = base["selic_variacao_pp"].apply(lambda v: "Alta" if v > 0 else ("Corte" if v < 0 else None))
    ultimo_mov = direcao.ffill()
    fase = ultimo_mov.copy()
    for rotulo in ("Alta", "Corte"):
        bloco = (ultimo_mov != ultimo_mov.shift()).cumsum()
        for _, idx in base[ultimo_mov == rotulo].groupby(bloco[ultimo_mov == rotulo]).groups.items():
            movs = [i for i in idx if direcao[i] == rotulo]
            fase[[i for i in idx if i > max(movs)]] = "Manutenção"
    base["fase"] = fase.fillna("Manutenção")

    grupos = (base["fase"] != base["fase"].shift()).cumsum()
    linhas = []
    for _, g in base.groupby(grupos):
        linhas.append({
            "fase": g["fase"].iloc[0],
            "inicio": g["data"].min(), "fim": g["data"].max(), "meses": len(g),
            # Selic antes da fase começar (mês anterior), para descrever "de X% para Y%"
            "selic_inicio": g["selic_meta"].iloc[0] - g["selic_variacao_pp"].iloc[0],
            "selic_fim": g["selic_meta"].iloc[-1],
            "ibc_inicio": g["ibc_br"].iloc[0], "ibc_fim": g["ibc_br"].iloc[-1],
        })
    fases = pd.DataFrame(linhas)
    fases["ibc_var_pct"] = (fases["ibc_fim"] / fases["ibc_inicio"] - 1) * 100
    return fases


def janelas_acima_da_media(df: pd.DataFrame) -> pd.DataFrame:
    """Sequências de meses seguidos com o dólar acima da média do quinquênio."""
    acima = df["dolar_ptax"] > df["dolar_ptax"].mean()
    bloco = (acima != acima.shift()).cumsum()
    janelas = [
        {"inicio": g["data"].min(), "fim": g["data"].max(), "meses": len(g), "pico": g["dolar_ptax"].max()}
        for _, g in df[acima].groupby(bloco[acima])
    ]
    return pd.DataFrame(janelas).sort_values("meses", ascending=False)


# ---------------- As 5 respostas ----------------
def resposta_selic(df: pd.DataFrame) -> Resposta:
    minima, maxima = df["selic_meta"].min(), df["selic_meta"].max()
    meses_min = df.loc[df["selic_meta"] == minima, "data"]
    meses_max = df.loc[df["selic_meta"] == maxima, "data"]
    pico = df.loc[df["juro_real_ex_post"].idxmax()]
    vale = df.loc[df["juro_real_ex_post"].idxmin()]
    negativo = df[df["juro_real_ex_post"] < 0]
    juro_2023 = df.loc[df["ano"] == df["ano"].max(), "juro_real_ex_post"].mean()
    inicio, fim = df.iloc[0], df.iloc[-1]

    return Resposta(
        pergunta="Como a Selic Meta evoluiu em 2019–2023 e quando o Brasil teve os maiores juros reais?",
        resumo=(f"A Selic caiu de {fmt(inicio['selic_meta'])}% para a mínima de {fmt(minima)}% e subiu até "
                f"{fmt(maxima)}%; o juro real mais alto foi {fmt(pico['juro_real_ex_post'])}% a.a. em {_mes(pico['data'])}."),
        contexto=(f"A Selic começou o período em {fmt(inicio['selic_meta'])}% a.a., ficou na mínima de "
                  f"**{fmt(minima)}%** de {_intervalo(meses_min)} e chegou a **{fmt(maxima)}%** de "
                  f"{_intervalo(meses_max)}, fechando em {fmt(fim['selic_meta'])}%."),
        insight=(f"O juro real ficou **negativo por {len(negativo)} meses** ({_intervalo(negativo['data'])}), com a "
                 f"mínima de {fmt(vale['juro_real_ex_post'])}% em {_mes(vale['data'])}: a Selic não cobria a inflação. "
                 f"Os maiores juros reais vieram em **{int(pico['ano'])}** (média de {fmt(juro_2023)}% a.a.), "
                 f"com pico de **{fmt(pico['juro_real_ex_post'])}% em {_mes(pico['data'])}**: Selic ainda em "
                 f"{fmt(pico['selic_meta'])}% e IPCA já recuando para {fmt(pico['ipca_12m'])}%."),
        acao=("Com juro real alto, aplicações pós-fixadas (CDI) ganham atratividade e o crédito fica caro: "
              "um gestor financeiro tende a priorizar caixa e reduzir dívida atrelada ao CDI. Com juro real "
              "negativo, manter dinheiro parado perde poder de compra."),
    )


def resposta_dolar(df: pd.DataFrame) -> Resposta:
    media = df["dolar_ptax"].mean()
    janelas = janelas_acima_da_media(df)
    principal = janelas.iloc[0]
    maximo, minimo = df.loc[df["dolar_ptax"].idxmax()], df.loc[df["dolar_ptax"].idxmin()]
    total_acima = int((df["dolar_ptax"] > media).sum())
    lista = "; ".join(
        f"{_mes(j.inicio)} a {_mes(j.fim)} ({j.meses} {'mês' if j.meses == 1 else 'meses'})"
        for j in janelas.sort_values("inicio").itertuples()
    )

    return Resposta(
        pergunta="Qual foi a trajetória do Dólar PTAX e quando ele ficou acima da média do quinquênio?",
        resumo=(f"O dólar ficou acima da média de R$ {fmt(media, 4)} em {total_acima} dos {len(df)} meses, "
                f"principalmente de {_mes(principal['inicio'])} a {_mes(principal['fim'])}."),
        contexto=(f"O dólar partiu da mínima de **R$ {fmt(minimo['dolar_ptax'], 4)}** ({_mes(minimo['data'])}) "
                  f"e chegou ao pico de **R$ {fmt(maximo['dolar_ptax'], 4)}** ({_mes(maximo['data'])}). "
                  f"A média do quinquênio foi R$ {fmt(media, 4)}."),
        insight=(f"O câmbio ficou acima da média em **{total_acima} de {len(df)} meses**, em {len(janelas)} janelas: "
                 f"{lista}. A mais longa ({principal['meses']} meses) começou no choque da pandemia, "
                 f"quando o Real perdeu valor rapidamente."),
        acao=("Empresas importadoras ou com dívida em dólar deveriam usar proteção cambial (hedge) nas janelas "
              "de câmbio alto; exportadoras tiveram receita em reais favorecida no mesmo período."),
    )


def resposta_cambio_inflacao(df: pd.DataFrame) -> tuple[Resposta, pd.DataFrame]:
    defas = correlacao_defasada(df, "dolar_var_12m", "ipca_12m")
    r0 = defas.loc[defas["defasagem_meses"] == 0, "correlacao"].item()
    melhor = defas.loc[defas["correlacao"].idxmax()]
    choque = df.loc[df["dolar_var_12m"].idxmax()]
    pico_ipca = df.loc[df["ipca_12m"].idxmax()]
    distancia = (pico_ipca["data"].year - choque["data"].year) * 12 + (pico_ipca["data"].month - choque["data"].month)
    nivel = df["dolar_ptax"].corr(df["ipca_12m"])

    resposta = Resposta(
        pergunta="Existe correlação entre os choques de desvalorização do Real e o avanço posterior do IPCA?",
        resumo=(f"Há sinais, mas com atraso: no mês do choque a correlação é {fmt(r0)}, e ela fica positiva "
                f"({fmt(melhor['correlacao'])}) cerca de {int(melhor['defasagem_meses'])} meses depois."),
        contexto=(f"O maior choque cambial foi em **{_mes(choque['data'])}**: dólar **+{fmt(choque['dolar_var_12m'], 1)}%** "
                  f"em 12 meses. O IPCA 12M atingiu o pico de **{fmt(pico_ipca['ipca_12m'])}%** em "
                  f"{_mes(pico_ipca['data'])}, {distancia} meses depois. No mesmo mês, dólar e IPCA têm "
                  f"correlação de apenas {fmt(nivel)}."),
        insight=(f"Comparando a alta do dólar em 12 meses com o IPCA **k meses depois**, a correlação sai de "
                 f"**{fmt(r0)}** (k = 0) e sobe até **{fmt(melhor['correlacao'])}** (k = {int(melhor['defasagem_meses'])}). "
                 "O padrão é compatível com o repasse cambial (produtos importados encarecem aos poucos), "
                 "mas no mesmo período houve choques de commodities, energia e a reabertura pós-pandemia."),
        acao=("Uma desvalorização forte do Real serve como **sinal de alerta antecipado** de pressão inflacionária "
              "nos meses seguintes, útil para revisar preços, contratos e orçamento, não como previsão exata."),
    )
    return resposta, defas


def resposta_atividade(df: pd.DataFrame) -> tuple[Resposta, pd.DataFrame]:
    fases = fases_politica_monetaria(df)
    alta = fases[fases["fase"] == "Alta"].sort_values("meses").iloc[-1]
    topo = fases[(fases["fase"] == "Manutenção") & (fases["inicio"] > alta["fim"])].iloc[0]
    corte = fases[fases["fase"] == "Corte"].sort_values("inicio").iloc[0]
    vale = df.loc[df["ibc_br"].idxmin()]
    pre = df[df["data"] < vale["data"]].iloc[-2]  # mês anterior ao início da queda
    pico = df.loc[df["ibc_br"].idxmax()]

    resposta = Resposta(
        pergunta="Como o IBC-Br reagiu aos períodos de aperto monetário (alta da Selic) e de corte?",
        resumo=(f"Ao contrário do senso comum, a atividade cresceu {fmt(alta['ibc_var_pct'], 1)}% durante a alta "
                f"da Selic e caiu {fmt(abs(corte['ibc_var_pct']), 1)}% no ciclo de corte que atravessou a pandemia."),
        contexto=(f"No ciclo de corte ({_mes(corte['inicio'])} a {_mes(corte['fim'])}, Selic de "
                  f"{fmt(corte['selic_inicio'])}% para {fmt(corte['selic_fim'])}%), o IBC-Br foi de "
                  f"{fmt(corte['ibc_inicio'])} para {fmt(corte['ibc_fim'])} pontos, com o vale de "
                  f"**{fmt(vale['ibc_br'])} em {_mes(vale['data'])}** (queda de "
                  f"{fmt(abs(vale['ibc_br'] / pre['ibc_br'] - 1) * 100, 1)}% frente a {_mes(pre['data'])}). "
                  f"Na alta ({_mes(alta['inicio'])} a {_mes(alta['fim'])}, Selic de {fmt(alta['selic_inicio'])}% para "
                  f"{fmt(alta['selic_fim'])}%), subiu de {fmt(alta['ibc_inicio'])} para {fmt(alta['ibc_fim'])} "
                  f"(**+{fmt(alta['ibc_var_pct'], 1)}%**)."),
        insight=("Isso **não** significa que juro alto acelera a economia. Dois fatores explicam a coincidência: "
                 "(1) o Copom **reage** à economia e à inflação: aprofundou os cortes quando a atividade desabou "
                 "na pandemia e subiu os juros para conter a inflação durante a recuperação; (2) os efeitos dos juros sobre crédito e consumo aparecem com "
                 "**defasagem de vários meses**. Coerente com isso, com a Selic parada no topo "
                 f"({_mes(topo['inicio'])} a {_mes(topo['fim'])}) o IBC-Br cresceu só "
                 f"+{fmt(topo['ibc_var_pct'], 1)}% em {topo['meses']} meses, ritmo bem menor que antes; "
                 f"o recorde de {fmt(pico['ibc_br'])} veio em {_mes(pico['data'])}, já com cortes."),
        acao=("Não use a Selic do mês para prever a atividade do mesmo mês. Para planejar vendas e crédito, "
              "acompanhe a trajetória esperada dos juros (expectativas do Boletim Focus) e considere o atraso."),
    )
    return resposta, fases


def resposta_correlacoes(df: pd.DataFrame) -> Resposta:
    pares = pares_mais_correlacionados(matriz_correlacao(df), n=3)
    p1, p2, p3 = pares.iloc[0], pares.iloc[1], pares.iloc[2]

    def par(p) -> str:
        return f"{p.variavel_1} × {p.variavel_2} (**r = {fmt(p.correlacao)}**)"

    return Resposta(
        pergunta="Quais pares de variáveis tiveram os maiores coeficientes de correlação de Pearson?",
        resumo=f"Os pares mais fortes foram {p1.variavel_1} × {p1.variavel_2} (r = {fmt(p1.correlacao)}) "
               f"e {p2.variavel_1} × {p2.variavel_2} (r = {fmt(p2.correlacao)}).",
        contexto=(f"Nos {len(df)} meses, os três pares com maior correlação linear foram: {par(p1)}, "
                  f"{par(p2)} e {par(p3)}."),
        insight=(f"O 1º par é em parte **mecânico**: o juro real é calculado a partir da Selic. O 2º "
                 "reflete **tendências em comum** (Selic e IBC-Br subiram juntos depois de 2020), não "
                 "um efeito de um sobre o outro. Séries com tendência tendem a mostrar correlações altas "
                 "mesmo sem relação direta (correlação espúria)."),
        acao=("Use a matriz para escolher quais indicadores acompanhar juntos, mas confirme qualquer "
              "relação com modelos que considerem defasagens e outros fatores antes de decidir com base nela."),
    )


# ---------------- Exibição ----------------
def renderizar_resposta(resposta: Resposta) -> None:
    """Pirâmide Invertida: pergunta e resposta curta no topo, detalhes logo abaixo."""
    with st.container(border=True):
        st.markdown(f"**❓ {resposta.pergunta}**")
        st.markdown(f"💡 {resposta.resumo}")
        contexto, insight, acao = st.columns(3)
        contexto.markdown(f"**1 · Contexto**\n\n{resposta.contexto}")
        insight.markdown(f"**2 · Insight**\n\n{resposta.insight}")
        acao.markdown(f"**3 · Ação**\n\n{resposta.acao}")
        st.caption("Resposta calculada com o quinquênio completo (01/2019 a 12/2023), independente dos filtros.")


def grafico_defasagem(defas: pd.DataFrame):
    """Barras da correlação dólar (var. 12m) × IPCA 12M k meses depois."""
    base = defas.assign(sinal=defas["correlacao"].apply(lambda r: "Positiva" if r >= 0 else "Negativa"))
    fig = px.bar(
        base, x="defasagem_meses", y="correlacao", color="sinal",
        color_discrete_map={"Positiva": "#d03b3b", "Negativa": "#1c5cab"},
        labels={"defasagem_meses": "Meses depois do choque cambial (k)", "correlacao": "Correlação (r)", "sinal": ""},
        title="Alta do dólar em 12 meses × IPCA 12M k meses depois",
    )
    fig.update_layout(
        separators=",.", template="plotly_white", height=330, barcornerradius=4,
        margin=dict(l=10, r=10, t=60, b=10), legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom"),
        title=dict(font=dict(size=15), x=0),
    )
    fig.update_traces(hovertemplate="k = %{x} meses<br>r = %{y:.2f}<extra></extra>")
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(range=[-1, 1], zerolinecolor="#b9b8b3", gridcolor="#e6e5e1")
    return fig


def renderizar_resumo_executivo(df: pd.DataFrame) -> None:
    """Topo da pirâmide: as três mensagens principais do painel."""
    r_selic, r_dolar = resposta_selic(df), resposta_dolar(df)
    r_cambio, _ = resposta_cambio_inflacao(df)
    with st.container(border=True):
        st.markdown("#### 🧭 Resumo executivo (2019–2023)")
        st.markdown(
            f"- **Juros:** {r_selic.resumo}\n"
            f"- **Câmbio:** {r_dolar.resumo}\n"
            f"- **Câmbio e inflação:** {r_cambio.resumo}"
        )
        st.caption("Detalhes e evidências em cada aba de gráficos abaixo · Correlação não implica causalidade.")


def renderizar_limitacoes() -> None:
    st.subheader("⚠️ Limitações da análise")
    st.markdown(
        "- **Correlação não é causalidade:** as associações mostradas não provam que uma variável causa a outra; "
        "comprovar causa exigiria modelos econométricos (ex.: VAR, regressões com controles).\n"
        "- **Janela curta e atípica:** 60 meses que incluem a pandemia, um choque de commodities e um ciclo de juros "
        "excepcional. Os padrões podem não se repetir em outros períodos.\n"
        "- **Frequência mensal:** a Selic (diária) usa o valor do fim do mês e o dólar usa a média mensal, o que "
        "suaviza movimentos dentro do mês.\n"
        "- **Variáveis ausentes:** preços de commodities, política fiscal, expectativas (Focus) e cenário externo "
        "também influenciam inflação, câmbio e atividade e não estão na base.\n"
        "- **Juro real ex-post:** compara a Selic atual com a inflação **passada** (12 meses); o juro real esperado "
        "(ex-ante) pode ser diferente.\n"
        "- **Revisões:** o IBC-Br é revisado pelo Banco Central; números recentes podem mudar."
    )
