"""
Aplicação Principal - Dashboard Operacional Streamlit
Ponto de entrada que conecta o Backend (data_loader) ao Frontend (views_saida).
"""

import streamlit as st
from src.config.settings import PAGE_CONFIG
from src.back.data_loader import carregar_dados_status_saida, filtrar_dados_operacao
from src.front.views_saida import exibir_visao_saida

# Configura a página do Streamlit (Layout wide, Ícone)
st.set_page_config(**PAGE_CONFIG)


def main():
    # 1. Carrega os dados via Backend
    df_bruto = carregar_dados_status_saida()

    # 2. Aplica filtro inicial da operação (Ano de 2026)
    # Procurando a coluna de data para o filtro
    coluna_data = "Recepção" if "Recepção" in df_bruto.columns else None
    df_operacao = filtrar_dados_operacao(df_bruto, coluna_data=coluna_data)

    # 3. Renderiza a tela da operação
    exibir_visao_saida(df_operacao)


if __name__ == "__main__":
    main()