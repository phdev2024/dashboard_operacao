# -*- coding: utf-8 -*-
"""
DIAGNOSTICO DE BACKLOG  (somente leitura)
=========================================
Responde: quantas notas ficaram para tras dos meses anteriores e continuam abertas?
Nao altera nada, nao grava nada, nao encosta em tela.
Uso:  python diagnostico_backlog.py
"""
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

HEADER_LINHA = 4
STATUS_ABERTOS = ["EM PENDENTE", "PENDENTE", "EM SEPARACAO", "AGUARDANDO EXPEDICAO"]
PASTA_OPER_PADRAO = Path("data/status_saida/operacional")
PASTA_HIST_PADRAO = Path("data/status_saida/historico")
FAIXAS = [(0, 7, "0 a 7 dias"), (8, 15, "8 a 15 dias"), (16, 30, "16 a 30 dias"),
          (31, 60, "31 a 60 dias"), (61, 90, "61 a 90 dias"), (91, 999999, "mais de 90 dias")]

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def limpar(texto):
    base = unicodedata.normalize("NFKD", str(texto))
    return base.encode("ascii", "ignore").decode("ascii").strip().upper()


def achar_coluna(df, *termos):
    mapa = {limpar(c): c for c in df.columns}
    for termo in termos:
        alvo = limpar(termo)
        for chave, nome_real in mapa.items():
            if alvo in chave:
                return nome_real
    return None


def chave_nota(serie):
    numero = pd.to_numeric(serie, errors="coerce")
    if numero.notna().all():
        return numero.astype("int64").astype(str)
    return serie.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def ler_pasta(pasta):
    pasta = Path(pasta)
    if not pasta.exists():
        print("  [AVISO] pasta inexistente:", pasta)
        return pd.DataFrame()

    arquivos = [a for a in list(pasta.glob("*.xlsx")) + list(pasta.glob("*.xls")) + list(pasta.glob("*.csv"))
                if not a.name.startswith("~$")]
    if not arquivos:
        print("  [AVISO] nenhum arquivo nesta pasta:", pasta)
        return pd.DataFrame()

    pedacos = []
    for arq in sorted(arquivos):
        try:
            if arq.suffix.lower() == ".csv":
                tabela = pd.read_csv(arq, sep=None, engine="python", encoding="latin1", header=HEADER_LINHA)
            else:
                tabela = pd.read_excel(arq, header=HEADER_LINHA)
            if tabela.empty:
                print("  [VAZIO]", arq.name)
                continue
            tabela.columns = [str(c).strip() for c in tabela.columns]
            tabela["_Arquivo"] = arq.name
            tabela["_Mtime"] = arq.stat().st_mtime
            pedacos.append(tabela)
            print("  [OK] {}  {} linhas".format(arq.name.ljust(28), len(tabela)))
        except Exception as erro:
            print("  [FALHA] {}: {}".format(arq.name, erro))

    return pd.concat(pedacos, ignore_index=True) if pedacos else pd.DataFrame()


def titulo(texto):
    print()
    print("=" * 78)
    print(texto)
    print("=" * 78)


def main():
    pasta_oper = Path(sys.argv[1]) if len(sys.argv) > 1 else PASTA_OPER_PADRAO
    pasta_hist = Path(sys.argv[2]) if len(sys.argv) > 2 else PASTA_HIST_PADRAO

    agora = datetime.now()
    hoje = agora.date()

    titulo("DIAGNOSTICO DE BACKLOG  -  pedidos abertos fora do mes vigente")
    print("Executado em {:%d/%m/%Y as %H:%M}".format(agora))

    print("\n[1] BASE OPERACIONAL (mes vigente)")
    df_oper = ler_pasta(pasta_oper)

    print("\n[2] BASE HISTORICA (meses anteriores)")
    df_hist = ler_pasta(pasta_hist)

    if df_hist.empty:
        titulo("RESULTADO")
        print("Historico vazio: nao existe backlog recuperavel pelo codigo.")
        return

    col_nf = achar_coluna(df_hist, "NF", "NOTA")
    col_st = achar_coluna(df_hist, "STATUS", "SITUACAO")
    col_rc = achar_coluna(df_hist, "RECEPCAO")
    col_vol = achar_coluna(df_hist, "VOLUMES", "VOLUME", "QTDE")
    col_cli = achar_coluna(df_hist, "CLIENTE")
    col_trp = achar_coluna(df_hist, "TRANSPORTADORA")

    if col_nf is None:
        titulo("ERRO")
        print("Nao localizei a coluna da Nota Fiscal. Cabecalhos encontrados:")
        for coluna in df_hist.columns:
            print("   -", coluna)
        return

    print("\nColunas: NF = {} | Status = {} | Recepcao = {} | Volumes = {}".format(
        col_nf, col_st, col_rc, col_vol))

    df_hist["_Recepcao"] = (pd.to_datetime(df_hist[col_rc], errors="coerce", dayfirst=True)
                            if col_rc else pd.NaT)

    # ---- ETAPA A: a data-referencia de cada arquivo (a "foto") ----
    titulo("ETAPA A  -  Qual foto cada arquivo representa?")
    retrato = df_hist.groupby("_Arquivo")["_Recepcao"].max()
    df_hist["_Retrato"] = df_hist["_Arquivo"].map(retrato)

    sem_data = df_hist["_Retrato"].isna()
    if sem_data.any():
        df_hist.loc[sem_data, "_Retrato"] = pd.to_datetime(df_hist.loc[sem_data, "_Mtime"], unit="s")

    resumo = (df_hist.groupby("_Arquivo")
              .agg(Linhas=("_Arquivo", "size"), Foto=("_Retrato", "max"))
              .sort_values("Foto"))
    for nome, linha in resumo.iterrows():
        print("  {:<30} {:>7} linhas   foto: {}".format(nome, linha["Linhas"],
                                                        linha["Foto"].strftime("%d/%m/%Y")))

    # ---- ETAPA B: uma linha por nota, ficando com a foto mais recente ----
    titulo("ETAPA B  -  Notas unicas no historico")
    df_hist["_NF"] = chave_nota(df_hist[col_nf])
    brutas = len(df_hist)
    df_hist = (df_hist.sort_values(["_Retrato", "_Mtime"])
                      .drop_duplicates(subset="_NF", keep="last"))
    print("  Linhas cruas .............................. {}".format(brutas))
    print("  Notas unicas (foto mais recente de cada) ... {}".format(len(df_hist)))
    print("  Linhas descartadas (fotos repetidas) ...... {}".format(brutas - len(df_hist)))

    # ---- ETAPA C: o operacional vence o historico ----
    titulo("ETAPA C  -  O que ja esta no mes vigente")
    col_nf_oper = achar_coluna(df_oper, "NF", "NOTA") if not df_oper.empty else None

    if col_nf_oper is not None:
        chaves_oper = set(chave_nota(df_oper[col_nf_oper]))
        print("  Notas distintas no relatorio do mes vigente . {}".format(len(chaves_oper)))
    else:
        chaves_oper = set()
        print("  [AVISO] nao localizei a coluna de NF no operacional.")

    ja_no_oper = df_hist["_NF"].isin(chaves_oper)
    print("  Notas do historico JA no operacional ....... {}".format(int(ja_no_oper.sum())))
    print("  Notas orfas (sumiram do relatorio do mes) .. {}".format(int((~ja_no_oper).sum())))
    df_orfas = df_hist[~ja_no_oper].copy()

    # ---- ETAPA D: das orfas, quais continuam abertas? ----
    titulo("ETAPA D  -  Das orfas, quais continuam ABERTAS?")
    df_orfas["_Status_Chave"] = df_orfas[col_st].map(limpar) if col_st else ""
    for status, qtd in df_orfas["_Status_Chave"].value_counts().items():
        marca = "ABERTO" if status in STATUS_ABERTOS else "fechado/ignorado"
        print("    {:<28} {:>7}   [{}]".format(status, qtd, marca))

    divida = df_orfas[df_orfas["_Status_Chave"].isin(STATUS_ABERTOS)].copy()

    # ---- RESULTADO ----
    titulo("RESULTADO  -  A DIVIDA REAL")
    print("  Notas abertas fora do mes vigente: {}".format(len(divida)))

    if divida.empty:
        print("\n  Nada ficou para tras. O painel atual nao esta escondendo pendencia.")
        return

    divida["_Vol"] = (pd.to_numeric(divida[col_vol], errors="coerce").fillna(0)
                      if col_vol else 0)
    diferenca = hoje - divida["_Recepcao"].dt.date
    divida["_Dias"] = diferenca.apply(lambda delta: delta.days if pd.notna(delta) else None)

    mais_antiga = divida.sort_values("_Dias", ascending=False).iloc[0]
    print("  Volume total parado ............... {:.0f}".format(divida["_Vol"].sum()))
    print("  Nota mais antiga .................. {}  {}".format(
        mais_antiga["_NF"],
        mais_antiga["_Recepcao"].strftime("(entrada %d/%m/%Y)") if pd.notna(mais_antiga["_Recepcao"]) else ""))
    media = divida["_Dias"].dropna().mean()
    print("  Idade media ....................... {:.0f} dias".format(media if pd.notna(media) else 0))
    print("  Notas sem data de recepcao ........ {}".format(int(divida["_Dias"].isna().sum())))

    print("\n  --- Por faixa de idade ---")
    for inicio, fim, rotulo in FAIXAS:
        faixa = divida[(divida["_Dias"] >= inicio) & (divida["_Dias"] <= fim)]
        if len(faixa):
            print("    {:<16} {:>5} notas   {:>10.0f} volumes".format(
                rotulo, len(faixa), faixa["_Vol"].sum()))

    print("\n  --- Por status (a divida) ---")
    for status, qtd in divida["_Status_Chave"].value_counts().items():
        print("    {:<28} {:>5} notas".format(status, qtd))

    print("\n  --- De qual foto vem a divida ---")
    for mes, qtd in divida["_Retrato"].dt.strftime("%m/%Y").value_counts().sort_index().items():
        print("    foto de {:<9} {:>5} notas".format(mes, qtd))

    if col_cli:
        print("\n  --- Top 5 clientes ---")
        top = (divida.groupby(col_cli)
               .agg(Notas=("_NF", "size"), Volumes=("_Vol", "sum"), Mais_Antiga=("_Recepcao", "min"))
               .sort_values("Notas", ascending=False).head(5))
        for cliente, linha in top.iterrows():
            print("    {:<28} {:>4} notas  {:>9.0f} vol  desde {}".format(
                str(cliente)[:28], linha["Notas"], linha["Volumes"],
                linha["Mais_Antiga"].strftime("%d/%m/%Y") if pd.notna(linha["Mais_Antiga"]) else "-"))

    if col_trp:
        print("\n  --- Top 5 transportadoras ---")
        top = (divida.groupby(col_trp)
               .agg(Notas=("_NF", "size"), Volumes=("_Vol", "sum"))
               .sort_values("Notas", ascending=False).head(5))
        for trp, linha in top.iterrows():
            print("    {:<28} {:>4} notas  {:>9.0f} vol".format(str(trp)[:28], linha["Notas"], linha["Volumes"]))

    print("\n  --- As 15 mais antigas ---")
    for _, linha in divida.sort_values("_Dias", ascending=False).head(15).iterrows():
        data_txt = linha["_Recepcao"].strftime("%d/%m/%Y") if pd.notna(linha["_Recepcao"]) else "--/--/----"
        print("    NF {:<12} {:<11} {:<10} {:<26} {}".format(
            str(linha["_NF"]), "D-" + str(int(linha["_Dias"])) if pd.notna(linha["_Dias"]) else "sem data",
            data_txt,
            str(linha[col_st])[:26] if col_st else "",
            str(linha[col_cli])[:26] if col_cli else ""))

    print("\n" + "=" * 78)
    print("FIM. Nenhum arquivo foi alterado.")
    print("=" * 78)


if __name__ == "__main__":
    main()
