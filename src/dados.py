"""Carregamento resiliente dos dados do Data App.

Ordem de tentativa:
1. Banco PostgreSQL na nuvem (ex.: Supabase) via st.connection, se as credenciais
   existirem em .streamlit/secrets.toml (ou nos Secrets do Streamlit Cloud);
2. Contingência (fallback): CSV local em data/processed/macro_indicadores.csv.

Assim o app nunca "quebra" por falta de banco, senha errada ou rede fora do ar.
"""

import pandas as pd
import streamlit as st

from src.config import ARQUIVO_INDICADORES

TABELA = "macro_indicadores"
TEMPO_CACHE = 3600  # segundos (1 hora)

ORIGEM_BANCO = "Banco de dados PostgreSQL (nuvem)"
ORIGEM_CSV = "Arquivo local (contingência CSV)"


def _tem_credenciais_banco() -> bool:
    """Verifica se existe a seção [connections.postgresql] nos secrets, sem gerar erro."""
    try:
        return "postgresql" in st.secrets.get("connections", {})
    except Exception:  # secrets.toml ausente ou mal formatado
        return False


def _ler_banco() -> pd.DataFrame:
    conexao = st.connection("postgresql", type="sql")
    return conexao.query(f"SELECT * FROM {TABELA} ORDER BY data", ttl=TEMPO_CACHE)


def _ler_csv() -> pd.DataFrame:
    return pd.read_csv(ARQUIVO_INDICADORES, encoding="utf-8")


def _tratar_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """Garante os mesmos tipos do dicionário de dados, venha do banco ou do CSV."""
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    df["ano"] = df["ano"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["dolar_acima_media"] = df["dolar_acima_media"].astype(str).str.lower().isin(["true", "1", "t"])
    return df.sort_values("data").reset_index(drop=True)


@st.cache_data(ttl=TEMPO_CACHE, show_spinner="Carregando dados do Banco Central...")
def carregar_dados() -> tuple[pd.DataFrame, str, str | None]:
    """Retorna (dados tratados, origem dos dados, aviso de contingência ou None)."""
    aviso = None
    if _tem_credenciais_banco():
        try:
            return _tratar_tipos(_ler_banco()), ORIGEM_BANCO, None
        except Exception as erro:
            aviso = f"Não foi possível acessar o banco ({type(erro).__name__}). Usando o CSV local."

    return _tratar_tipos(_ler_csv()), ORIGEM_CSV, aviso
