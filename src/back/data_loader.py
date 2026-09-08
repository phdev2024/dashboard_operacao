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


def obter_timestamp_pasta(pasta: Path) -> str:
    """Retorna uma assinatura única baseada no tamanho e data dos arquivos da pasta."""
    pasta_alvo = Path(pasta)
    if not pasta_alvo.exists():
        return "vazio"
    
    arquivos = [
        arq for arq in pasta_alvo.glob("*.*") 
        if not arq.name.startswith("~$") and arq.suffix.lower() in [".xlsx", ".xls", ".csv"]
    ]
    if not arquivos:
        return "vazio"
    
    # Cria uma assinatura somando o mtime e o tamanho em bytes de todos os arquivos
    # Se mudar o nome, a data ou o tamanho, a assinatura muda instantaneamente!
    assinatura = "_".join(f"{arq.name}-{arq.stat().st_mtime}-{arq.stat().st_size}" for arq in arquivos)
    return assinatura


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


@st.cache_data(ttl=300)
def carregar_dados_status_saida(assinatura_pasta: str = "", pasta_dados: Path = None) -> pd.DataFrame:
    """
    Lê a base operacional do mês atual dentro de data/status_saida/operacional/
    A assinatura_pasta garante que qualquer mudança no arquivo recarregue os dados na hora.
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

def ler_arquivo_upload(uploaded_file) -> pd.DataFrame:
    """Lê diretamente um arquivo carregado via st.file_uploader sem precisar salvar em disco."""
    try:
        nome = uploaded_file.name.lower()
        if nome.endswith(".csv"):
            df = pd.read_csv(uploaded_file, sep=None, engine="python", encoding="latin1", header=4)
        else:
            df = pd.read_excel(uploaded_file, header=4)

        if df.empty:
            return pd.DataFrame()

        df.columns = [str(c).strip() for c in df.columns]

        if "Recepção" in df.columns:
            df["Recepção"] = pd.to_datetime(df["Recepção"], errors="coerce", dayfirst=True)
            df = df.sort_values(by="Recepção", ascending=True).reset_index(drop=True)

        return df
    except Exception as e:
        st.error(f"Erro ao processar planilha enviada: {e}")
        return pd.DataFrame()