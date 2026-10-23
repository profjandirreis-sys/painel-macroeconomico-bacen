"""Etapa 3 do ETL – Indicadores derivados e funções analíticas.

Lê a base mensal tratada (data/processed/macro_mensal.csv), calcula os indicadores
derivados e salva a base final usada pelo app: data/processed/macro_indicadores.csv

As funções deste módulo também são usadas pelo app.py (Streamlit) sobre os dados filtrados.

Uso (na raiz do projeto):
    python -m src.indicadores
"""

import pandas as pd

from src.config import ARQUIVO_BASE, ARQUIVO_INDICADORES

# Colunas numéricas analisadas na matriz de correlação (nome técnico -> rótulo amigável)
VARIAVEIS_CORRELACAO = {
    "selic_meta": "Selic Meta",
    "ipca_12m": "IPCA 12M",
    "juro_real_ex_post": "Juro Real Ex-Post",
    "dolar_ptax": "Dólar PTAX",
    "ibc_br": "IBC-Br",
}


def juro_real_ex_post(selic: pd.Series, ipca_12m: pd.Series) -> pd.Series:
    """Juro real ex-post pela equação de Fisher: ((1 + Selic) / (1 + IPCA 12M) − 1) × 100."""
    return ((1 + selic / 100) / (1 + ipca_12m / 100) - 1) * 100


def classificar_ciclo(variacao_selic: pd.Series) -> pd.Series:
    """Classifica cada mês conforme a decisão de política monetária refletida na meta."""
    ciclo = pd.Series("Estável", index=variacao_selic.index)
    ciclo[variacao_selic > 0] = "Alta"
    ciclo[variacao_selic < 0] = "Corte"
    return ciclo


def adicionar_indicadores(base: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta à base mensal as colunas derivadas usadas nos KPIs e gráficos."""
    df = base.sort_values("data").copy()

    df["juro_real_ex_post"] = juro_real_ex_post(df["selic_meta"], df["ipca_12m"]).round(2)

    media_dolar = df["dolar_ptax"].mean()
    df["dolar_media_periodo"] = round(media_dolar, 4)
    df["dolar_acima_media"] = df["dolar_ptax"] > media_dolar

    df["dolar_var_12m"] = (df["dolar_ptax"].pct_change(12) * 100).round(2)
    df["ibc_br_var_12m"] = (df["ibc_br"].pct_change(12) * 100).round(2)

    variacao_selic = df["selic_meta"].diff().fillna(0)
    df["selic_variacao_pp"] = variacao_selic.round(2)
    df["ciclo_monetario"] = classificar_ciclo(variacao_selic)
    return df


def matriz_correlacao(df: pd.DataFrame, colunas: dict = VARIAVEIS_CORRELACAO) -> pd.DataFrame:
    """Matriz de correlação linear de Pearson entre as variáveis, com rótulos amigáveis."""
    return df[list(colunas)].corr(method="pearson").rename(index=colunas, columns=colunas).round(2)


def pares_mais_correlacionados(matriz: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Lista os pares de variáveis com maior correlação em módulo (sem repetir pares)."""
    pares = []
    nomes = list(matriz.columns)
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            pares.append({"variavel_1": a, "variavel_2": b, "correlacao": matriz.loc[a, b]})
    resultado = pd.DataFrame(pares)
    resultado["intensidade"] = resultado["correlacao"].abs()
    return resultado.sort_values("intensidade", ascending=False).head(n).drop(columns="intensidade")


def correlacao_defasada(df: pd.DataFrame, origem: str, destino: str, defasagens=range(0, 13)) -> pd.DataFrame:
    """Correlação entre `origem` hoje e `destino` k meses depois (k = defasagem em meses).

    Usada para investigar se choques cambiais antecedem movimentos da inflação.
    Correlação não implica causalidade: o resultado é apenas descritivo.
    """
    linhas = []
    for k in defasagens:
        corr = df[origem].corr(df[destino].shift(-k))
        linhas.append({"defasagem_meses": k, "correlacao": round(corr, 2)})
    return pd.DataFrame(linhas)


def executar() -> pd.DataFrame:
    base = pd.read_csv(ARQUIVO_BASE, parse_dates=["data"], encoding="utf-8")
    final = adicionar_indicadores(base)
    final.to_csv(ARQUIVO_INDICADORES, index=False, encoding="utf-8", date_format="%Y-%m-%d")
    print(f"Base com indicadores salva em {ARQUIVO_INDICADORES.relative_to(ARQUIVO_INDICADORES.parents[2])}")
    return final


if __name__ == "__main__":
    executar()
