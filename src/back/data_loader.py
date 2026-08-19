"""
Módulo Backend: Data Loader
Responsável por varrer a pasta de arquivos, ler os formatos (Excel/CSV)
e entregar um DataFrame unificado e higienizado.
"""

import streamlit as st
from pathlib import Path
import pandas as pd
from src.config.settings import DEFAULT_OPERATIONAL_YEAR

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PASTA_STATUS_SAIDA = BASE_DIR / "data" / "status_saida"

# @st.cache_data guarda os dados na memória RAM para a tela carregar instantaneamente!
# @st.cache_data(ttl=300)  # Revalida o cache a cada 5 minutos
def carregar_dados_status_saida(pasta_dados: Path = PASTA_STATUS_SAIDA) -> pd.DataFrame:
    pasta = Path(pasta_dados)
    arquivos = list(pasta.glob("*.xlsx")) + list(pasta.glob("*.xls")) + list(pasta.glob("*.csv"))

    if not arquivos:
        return pd.DataFrame()

    lista_dfs = []
    for arquivo in arquivos:
        try:
            if arquivo.suffix.lower() in ['.xlsx', '.xls']:
                df_temp = pd.read_excel(arquivo, header=4)
            else:
                df_temp = pd.read_csv(arquivo, sep=None, engine='python', header=4)
            
            df_temp['arquivo_origem'] = arquivo.name
            lista_dfs.append(df_temp)
        except Exception as e:
            print(f"❌ Erro ao ler {arquivo.name}: {e}")

    if not lista_dfs:
        return pd.DataFrame()

    df_consolidado = pd.concat(lista_dfs, ignore_index=True)
    df_consolidado.dropna(how='all', inplace=True)
    
    return df_consolidado
    
    # Remove linhas totalmente vazias ou cabeçalhos repetidos que possam ter ficado no meio
    df_consolidado.dropna(how='all', inplace=True)
    
    return df_consolidado


def filtrar_dados_operacao(df: pd.DataFrame, coluna_data: str = None) -> pd.DataFrame:
    """
    Aplica as regras de negócio para a tela da TV da Operação:
    - Filtra dados mantendo apenas o escopo operacional do ano corrente (2026).
    """
    if df.empty:
        return df
        
    df_filtrado = df.copy()

    if coluna_data and coluna_data in df_filtrado.columns:
        df_filtrado[coluna_data] = pd.to_datetime(df_filtrado[coluna_data], errors='coerce')
        df_filtrado = df_filtrado[df_filtrado[coluna_data].dt.year == DEFAULT_OPERATIONAL_YEAR]

    return df_filtrado


if __name__ == "__main__":
    df_teste = carregar_dados_status_saida()
    print(f"✅ Total de linhas carregadas: {len(df_teste)}")
    if not df_teste.empty:
        print("📌 Nomes reais das colunas encontradas:")
        for col in df_teste.columns.tolist()[:10]:
            print(f"   - {col}")