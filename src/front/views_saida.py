"""
Módulo Frontend: Visão de Status de Saída (Gráfico Plotly com Rótulos + Status Mês Atual)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.config.settings import (
    BRAND_NAME, APP_TITLE, COLOR_BRAND_PRIMARY, 
    COLOR_CARD_BG, COLOR_TEXT_LIGHT, COLOR_TEXT_MUTED, 
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
)
from src.core.metrics import (
    calcular_total_notas_unicas, 
    obter_resumo_por_status_mes_atual,
    obter_evolucao_diaria_mes_atual,
    obter_evolucao_diaria_mes_atual
)


def renderizar_css_tv():
    st.markdown(
        f"""
        <style>
            .block-container {{
                padding-top: 1.5rem !important;
                padding-bottom: 1rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }}
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            .stApp {{ background-color: #0B1311; }}
            .kpi-card {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid #223834;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
            }}
            .kpi-title {{
                color: {COLOR_TEXT_MUTED};
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
                color: {COLOR_TEXT_LIGHT};
                font-size: 1.8rem;
                font-weight: 800;
                margin: 0;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


def exibir_visao_saida(df: pd.DataFrame):
    renderizar_css_tv()

    # --- 1. CABEÇALHO COMPACTO ---
    caminho_logo = Path("data/media/logo_logcare.png")
    c1, c2 = st.columns([3.5, 8.5], vertical_alignment="center")
    
    with c1:
        if caminho_logo.exists():
            st.image(str(caminho_logo), width=140)
        else:
            st.markdown(f"<h2 style='color: {COLOR_BRAND_PRIMARY}; margin:0;'>LOGCARE</h2>", unsafe_allow_html=True)
            
    with c2:
        st.markdown(f"<h2 class='header-title' style='padding-left: 15px;'>{APP_TITLE}</h2>", unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border-color: #223834;'>", unsafe_allow_html=True)

    if df.empty:
        st.warning("⚠️ Nenhum dado operacional encontrado para o ano de 2026.")
        return

    # --- 2. CÁLCULO DAS MÉTRICAS ---
    total_nfs_ano = calcular_total_notas_unicas(df)
    
    # 1. Tabela de status exclusiva do MÊS ATUAL
    df_status_mes = obter_resumo_por_status_mes_atual(df, coluna_data="Recepção")

    # 2. Filtragem direta das Pendências no Mês Atual (à prova de falhas)
    status_pendentes_busca = ["EM SEPARACAO", "EM SEPARAÇÃO", "PENDENTE", "EM CONFERENCIA", "EM CONFERÊNCIA", "AGUARDANDO EXPEDICAO", "AGUARDANDO EXPEDIÇÃO"]
    
    if "Recepção" in df.columns and "Status" in df.columns:
        df_temp = df.copy()
        df_temp["Recepção"] = pd.to_datetime(df_temp["Recepção"], errors="coerce")
        data_maxima = df_temp["Recepção"].max()
        
        # Filtra o mês atual e os status pendentes
        df_pendentes_mes = df_temp[
            (df_temp["Recepção"].dt.year == data_maxima.year) & 
            (df_temp["Recepção"].dt.month == data_maxima.month) &
            (df_temp["Status"].astype(str).str.strip().str.upper().isin(status_pendentes_busca))
        ]
        total_pendentes = calcular_total_notas_unicas(df_pendentes_mes)
    else:
        total_pendentes = 0

    # Expedidas no Ano
    df_expedidas = df[df["Status"] == "EXPEDIDO"] if "Status" in df.columns else pd.DataFrame()
    total_expedidas = calcular_total_notas_unicas(df_expedidas)

    # --- 3. LINHA DE CARDS ---
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Total Acumulado (2026)</div>
                <div class='kpi-value' style='color: {COLOR_BRAND_PRIMARY};'>{total_nfs_ano:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Expedidas (Concluídas)</div>
                <div class='kpi-value' style='color: {COLOR_SUCCESS};'>{total_expedidas:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    with c3:
        cor_pendencia = COLOR_DANGER if total_pendentes > 50 else COLOR_WARNING
        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Pendências Operacionais</div>
                <div class='kpi-value' style='color: {cor_pendencia};'>{total_pendentes:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    with c4:
        if "Recepção" in df.columns and not df["Recepção"].dropna().empty:
            data_maxima = df["Recepção"].max().strftime("%d/%m")
            df_hoje = df[df["Recepção"].dt.date == df["Recepção"].max().date()]
            total_hoje = calcular_total_notas_unicas(df_hoje)
        else:
            data_maxima = "Hoje"
            total_hoje = 0

        st.markdown(
            f"""
            <div class='kpi-card'>
                <div class='kpi-title'>Entradas em {data_maxima}</div>
                <div class='kpi-value' style='color: {COLOR_TEXT_LIGHT};'>{total_hoje:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    st.write("")

    # --- 4. VISUALIZAÇÃO OPERACIONAL ---
    col_grafico, col_tabela = st.columns([1.2, 0.8])

    with col_grafico:
        st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>📈 Ritmo Diário de Entradas (Mês Atual)</h4>", unsafe_allow_html=True)
        
        df_tendencia = obter_evolucao_diaria_mes_atual(df, coluna_data="Recepção")
        
        if not df_tendencia.empty:
            # Gráfico Plotly customizado: Datas na horizontal + Números no topo dos pontos
            fig = px.line(
                df_tendencia, 
                x="Dia", 
                y="Qtd_NFs", 
                text="Qtd_NFs",
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
                margin=dict(l=10, r=10, t=25, b=10),
                xaxis=dict(
                    type="category", 
                    tickangle=0,  # Garante datas 100% HORIZONTAIS
                    tickfont=dict(color=COLOR_TEXT_MUTED, size=11),
                    gridcolor="#1F332E"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#1F332E",
                    tickfont=dict(color=COLOR_TEXT_MUTED)
                ),
                height=323
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sem dados de datas válidos para o gráfico de tendência.")

    with col_tabela:
        st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>🎯 Status da Operação (Mês Atual)</h4>", unsafe_allow_html=True)
        
        status_ignorados = ["REJEITADA", "CANCELADA"]
        df_status_operacional = df_status_mes[~df_status_mes["Status"].isin(status_ignorados)] if not df_status_mes.empty else pd.DataFrame()

        st.dataframe(
            df_status_operacional.style.format({
                "Qtd_NFs": "{:,.0f}",
                "% Representatividade": "{:.1f}%"
            }),
            use_container_width=True,
            hide_index=True,
            height=280
            )
        