"""
Módulo de Integração: Controle de Transporte (Google Sheets Nativo)
Lê diretamente via exportação CSV leve e em tempo real com retry defensivo.
Com separação entre Operacional (Pendentes) e Atendimento (Em Trânsito / Entregue).
"""

import time
import re
from urllib.parse import quote_plus
import pandas as pd
import streamlit as st

LINK_COMPARTILHADO = "https://docs.google.com/spreadsheets/d/1CSxm8VLmnpYJb32nqIehYbxaLJyJAvro8mCEsHj-_TY/edit"


def montar_url_csv(link: str, nome_aba: str = "COLETAS E ENTREGAS") -> str:
    """Extrai o identificador da planilha e codifica o nome da aba para a URL."""
    padrao = r"/d/([a-zA-Z0-9-_]+)"
    match = re.search(padrao, link)
    if match:
        sheet_id = match.group(1)
        aba_codificada = quote_plus(nome_aba)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={aba_codificada}"
    return link


def mapear_ordem_status(status_txt: str) -> int:
    """Função para dar peso de prioridade a cada status."""
    st_upper = str(status_txt).strip().upper()
    if "PENDENTE" in st_upper:
        return 1
    elif "EM ANDAMENTO" in st_upper or "EM TRÂNSITO" in st_upper or "EM TRANSITO" in st_upper:
        return 2
    elif "ENTREGUE" in st_upper:
        return 3
    else:
        return 4


@st.cache_data(ttl=180)
def carregar_coletas_pendentes() -> pd.DataFrame:
    """Consulta o Google Sheets trazendo APENAS as coletas com status PENDENTE para o operacional."""
    url_csv = montar_url_csv(LINK_COMPARTILHADO)

    for tentativa in range(3):
        try:
            df = pd.read_csv(url_csv, dtype=str)
            if df.empty:
                return pd.DataFrame()

            df = df.fillna("")
            df.columns = [str(col).strip().upper() for col in df.columns]

            if "STATUS" not in df.columns:
                return pd.DataFrame()

            # Filtrar estritamente PENDENTE (com saneamento de espaço e maiúscula)
            df["STATUS_LIMPO"] = df["STATUS"].astype(str).str.strip().str.upper()
            df_pendentes = df[df["STATUS_LIMPO"].str.contains("PENDENTE", na=False)].copy()

            if df_pendentes.empty:
                return pd.DataFrame()

            colunas_vitais = [
                "ORDEM COLETA", "STATUS", "DATA COLETA", "CLIENTE", 
                "PEDIDO / NF", "TIPO DE OPERAÇÃO", "MOTORISTA", "PLACA", "VEICULO", "REGIÃO"
            ]
            colunas_existentes = [col for col in colunas_vitais if col in df_pendentes.columns]
            df_operacao = df_pendentes[colunas_existentes].copy()

            # Ordenação por Ordem de Coleta e Data
            ordem_colunas = []
            if "ORDEM COLETA" in df_operacao.columns:
                df_operacao["_ORDEM_NUM"] = pd.to_numeric(df_operacao["ORDEM COLETA"], errors='coerce').fillna(999)
                ordem_colunas.append("_ORDEM_NUM")
            
            if "DATA COLETA" in df_operacao.columns:
                df_operacao["_DATA_DT"] = pd.to_datetime(df_operacao["DATA COLETA"], format="%d/%m/%Y", errors="coerce")
                ordem_colunas.append("_DATA_DT")

            if ordem_colunas:
                df_operacao = df_operacao.sort_values(by=ordem_colunas, ascending=[True, True]).reset_index(drop=True)

            # Remover colunas auxiliares
            df_operacao = df_operacao.drop(columns=["_ORDEM_NUM", "_DATA_DT"], errors="ignore")
            return df_operacao

        except Exception as e:
            time.sleep(1)
            continue

    return pd.DataFrame()


@st.cache_data(ttl=180)
def carregar_coletas_atendimento() -> pd.DataFrame:
    """Consulta o Google Sheets trazendo coletas EM TRÂNSITO e ENTREGUE para a equipe de atendimento."""
    url_csv = montar_url_csv(LINK_COMPARTILHADO)

    for tentativa in range(3):
        try:
            df = pd.read_csv(url_csv, dtype=str)
            if df.empty:
                return pd.DataFrame()

            df = df.fillna("")
            df.columns = [str(col).strip().upper() for col in df.columns]

            if "STATUS" not in df.columns:
                return pd.DataFrame()

            # Filtrar o que NÃO é pendente e NÃO é finalizado (foco em Em Trânsito e Entregue)
            df["STATUS_LIMPO"] = df["STATUS"].astype(str).str.strip().str.upper()
            status_atendimento = ["EM TRANSITO", "EM TRÂNSITO", "ENTREGUE", "EM ANDAMENTO"]
            df_atendimento = df[df["STATUS_LIMPO"].isin(status_atendimento)].copy()

            if df_atendimento.empty:
                return pd.DataFrame()

            colunas_vitais = [
                "ORDEM COLETA", "STATUS", "DATA COLETA", "CLIENTE", 
                "PEDIDO / NF", "TIPO DE OPERAÇÃO", "MOTORISTA", "PLACA", "VEICULO", "REGIÃO"
            ]
            colunas_existentes = [col for col in colunas_vitais if col in df_atendimento.columns]
            df_resultado = df_atendimento[colunas_existentes].copy()

            return df_resultado

        except Exception as e:
            time.sleep(1)
            continue

    return pd.DataFrame()