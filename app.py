"""
Ponto de Entrada Principal (Main Application)
Painel Operacional Logcare com Suporte a Carrossel de TV, Coletas, Upload Inteligente e Mapa de Hubs
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
from src.back.bases_hubs import processar_base_hubs

from src.front.views_saida import exibir_visao_saida
from src.front.views_volumes import exibir_visao_volumes
from src.front.views_coletas import exibir_visao_coletas
from src.front.views_sla import exibir_visao_sla
from src.front.views_mapa import exibir_visao_mapa

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
    
    # 1. Ponto de Inclusão: Mapeamento amigável para o seletor manual
    opcoes_telas = {
        "Notas": "Notas Recebidas",
        "Volumes": "Volumes & Clientes",
        "SLA": "Radar de SLA & Alertas",
        "Coletas": "Programação de Coletas",
        "Mapa": "Malha de Hubs & Bases"
    }
    opcoes_invertidas = {v: k for k, v in opcoes_telas.items()}

    escolha_manual = st.radio(
        "Selecione a Visão:",
        list(opcoes_telas.values()),
        index=list(opcoes_telas.keys()).index(st.session_state.tela_ativa)
    )
    
    if not st.session_state.modo_tv:
        st.session_state.tela_ativa = opcoes_invertidas[escolha_manual]

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

# --- CARREGAMENTO DOS DADOS ---
if arquivo_enviado is not None:
    df_operacao = ler_arquivo_upload(arquivo_enviado)
else:
    assinatura_atual = obter_timestamp_pasta(PASTA_OPERACIONAL_SAIDA)
    df_operacao = carregar_dados_saida(assinatura_pasta=assinatura_atual)

with st.spinner("Sincronizando fila de coletas..."):
    df_coletas = carregar_coletas_pendentes()

# Cache dos dados do mapa para não consultar geocodificação a cada troca de tela
@st.cache_data
def carregar_dados_mapa():
    return processar_base_hubs()

df_mapa = carregar_dados_mapa()

# --- 2. Ponto de Inclusão: RENDERIZAÇÃO DA TELA SELECIONADA ---
if st.session_state.tela_ativa == "Notas":
    exibir_visao_saida(df_operacao)
elif st.session_state.tela_ativa == "Volumes":
    exibir_visao_volumes(df_operacao)
elif st.session_state.tela_ativa == "SLA":
    exibir_visao_sla(df_operacao)
elif st.session_state.tela_ativa == "Coletas":
    exibir_visao_coletas(df_coletas)
elif st.session_state.tela_ativa == "Mapa":
    exibir_visao_mapa(df_mapa)

# --- 3. Ponto de Inclusão: MECANISMO DO CARROSSEL AUTOMÁTICO (ROTAÇÃO CIRCULAR) ---
if st.session_state.modo_tv:
    time.sleep(tempo_troca)
    
    # Ordem: Notas -> Volumes -> SLA -> Coletas -> Mapa -> Notas
    proxima_tela = {
        "Notas": "Volumes",
        "Volumes": "SLA",
        "SLA": "Coletas",
        "Coletas": "Mapa",
        "Mapa": "Notas"
    }
    st.session_state.tela_ativa = proxima_tela.get(st.session_state.tela_ativa, "Notas")
    st.rerun()