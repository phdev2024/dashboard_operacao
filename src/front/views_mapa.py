"""
Módulo Frontend: Visão da Malha Operacional (Bases e Hubs)
Renderiza os indicadores executivos e o mapa geoespacial com círculos de cobertura.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from src.back.bases_hubs import gerar_circulos_cobertura


def exibir_visao_mapa(df: pd.DataFrame):
    if df.empty:
        st.warning("⚠️ Planilha de Bases e Hubs ('bases_hubs.xlsx') não encontrada ou sem coordenadas válidas.")
        return

    # --- FILTROS RÁPIDOS NA BARRA LATERAL (SE NÃO ESTIVER NO MODO TV) ---
    df_filtrado = df.copy()

    # Só exibe os filtros específicos na barra lateral se a tela ativa for a do Mapa
    tipos_disponiveis = ["Todos"] + sorted(list(df["Tipo"].dropna().unique()))
    tipo_selecionado = st.sidebar.selectbox("Filtrar por Tipo:", tipos_disponiveis, key="filtro_tipo_mapa")

    ufs_disponiveis = ["Todos"] + sorted(list(df["UF"].dropna().unique()))
    uf_selecionada = st.sidebar.selectbox("Filtrar por UF:", ufs_disponiveis, key="filtro_uf_mapa")

    ativar_raio = st.sidebar.checkbox("Exibir Raio de Alcance", value=True, key="filtro_raio_mapa")
    raio_selecionado = st.sidebar.slider("Raio de Suporte (em km):", min_value=10, max_value=150, value=50, step=10, key="slider_raio_mapa")

    # Aplicação dos filtros
    if tipo_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_selecionado]
    if uf_selecionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado["UF"] == uf_selecionada]

    # --- CABEÇALHO & CARDS KPI ---
    col_titulo, col_kpi1, col_kpi2, col_kpi3 = st.columns([2.5, 1, 1, 1], vertical_alignment="center")

    with col_titulo:
        st.markdown("<h2 style='color: #FFFFFF; font-size: 1.8rem; font-weight: 800; margin: 0;'>🗺️ Malha Operacional</h2>", unsafe_allow_html=True)
        st.caption("Bases Ativas e Novos Hubs de Suporte Imediato")

    with col_kpi1:
        st.metric("Total Unidades", len(df_filtrado))

    with col_kpi2:
        st.metric("Bases Principais", len(df_filtrado[df_filtrado["Tipo"].str.upper() == "BASE"]))

    with col_kpi3:
        st.metric("Hubs de Suporte", len(df_filtrado[df_filtrado["Tipo"].str.upper() == "HUB"]))

    st.write("")

    # --- CONSTRUÇÃO DO MAPA GEOESPACIAL ---
    mapa_cores = {"Base": "#0052cc", "Hub": "#ff5500"}

    # Proteção de colunas para o hover
    hover_cols = {
        "Cidade": True,
        "UF": True,
        "Tipo": True,
        "Latitude": False,
        "Longitude": False
    }
    for col_opcional in ["Bairro", "Rua"]:
        if col_opcional in df_filtrado.columns:
            hover_cols[col_opcional] = True

    coluna_hover_nome = "Nome_Base" if "Nome_Base" in df_filtrado.columns else "Cidade"

    fig = px.scatter_map(
        df_filtrado,
        lat="Latitude",
        lon="Longitude",
        color="Tipo",
        color_discrete_map=mapa_cores,
        zoom=4.2,
        center={"lat": -18.0, "lon": -48.0},
        hover_name=coluna_hover_nome,
        hover_data=hover_cols,
        map_style="open-street-map"
    )

    fig.update_traces(marker=dict(size=14, opacity=0.9))

    fig.update_layout(
        height=620,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend=dict(
            title_text="",
            orientation="h",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(22, 36, 33, 0.85)",
            bordercolor="#223834",
            borderwidth=1,
            font=dict(size=13, color="#FFFFFF")
        )
    )

    if ativar_raio:
        geojson_raio = gerar_circulos_cobertura(df_filtrado, raio_km=raio_selecionado)
        fig.update_layout(
            map_layers=[
                {
                    "sourcetype": "geojson",
                    "source": geojson_raio,
                    "type": "fill",
                    "color": "rgba(43, 92, 143, 0.20)",
                },
                {
                    "sourcetype": "geojson",
                    "source": geojson_raio,
                    "type": "line",
                    "color": "rgba(43, 92, 143, 0.65)",
                    "line": {"width": 1.5}
                }
            ]
        )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Ver tabela de dados detalhada"):
        cols_exibir = [c for c in ["Nome_Base", "Tipo", "Cidade", "UF", "Bairro", "Rua"] if c in df_filtrado.columns]
        st.dataframe(df_filtrado[cols_exibir], use_container_width=True, hide_index=True)