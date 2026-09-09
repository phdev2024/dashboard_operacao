"""
Módulo Frontend: Visão de SLA e Fila Crítica de Expedição
Monitora pedidos em separação e aguardando expedição com base no horário de corte (12h00).
"""

from datetime import datetime, timedelta, time as dtime
import pandas as pd
import streamlit as st


def _definir_farol(data_recepcao: pd.Timestamp, agora: datetime) -> tuple[str, str]:
    """
    Classifica a criticidade com base na janela operacional de expedição (dias úteis):
    - Dias úteis: Segunda a Sexta.
    - Janela do lote: Do último dia útil às 12h00 até hoje às 12h00.
    - Prazo fatal de expedição do lote: Hoje até as 18h00.
    """
    if pd.isna(data_recepcao):
        return "🔴 Crítico", "Sem Data"

    data_rec = data_recepcao.to_pydatetime()
    hoje = agora.date()

    # Define quantos dias voltar para encontrar o último dia útil:
    # Se hoje é segunda (0), o último dia útil foi sexta (3 dias atrás).
    # Se hoje for domingo (6), volta 2 dias (sexta).
    # Se hoje for sábado (5), volta 1 dia (sexta).
    # Para terça a sexta, volta 1 dia normal.
    dia_semana = hoje.weekday()
    if dia_semana == 0:
        dias_retroativos = 3
    elif dia_semana == 6:
        dias_retroativos = 2
    elif dia_semana == 5:
        dias_retroativos = 1
    else:
        dias_retroativos = 1

    ultimo_dia_util = hoje - timedelta(days=dias_retroativos)
    inicio_lote_hoje = datetime.combine(ultimo_dia_util, dtime(12, 0, 0))
    corte_lote_hoje = datetime.combine(hoje, dtime(12, 0, 0))

    # Caso 1: Entrou antes das 12h00 do último dia útil (já deveria ter saído)
    if data_rec < inicio_lote_hoje:
        dias_atraso = (hoje - data_rec.date()).days
        return "🔴 Crítico", f"Pendente D-{dias_atraso}"

    # Caso 2: Entrou hoje após as 12h00 (pertence ao lote do próximo dia útil)
    if data_rec > corte_lote_hoje:
        return "🟢 No Prazo", "Lote Seguinte"

    # Caso 3: Lote Operacional do Dia (meta de saída até 18h00)
    hora_atual = agora.time()
    if hora_atual >= dtime(18, 0):
        return "🔴 Atrasado", "Expedição 18h Estourada"
    elif hora_atual >= dtime(16, 0):
        return "🟡 Atenção", "Janela Final (Até 18h)"
    else:
        return "🟢 No Prazo", "Meta Hoje 18h"


def exibir_visao_sla(df: pd.DataFrame):
    """Renderiza a visão executiva de SLA e Alertas Críticos da Expedição."""
    st.markdown("## ⏱️ Radar de SLA & Fila Crítica da Expedição")
    st.caption("Monitoramento dinâmico de pedidos pendentes com base no corte operacional das 12h00.")

    if df.empty:
        st.warning("⚠️ Nenhum dado operacional disponível para apuração de SLA.")
        return

    # Normalização de nomes de colunas
    df_sla = df.copy()
    colunas_map = {col.strip().upper(): col for col in df_sla.columns}

    col_status = colunas_map.get("STATUS")
    col_recepcao = colunas_map.get("RECEPÇÃO", colunas_map.get("RECEPCAO"))
    col_cliente = colunas_map.get("CLIENTE")
    col_transp = colunas_map.get("TRANSPORTADORA")
    col_vol = colunas_map.get("QTDE DE VOLUMES", colunas_map.get("VOLUME"))

    if not col_status or not col_recepcao:
        st.error("Colunas essenciais ('Status' e 'Recepção') não foram localizadas na planilha.")
        return

    # Filtra apenas o funil operacional de risco
    # Filtra apenas o funil operacional de risco (aceita com ou sem acentuação)
    status_alvo = [
        "EM SEPARACAO", "EM SEPARAÇÃO",
        "AGUARDANDO EXPEDICAO", "AGUARDANDO EXPEDIÇÃO"
    ]
    df_sla["STATUS_LIMPO"] = df_sla[col_status].astype(str).str.strip().str.upper()
    df_pendentes = df_sla[df_sla["STATUS_LIMPO"].isin(status_alvo)].copy()

    if df_pendentes.empty:
        st.markdown(
            """
            <div style="text-align: center; padding: 60px 20px; background-color: rgba(30, 90, 40, 0.2); border: 2px dashed #2e7d32; border-radius: 10px; margin-top: 30px;">
                <h1 style="color: #4CAF50; margin-bottom: 10px;">🎉 Operação 100% em Dia!</h1>
                <h4 style="color: #aaaaaa; font-weight: normal;">Nenhum pedido em Separação ou Aguardando Expedição fora do prazo no momento.</h4>
            </div>
            """, 
            unsafe_allow_html=True
        )
        return

    # Conversão de tipos defensiva
    agora = datetime.now()
    df_pendentes["Data_Ref"] = pd.to_datetime(df_pendentes[col_recepcao], errors="coerce", dayfirst=True)

    if col_vol and col_vol in df_pendentes.columns:
        df_pendentes["Volumes_Num"] = pd.to_numeric(df_pendentes[col_vol], errors="coerce").fillna(0)
    else:
        df_pendentes["Volumes_Num"] = 0

    # Aplicação do farol
    farois = [
        _definir_farol(data, agora) 
        for data in df_pendentes["Data_Ref"]
    ]
    df_pendentes["Farol"] = [f[0] for f in farois]
    df_pendentes["Motivo_SLA"] = [f[1] for f in farois]

    # Contadores de Destaque (Cards no Topo)
    total_critico = (df_pendentes["Farol"].str.startswith("🔴")).sum()
    total_atencao = (df_pendentes["Farol"].str.startswith("🟡")).sum()
    total_no_prazo = (df_pendentes["Farol"].str.startswith("🟢")).sum()
    total_pendente = len(df_pendentes)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total na Fila", f"{total_pendente} ped.")
    with c2:
        st.metric("🔴 Crítico / Atrasado", f"{total_critico} ped.")
    with c3:
        st.metric("🟡 Reta Final (16h - 18h)", f"{total_atencao} ped.")
    with c4:
        st.metric("🟢 Meta Hoje 18h / Novo Lote", f"{total_no_prazo} ped.")

    st.markdown("---")

    # Consolidação em tabela enxuta (sem rolagem excessiva)
    col_cliente_real = col_cliente if col_cliente else "Cliente"
    col_transp_real = col_transp if col_transp else "Transportadora"

    if col_cliente_real not in df_pendentes.columns:
        df_pendentes[col_cliente_real] = "Não Informado"
    if col_transp_real not in df_pendentes.columns:
        df_pendentes[col_transp_real] = "Não Informado"

    df_agrupado = df_pendentes.groupby(
        ["Farol", col_cliente_real, col_transp_real, col_status], 
        as_index=False
    ).agg(
        Qtd_Pedidos=("Farol", "count"),
        Total_Volumes=("Volumes_Num", "sum"),
        Entrada_Mais_Antiga=("Data_Ref", "min")
    )

    # Formatação de datas e ordenação por criticidade
    df_agrupado["Entrada_Mais_Antiga"] = df_agrupado["Entrada_Mais_Antiga"].dt.strftime("%d/%m %H:%M").fillna("-")
    df_agrupado["Total_Volumes"] = df_agrupado["Total_Volumes"].astype(int)

    # Ordem customizada: Vermelho primeiro, depois Amarelo, depois Verde
    ordem_farol = {"🔴 Crítico": 1, "🔴 Atrasado": 2, "🟡 Atenção": 3, "🟢 No Prazo": 4}
    df_agrupado["Ordem"] = df_agrupado["Farol"].map(ordem_farol).fillna(5)
    df_agrupado = df_agrupado.sort_values(by=["Ordem", "Qtd_Pedidos"], ascending=[True, False]).drop(columns=["Ordem"])

    df_agrupado.rename(
        columns={
            "Farol": "Farol SLA",
            col_cliente_real: "Cliente",
            col_transp_real: "Transportadora",
            col_status: "Status Atual",
            "Qtd_Pedidos": "Qtd Pedidos",
            "Total_Volumes": "Volumes",
            "Entrada_Mais_Antiga": "Primeira Entrada"
        },
        inplace=True
    )

    st.dataframe(
        df_agrupado,
        use_container_width=True,
        hide_index=True
    )