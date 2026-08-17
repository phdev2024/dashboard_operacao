"""
Módulo Frontend: Visão Operacional de Volumes e Clientes (Tela 2)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.config.settings import (
    COLOR_BRAND_PRIMARY, COLOR_CARD_BG, COLOR_TEXT_LIGHT, 
    COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
)
from src.core.metrics import (
    calcular_total_volumes,
    obter_evolucao_diaria_volumes_mes_atual,
    obter_top_clientes_volumes_mes_atual
)


def renderizar_css_tv():
    st.markdown(
        f"""
        <style>
            /* Reduz margens para aproveitar o espaço da tela sem quebrar menus nativos */
            .block-container {{
                padding-top: 3.5rem !important;
                padding-bottom: 1rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }}
            
            .stApp {{
                opacity: 1 !important;
            }}
            
            /* Estilização uniforme dos cartões de KPI */
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
        </style>
        """,
        unsafe_allow_html=True
    )


def exibir_visao_volumes(df: pd.DataFrame):
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
        st.markdown("<h2 class='header-title' style='padding-left: 15px;'>Painel Operacional - Volumes/Clientes</h2>", unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border-color: #223834;'>", unsafe_allow_html=True)

    if df.empty:
        st.warning("⚠️ Nenhum dado operacional encontrado.")
        return

    # --- 2. CÁLCULO DAS MÉTRICAS DO MÊS ATUAL ---
    if "Recepção" in df.columns:
        df_temp = df.copy()
        df_temp["Recepção"] = pd.to_datetime(df_temp["Recepção"], errors="coerce")
        df_temp = df_temp.dropna(subset=["Recepção"])
        
        if not df_temp.empty:
            data_maxima = df_temp["Recepção"].max()
            ano_atual = data_maxima.year
            mes_atual = data_maxima.month
            nome_mes_ano = data_maxima.strftime("%m/%Y")
            data_hoje_str = data_maxima.strftime("%d/%m")
            
            df_mes = df_temp[(df_temp["Recepção"].dt.year == ano_atual) & (df_temp["Recepção"].dt.month == mes_atual)]
            df_hoje = df_mes[df_mes["Recepção"].dt.date == data_maxima.date()]
            total_volumes_hoje = calcular_total_volumes(df_hoje)
        else:
            df_mes = pd.DataFrame()
            nome_mes_ano = "Mês Atual"
            data_hoje_str = "Hoje"
            total_volumes_hoje = 0
    else:
        df_mes = df.copy()
        nome_mes_ano = "Mês Atual"
        data_hoje_str = "Hoje"
        total_volumes_hoje = 0

    total_volumes_mes = calcular_total_volumes(df_mes)

    # Volumes Expedidos
    df_expedidas_mes = df_mes[df_mes["Status"] == "EXPEDIDO"] if "Status" in df_mes.columns else pd.DataFrame()
    total_volumes_expedidos = calcular_total_volumes(df_expedidas_mes)

    # Volumes com Pendência
    status_finalizados = ["EXPEDIDO", "CANCELADA", "REJEITADA", "CANCELADO", "REJEITADO"]
    if "Status" in df_mes.columns:
        df_pendentes_mes = df_mes[~df_mes["Status"].astype(str).str.strip().str.upper().isin(status_finalizados)]
        total_volumes_pendentes = calcular_total_volumes(df_pendentes_mes)
    else:
        total_volumes_pendentes = 0

    # --- 3. LINHA DE CARDS ---
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Total Volumes ({nome_mes_ano})</div>
                <div class='kpi-value' style='color: {COLOR_BRAND_PRIMARY};'>{total_volumes_mes:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Volumes Expedidos</div>
                <div class='kpi-value' style='color: {COLOR_SUCCESS};'>{total_volumes_expedidos:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    with c3:
        cor_pendencia = COLOR_DANGER if total_volumes_pendentes > 500 else COLOR_WARNING
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Volumes Pendentes</div>
                <div class='kpi-value' style='color: {cor_pendencia};'>{total_volumes_pendentes:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Volumes em {data_hoje_str}</div>
                <div class='kpi-value' style='color: {COLOR_TEXT_LIGHT};'>{total_volumes_hoje:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    st.write("")

    # --- 4. VISUALIZAÇÃO OPERACIONAL ---
    col_grafico, col_clientes = st.columns([1.1, 0.9])

    with col_grafico:
        st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>📈 Ritmo Diário de Volumes (Mês Atual)</h4>", unsafe_allow_html=True)
        
        df_tendencia_vol = obter_evolucao_diaria_volumes_mes_atual(df)
        
        if not df_tendencia_vol.empty:
            fig = px.line(
                df_tendencia_vol, 
                x="Dia", 
                y="Qtd_Volumes", 
                text="Qtd_Volumes",
                markers=True
            )
            fig.update_traces(
                line_color=COLOR_BRAND_PRIMARY,
                line_width=3,
                marker_size=8,
                textposition="top center",
                textfont=dict(color="white", size=12)
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis=dict(
                    type="category", 
                    tickangle=0,
                    tickfont=dict(color=COLOR_TEXT_MUTED, size=11),
                    gridcolor="#1F332E"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#1F332E",
                    tickfont=dict(color=COLOR_TEXT_MUTED)
                ),
                height=380
            )
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Sem dados de volumes válidos para o gráfico de tendência.")

    with col_clientes:
        st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>🏢 Top Clientes por Volume (Mês Atual)</h4>", unsafe_allow_html=True)
        
        df_top_clientes = obter_top_clientes_volumes_mes_atual(df, top_n=6)

        if not df_top_clientes.empty:
            # Apresentação via Tabela com colunas limpas (sem cortar nem espremer)
            st.dataframe(
                df_top_clientes[["Cliente_Exibicao", "Qtd_Volumes", "% Representatividade"]].rename(
                    columns={"Cliente_Exibicao": "Cliente"}
                ).style.format({
                    "Qtd_Volumes": lambda x: f"{x:,.0f}".replace(",", "."),
                    "% Representatividade": lambda x: f"{x:.1f}%".replace(",", ".")
                }),
                width='stretch',
                hide_index=True,
                height=320
            )
        else:
            st.info("Sem dados de clientes disponíveis.")