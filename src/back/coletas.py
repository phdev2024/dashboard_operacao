"""
Módulo de Integração: Coletas Agendadas (Google Sheets Nativo)
Lê diretamente via exportação CSV leve e em tempo real.
"""

import pandas as pd
import streamlit as st
import re

# Cole aqui o link copiado da Planilha Google nativa
LINK_COMPARTILHADO = "https://docs.google.com/spreadsheets/d/1KSBf6LbG5DffwAJpsCPXp0PmExjeh4_8b6EQDneHvEQ/edit?usp=sharing"


def montar_url_csv(link: str, nome_aba: str = "Coletas") -> str:
    """
    Extrai o identificador da planilha e adiciona o parâmetro 
    da aba específica para exportação em CSV.
    """
    padrao = r"/d/([a-zA-Z0-9-_]+)"
    match = re.search(padrao, link)
    if match:
        sheet_id = match.group(1)
        # O parâmetro &sheet= garante que o Google leia a aba correta
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
    return link


@st.cache_data(ttl=300)
def carregar_coletas_pendentes() -> pd.DataFrame:
    """Consulta o Google Sheets e entrega a fila operacional de coletas pendentes."""
    try:
        url_csv = montar_url_csv(LINK_COMPARTILHADO, nome_aba="Coletas")
        
        # 1. Pergunta ao Pandas: 'Leia os dados tabulares da URL'
        df = pd.read_csv(url_csv)
        if df.empty:
            return pd.DataFrame()

        # 2. Padroniza colunas
        df.columns = [str(col).strip().upper() for col in df.columns]

        if "STATUS" not in df.columns:
            return pd.DataFrame()

        # 3. Ordem lógica: carregar apenas quem está aguardando doca
        df_pendentes = df[df["STATUS"].astype(str).str.strip().str.upper() == "PENDENTE"].copy()
        if df_pendentes.empty:
            return pd.DataFrame()

        # 4. Seleção das colunas chave para a equipe de armazém
        colunas_vitais = [
            "DATA COLETA", "CLIENTE", "PEDIDO / NF", 
            "TIPO DE OPERAÇÃO", "MOTORISTA", "PLACA", "VEICULO", "REGIÃO"
        ]
        colunas_existentes = [col for col in colunas_vitais if col in df_pendentes.columns]
        df_operacao = df_pendentes[colunas_existentes].copy()

        # 5. Ordenação cronológica por Data da Coleta
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