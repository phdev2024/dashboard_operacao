"""
Módulo de Integração: Coletas Agendadas (Google Sheets Nativo)
Lê diretamente via exportação CSV leve e em tempo real.
"""

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


@st.cache_data(ttl=180)
def carregar_coletas_pendentes() -> pd.DataFrame:
    """Consulta o Google Sheets e entrega a fila operacional de coletas pendentes."""
    try:
        url_csv = montar_url_csv(LINK_COMPARTILHADO)
        
        # 1. dtype=str força a leitura de tudo como texto (evita quebrar com números mistos)
        df = pd.read_csv(url_csv, dtype=str)
        if df.empty:
            return pd.DataFrame()

        # 2. Substitui eventuais nulos/NaN por vazio para nunca exibir 'None' na TV
        df = df.fillna("")

        # 3. Padroniza colunas
        df.columns = [str(col).strip().upper() for col in df.columns]

        if "STATUS" not in df.columns:
            return pd.DataFrame()

        # 4. Filtra apenas coletas com status PENDENTE
        df_pendentes = df[df["STATUS"].astype(str).str.strip().str.upper() == "PENDENTE"].copy()
        if df_pendentes.empty:
            return pd.DataFrame()

        # 5. Colunas operacionais para a doca
        colunas_vitais = [
            "DATA COLETA", "CLIENTE", "PEDIDO / NF", 
            "TIPO DE OPERAÇÃO", "MOTORISTA", "PLACA", "VEICULO", "REGIÃO"
        ]
        colunas_existentes = [col for col in colunas_vitais if col in df_pendentes.columns]
        df_operacao = df_pendentes[colunas_existentes].copy()

        # 6. Ordenação cronológica por Data da Coleta
        if "DATA COLETA" in df_operacao.columns:
            df_operacao["Data_Ref"] = pd.to_datetime(
                df_operacao["DATA COLETA"], format="%d/%m/%Y", errors="coerce"
            )
            df_operacao = df_operacao.sort_values(by="Data_Ref", ascending=True)
            df_operacao = df_operacao.drop(columns=["Data_Ref"])

        return df_operacao

    except Exception as e:
        st.error(f"Erro ao consultar planilha de coletas: {e}")
        return pd.DataFrame()