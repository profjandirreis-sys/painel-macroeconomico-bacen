"""Executa o pipeline de dados completo: extração → limpeza → indicadores.

Uso (na raiz do projeto):
    python -m src.pipeline             # roda tudo, inclusive o download da API
    python -m src.pipeline --sem-api   # reaproveita os arquivos já salvos em data/raw/
"""

import sys

from src import extracao, indicadores, limpeza


def main(baixar: bool = True) -> None:
    if baixar:
        print("== 1/3 Extração ==")
        extracao.extrair_todas()
    print("== 2/3 Limpeza e consolidação ==")
    limpeza.executar()
    print("== 3/3 Indicadores derivados ==")
    indicadores.executar()
    print("Pipeline concluído.")


if __name__ == "__main__":
    main(baixar="--sem-api" not in sys.argv)
