"""
Módulo Frontend: Visão de Atendimento - Acompanhamento de Coletas (Tela 3B)
Foco em Em Trânsito e Entregue para a equipe de atendimento.
"""

import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

from src.config.settings import (
    COLOR_BRAND_PRIMARY, COLOR_CARD_BG, COLOR_TEXT_LIGHT, 
    COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
)


def exibir_visao_atendimento(df: pd.DataFrame):
    # --- 1. CABEÇALHO ---
    caminho_logo = Path("data/media/logo_logcare.png")
    c1, c2 = st.columns([3, 8.5], vertical_alignment="center")
    
    with c1:
        if caminho_logo.exists():
            st.image(str(caminho_logo), width=140)
        else:
            st.markdown(f"<h2 style='color: {COLOR_BRAND_PRIMARY}; margin:0;'>LOGCARE</h2>", unsafe_allow_html=True)
            
    with c2:
        st.markdown(f"<h2 style='color: {COLOR_TEXT_LIGHT}; font-weight: 300; font-size: 2.2rem; margin:0;'>Painel de Atendimento - Coletas em Andamento & Entregues</h2>", unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border-color: #223834;'>", unsafe_allow_html=True)
    
    # --- VALIDAÇÃO DO DATAFRAME ---
    if df is None or df.empty:
        st.markdown(
            """
            <div style='text-align: center; padding: 60px 20px; background-color: rgba(30, 90, 40, 0.2); border: 2px dashed #2e7d32; border-radius: 10px; margin-top: 30px;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>🚛💨</div>
                <div style='color: #4CAF50; font-size: 26px; font-weight: 700; margin-bottom: 8px;'>Nenhuma Coleta em Trânsito ou Entregue</div>
                <div style='color: #aaaaaa; font-size: 16px;'>Não há registros de trânsito ou entregas no momento.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # --- 2. CÁLCULO DE MÉTRICAS DE ATENDIMENTO ---
    total_registros = len(df)
    
    # Contar por status limpo se houver
    status_col = "STATUS" if "STATUS" in df.columns else None
    em_transito = 0
    entregues = 0
    
    if status_col:
        st_upper = df[status_col].astype(str).str.strip().str.upper()
        em_transito = st_upper.str.contains("TRANSITO|TRÂNSITO|ANDAMENTO", na=False).sum()
        entregues = st_upper.str.contains("ENTREGUE", na=False).sum()

    # --- 3. LINHA DE CARDS KPI ---
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
            <div style='background-color: #162421; border: 1px solid #223834; border-radius: 10px; padding: 12px; text-align: center;'>
                <div style='color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 500; margin-bottom: 4px;'>Total Acompanhamento</div>
                <div style='color: {COLOR_BRAND_PRIMARY}; font-size: 32px; font-weight: 700;'>{total_registros}</div>
            </div>
            """, unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div style='background-color: #162421; border: 1px solid #223834; border-radius: 10px; padding: 12px; text-align: center;'>
                <div style='color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 500; margin-bottom: 4px;'>Em Trânsito / Andamento</div>
                <div style='color: {COLOR_WARNING}; font-size: 32px; font-weight: 700;'>{em_transito}</div>
            </div>
            """, unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div style='background-color: #162421; border: 1px solid #223834; border-radius: 10px; padding: 12px; text-align: center;'>
                <div style='color: {COLOR_TEXT_MUTED}; font-size: 14px; font-weight: 500; margin-bottom: 4px;'>Entregues</div>
                <div style='color: {COLOR_SUCCESS}; font-size: 32px; font-weight: 700;'>{entregues}</div>
            </div>
            """, unsafe_allow_html=True
        )

    st.write("")

    # --- 4. TABELA DE ACOMPANHAMENTO ---
    st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>📋 Histórico e Acompanhamento de Transporte</h4>", unsafe_allow_html=True)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=450
    )