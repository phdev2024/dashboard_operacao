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
    PASTA_STATUS_SAIDA
)
from src.back.data_loader import carregar_dados_status_saida as carregar_dados_saida
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

# Carrega a base operacional rápida (mês atual) e a fila de coletas pendentes
df_operacao = carregar_dados_saida()
df_coletas = carregar_coletas_pendentes()

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

    st.markdown("---")
    
    # --- ÁREA DE UPLOAD OPERACIONAL ---
    with st.expander("📤 Atualizar Dados Operacionais", expanded=False):
        st.caption("Envie o relatório do mês atual (.xlsx)")
        arquivo_enviado = st.file_uploader(
            "Selecione a planilha",
            type=["xlsx"],
            accept_multiple_files=False,
            label_visibility="collapsed"
        )
        
        if arquivo_enviado is not None:
            if st.button("💾 Salvar e Atualizar TV", use_container_width=True):
                PASTA_OPERACIONAL_SAIDA.mkdir(parents=True, exist_ok=True)
                
                for arquivo_antigo in PASTA_OPERACIONAL_SAIDA.glob("*.*"):
                    try:
                        arquivo_antigo.unlink()
                    except Exception:
                        pass

                caminho_destino = PASTA_OPERACIONAL_SAIDA / arquivo_enviado.name
                with open(caminho_destino, "wb") as f:
                    f.write(arquivo_enviado.getbuffer())
                
                st.cache_data.clear()
                st.success(f"Base operacional atualizada com '{arquivo_enviado.name}'!")
                time.sleep(1)
                st.rerun()

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