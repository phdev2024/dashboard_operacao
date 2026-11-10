"""
Módulo de Integração: Controle de Transporte (Google Sheets Nativo)
Lê diretamente via exportação CSV leve e em tempo real com retry defensivo.
Com funcionalidade de Ordem de Coleta
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
        return 1  # Primeira prioridade
    elif "EM ANDAMENTO" in st_upper or "EM TRÂNSITO" in st_upper:
        return 2  # Segunda prioridade
    else:
        return 3  # Terceira prioridade (outros)


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
                "ORDEM COLETA",  # ← NOVA COLUNA - ordem numérica do usuário
                "STATUS", 
                "DATA COLETA", 
                "CLIENTE", 
                "PEDIDO / NF", 
                "TIPO DE OPERAÇÃO", 
                "MOTORISTA", 
                "PLACA", 
                "VEICULO", 
                "REGIÃO"
            ]
            colunas_existentes = [col for col in colunas_vitais if col in df_ativos.columns]
            df_operacao = df_ativos[colunas_existentes].copy()

            # 3. REGRA DE ORDENAÇÃO MULTINÍVEL NOVA:
            # --- INICIALIZAR LISTA DE CRITÉRIOS DE ORDENAÇÃO ---
            ordem_colunas = []
            
            # 3.1. PRIMEIRO CRITÉRIO: ORDEM COLETA (se existir e estiver preenchida)
            if "ORDEM COLETA" in df_operacao.columns:
                # Criar coluna numérica para ordenação
                df_operacao["_ORDEM_NUM"] = pd.to_numeric(
                    df_operacao["ORDEM COLETA"], 
                    errors='coerce'
                ).fillna(999)  # Colocar valores inválidos/nulos no final (999)
                ordem_colunas.append("_ORDEM_NUM")
            
            # 3.2. SEGUNDO CRITÉRIO: Status (mantém a prioridade original)
            if "STATUS" in df_operacao.columns:
                df_operacao["_PESO_STATUS"] = df_operacao["STATUS"].apply(mapear_ordem_status)
                ordem_colunas.append("_PESO_STATUS")
            
            # 3.3. TERCEIRO CRITÉRIO: Data de Coleta
            if "DATA COLETA" in df_operacao.columns:
                # Converter para datetime para ordenação cronológica correta
                df_operacao["_DATA_DT"] = pd.to_datetime(
                    df_operacao["DATA COLETA"], 
                    format="%d/%m/%Y", 
                    errors="coerce"
                )
                ordem_colunas.append("_DATA_DT")
            
            # APLICAR ORDENAÇÃO SE HOUVER CRITÉRIOS
            if ordem_colunas:
                df_operacao = df_operacao.sort_values(
                    by=ordem_colunas, 
                    ascending=[True, True, True]  # Ordem crescente para todos
                ).reset_index(drop=True)
            
            # REMOVER COLUNAS AUXILIARES
            colunas_aux_remover = [
                "_ORDEM_NUM", "_PESO_STATUS", "_DATA_DT", 
                "STATUS_LIMPO"
            ]
            df_operacao = df_operacao.drop(
                columns=[col for col in colunas_aux_remover if col in df_operacao.columns], 
                errors="ignore"
            )

            return df_operacao

        except Exception as e:
            print(f"Erro na tentativa {tentativa}: {e}")
            time.sleep(1)
            continue

    return pd.DataFrame()