"""Etapa 2 do ETL – Limpeza, tratamento e consolidação mensal das séries do SGS.

Lê os arquivos brutos de data/raw/, trata tipos, datas, nulos e duplicados,
padroniza todas as séries na periodicidade mensal e une tudo em uma base única:
data/processed/macro_mensal.csv

Regras de padronização mensal:
- selic_meta (diária): meta vigente no último dia do mês
- dolar_ptax (dias úteis): média mensal das cotações de venda
- ipca_mensal, ipca_12m e ibc_br (mensais): mantidas como publicadas

Uso (na raiz do projeto):
    python -m src.limpeza
"""

import pandas as pd

from src.config import ARQUIVO_BASE, PASTA_BRUTOS, SERIES_SGS

# Como cada série diária vira mensal
AGREGACAO_MENSAL = {
    "selic_meta": "last",
    "dolar_ptax": "mean",
}


def ler_serie_bruta(codigo: int) -> pd.DataFrame:
    """Lê um arquivo bruto com encoding explícito e mantém tudo como texto para tratar depois."""
    caminho = PASTA_BRUTOS / f"sgs_{codigo}.csv"
    return pd.read_csv(caminho, dtype=str, encoding="utf-8")


def tratar_serie(bruto: pd.DataFrame, nome: str) -> pd.DataFrame:
    """Converte datas e valores, remove nulos e duplicados e devolve a série ordenada por data."""
    df = bruto.copy()
    df.columns = [coluna.strip().lower() for coluna in df.columns]

    # Datas no padrão brasileiro dd/mm/aaaa -> datetime
    df["data"] = pd.to_datetime(df["data"].str.strip(), format="%d/%m/%Y", errors="coerce")

    # Valores: remove espaços, troca vírgula decimal por ponto e converte para float
    df["valor"] = pd.to_numeric(
        df["valor"].str.strip().str.replace(",", ".", regex=False), errors="coerce"
    )

    linhas_antes = len(df)
    nulos = int(df[["data", "valor"]].isna().any(axis=1).sum())
    df = df.dropna(subset=["data", "valor"])

    duplicados = int(df.duplicated(subset="data").sum())
    df = df.drop_duplicates(subset="data", keep="last")

    df = df.sort_values("data").rename(columns={"valor": nome}).reset_index(drop=True)
    print(
        f"  {nome:<12} {linhas_antes:>5} registros | nulos removidos: {nulos} | "
        f"duplicados removidos: {duplicados}"
    )
    return df[["data", nome]]


def para_mensal(serie: pd.DataFrame, nome: str) -> pd.DataFrame:
    """Padroniza a série para um registro por mês, com a data no primeiro dia do mês."""
    regra = AGREGACAO_MENSAL.get(nome, "last")
    mensal = serie.set_index("data")[nome].resample("MS").agg(regra)
    return mensal.to_frame().reset_index()


def consolidar() -> pd.DataFrame:
    """Executa a limpeza de todas as séries e devolve a base mensal consolidada."""
    print("Tratando séries brutas:")
    base = None
    for codigo, nome in SERIES_SGS.items():
        serie = tratar_serie(ler_serie_bruta(codigo), nome)
        mensal = para_mensal(serie, nome)
        base = mensal if base is None else base.merge(mensal, on="data", how="outer")

    base = base.sort_values("data").reset_index(drop=True)
    base.insert(1, "ano", base["data"].dt.year.astype(int))
    base.insert(2, "mes", base["data"].dt.month.astype(int))
    base["dolar_ptax"] = base["dolar_ptax"].round(4)
    return base


def validar(base: pd.DataFrame) -> None:
    """Checagens de qualidade da base final."""
    meses_esperados = pd.date_range("2019-01-01", "2023-12-01", freq="MS")
    assert len(base) == len(meses_esperados), f"Esperado {len(meses_esperados)} meses, veio {len(base)}"
    assert base["data"].tolist() == list(meses_esperados), "Há meses faltando ou fora de ordem"
    assert not base.isna().any().any(), "A base final tem valores nulos"
    assert not base["data"].duplicated().any(), "A base final tem meses duplicados"
    print(f"Validação OK: {len(base)} meses (jan/2019 a dez/2023), sem nulos e sem duplicados.")


def executar() -> pd.DataFrame:
    base = consolidar()
    validar(base)
    ARQUIVO_BASE.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(ARQUIVO_BASE, index=False, encoding="utf-8", date_format="%Y-%m-%d")
    print(f"Base salva em {ARQUIVO_BASE.relative_to(ARQUIVO_BASE.parents[2])}")
    return base


if __name__ == "__main__":
    executar()
