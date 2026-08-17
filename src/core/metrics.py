"""
Módulo Core: Métricas da Operação (Regras de Negócio)
"""

import pandas as pd


def calcular_total_notas_unicas(df: pd.DataFrame, coluna_nf: str = "Nº NF-e") -> int:
    """Calcula a quantidade de Notas Fiscais únicas."""
    if df.empty or coluna_nf not in df.columns:
        return 0
    return df[coluna_nf].dropna().nunique()


def calcular_total_pedidos_unicos(df: pd.DataFrame, coluna_pedido: str = "Número do Pedido") -> int:
    """Calcula a quantidade de Pedidos únicos."""
    if df.empty or coluna_pedido not in df.columns:
        return 0
    return df[coluna_pedido].dropna().nunique()


def obter_resumo_por_status(df: pd.DataFrame, coluna_status: str = "Status", coluna_nf: str = "Nº NF-e") -> pd.DataFrame:
    """Gera tabela resumida com a quantidade de NFs únicas por Status."""
    if df.empty or coluna_status not in df.columns:
        return pd.DataFrame()

    resumo = (
        df.groupby(coluna_status)[coluna_nf]
        .nunique()
        .reset_index()
        .rename(columns={coluna_status: "Status", coluna_nf: "Qtd_NFs"})
    )

    resumo = resumo.sort_values(by="Qtd_NFs", ascending=False).reset_index(drop=True)

    total_geral = resumo["Qtd_NFs"].sum()
    if total_geral > 0:
        resumo["% Representatividade"] = (resumo["Qtd_NFs"] / total_geral) * 100
    else:
        resumo["% Representatividade"] = 0

    return resumo


def obter_resumo_por_status_mes_atual(df: pd.DataFrame, coluna_status: str = "Status", coluna_nf: str = "Nº NF-e", coluna_data: str = "Recepção") -> pd.DataFrame:
    """Gera o resumo de status considerando apenas o Mês Corrente do dado."""
    if df.empty or coluna_status not in df.columns:
        return pd.DataFrame()

    df_mes = df.copy()
    if coluna_data in df_mes.columns:
        df_mes[coluna_data] = pd.to_datetime(df_mes[coluna_data], errors="coerce")
        df_mes = df_mes.dropna(subset=[coluna_data])
        
        if not df_mes.empty:
            data_maxima = df_mes[coluna_data].max()
            df_mes = df_mes[(df_mes[coluna_data].dt.year == data_maxima.year) & (df_mes[coluna_data].dt.month == data_maxima.month)]

    return obter_resumo_por_status(df_mes, coluna_status=coluna_status, coluna_nf=coluna_nf)


def obter_evolucao_diaria_mes_atual(df: pd.DataFrame, coluna_data: str = "Recepção", coluna_nf: str = "Nº NF-e") -> pd.DataFrame:
    """Agrupa a quantidade de NFs únicas por dia do mês mais recente."""
    if df.empty or coluna_data not in df.columns:
        return pd.DataFrame()

    df_data = df.copy()
    df_data[coluna_data] = pd.to_datetime(df_data[coluna_data], errors="coerce")
    df_data = df_data.dropna(subset=[coluna_data])

    if df_data.empty:
        return pd.DataFrame()

    data_maxima = df_data[coluna_data].max()
    df_mes = df_data[(df_data[coluna_data].dt.year == data_maxima.year) & (df_data[coluna_data].dt.month == data_maxima.month)]

    evolucao = (
        df_mes.groupby(df_mes[coluna_data].dt.date)[coluna_nf]
        .nunique()
        .reset_index()
        .rename(columns={coluna_data: "Data", coluna_nf: "Qtd_NFs"})
    )

    evolucao["Dia"] = pd.to_datetime(evolucao["Data"]).dt.strftime("%d/%m")
    return evolucao[["Dia", "Qtd_NFs"]]

def calcular_total_volumes(df: pd.DataFrame, coluna_vol: str = "Qtde de Volumes") -> int:
    """Calcula o total acumulado de volumes."""
    if df.empty or coluna_vol not in df.columns:
        return 0
    return int(pd.to_numeric(df[coluna_vol], errors="coerce").fillna(0).sum())


def obter_evolucao_diaria_volumes_mes_atual(
    df: pd.DataFrame, 
    coluna_data: str = "Recepção", 
    coluna_vol: str = "Qtde de Volumes"
) -> pd.DataFrame:
    """Calcula a soma diária de volumes para o mês mais recente."""
    if df.empty or coluna_data not in df.columns or coluna_vol not in df.columns:
        return pd.DataFrame()

    df_data = df.copy()
    df_data[coluna_data] = pd.to_datetime(df_data[coluna_data], errors="coerce")
    df_data[coluna_vol] = pd.to_numeric(df_data[coluna_vol], errors="coerce").fillna(0)
    df_data = df_data.dropna(subset=[coluna_data])

    if df_data.empty:
        return pd.DataFrame()

    data_maxima = df_data[coluna_data].max()
    df_mes = df_data[
        (df_data[coluna_data].dt.year == data_maxima.year) & 
        (df_data[coluna_data].dt.month == data_maxima.month)
    ]

    evolucao = (
        df_mes.groupby(df_mes[coluna_data].dt.date)[coluna_vol]
        .sum()
        .reset_index()
        .rename(columns={coluna_data: "Data", coluna_vol: "Qtd_Volumes"})
    )

    evolucao["Dia"] = pd.to_datetime(evolucao["Data"]).dt.strftime("%d/%m")
    evolucao["Qtd_Volumes"] = evolucao["Qtd_Volumes"].astype(int)
    
    return evolucao[["Dia", "Qtd_Volumes"]]


def obter_top_clientes_volumes_mes_atual(
    df: pd.DataFrame, 
    coluna_cliente: str = "Cliente", 
    coluna_vol: str = "Qtde de Volumes", 
    coluna_data: str = "Recepção", 
    top_n: int = 6
) -> pd.DataFrame:
    """Agrupa por cliente no mês atual e resume os nomes longos."""
    if df.empty or coluna_cliente not in df.columns or coluna_vol not in df.columns:
        return pd.DataFrame()

    df_mes = df.copy()
    if coluna_data in df_mes.columns:
        df_mes[coluna_data] = pd.to_datetime(df_mes[coluna_data], errors="coerce")
        df_mes = df_mes.dropna(subset=[coluna_data])
        if not df_mes.empty:
            data_maxima = df_mes[coluna_data].max()
            df_mes = df_mes[
                (df_mes[coluna_data].dt.year == data_maxima.year) & 
                (df_mes[coluna_data].dt.month == data_maxima.month)
            ]

    df_mes[coluna_vol] = pd.to_numeric(df_mes[coluna_vol], errors="coerce").fillna(0)

    resumo = (
        df_mes.groupby(coluna_cliente)[coluna_vol]
        .sum()
        .reset_index()
        .rename(columns={coluna_cliente: "Cliente", coluna_vol: "Qtd_Volumes"})
    )

    resumo = resumo.sort_values(by="Qtd_Volumes", ascending=False).reset_index(drop=True)
    resumo["Qtd_Volumes"] = resumo["Qtd_Volumes"].astype(int)

    total_geral = resumo["Qtd_Volumes"].sum()
    if total_geral > 0:
        resumo["% Representatividade"] = (resumo["Qtd_Volumes"] / total_geral) * 100
    else:
        resumo["% Representatividade"] = 0

    # Trunca nomes com mais de 25 caracteres para exibição
    resumo["Cliente_Exibicao"] = resumo["Cliente"].apply(
        lambda x: (str(x)[:22] + "...") if len(str(x)) > 25 else str(x)
    )

    return resumo.head(top_n)