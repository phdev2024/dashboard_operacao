"""
Módulo Frontend: Visão de Status de Saída (MVP TV Operacional)
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from src.config.settings import (
    BRAND_NAME, APP_TITLE, COLOR_BRAND_PRIMARY, 
    COLOR_CARD_BG, COLOR_TEXT_LIGHT, COLOR_TEXT_MUTED, 
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
)
from src.core.metrics import (
    calcular_total_notas_unicas, 
    obter_resumo_por_status
)


def renderizar_css_tv():
    """Aplica CSS para eliminar espaçamentos excessivos no topo e travar o Dark Mode."""
    st.markdown(
        f"""
        <style>
            /* Reduz a margem superior padrão do Streamlit (aproveita o topo) */
            .block-container {{
                padding-top: 1.5rem !important;
                padding-bottom: 1rem !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }}
            /* Oculta o menu superior padrão do Streamlit para modo TV limpo */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            
            /* Fundo escuro fixo operacional */
            .stApp {{ background-color: #0B1311; }}
            
            /* Estilo dos Cards de KPI */
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
            
            /* Cabeçalho Inline (Logo + Título lado a lado) */
            .header-container {{
                display: flex;
                align-items: center;
                gap: 20px;
                margin-bottom: 10px;
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

    # --- 1. CABEÇALHO COMPACTO (Logo + Título na mesma linha) ---
    caminho_logo = Path("data/media/logo_logcare.png")
    
    # Ajustamos a proporção das colunas (1.5 para a logo, 8.5 para o título)
    # E ativamos vertical_alignment="center" para alinhar o título no meio da logo
    c1, c2 = st.columns([3, 8.5], vertical_alignment="center")
    
    with c1:
        if caminho_logo.exists():
            # Controlamos a largura máxima do logo para não ficar gigante
            st.image(str(caminho_logo), width=160)
        else:
            st.markdown(f"<h2 style='color: {COLOR_BRAND_PRIMARY}; margin:0;'>LOGCARE</h2>", unsafe_allow_html=True)
            
    with c2:
        # Adicionamos um padding-left para afastar o título da imagem
        st.markdown(
            f"<h2 class='header-title' style='padding-left: 15px; margin: 0;'>{APP_TITLE}</h2>", 
            unsafe_allow_html=True
        )

    st.markdown("<hr style='margin-top: 10px; margin-bottom: 15px; border-color: #223834;'>", unsafe_allow_html=True)

    if df.empty:
        st.warning("⚠️ Nenhum dado operacional encontrado para o ano de 2026.")
        return

    # --- 2. CÁLCULO DAS MÉTRICAS ---
    total_nfs_ano = calcular_total_notas_unicas(df)
    df_status = obter_resumo_por_status(df)

    # Identificar Pendências (Ação Imediata)
    status_pendentes = ["EM SEPARAÇÃO", "PENDENTE", "EM CONFERENCIA", "AGUARDANDO EXPEDICAO"]
    df_pendentes = df[df["Status"].isin(status_pendentes)] if "Status" in df.columns else pd.DataFrame()
    total_pendentes = calcular_total_notas_unicas(df_pendentes)

    # Identificar Expedidas
    df_expedidas = df[df["Status"] == "EXPEDIDO"] if "Status" in df.columns else pd.DataFrame()
    total_expedidas = calcular_total_notas_unicas(df_expedidas)

    # --- 3. LINHA DE 4 CARDS ESTRATÉGICOS ---
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
                <div class='kpi-title'>Total Recebido em {data_maxima}</div>
                <div class='kpi-value' style='color: {COLOR_TEXT_LIGHT};'>{total_hoje:,}</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True
        )

    st.write("")

    # --- 4. VISUALIZAÇÃO DOS STATUS (Com tabela expandida) ---
    col_grafico, col_tabela = st.columns([1, 1])

    with col_grafico:
        st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>Distribuição por Status</h4>", unsafe_allow_html=True)
        st.bar_chart(
            data=df_status.set_index("Status")["Qtd_NFs"],
            color=COLOR_BRAND_PRIMARY,
            horizontal=True
        )

    with col_tabela:
        st.markdown(f"<h4 style='color: {COLOR_TEXT_LIGHT}; margin-bottom: 10px;'>Detalhamento Quantitativo</h4>", unsafe_allow_html=True)
        st.dataframe(
            df_status.style.format({
                "Qtd_NFs": "{:,.0f}",
                "% Representatividade": "{:.1f}%"
            }),
            use_container_width=True,
            hide_index=True
        )