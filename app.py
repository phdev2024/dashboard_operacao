"""
Ponto de Entrada Principal (Main Application)
Painel Operacional Logcare com Suporte a Carrossel de TV
"""

import streamlit as st
import time
from src.config.settings import APP_TITLE, BRAND_NAME
from src.back.data_loader import carregar_dados_status_saida as carregar_dados_saida
from src.front.views_saida import exibir_visao_saida
from src.front.views_volumes import exibir_visao_volumes

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

# Carrega a base tratada com cache
df_operacao = carregar_dados_saida()

# --- BARRA LATERAL: CONTROLES DE NAVEGAÇÃO ---
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    st.session_state.modo_tv = st.toggle("Modo Carrossel TV (Auto-Troca)", value=st.session_state.modo_tv)
    
    tempo_troca = st.slider("Tempo de transição (segundos)", min_value=10, max_value=120, value=30, step=5)
    
    st.markdown("---")
    escolha_manual = st.radio(
        "Selecione a Visão:",
        ["Notas Recebidas", "Volumes & Clientes"],
        index=0 if st.session_state.tela_ativa == "Notas" else 1
    )
    
    if not st.session_state.modo_tv:
        st.session_state.tela_ativa = "Notas" if escolha_manual == "Notas Recebidas" else "Volumes"

# --- RENDERIZAÇÃO DA TELA SELECIONADA ---
if st.session_state.tela_ativa == "Notas":
    exibir_visao_saida(df_operacao)
else:
    exibir_visao_volumes(df_operacao)

# --- MECANISMO DO CARROSSEL AUTOMÁTICO ---
if st.session_state.modo_tv:
    time.sleep(tempo_troca)
    # Alterna entre as telas
    st.session_state.tela_ativa = "Volumes" if st.session_state.tela_ativa == "Notas" else "Notas"
    st.rerun()