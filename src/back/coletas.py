"""
Módulo de Integração: Controle de Transporte (Google Sheets Nativo)
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
    """Consulta o Google Sheets trazendo todas as operações ativas (exceto Finalizadas)."""
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

            # 1. PERGUNTA: Quais registros NÃO devem subir para a TV?
            # RESPOSTA: O que já foi concluído/finalizado ou marcado como entregue anteriormente.
            status_excluidos = ["FINALIZADO", "ENTREGUE"]
            df["STATUS_LIMPO"] = df["STATUS"].astype(str).str.strip().str.upper()
            df_ativos = df[~df["STATUS_LIMPO"].isin(status_excluidos)].copy()

            if df_ativos.empty:
                return pd.DataFrame()

            # 2. PERGUNTA: Quais colunas a operação precisa enxergar na TV?
            # Incluímos o STATUS agora de forma visível
            colunas_vitais = [
                "STATUS", "DATA COLETA", "CLIENTE", "PEDIDO / NF", 
                "TIPO DE OPERAÇÃO", "MOTORISTA", "PLACA", "VEICULO", "REGIÃO"
            ]
            colunas_existentes = [col for col in colunas_vitais if col in df_ativos.columns]
            df_operacao = df_ativos[colunas_existentes].copy()

            # 3. REGRA DE ORDENAÇÃO MULTINÍVEL:
            # Função para dar peso de prioridade a cada status
            def mapear_ordem_status(status_txt: str) -> int:
                st_upper = str(status_txt).strip().upper()
                if "PENDENTE" in st_upper:
                    return 1
                elif "TRANSIT" in st_upper:
                    return 2
                elif "ANDAMENTO" in st_upper:
                    return 3
                return 4

            df_operacao["Ordem_Status"] = df_operacao["STATUS"].apply(mapear_ordem_status)

            # Conversão defensiva de data para ordenação cronológica
            if "DATA COLETA" in df_operacao.columns:
                df_operacao["Data_Ref"] = pd.to_datetime(
                    df_operacao["DATA COLETA"], format="%d/%m/%Y", errors="coerce"
                )
            else:
                df_operacao["Data_Ref"] = pd.NaT

            # Ordena por: 1º Status (Pendente -> Em Trânsito -> Em Andamento), 2º Data mais antiga
            df_operacao = df_operacao.sort_values(
                by=["Ordem_Status", "Data_Ref"], 
                ascending=[True, True]
            )

            # Remove colunas auxiliares para deixar a tabela visualmente limpa
            df_operacao = df_operacao.drop(columns=["Ordem_Status", "Data_Ref"])

            return df_operacao

        except Exception as e:
            time.sleep(1)
            if tentativa == 2:
                st.error(f"Erro persistente ao conectar com o Google Sheets: {e}")
                return pd.DataFrame()

    return pd.DataFrame()