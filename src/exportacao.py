"""Exportação da base filtrada em CSV (botão de download do Data App).

Formato pensado para abrir direto no Excel em português:
- separador ";" e vírgula como separador decimal;
- encoding UTF-8 com BOM ("utf-8-sig"), para os acentos aparecerem corretamente;
- datas no formato dd/mm/aaaa.
"""

import pandas as pd


def nome_arquivo(filtrados: pd.DataFrame) -> str:
    """Ex.: dados_macro_filtrados_2019-01_a_2023-12.csv"""
    inicio, fim = filtrados["data"].min(), filtrados["data"].max()
    return f"dados_macro_filtrados_{inicio:%Y-%m}_a_{fim:%Y-%m}.csv"


def gerar_csv(filtrados: pd.DataFrame) -> bytes:
    """Converte a base filtrada (todas as colunas do dicionário de dados) em CSV."""
    base = filtrados.sort_values("data").copy()
    base["dolar_acima_media"] = base["dolar_acima_media"].map({True: "Sim", False: "Não"})
    return base.to_csv(
        index=False,
        sep=";",
        decimal=",",
        date_format="%d/%m/%Y",
    ).encode("utf-8-sig")  # o BOM do UTF-8 faz o Excel reconhecer os acentos
