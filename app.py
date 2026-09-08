"""
Ponto de Entrada Principal (Main Application)
Painel Operacional Logcare com Suporte a Carrossel de TV, Coletas e Upload Inteligente
"""

import streamlit as st
import time
from pathlib import Path

from src.config.settings import (
    APP_TITLE,
    BRAND_NAME,
    PASTA_OPERACIONAL_SAIDA,
    PASTA_STATUS_SAIDA,
)
from src.back.data_loader import (
    carregar_dados_status_saida as carregar_dados_saida, 
    obter_timestamp_pasta, 
    ler_arquivo_upload
)
from src.back.coletas import carregar_coletas_pendentes
from src.front.views_saida import exibir_visao_saida
from src.front.views_volumes import exibir_visao_volumes
from src.front.views_coletas import exibir_visao_coletas

# Configuração da página
st.set_page_config(
    page_title=f"{BRAND_NAME} - {APP_TITLE}",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o estado da tela no session_state
if "tela_ativa" not in st.session_state:
    st.session_state.tela_ativa = "Notas"

if "modo_tv" not in st.session_state:
    st.session_state.modo_tv = False

# --- BARRA LATERAL: CONTROLES DE NAVEGAÇÃO & UPLOAD ---
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    st.session_state.modo_tv = st.toggle("Modo Carrossel TV (Auto-Troca)", value=st.session_state.modo_tv)
    
    tempo_troca = st.slider("Tempo de transição (segundos)", min_value=10, max_value=120, value=30, step=5)
    
    st.markdown("---")
    
    # Mapeamento amigável para o seletor manual
    opcoes_telas = {
        "Notas": "Notas Recebidas",
        "Volumes": "Volumes & Clientes",
        "Coletas": "Programação de Coletas"
    }
    opcoes_invertidas = {v: k for k, v in opcoes_telas.items()}

    escolha_manual = st.radio(
        "Selecione a Visão:",
        list(opcoes_telas.values()),
        index=list(opcoes_telas.keys()).index(st.session_state.tela_ativa)
    )
    
    # Se o modo TV estiver desligado, obedece à escolha manual do operador
    if not st.session_state.modo_tv:
        st.session_state.tela_ativa = opcoes_invertidas[escolha_manual]

    # --- ÁREA DE UPLOAD OPERACIONAL NA BARRA LATERAL ---
    st.markdown("---")
    st.subheader("📤 Atualização Operacional")
    
    arquivo_enviado = st.file_uploader(
        "Carregar novo relatório (.xlsx):", 
        type=["xlsx", "xls", "csv"],
        help="Envie a planilha para atualizar os painéis imediatamente nesta sessão."
    )

    if st.button("🔄 Atualizar Painel Agora", use_container_width=True):
        st.cache_data.clear()
        st.toast("Dados atualizados com sucesso!", icon="✅")
        time.sleep(0.3)
        st.rerun()

# --- CARREGAMENTO INTELIGENTE DOS DADOS (PRIORIDADE AO UPLOAD) ---
if arquivo_enviado is not None:
    df_operacao = ler_arquivo_upload(arquivo_enviado)
else:
    assinatura_atual = obter_timestamp_pasta(PASTA_OPERACIONAL_SAIDA)
    df_operacao = carregar_dados_saida(assinatura_pasta=assinatura_atual)

# Carrega a fila de coletas do Google Sheets com spinner de proteção
with st.spinner("Sincronizando fila de coletas..."):
    df_coletas = carregar_coletas_pendentes()

# --- RENDERIZAÇÃO DA TELA SELECIONADA ---
if st.session_state.tela_ativa == "Notas":
    exibir_visao_saida(df_operacao)
elif st.session_state.tela_ativa == "Volumes":
    exibir_visao_volumes(df_operacao)
elif st.session_state.tela_ativa == "Coletas":
    exibir_visao_coletas(df_coletas)

# --- MECANISMO DO CARROSSEL AUTOMÁTICO (ROTAÇÃO CIRCULAR) ---
if st.session_state.modo_tv:
    time.sleep(tempo_troca)
    
    # Ordem de transição da esteira: Notas -> Volumes -> Coletas -> Notas
    proxima_tela = {
        "Notas": "Volumes",
        "Volumes": "Coletas",
        "Coletas": "Notas"
    }
    st.session_state.tela_ativa = proxima_tela.get(st.session_state.tela_ativa, "Notas")
    st.rerun()