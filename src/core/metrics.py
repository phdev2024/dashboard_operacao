"""
Módulo Core: Métricas da Operação (Regras de Negócio)
Traduz as regras operacionais em funções Python reutilizáveis e puras.
"""

import pandas as pd


def calcular_total_notas_unicas(df: pd.DataFrame, coluna_nf: str = "Nº NF-e") -> int:
    """
    Calcula a quantidade de Notas Fiscais únicas (Equivalente ao DISTINCTCOUNT do DAX).
    """
    if df.empty or coluna_nf not in df.columns:
        return 0
    # Remove valores nulos ou vazios e conta os únicos
    return df[coluna_nf].dropna().nunique()


def calcular_total_pedidos_unicos(df: pd.DataFrame, coluna_pedido: str = "Número do Pedido") -> int:
    """
    Calcula a quantidade de Pedidos únicos.
    """
    if df.empty or coluna_pedido not in df.columns:
        return 0
    return df[coluna_pedido].dropna().nunique()


def obter_resumo_por_status(df: pd.DataFrame, coluna_status: str = "Status", coluna_nf: str = "Nº NF-e") -> pd.DataFrame:
    """
    Gera uma tabela resumida com a quantidade de NFs únicas por Status e o % de representatividade.
    """
    if df.empty or coluna_status not in df.columns:
        return pd.DataFrame()

    # Agrupa por status e conta as NFs únicas
    resumo = (
        df.groupby(coluna_status)[coluna_nf]
        .nunique()
        .reset_index()
        .rename(columns={coluna_status: "Status", coluna_nf: "Qtd_NFs"})
    )

    # Ordena do maior para o menor
    resumo = resumo.sort_values(by="Qtd_NFs", ascending=False).reset_index(drop=True)

    # Calcula o percentual sobre o total de notas
    total_geral = resumo["Qtd_NFs"].sum()
    if total_geral > 0:
        resumo["% Representatividade"] = (resumo["Qtd_NFs"] / total_geral) * 100
    else:
        resumo["% Representatividade"] = 0

    return resumo