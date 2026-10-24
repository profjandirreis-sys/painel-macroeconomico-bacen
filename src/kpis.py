"""KPIs do Data App: Selic Meta, IPCA 12M, Juro Real Ex-Post e Dólar PTAX.

Regra de comparação (reage aos filtros):
- valor exibido = último mês selecionado;
- delta = diferença em relação ao primeiro mês selecionado.

Taxas (Selic, IPCA, juro real) têm delta em pontos percentuais (p.p.);
o dólar tem delta em variação percentual (%).
"""

from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass
class KPI:
    rotulo: str
    valor: str
    delta: str | None
    cor_delta: str  # "normal", "inverse" ou "off" (padrão do st.metric)
    ajuda: str


def formatar_numero(valor: float, casas: int = 2) -> str:
    """Formata no padrão brasileiro: 1234.5 -> '1.234,50'."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _delta(valor: float, unidade: str, casas: int = 2) -> str:
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{formatar_numero(valor, casas)} {unidade}"


def calcular_kpis(filtrados: pd.DataFrame, indicadores: list) -> list[KPI]:
    """Monta os KPIs a partir da base já filtrada, respeitando os indicadores escolhidos."""
    base = filtrados.sort_values("data")
    primeiro, ultimo = base.iloc[0], base.iloc[-1]
    tem_comparacao = len(base) > 1
    ref = f"{ultimo['data']:%m/%Y}"
    desde = f"{primeiro['data']:%m/%Y}"

    def variacao_pp(coluna: str) -> str | None:
        return _delta(ultimo[coluna] - primeiro[coluna], "p.p.") if tem_comparacao else None

    kpis = []

    if "selic_meta" in indicadores:
        kpis.append(KPI(
            rotulo="Selic Meta",
            valor=f"{formatar_numero(ultimo['selic_meta'])}% a.a.",
            delta=variacao_pp("selic_meta"),
            cor_delta="off",
            ajuda=f"Taxa definida pelo Copom vigente em {ref}. Delta: mudança desde {desde}.",
        ))

    if "ipca_12m" in indicadores:
        kpis.append(KPI(
            rotulo="IPCA 12 meses",
            valor=f"{formatar_numero(ultimo['ipca_12m'])}%",
            delta=variacao_pp("ipca_12m"),
            cor_delta="inverse",  # inflação subindo = vermelho
            ajuda=f"Inflação acumulada em 12 meses até {ref}. Delta: mudança desde {desde}.",
        ))

    if "selic_meta" in indicadores and "ipca_12m" in indicadores:
        kpis.append(KPI(
            rotulo="Juro Real Ex-Post",
            valor=f"{formatar_numero(ultimo['juro_real_ex_post'])}% a.a.",
            delta=variacao_pp("juro_real_ex_post"),
            cor_delta="normal",
            ajuda=(
                f"Quanto a Selic ficou acima da inflação em {ref} (equação de Fisher). "
                f"Aparece quando Selic e IPCA estão selecionados. Delta: mudança desde {desde}."
            ),
        ))

    if "dolar_ptax" in indicadores:
        media = base["dolar_ptax"].mean()
        variacao = (ultimo["dolar_ptax"] / primeiro["dolar_ptax"] - 1) * 100
        kpis.append(KPI(
            rotulo="Dólar PTAX",
            valor=f"R$ {formatar_numero(ultimo['dolar_ptax'], 4)}",
            delta=_delta(variacao, "%", 1) if tem_comparacao else None,
            cor_delta="inverse",  # dólar subindo = real desvalorizado
            ajuda=(
                f"Média das cotações de venda em {ref}. Média do período selecionado: "
                f"R$ {formatar_numero(media, 4)}. Delta: variação desde {desde}."
            ),
        ))

    return kpis


def renderizar_kpis(filtrados: pd.DataFrame, indicadores: list) -> None:
    """Mostra os KPIs lado a lado (st.columns + st.metric com borda)."""
    kpis = calcular_kpis(filtrados, indicadores)
    if not kpis:
        st.caption("Os KPIs aparecem quando Selic, IPCA ou Dólar estão selecionados nos filtros.")
        return

    inicio, fim = filtrados["data"].min(), filtrados["data"].max()
    st.subheader("📌 Indicadores-chave")
    st.caption(f"Valores de {fim:%m/%Y} · setas comparam com {inicio:%m/%Y}")

    for coluna, kpi in zip(st.columns(len(kpis)), kpis):
        coluna.metric(
            label=kpi.rotulo,
            value=kpi.valor,
            delta=kpi.delta,
            delta_color=kpi.cor_delta,
            help=kpi.ajuda,
            border=True,
        )
