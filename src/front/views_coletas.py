"""
Módulo Frontend: Visão Operacional de Coletas e Transportes (Tela 3)
"""

import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

from src.config.settings import (
    COLOR_BRAND_PRIMARY, COLOR_CARD_BG, COLOR_TEXT_LIGHT, 
    COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
)


def renderizar_css_tv():
    st.markdown(
        f"""
        <style>
            .block-container {{
                padding-top: 3.5rem !important;
                padding-bottom: 1rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }}
            .stApp {{
                opacity: 1 !important;
            }}
            .kpi-card {{
                background-color: #162421;
                border: 1px solid #223834;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
            }}
            .kpi-title {{
                color: #8DAA9D;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 4px;
            }}
            .kpi-value {{
                font-size: 2.2rem;
                font-weight: 800;
                line-height: 1.1;
            }}
            .header-title {{
                color: #FFFFFF;
                font-size: 1.8rem;
                font-weight: 800;
                margin: 0;
            }}
            .doca-livre-box {{
                background: linear-gradient(145deg, #10261f, #16362c);
                border: 2px solid #2bb673;
                border-radius: 16px;
                padding: 45px 25px;
                text-align: center;
                margin-top: 30px;
                box-shadow: 0px 8px 24px rgba(0, 0, 0, 0.4);
            }}
            .doca-livre-icone {{
                font-size: 4.5rem;
                line-height: 1;
                margin-bottom: 15px;
            }}
            .doca-livre-titulo {{
                color: #FFFFFF;
                font-size: 2.4rem;
                font-weight: 800;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }}
            .doca-livre-sub {{
                color: #8DAA9D;
                font-size: 1.2rem;
                font-weight: 500;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


def exibir_visao_coletas(df: pd.DataFrame):
    renderizar_css_tv()

    # --- 1. CABEÇALHO ---
    caminho_logo = Path("data/media/logo_logcare.png")
    c1, c2 = st.columns([3, 8.5], vertical_alignment="center")
    
    with c1:
        if caminho_logo.exists():
            st.image(str(caminho_logo), width=140)
        else:
            st.markdown(f"<h2 style='color: {COLOR_BRAND_PRIMARY}; margin:0;'>LOGCARE</h2>", unsafe_allow_html=True)
            
    with c2:
        st.markdown("<h2 class='header-title' style='padding-left: 15px;'>Painel Operacional - Programação de Coletas</h2>", unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border-color: #223834;'>", unsafe_allow_html=True)

    # --- 2. QUANDO NÃO HÁ COLETAS PENDENTES (DOCA LIVRE) ---
    if df.empty:
        st.markdown(
            """
            <div class='doca-livre-box'>
                <div class='doca-livre-icone'>🟢 🚛</div>
                <div class='doca-livre-titulo'>DOCAS LIVRES</div>
                <div class='doca-livre-sub'>Nenhuma coleta pendente no momento. Pátio e expedição liberados!</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # --- 3. CÁLCULO DE MÉTRICAS OPERACIONAIS ---
    total_pendentes = len(df)
    hoje = date.today()
    coletas_hoje = 0
    coletas_futuras = 0

    if "DATA COLETA" in df.columns:
        datas_convertidas = pd.to_datetime(df["DATA COLETA"], format="%d/%m/%Y", errors="coerce").dt.date
        coletas_hoje = int((datas_convertidas == hoje).sum())
        coletas_futuras = int((datas_convertidas > hoje).sum())

    veiculos_unicos = df["PLACA"].nunique() if "PLACA" in df.columns else total_pendentes

    # --- 4. LINHA DE CARDS KPI ---
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Total Pendentes</div>
                <div class='kpi-value' style='color: {COLOR_BRAND_PRIMARY};'>{total_pendentes}</div>
            </div>
            """, unsafe_allow_html=True
        )

    with c2:
        cor_hoje = COLOR_DANGER if coletas_hoje > 0 else COLOR_SUCCESS
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Programadas para Hoje</div>
                <div class='kpi-value' style='color: {cor_hoje};'>{coletas_hoje}</div>
            </div>
            """, unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Próximos Dias</div>
                <div class='kpi-value' style='color: {COLOR_WARNING};'>{coletas_futuras}</div>
            </div>
            """, unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Veículos / Placas</div>
                <div class='kpi-value' style='color: {COLOR_TEXT_LIGHT};'>{veiculos_unicos}</div>
            </div>
            """, unsafe_allow_html=True
        )

    st.write("")

    # --- 5. LISTAGEM OPERACIONAL DE COLETAS ---
    st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>🚛 Fila de Coletas Programadas</h4>", unsafe_allow_html=True)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=420
    )