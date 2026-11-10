"""
Módulo Frontend: Visão Operacional de Coletas e Transportes (Tela 3)
Com funcionalidade de Ordem de Coleta
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
                min-height: 90px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }}
            .kpi-title {{
                color: {COLOR_TEXT_MUTED};
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 4px;
            }}
            .kpi-value {{
                color: {COLOR_BRAND_PRIMARY};
                font-size: 32px;
                font-weight: 700;
                letter-spacing: -0.5px;
            }}
            .header-title {{
                color: {COLOR_TEXT_LIGHT};
                font-weight: 300;
                font-size: 2.2rem;
                letter-spacing: -0.5px;
            }}
            .doca-livre-box {{
                text-align: center;
                padding: 60px 20px;
                background-color: rgba(30, 90, 40, 0.2);
                border: 2px dashed #2e7d32;
                border-radius: 10px;
                margin-top: 30px;
            }}
            .doca-livre-icone {{
                font-size: 48px;
                margin-bottom: 10px;
            }}
            .doca-livre-titulo {{
                color: #4CAF50;
                font-size: 26px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .doca-livre-sub {{
                color: #aaaaaa;
                font-size: 16px;
            }}
            .ordem-coleta-badge {{
                background-color: {COLOR_BRAND_PRIMARY};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 13px;
                display: inline-block;
                min-width: 30px;
                text-align: center;
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
        st.markdown("<h2 class='header-title' style='padding-left: 15px;'>Painel Operacional - Controle de Transporte</h2>", unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border-color: #223834;'>", unsafe_allow_html=True)
    
    # --- VALIDAÇÃO DO DATAFRAME ---
    if df is None or df.empty:
        st.markdown(
            """
            <div class='doca-livre-box'>
                <div class='doca-livre-icone'>🟢 🚛</div>
                <div class='doca-livre-titulo'>Todos os Transportes Finalizados</div>
                <div class='doca-livre-sub'>Nenhuma coleta ou transporte em andamento no momento.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return  # ← ESTE return está correto, fecha a função se não há dados

    # --- 2. CÁLCULO DE MÉTRICAS OPERACIONAIS ---
    total_pendentes = len(df)
    hoje = date.today()
    coletas_hoje = 0
    coletas_futuras = 0

    # Cálculo de coletas programadas para hoje
    if "DATA COLETA" in df.columns:
        try:
            # Converter datas (pode conter NaT para valores inválidos)
            datas_convertidas = pd.to_datetime(df["DATA COLETA"], format="%d/%m/%Y", errors="coerce")
            
            # Remover datas inválidas antes de comparar
            datas_validas = datas_convertidas.dropna()
            
            # Contar as de hoje e as futuras
            coletas_hoje = (datas_validas.dt.date == hoje).sum()
            coletas_futuras = (datas_validas.dt.date > hoje).sum()
        except Exception:
            coletas_hoje = 0
            coletas_futuras = 0

    veiculos_unicos = df["PLACA"].nunique() if "PLACA" in df.columns else total_pendentes

    # --- 3. LINHA DE CARDS KPI ---
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

    st.write("")  # Espaço vazio para separação

    # --- 4. TRATAMENTO DA ORDEM DE COLETA ---
    def formatar_ordem(valor):
        """Converte números em formato de ordem: 1 -> '1º', 2 -> '2º', etc."""
        if pd.isna(valor) or valor == "" or str(valor).strip() == "":
            return ""
        try:
            num = float(str(valor).strip())
            if num.is_integer():
                return f"{int(num)}º"
            else:
                return f"{int(round(num))}º"
        except:
            return str(valor)

    # Se houver coluna ORDEM COLETA, vamos processá-la
    if "ORDEM COLETA" in df.columns:
        # Criar nova coluna formatada
        df["ORDEM"] = df["ORDEM COLETA"].apply(formatar_ordem)
        
        # Reorganizar colunas para que ORDEM aparece primeiro
        colunas = list(df.columns)
        colunas.remove("ORDEM COLETA")
        colunas.remove("ORDEM")
        
        # Criar nova ordem das colunas
        ordem_colunas = ["ORDEM"] + colunas
        
        # Reorganizar DataFrame
        df = df[ordem_colunas]
    
    # --- 5. LISTAGEM OPERACIONAL DE TRANSPORTES ---
    st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>🚛 Fila Ativa de Transportes</h4>", unsafe_allow_html=True)
    
    # VERIFICAÇÃO FINAL: garantir que df não está vazio
    if not df.empty:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=420
        )
    else:
        st.markdown(
            """
            <div class='doca-livre-box'>
                <div class='doca-livre-icone'>ℹ️</div>
                <div class='doca-livre-titulo'>Sem dados para exibir</div>
                <div class='doca-livre-sub'>Os registros podem não conter colunas esperadas ou podem estar vazios.</div>
            </div>
            """,
            unsafe_allow_html=True
        )