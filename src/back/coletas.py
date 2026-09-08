"""
Módulo de Integração: Coletas Agendadas (Google Sheets Nativo)
Lê diretamente via exportação CSV leve e em tempo real com retry defensivo.
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


@st.cache_data(ttl=180)
def carregar_coletas_pendentes() -> pd.DataFrame:
    """Consulta o Google Sheets com até 3 tentativas para contornar oscilações de rede."""
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

            df_pendentes = df[df["STATUS"].astype(str).str.strip().str.upper() == "PENDENTE"].copy()
            if df_pendentes.empty:
                return pd.DataFrame()

            colunas_vitais = [
                "DATA COLETA", "CLIENTE", "PEDIDO / NF", 
                "TIPO DE OPERAÇÃO", "MOTORISTA", "PLACA", "VEICULO", "REGIÃO"
            ]
            colunas_existentes = [col for col in colunas_vitais if col in df_pendentes.columns]
            df_operacao = df_pendentes[colunas_existentes].copy()

            if "DATA COLETA" in df_operacao.columns:
                df_operacao["Data_Ref"] = pd.to_datetime(
                    df_operacao["DATA COLETA"], format="%d/%m/%Y", errors="coerce"
                )
                df_operacao = df_operacao.sort_values(by="Data_Ref", ascending=True)
                df_operacao = df_operacao.drop(columns=["Data_Ref"])

            return df_operacao

        except Exception as e:
            time.sleep(1)
            if tentativa == 2:
                st.error(f"Erro persistente ao conectar com o Google Sheets: {e}")
                return pd.DataFrame()

    return pd.DataFrame()