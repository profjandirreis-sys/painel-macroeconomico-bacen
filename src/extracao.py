"""Etapa 1 do ETL – Extração das séries do SGS (Banco Central do Brasil).

Consome a API pública oficial do Sistema Gerenciador de Séries Temporais (SGS)
e salva cada série, sem nenhuma alteração, em data/raw/sgs_<codigo>.csv.

Uso (na raiz do projeto):
    python -m src.extracao
"""

import time

import pandas as pd
import requests

from src.config import DATA_FINAL, DATA_INICIAL, PASTA_BRUTOS, SERIES_SGS, URL_SGS

PAUSA_ENTRE_REQUISICOES = 1.5  # segundos – respeita os limites da API pública
TENTATIVAS = 3


def baixar_serie(codigo: int, data_inicial: str = DATA_INICIAL, data_final: str = DATA_FINAL) -> pd.DataFrame:
    """Baixa uma série do SGS no período informado e devolve um DataFrame bruto (data, valor como texto)."""
    parametros = {"formato": "json", "dataInicial": data_inicial, "dataFinal": data_final}
    url = URL_SGS.format(codigo=codigo)

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(url, params=parametros, timeout=60)
            resposta.raise_for_status()
            dados = resposta.json()
            if not dados:
                raise ValueError(f"A série {codigo} voltou vazia.")
            return pd.DataFrame(dados)
        except (requests.RequestException, ValueError) as erro:
            print(f"  tentativa {tentativa}/{TENTATIVAS} da série {codigo} falhou: {erro}")
            time.sleep(PAUSA_ENTRE_REQUISICOES * tentativa)

    raise RuntimeError(f"Não foi possível baixar a série {codigo} do SGS.")


def extrair_todas() -> None:
    """Baixa todas as séries configuradas e salva os arquivos brutos em data/raw/."""
    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)

    for codigo, nome in SERIES_SGS.items():
        print(f"Baixando série {codigo} ({nome})...")
        bruto = baixar_serie(codigo)
        destino = PASTA_BRUTOS / f"sgs_{codigo}.csv"
        bruto.to_csv(destino, index=False, encoding="utf-8")
        print(f"  {len(bruto)} registros salvos em {destino.relative_to(PASTA_BRUTOS.parent.parent)}")
        time.sleep(PAUSA_ENTRE_REQUISICOES)


if __name__ == "__main__":
    extrair_todas()
