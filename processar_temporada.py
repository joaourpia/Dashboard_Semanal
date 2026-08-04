# -*- coding: utf-8 -*-
"""
================================================================================
 ETL - ENTREGA DIARIA E ABSENTEISMO | TEMPORADA DE JULHO/2026
 Mendes RH  x  Aviva / Rio Quente Resorts
================================================================================

ENTRADAS  (pasta  dados/temporada_julho/entrada/)
  sth_temporada.xlsx    -> DEMANDA : quantidade solicitada por funcao x dia.
                           Usa-se APENAS cargo, data inicial, data final e
                           status. Nome do temporario e ignorado de proposito.
  ponto_julho_2026.csv  -> ENTREGA : espelho de ponto (todos os temporarios).

REGRA DE NEGOCIO (definida pelo cliente)
  Nao entregue no dia = SOMENTE quando o espelho traz explicitamente "Falta".
  Entregue no dia     = bateu ponto OU folga OU atestado OU outra justificativa.
  Fora do contrato    = celula "-" ou vazia (admissao posterior/desligamento).
  Classificacao validada contra o Resumo_Ponto do cliente: 177/177 pessoas OK.

INDICADORES
  Solicitado    : vagas do STH ativas no dia, excluidas as canceladas.
  Entregue      : Trabalhou + Folga + Atestado + Outra justificativa.
  Falta         : dias marcados como falta.
  Absenteismo % : Falta / (Entregue + Falta).
  Cobertura %   : Entregue / Solicitado.
  Em posto %    : Trabalhou / Solicitado.

SAIDAS  (pasta dados/temporada_julho/)
  ABSENTEISMO_DIA_FUNCAO.csv | ABSENTEISMO_DIA_TOTAL.csv
  ABSENTEISMO_FUNCAO.csv     | RESUMO_TEMPORADA.csv | CONCILIACAO_STH.csv
================================================================================
"""
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
PASTA = BASE / "dados" / "temporada_julho"
ENTRADA = PASTA / "entrada"
PASTA.mkdir(parents=True, exist_ok=True)
ENTRADA.mkdir(parents=True, exist_ok=True)

ANO, MES = 2026, 7
DIAS = pd.date_range(f"{ANO}-{MES:02d}-01", periods=31, freq="D")
DIA_SEMANA = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sab", 6: "Dom"}

ARQ_STH = "sth_temporada.xlsx"
ARQ_PONTO = "ponto_julho_2026.csv"
# Espelhos complementares (contratacoes pontuais). Qualquer arquivo .xlsx cujo
# nome comece com "diaristas" e lido automaticamente. Nesses espelhos SO conta
# dia efetivamente trabalhado - falta e atestado nao entram em nenhum indicador.
PADRAO_COMPLEMENTAR = "diaristas*.xlsx"


# ------------------------------------------------------------------ utilitarios
def norm(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"\s+", " ", s).upper().strip()
    return "" if s in ("NAN", "NAT", "NONE", "-") else s


def so_digitos(x) -> str:
    d = re.sub(r"\D", "", str(x))
    return d.zfill(11) if d else ""


# De-para entre a nomenclatura do STH (requisicao) e a da folha/ponto (CLT).
# Chave sem acento e em caixa alta; valor = nome canonico exibido no painel.
MAPA_FUNCAO = {
    # requisicao (STH)                  # folha (ponto)
    "OPERADOR DE ATRACOES": "Atendente de Parque",
    "ATENDENTE DE PARQUE": "Atendente de Parque",
    "GARCOM": "Garçom",
    "GARCONETE": "Garçom",
    "RECEPCIONISTA DE PARQUES": "Recepcionista de Parques",
    "RECEPCIONISTA": "Recepcionista de Parques",
    "AUXILIAR SERVICOS GERAIS": "Aux. Serviços Gerais / Limpeza",
    "AUXILIAR DE SERVICOS GERAIS": "Aux. Serviços Gerais / Limpeza",
    "AUX SERVICOS GERAIS": "Aux. Serviços Gerais / Limpeza",
    "AUXILIAR DE LIMPEZA": "Aux. Serviços Gerais / Limpeza",
    "AUXILIAR OPERACIONAL": "Aux. Serviços Gerais / Limpeza",
    "AJUDANTE COZINHA": "Auxiliar de Cozinha",
    "AJUDANTE DE COZINHA": "Auxiliar de Cozinha",
    "AUXILIAR DE COZINHA": "Auxiliar de Cozinha",
    "AUXILIAR COZINHA": "Auxiliar de Cozinha",
    "MONITOR DE LAZER E RECREACAO": "Monitor de Lazer e Recreação",
    "MONITOR DE LAZER E RECREACAO I": "Monitor de Lazer e Recreação",
    "MONITOR DE LAZER": "Monitor de Lazer e Recreação",
    "ATENDENTE DE HOTELARIA": "Atendente de Hotelaria",
    "CAMAREIRA": "Camareira",
    "CAMAREIRO": "Camareira",
    "VENDEDOR INTERNO": "Vendedor Interno",
    "VENDEDORA": "Vendedor Interno",
    "VENDEDOR": "Vendedor Interno",
    "AUXILIAR DE LAVANDERIA": "Auxiliar de Lavanderia",
    "AUXILIAR LAVANDERIA": "Auxiliar de Lavanderia",
    "ATENDENTE DE PORTARIA": "Atendente de Portaria",
    "PORTEIRO": "Atendente de Portaria",
    "OPERADOR DE LAVA-JATO": "Operador de Lava-Jato",
    "OPERADOR DE LAVA JATO": "Operador de Lava-Jato",
    "CONCIERGE": "Concierge",
    "ROUPEIRO": "Roupeiro",
    "ROUPEIRA": "Roupeiro",
    "GUIA DE FERIAS": "Guia de Férias",
    "ASSISTENTE ADMINISTRATIVO": "Assistente Administrativo",
    "COORDENADOR": "Coordenador",
}


def funcao_canonica(cargo) -> str:
    c = norm(cargo)
    if not c:
        return "Não informado"
    return MAPA_FUNCAO.get(c, str(cargo).strip().title())


# ------------------------------------------------------------------ 1) DEMANDA
def carregar_sth() -> pd.DataFrame:
    sth = pd.read_excel(ENTRADA / ARQ_STH, header=1)
    sth.columns = [str(c).strip() for c in sth.columns]

    ini = pd.to_datetime(sth["DATA INICIAL"], errors="coerce")
    fim = pd.to_datetime(sth["DATA FINAL"], errors="coerce")
    # STH 27749 chega com a data inicial preenchida como texto ("STH");
    # as demais vagas do mesmo lote iniciam em 01/07 - assumimos o lote.
    sth["_ini"] = ini.fillna(pd.Timestamp(f"{ANO}-{MES:02d}-01"))
    sth["_fim"] = fim.fillna(pd.Timestamp(f"{ANO}-{MES:02d}-31"))
    sth["_status"] = sth["STATUS VAGA"].map(norm)
    sth["Funcao"] = sth["CARGO"].map(funcao_canonica)
    return sth


def expandir_demanda(sth: pd.DataFrame):
    ativas = sth[sth["_status"] != "CANCELADO"]
    linhas = []
    for _, r in ativas.iterrows():
        for d in DIAS:
            if r["_ini"] <= d <= r["_fim"]:
                linhas.append({"Dia": d, "Funcao": r["Funcao"], "STH": r["N° STH"],
                               "CCusto": r.get("CCUSTO"), "BU": r.get("BU")})
    det = pd.DataFrame(linhas)
    dem = det.groupby(["Dia", "Funcao"]).size().rename("Solicitado").reset_index()
    return dem, det


# ------------------------------------------------------------------ 2) ENTREGA
COLS_PONTO = ["Entrada 1", "Saída 1", "Entrada 2", "Saída 2"]
RE_HORA = re.compile(r"\d{1,2}:\d{2}")

ST_TRAB, ST_FOLGA, ST_ATEST = "Trabalhou", "Folga", "Atestado"
ST_JUST, ST_FALTA, ST_FORA = "Outra justificativa", "Falta", "Fora do contrato"
ORDEM = [ST_TRAB, ST_FOLGA, ST_ATEST, ST_JUST, ST_FALTA, ST_FORA]


def classificar(vals) -> str:
    vals = [str(v).strip() for v in vals]
    txt = " | ".join(vals).lower()
    if all(v in ("", "-", "nan") for v in vals):
        return ST_FORA
    if RE_HORA.search(txt):
        return ST_TRAB          # regra do cliente: bateu ponto = trabalhado
    if "falta" in txt:
        return ST_FALTA
    if "folga" in txt:
        return ST_FOLGA
    if "atestado" in txt:
        return ST_ATEST
    if "justificado" in txt:
        return ST_JUST
    return ST_FORA


def carregar_ponto() -> pd.DataFrame:
    p = pd.read_csv(ENTRADA / ARQ_PONTO, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    p.columns = [str(c).strip() for c in p.columns]
    p["Dia"] = pd.to_datetime(p["Dia"].str.extract(r"(\d{2}/\d{2}/\d{4})")[0], format="%d/%m/%Y")
    p["Funcao"] = p["Nome do cargo"].map(funcao_canonica)
    p["Status"] = p[COLS_PONTO].apply(classificar, axis=1)
    p["Nome"] = p["Nome do funcionário"].str.strip()
    p["_cpf"] = p["CPF do funcionário"].map(so_digitos)
    p["Departamento"] = p["Nome do departamento"].str.strip()
    p["So_trabalho"] = False
    return p


def carregar_complementares() -> pd.DataFrame:
    """Espelhos de contratacoes pontuais: apenas dias efetivamente trabalhados."""
    frames = []
    for arq in sorted(ENTRADA.glob(PADRAO_COMPLEMENTAR)):
        d = pd.read_excel(arq)
        d.columns = [str(c).strip() for c in d.columns]
        for c in COLS_PONTO:
            d[c] = d.get(c, "").fillna("").astype(str)
        d["Dia"] = pd.to_datetime(d["Dia"].astype(str).str.extract(r"(\d{2}/\d{2}/\d{4})")[0],
                                  format="%d/%m/%Y")
        d["Funcao"] = d["Nome do cargo"].map(funcao_canonica)
        tem_hora = d[COLS_PONTO].apply(
            lambda r: bool(RE_HORA.search(" | ".join(str(v) for v in r))), axis=1)
        d["Status"] = np.where(tem_hora, ST_TRAB, ST_FORA)
        d["Nome"] = d["Nome do funcionário"].astype(str).str.strip()
        d["_cpf"] = d["CPF do funcionário"].map(so_digitos)
        d["Departamento"] = d.get("Nome do departamento", "").astype(str).str.strip()
        d["So_trabalho"] = True
        frames.append(d[["Dia", "Funcao", "Status", "Nome", "_cpf", "Departamento", "So_trabalho"]])
    if not frames:
        return pd.DataFrame(columns=["Dia", "Funcao", "Status", "Nome", "_cpf",
                                     "Departamento", "So_trabalho"])
    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------- 3) CONSOLIDACAO
def consolidar(demanda: pd.DataFrame, ponto: pd.DataFrame) -> pd.DataFrame:
    piv = (ponto.pivot_table(index=["Dia", "Funcao"], columns="Status",
                             values="Nome", aggfunc="count")
           .reindex(columns=ORDEM).fillna(0).astype(int).reset_index())

    df = demanda.merge(piv, on=["Dia", "Funcao"], how="outer")
    for c in ORDEM:
        df[c] = df[c].fillna(0).astype(int)
    df["Solicitado"] = df["Solicitado"].fillna(0).astype(int)
    df["Dia"] = pd.to_datetime(df["Dia"])

    # Entregue reune trabalhado + folga + atestado + demais justificativas
    df["Entregue"] = df[[ST_TRAB, ST_FOLGA, ST_ATEST, ST_JUST]].sum(axis=1)
    df["Escala"] = df["Entregue"] + df[ST_FALTA]
    df["Absenteismo_%"] = np.where(df["Escala"] > 0, df[ST_FALTA] / df["Escala"] * 100, np.nan)
    df["Cobertura_%"] = np.where(df["Solicitado"] > 0, df["Entregue"] / df["Solicitado"] * 100, np.nan)
    df["Em_posto_%"] = np.where(df["Solicitado"] > 0, df[ST_TRAB] / df["Solicitado"] * 100, np.nan)
    df["Saldo"] = df["Entregue"] - df["Solicitado"]
    df["DiaNum"] = df["Dia"].dt.day
    df["DiaSemana"] = df["Dia"].dt.dayofweek.map(DIA_SEMANA)
    df["FimDeSemana"] = df["Dia"].dt.dayofweek >= 5
    return df.sort_values(["Dia", "Funcao"]).reset_index(drop=True)


SOMAS = ["Solicitado", "Entregue", "Escala", ST_TRAB, ST_FOLGA, ST_ATEST, ST_JUST, ST_FALTA]


def agregar(df: pd.DataFrame, chaves) -> pd.DataFrame:
    g = df.groupby(chaves, dropna=False)[SOMAS].sum().reset_index()
    g["Absenteismo_%"] = g[ST_FALTA] / g["Escala"].replace(0, np.nan) * 100
    g["Cobertura_%"] = g["Entregue"] / g["Solicitado"].replace(0, np.nan) * 100
    g["Em_posto_%"] = g[ST_TRAB] / g["Solicitado"].replace(0, np.nan) * 100
    g["Saldo"] = g["Entregue"] - g["Solicitado"]
    return g


def salvar(df: pd.DataFrame, nome: str):
    df.to_csv(PASTA / nome, sep=";", decimal=",", index=False, encoding="utf-8-sig")


# ------------------------------------------------------------------- 4) MAIN
def main(verbose=True):
    sth = carregar_sth()
    demanda, _ = expandir_demanda(sth)
    ponto = carregar_ponto()
    extra = carregar_complementares()
    if len(extra):
        ponto = pd.concat([ponto, extra], ignore_index=True)

    # Funcoes sem nenhuma vaga no STH da temporada nao fazem parte do escopo
    # (efetivos/outros contratos que aparecem no mesmo espelho de ponto).
    escopo = set(demanda["Funcao"])
    fora = sorted(set(ponto["Funcao"]) - escopo)
    ponto_escopo = ponto[ponto["Funcao"].isin(escopo)].copy()

    det = consolidar(demanda, ponto_escopo)
    salvar(det, "ABSENTEISMO_DIA_FUNCAO.csv")
    salvar(agregar(det, ["Dia", "DiaNum", "DiaSemana", "FimDeSemana"]), "ABSENTEISMO_DIA_TOTAL.csv")
    salvar(agregar(det, ["Funcao"]).sort_values("Solicitado", ascending=False),
           "ABSENTEISMO_FUNCAO.csv")
    resumo = agregar(det, [lambda _: "TOTAL"]) if False else agregar(det.assign(_k="TOTAL"), ["_k"])
    salvar(resumo, "RESUMO_TEMPORADA.csv")

    # ------------------------------------------------ conciliacao (fora do app)
    conc = agregar(det, ["Funcao"]).sort_values("Solicitado", ascending=False)
    conc["Alerta"] = np.where(
        conc["Cobertura_%"] > 130, "STH registra menos diárias do que o ponto comprova",
        np.where(conc["Cobertura_%"] < 80, "Entrega abaixo do solicitado", ""))
    for f in fora:
        n = ponto.loc[ponto["Funcao"] == f, "Nome"].nunique()
        conc = pd.concat([conc, pd.DataFrame([{
            "Funcao": f, "Solicitado": 0,
            "Alerta": f"Fora do escopo: {n} pessoa(s) no ponto sem vaga no STH"}])],
            ignore_index=True)
    salvar(conc, "CONCILIACAO_STH.csv")

    if verbose:
        if len(extra):
            trab = int((extra["Status"] == ST_TRAB).sum())
            print(f"\n  + {extra['Nome'].nunique()} espelhos complementares: "
                  f"{trab} diárias trabalhadas somadas à entrega.")
        r = resumo.iloc[0]
        print("\n" + "=" * 66)
        print(f"  TEMPORADA {MES:02d}/{ANO}  ·  {ponto_escopo['Nome'].nunique()} temporários no escopo")
        print("=" * 66)
        print(f"  Solicitado (STH) ....... {r.Solicitado:>6.0f} diárias")
        print(f"  Entregue ............... {r.Entregue:>6.0f} diárias   "
              f"(trab {r[ST_TRAB]:.0f} + folga {r[ST_FOLGA]:.0f} + atest {r[ST_ATEST]:.0f}"
              f" + outras {r[ST_JUST]:.0f})")
        print(f"  Faltas ................. {r[ST_FALTA]:>6.0f} diárias")
        print(f"  Cobertura .............. {r['Cobertura_%']:>6.1f}%")
        print(f"  Absenteísmo ............ {r['Absenteismo_%']:>6.2f}%")
        if fora:
            print(f"\n  Fora do escopo (função sem vaga no STH): {', '.join(fora)}")
        alertas = conc[conc["Alerta"] != ""]
        if len(alertas):
            print("\n  Conciliação STH x ponto (ver CONCILIACAO_STH.csv):")
            for _, a in alertas.iterrows():
                print(f"    - {a.Funcao}: {a.Alerta}")
        print("\n  Arquivos em", PASTA, "\n")
    return det


if __name__ == "__main__":
    main()
