"""
Módulo Backend: Carregamento de Dados Operacionais e Históricos
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from src.config.settings import (
    PASTA_OPERACIONAL_SAIDA,
    PASTA_HISTORICO_SAIDA,
    PASTA_STATUS_SAIDA
)


def _ler_pasta_arquivos(pasta: Path) -> pd.DataFrame:
    """Lê e consolida os arquivos Excel/CSV iniciando na linha padrão (header=4)."""
    pasta_alvo = Path(pasta)
    if not pasta_alvo.exists():
        return pd.DataFrame()

    arquivos = (
        list(pasta_alvo.glob("*.xlsx")) +
        list(pasta_alvo.glob("*.xls")) +
        list(pasta_alvo.glob("*.csv"))
    )
    arquivos = [arq for arq in arquivos if not arq.name.startswith("~$")]

    if not arquivos:
        return pd.DataFrame()

    lista_dfs = []
    for arquivo in arquivos:
        try:
            if arquivo.suffix.lower() == ".csv":
                df_temp = pd.read_csv(arquivo, sep=None, engine="python", encoding="latin1", header=4)
            else:
                # Linha 5 do Excel = índice 4 no Pandas
                df_temp = pd.read_excel(arquivo, header=4)

            if not df_temp.empty:
                lista_dfs.append(df_temp)
        except Exception:
            continue

    if not lista_dfs:
        return pd.DataFrame()

    df_consolidado = pd.concat(lista_dfs, ignore_index=True)

    # Limpeza de espaços nos nomes das colunas
    df_consolidado.columns = [str(c).strip() for c in df_consolidado.columns]

    if "Recepção" in df_consolidado.columns:
        df_consolidado["Recepção"] = pd.to_datetime(
            df_consolidado["Recepção"], errors="coerce", dayfirst=True
        )
        df_consolidado = df_consolidado.sort_values(by="Recepção", ascending=True).reset_index(drop=True)

    return df_consolidado


@st.cache_data(ttl=900)
def carregar_dados_status_saida(pasta_dados: Path = None) -> pd.DataFrame:
    """
    Lê a base operacional do mês atual dentro de data/status_saida/operacional/
    """
    if pasta_dados is not None:
        return _ler_pasta_arquivos(pasta_dados)

    if PASTA_OPERACIONAL_SAIDA.exists() and any(PASTA_OPERACIONAL_SAIDA.iterdir()):
        return _ler_pasta_arquivos(PASTA_OPERACIONAL_SAIDA)

    return _ler_pasta_arquivos(PASTA_STATUS_SAIDA)


@st.cache_data(ttl=1800)
def carregar_dados_historicos_saida() -> pd.DataFrame:
    """
    Lê todo o histórico acumulado dentro de data/status_saida/historico/
    """
    return _ler_pasta_arquivos(PASTA_HISTORICO_SAIDA)