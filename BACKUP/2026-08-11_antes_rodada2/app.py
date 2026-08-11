# -*- coding: utf-8 -*-
"""
================================================================================
 DASHBOARD DE GESTAO DE TEMPORARIOS
 Mendes RH  x  Aviva / Rio Quente Resorts
================================================================================
Abas: Visao Geral | Analise SLA | Diarias | Historico | Temporada (sazonal)

Estrutura esperada em  dados/<pasta da semana>/ :
  SLA.csv               Mes;Solicitado;No_prazo;Fora_prazo;taxa
  ANALISE_PEDIDO.csv    Mes;Solicitado;Entregue;Taxa
  HISTORICO_SLA.csv     Mes;Taxa
  HISTORICO_ENTREGA.csv Mes;Solicitado;Entregue;Taxa
================================================================================
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ui_dashboard as ui
import relatorio_pdf

st.set_page_config(page_title="Dashboard Operacional Mendes RH", layout="wide",
                   initial_sidebar_state="collapsed")
ui.aplicar_css()

# --------------------------------------------------------------------- metas
META_SLA = 100.0        # % de vagas fechadas dentro do prazo
META_DIARIA = 100.0     # % de diarias entregues sobre solicitadas

# Antecedencia media com que as requisicoes (STH) chegam ao RH. Usada nos
# textos de analise para posicionar corretamente o gargalo: com o pedido
# chegando com folga, o atraso nao vem do aviso e sim da captacao/admissao.
ANTECEDENCIA_PEDIDO_DIAS = 20

base_dados = Path(__file__).resolve().parent / "dados"

# ---------------------------------------------------------------------------
# ABAS OPCIONAIS
# ---------------------------------------------------------------------------
# A aba da temporada e sazonal. Controle aqui se ela aparece na apresentacao:
#   "auto"  -> aparece so enquanto existir a base em dados/temporada_julho/
#   True    -> forca exibir
#   False   -> esconde (use isto a partir de agosto)
# Alternativa sem mexer no codigo: renomear dados/temporada_julho para
# dados/_temporada_julho.
MOSTRAR_TEMPORADA = "auto"
ABA_TEMPORADA = "Temporada Julho"

_base_temp = base_dados / "temporada_julho" / "ABSENTEISMO_DIA_FUNCAO.csv"
MOSTRAR_TEMPORADA = (_base_temp.exists() if MOSTRAR_TEMPORADA == "auto"
                     else bool(MOSTRAR_TEMPORADA))

# A aba da pesquisa aparece enquanto existir a base exportada do Google Forms
# em dados/pesquisa/RESPOSTAS_PESQUISA.xlsx. Mesma logica da aba da temporada.
MOSTRAR_PESQUISA = "auto"
ABA_PESQUISA = "Pesquisa"

_base_pesq = base_dados / "pesquisa" / "RESPOSTAS_PESQUISA.xlsx"
MOSTRAR_PESQUISA = (_base_pesq.exists() if MOSTRAR_PESQUISA == "auto"
                    else bool(MOSTRAR_PESQUISA))

PASTAS_RESERVADAS = {"solicitacoes", "temporada_julho", "pesquisa"}


# ------------------------------------------------------------------- leitura
def safe_read_csv(caminho):
    for kw in (dict(sep=";", decimal=",", encoding="latin1"),
               dict(sep=";", decimal=",", encoding="utf-8-sig"),
               dict(sep=",", decimal=".", encoding="utf-8")):
        try:
            df = pd.read_csv(caminho, **kw)
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    return None


def obter_periodos():
    if not base_dados.exists():
        return []
    pastas = [i.name for i in base_dados.iterdir()
              if i.is_dir() and i.name.lower() not in PASTAS_RESERVADAS
              and not i.name.startswith((".", "_"))]
    if any(base_dados.glob("*.csv")) and "." not in pastas:
        pastas.append(".")
    return sorted(pastas, reverse=True)


periodos_disponiveis = obter_periodos()
if not periodos_disponiveis:
    lista_opcoes = ["Nenhuma pasta de dados encontrada"]
else:
    lista_opcoes = ["Acumulado (Todas as Semanas)"] + [p for p in periodos_disponiveis if p != "."]
    if "." in periodos_disponiveis and len(periodos_disponiveis) == 1:
        lista_opcoes = ["Dados Atuais (Arquivos soltos na Raiz)"]

# ------------------------------------------------------------------ cabecalho
_logo = ui.logo_b64(Path(__file__).resolve().parent / "images" / "Logo_Parceria.png")
logo_html = (f'<div class="app-logo"><img src="data:image/png;base64,{_logo}"></div>'
             if _logo else "")

with st.container(border=True):
    c_tit, c_logo, c_filtro = st.columns([2.6, 2.6, 1.6], vertical_alignment="center")
    with c_tit:
        st.markdown("<div class='app-head'><h1>Dashboard Gestão de Temporários</h1>"
                    "<div class='sub'>Mendes RH · Aviva / Rio Quente Resorts</div></div>",
                    unsafe_allow_html=True)
    with c_logo:
        st.markdown(logo_html, unsafe_allow_html=True)
    with c_filtro:
        periodo_selecionado = st.selectbox("Filtro de Período:", lista_opcoes,
                                           label_visibility="collapsed")


def obter_caminhos_alvo():
    if periodo_selecionado == "Nenhuma pasta de dados encontrada":
        return []
    if periodo_selecionado == "Acumulado (Todas as Semanas)":
        reais = [p for p in periodos_disponiveis if p != "."]
        return reais if reais else ["."]
    if periodo_selecionado == "Dados Atuais (Arquivos soltos na Raiz)":
        return ["."]
    return [periodo_selecionado]


# ------------------------------------------------------------------- navegacao
tab_names = ["Visão Geral", "Análise SLA", "Diárias", "Histórico Mensal"]
if MOSTRAR_TEMPORADA:
    tab_names.append(ABA_TEMPORADA)
if MOSTRAR_PESQUISA:
    tab_names.append(ABA_PESQUISA)
if "current_tab" not in st.session_state:
    st.session_state.current_tab = tab_names[0]
if st.session_state.current_tab not in tab_names:
    st.session_state.current_tab = tab_names[0]


def set_tab(tab):
    st.session_state.current_tab = tab


tab_cols = st.columns(len(tab_names))
for i, tab in enumerate(tab_names):
    tab_cols[i].button(tab, key=tab, on_click=set_tab, args=(tab,), use_container_width=True,
                       type="primary" if st.session_state.current_tab == tab else "secondary")


# ------------------------------------------------------------- agregacoes
def _caminho(p, arquivo):
    return (base_dados / arquivo) if p == "." else (base_dados / p / arquivo)


def load_sla_agregado(alvos):
    linhas = []
    for p in alvos:
        c = _caminho(p, "SLA.csv")
        if c.exists():
            df = safe_read_csv(c)
            if df is not None and not df.empty:
                linhas.append({"Periodo": p,
                               "Solicitado": float(df["Solicitado"].iloc[0]),
                               "No_prazo": float(df["No_prazo"].iloc[0]),
                               "Fora_prazo": float(df["Fora_prazo"].iloc[0])})
    det = pd.DataFrame(linhas)
    if det.empty:
        return pd.DataFrame({"Solicitado": [0.0], "No_prazo": [0.0],
                             "Fora_prazo": [0.0], "taxa": [0.0]}), det
    tot = det[["Solicitado", "No_prazo", "Fora_prazo"]].sum()
    taxa = tot.No_prazo / tot.Solicitado if tot.Solicitado else 0
    det["Taxa_%"] = det.No_prazo / det.Solicitado.replace(0, np.nan) * 100
    det = det.sort_values("Periodo").reset_index(drop=True)
    return pd.DataFrame({"Solicitado": [tot.Solicitado], "No_prazo": [tot.No_prazo],
                         "Fora_prazo": [tot.Fora_prazo], "taxa": [taxa]}), det


def load_analise_pedido_agregado(alvos):
    linhas = []
    for p in alvos:
        c = _caminho(p, "ANALISE_PEDIDO.csv")
        if c.exists():
            df = safe_read_csv(c)
            if df is not None and not df.empty:
                linhas.append({"Periodo": p,
                               "Solicitado": float(df["Solicitado"].iloc[0]),
                               "Entregue": float(df["Entregue"].iloc[0])})
    det = pd.DataFrame(linhas)
    if det.empty:
        return pd.DataFrame({"Solicitado": [0.0], "Entregue": [0.0], "Taxa": [0.0]}), det
    tot = det[["Solicitado", "Entregue"]].sum()
    taxa = tot.Entregue / tot.Solicitado if tot.Solicitado else 0
    det["Taxa_%"] = det.Entregue / det.Solicitado.replace(0, np.nan) * 100
    det = det.sort_values("Periodo").reset_index(drop=True)
    return pd.DataFrame({"Solicitado": [tot.Solicitado], "Entregue": [tot.Entregue],
                         "Taxa": [taxa]}), det


def _rotulo_periodo():
    if periodo_selecionado.startswith("Acumulado"):
        return "Acumulado do contrato"
    if periodo_selecionado.startswith("Dados Atuais"):
        return "Período corrente"
    return periodo_selecionado


def _sem_dados():
    st.info("Não há arquivos para o período selecionado. Verifique a pasta em `dados/`.")


# ============================================================== VISÃO GERAL
def construir_visao_geral(alvos):
    sec = {"titulo": "Visão Geral", "sub": _rotulo_periodo(), "blocos": []}
    if not alvos:
        return sec
    sla, sla_det = load_sla_agregado(alvos)
    ped, ped_det = load_analise_pedido_agregado(alvos)
    if sla["Solicitado"].iloc[0] == 0 and ped["Solicitado"].iloc[0] == 0:
        return sec

    tot_v = int(sla.Solicitado.iloc[0])
    no_p = int(sla.No_prazo.iloc[0])
    fora = int(sla.Fora_prazo.iloc[0])
    t_sla = sla.taxa.iloc[0] * 100
    sol_d = int(ped.Solicitado.iloc[0])
    ent_d = int(ped.Entregue.iloc[0])
    t_dia = ped.Taxa.iloc[0] * 100
    saldo = ent_d - sol_d
    gap = sol_d - ent_d

    sec["blocos"].append({
        "t": "hero", "titulo": "Visão geral da operação",
        "sub": f"{_rotulo_periodo()} · {len(alvos)} período(s) consolidado(s)",
        "chip": "Fonte: controle de STH e apontamento de diárias",
        "tiles": [
            {"lb": "Vagas solicitadas", "vl": ui.fmt(tot_v),
             "sb": "pedidos abertos via STH no período",
             "spark": ui.sparkline(sla_det.Solicitado) if len(sla_det) > 1 else ""},
            {"lb": "SLA de fechamento", "vl": ui.pc(t_sla),
             "sb": f"{ui.fmt(no_p)} no prazo · {ui.fmt(fora)} fora",
             "spark": ui.sparkline(sla_det["Taxa_%"]) if len(sla_det) > 1 else "",
             "badge": f"meta {ui.pc(META_SLA, 0)}"},
            {"lb": "Diárias entregues", "vl": ui.fmt(ent_d),
             "sb": f"sobre {ui.fmt(sol_d)} solicitadas",
             "spark": ui.sparkline(ped_det.Entregue) if len(ped_det) > 1 else ""},
            {"lb": "Atendimento de diárias", "vl": ui.pc(t_dia),
             "sb": ("saldo de +" + ui.fmt(saldo)) if saldo >= 0
                   else ("déficit de " + ui.fmt(abs(saldo))),
             "spark": ui.sparkline(ped_det["Taxa_%"]) if len(ped_det) > 1 else "",
             "badge": f"meta {ui.pc(META_DIARIA, 0)}"}]})

    # rosca de SLA
    fig_sla = go.Figure(go.Pie(
        labels=["No prazo", "Fora do prazo"], values=[no_p, fora], hole=0.62,
        sort=False, direction="clockwise",
        marker=dict(colors=[ui.S3, ui.CRIT], line=dict(color=ui.SURF, width=2)),
        texttemplate="<b>%{percent:.1%}</b>", textposition="auto",
        insidetextorientation="horizontal", textfont=dict(color="#fff", size=14),
        outsidetextfont=dict(color=ui.INK, size=12),
        hovertemplate="%{label}: %{value:,.0f} vagas (%{percent:.1%})<extra></extra>"))
    fig_sla.add_annotation(
        text=f"<b>{ui.fmt(tot_v)}</b><br>"
             f"<span style='font-size:11px;color:{ui.MUTED}'>vagas</span>",
        showarrow=False, font=dict(size=24, color=ui.INK), x=0.5, y=0.5)
    ui.layout(fig_sla, 300, hover="closest")
    fig_sla.update_layout(legend=dict(orientation="h", y=-0.04, x=0.5, xanchor="center"),
                          margin=dict(l=10, r=10, t=34, b=10),
                          uniformtext=dict(minsize=10, mode="show"))

    # barras de diárias
    fig_dia = go.Figure()
    fig_dia.add_trace(go.Bar(x=["Solicitadas"], y=[sol_d], name="Solicitadas",
                             marker=dict(color=ui.S1, line=dict(color=ui.SURF, width=1)),
                             text=[f"<b>{ui.fmt(sol_d)}</b>"], textposition="outside",
                             textfont=dict(size=13, color=ui.INK), cliponaxis=False,
                             hovertemplate="Solicitadas: %{y:,.0f}<extra></extra>"))
    fig_dia.add_trace(go.Bar(x=["Entregues"], y=[ent_d], name="Entregues",
                             marker=dict(color=ui.S3, line=dict(color=ui.SURF, width=1)),
                             text=[f"<b>{ui.fmt(ent_d)}</b>"], textposition="outside",
                             textfont=dict(size=13, color=ui.INK), cliponaxis=False,
                             hovertemplate="Entregues: %{y:,.0f}<extra></extra>"))
    ui.layout(fig_dia, 300, legenda=False, ytitulo="diárias", hover="closest")
    fig_dia.update_layout(bargap=0.45,
                          yaxis=dict(range=[0, max(sol_d, ent_d) * 1.2], gridcolor=ui.GRID,
                                     tickfont=dict(color=ui.MUTED, size=10.5),
                                     title=dict(text="diárias",
                                                font=dict(size=10.5, color=ui.MUTED))))
    if gap > 0:
        extra = [{"html": f"Faltaram <b>{ui.fmt(gap)} diárias</b> para cobrir integralmente "
                          f"a demanda do período.", "estilo": "warn"}]
    else:
        extra = [{"html": f"Demanda coberta integralmente, com <b>{ui.fmt(abs(gap))} diárias</b> "
                          f"acima do solicitado.", "estilo": "good"}]

    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Fechamento de vagas no prazo", "kicker": "sla",
          "desc": "Proporção das vagas fechadas dentro do prazo acordado.",
          "fig": fig_sla, "altura": 300}],
        [{"t": "fig", "titulo": "Diárias solicitadas × entregues", "kicker": "volume",
          "desc": "Total de diárias no período selecionado.",
          "fig": fig_dia, "altura": 300, "extras": extra}]]})

    sec["blocos"].append({
        "t": "texto", "titulo": "Leitura da operação", "kicker": "análise",
        "html": f'<div class="note">'
                + _texto_visao_geral(tot_v, no_p, fora, t_sla, sol_d, ent_d, t_dia,
                                     sla_det, ped_det) + "</div>"})
    return sec


# =============================================================== ANÁLISE SLA
def construir_analise_sla(alvos):
    sec = {"titulo": "Análise de SLA", "sub": _rotulo_periodo(), "blocos": []}
    if not alvos:
        return sec
    sla, det = load_sla_agregado(alvos)
    if sla["Solicitado"].iloc[0] == 0:
        return sec

    total = int(sla.Solicitado.iloc[0])
    dentro = int(sla.No_prazo.iloc[0])
    fora = int(sla.Fora_prazo.iloc[0])
    p_dentro = dentro / total * 100
    p_fora = fora / total * 100

    sec["blocos"].append({
        "t": "hero", "titulo": "Análise de SLA",
        "sub": f"{_rotulo_periodo()} · fechamento de vagas dentro do prazo",
        "chip": f"Meta contratual de SLA: {ui.pc(META_SLA, 0)}",
        "tiles": [
            {"lb": "Vagas solicitadas", "vl": ui.fmt(total),
             "sb": "pedidos abertos no período",
             "spark": ui.sparkline(det.Solicitado) if len(det) > 1 else ""},
            {"lb": "Fechadas no prazo", "vl": ui.fmt(dentro), "sb": f"{ui.pc(p_dentro)} do total",
             "spark": ui.sparkline(det.No_prazo) if len(det) > 1 else ""},
            {"lb": "Fora do prazo", "vl": ui.fmt(fora), "sb": f"{ui.pc(p_fora)} do total",
             "spark": ui.sparkline(det.Fora_prazo) if len(det) > 1 else "",
             "badge": "meta: zero"}]})

    cor = ui.GOOD if p_dentro >= META_SLA else (ui.WARN if p_dentro >= 90 else ui.CRIT)
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=p_dentro,
        number={"suffix": " %", "font": {"size": 40, "color": ui.INK}, "valueformat": ".1f"},
        gauge={"axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": ui.AXIS,
                        "tickfont": {"size": 10, "color": ui.MUTED}},
               "bar": {"color": cor, "thickness": 0.72},
               "bgcolor": "#f2f3f5", "borderwidth": 0,
               "threshold": {"line": {"color": ui.INK2, "width": 2},
                             "thickness": 0.9, "value": META_SLA}}))
    ui.layout(fig_g, 250, legenda=False, hover="closest")
    fig_g.update_layout(margin=dict(l=24, r=24, t=14, b=6), separators=",.")

    if len(det) > 1:
        cores = [ui.GOOD if v >= META_SLA else (ui.WARN if v >= 90 else ui.CRIT)
                 for v in det["Taxa_%"]]
        fig_c = go.Figure(go.Bar(
            x=det.Periodo, y=det["Taxa_%"],
            marker=dict(color=cores, line=dict(color=ui.SURF, width=1)),
            text=[f"<b>{ui.pc(v)}</b>" for v in det["Taxa_%"]],
            textposition="outside", textfont=dict(size=11.5, color=ui.INK), cliponaxis=False,
            customdata=np.stack([det.No_prazo, det.Solicitado], axis=-1),
            hovertemplate="%{x}<br>%{y:.1f}% · %{customdata[0]:,.0f} de "
                          "%{customdata[1]:,.0f} vagas<extra></extra>"))
        fig_c.add_hline(y=META_SLA, line=dict(color=ui.INK2, width=1.2, dash="dash"))
        ui.layout(fig_c, 250, legenda=False, ytitulo="% no prazo", hover="closest")
        fig_c.update_layout(bargap=0.45,
                            yaxis=dict(range=[0, 122], gridcolor=ui.GRID,
                                       tickfont=dict(color=ui.MUTED, size=10.5),
                                       title=dict(text="% no prazo",
                                                  font=dict(size=10.5, color=ui.MUTED))))
        bloco_dir = {"t": "fig", "titulo": "SLA por período", "kicker": "comparativo",
                     "desc": "Cada barra é um período da pasta de dados.",
                     "fig": fig_c, "altura": 250}
    else:
        fig_c = go.Figure()
        for nome, val, c in [("No prazo", dentro, ui.S3), ("Fora do prazo", fora, ui.CRIT)]:
            fig_c.add_trace(go.Bar(
                y=["Vagas"], x=[val], orientation="h", name=nome,
                marker=dict(color=c, line=dict(color=ui.SURF, width=2)),
                text=[f"<b>{ui.fmt(val)}</b>"] if val else [""],
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color="#fff", size=13),
                hovertemplate=f"{nome}: {ui.fmt(val)} vagas<extra></extra>"))
        ui.layout(fig_c, 250, hover="closest")
        fig_c.update_layout(barmode="stack", bargap=0.82,
                            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
                            xaxis=dict(visible=False), yaxis=dict(visible=False))
        bloco_dir = {"t": "fig", "titulo": "Composição do período", "kicker": "detalhe",
                     "fig": fig_c, "altura": 250}

    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "SLA cumprido", "kicker": "indicador",
          "desc": f"Traço escuro no arco: meta de {ui.pc(META_SLA, 0)}.",
          "fig": fig_g, "altura": 250}],
        [bloco_dir]]})

    sec["blocos"].append({
        "t": "texto", "titulo": "Leitura da operação", "kicker": "análise",
        "html": '<div class="note">' + _texto_sla(total, dentro, fora, p_dentro, det) + "</div>"})
    return sec


# ==================================================================== DIÁRIAS
def construir_diarias(alvos):
    sec = {"titulo": "Diárias", "sub": _rotulo_periodo(), "blocos": []}
    if not alvos:
        return sec
    ped, det = load_analise_pedido_agregado(alvos)
    if ped["Solicitado"].iloc[0] == 0:
        return sec

    sol = int(ped.Solicitado.iloc[0])
    ent = int(ped.Entregue.iloc[0])
    taxa = ped.Taxa.iloc[0] * 100
    saldo = ent - sol

    sec["blocos"].append({
        "t": "hero", "titulo": "Diárias",
        "sub": f"{_rotulo_periodo()} · volume contratado × volume entregue",
        "chip": "Fonte: apontamento de diárias por período",
        "tiles": [
            {"lb": "Solicitadas", "vl": ui.fmt(sol), "sb": "diárias contratadas no período",
             "spark": ui.sparkline(det.Solicitado) if len(det) > 1 else ""},
            {"lb": "Entregues", "vl": ui.fmt(ent),
             "sb": ("saldo de +" + ui.fmt(saldo)) if saldo >= 0
                   else ("déficit de " + ui.fmt(abs(saldo))),
             "spark": ui.sparkline(det.Entregue) if len(det) > 1 else ""},
            {"lb": "Taxa de atendimento", "vl": ui.pc(taxa), "sb": "entregues sobre solicitadas",
             "spark": ui.sparkline(det["Taxa_%"]) if len(det) > 1 else "",
             "badge": f"meta {ui.pc(META_DIARIA, 0)}"}]})

    if len(det) > 1:
        fig_v = go.Figure()
        fig_v.add_trace(go.Bar(x=det.Periodo, y=det.Solicitado, name="Solicitadas",
                               marker=dict(color=ui.S1, line=dict(color=ui.SURF, width=1)),
                               text=[ui.fmt(v) for v in det.Solicitado],
                               textposition="outside", textfont=dict(size=11, color=ui.INK2),
                               cliponaxis=False,
                               hovertemplate="Solicitadas: %{y:,.0f}<extra></extra>"))
        fig_v.add_trace(go.Bar(x=det.Periodo, y=det.Entregue, name="Entregues",
                               marker=dict(color=ui.S3, line=dict(color=ui.SURF, width=1)),
                               text=[ui.fmt(v) for v in det.Entregue],
                               textposition="outside", textfont=dict(size=11, color=ui.INK2),
                               cliponaxis=False,
                               hovertemplate="Entregues: %{y:,.0f}<extra></extra>"))
        ui.layout(fig_v, 330, ytitulo="diárias")
        fig_v.update_layout(barmode="group", bargap=0.3, bargroupgap=0.06,
                            yaxis=dict(range=[0, max(det.Solicitado.max(),
                                                     det.Entregue.max()) * 1.22],
                                       gridcolor=ui.GRID,
                                       tickfont=dict(color=ui.MUTED, size=10.5),
                                       title=dict(text="diárias",
                                                  font=dict(size=10.5, color=ui.MUTED))))
        sec["blocos"].append({"t": "fig", "titulo": "Solicitadas × entregues por período",
                              "kicker": "volume",
                              "desc": "Volume de cada período da pasta de dados.",
                              "fig": fig_v, "altura": 330})

        cores = [ui.GOOD if v >= META_DIARIA else (ui.WARN if v >= 90 else ui.CRIT)
                 for v in det["Taxa_%"]]
        fig_t = go.Figure(go.Bar(
            x=det.Periodo, y=det["Taxa_%"],
            marker=dict(color=cores, line=dict(color=ui.SURF, width=1)),
            text=[f"<b>{ui.pc(v)}</b>" for v in det["Taxa_%"]], textposition="outside",
            textfont=dict(size=11.5, color=ui.INK), cliponaxis=False,
            customdata=np.stack([det.Entregue, det.Solicitado], axis=-1),
            hovertemplate="%{x}<br>%{y:.1f}% · %{customdata[0]:,.0f} de "
                          "%{customdata[1]:,.0f}<extra></extra>"))
        fig_t.add_hline(y=META_DIARIA, line=dict(color=ui.INK2, width=1.2, dash="dash"))
        ui.layout(fig_t, 250, legenda=False, ytitulo="% de atendimento", hover="closest")
        fig_t.update_layout(bargap=0.5,
                            yaxis=dict(range=[0, 118], gridcolor=ui.GRID,
                                       tickfont=dict(color=ui.MUTED, size=10.5),
                                       title=dict(text="% de atendimento",
                                                  font=dict(size=10.5, color=ui.MUTED))))
        sec["blocos"].append({"t": "fig", "titulo": "Taxa de atendimento por período",
                              "kicker": "aderência", "fig": fig_t, "altura": 250})
    else:
        fig_v = go.Figure()
        fig_v.add_trace(go.Bar(x=["Solicitadas"], y=[sol], name="Solicitadas",
                               marker=dict(color=ui.S1, line=dict(color=ui.SURF, width=1)),
                               text=[f"<b>{ui.fmt(sol)}</b>"], textposition="outside",
                               textfont=dict(size=13, color=ui.INK), cliponaxis=False,
                               hovertemplate="Solicitadas: %{y:,.0f}<extra></extra>"))
        fig_v.add_trace(go.Bar(x=["Entregues"], y=[ent], name="Entregues",
                               marker=dict(color=ui.S3, line=dict(color=ui.SURF, width=1)),
                               text=[f"<b>{ui.fmt(ent)}</b>"], textposition="outside",
                               textfont=dict(size=13, color=ui.INK), cliponaxis=False,
                               hovertemplate="Entregues: %{y:,.0f}<extra></extra>"))
        ui.layout(fig_v, 320, legenda=False, ytitulo="diárias", hover="closest")
        fig_v.update_layout(bargap=0.5,
                            yaxis=dict(range=[0, max(sol, ent) * 1.2], gridcolor=ui.GRID,
                                       tickfont=dict(color=ui.MUTED, size=10.5),
                                       title=dict(text="diárias",
                                                  font=dict(size=10.5, color=ui.MUTED))))
        sec["blocos"].append({"t": "fig", "titulo": "Solicitadas × entregues",
                              "kicker": "volume", "fig": fig_v, "altura": 320})

    sec["blocos"].append({
        "t": "texto", "titulo": "Leitura da operação", "kicker": "análise",
        "html": '<div class="note">' + _texto_diarias(sol, ent, taxa, saldo, det) + "</div>"})
    return sec


# ================================================================== HISTÓRICO
def _melhor_historico(alvos, arquivo):
    """Entre os períodos-alvo, usa o arquivo de histórico mais completo."""
    melhor, n = None, -1
    for p in alvos:
        c = _caminho(p, arquivo)
        if c.exists():
            df = safe_read_csv(c)
            if df is not None and len(df) > n:
                melhor, n = df, len(df)
    return melhor


def construir_historico(alvos):
    sec = {"titulo": "Histórico do contrato", "sub": "", "blocos": []}
    if not alvos:
        return sec
    sla_hist = _melhor_historico(alvos, "HISTORICO_SLA.csv")
    ent_hist = _melhor_historico(alvos, "HISTORICO_ENTREGA.csv")
    if sla_hist is None or ent_hist is None:
        sec["blocos"].append({"t": "nota", "estilo": "warn",
                              "html": "Arquivos <b>HISTORICO_SLA.csv</b> e "
                                      "<b>HISTORICO_ENTREGA.csv</b> não encontrados nas "
                                      "pastas do período selecionado."})
        return sec

    sla_hist = sla_hist.iloc[:, :2].copy()
    sla_hist.columns = ["Periodo", "Taxa"]
    sla_hist["Taxa"] = sla_hist["Taxa"].map(lambda x: float(str(x).replace(",", ".").strip()))
    sla_hist["No_prazo_%"] = sla_hist["Taxa"] * 100
    sla_hist["Fora_%"] = (1 - sla_hist["Taxa"]) * 100

    ent_hist = ent_hist.iloc[:, :4].copy()
    ent_hist.columns = ["Periodo", "Solicitadas", "Entregues", "Taxa"]
    for c in ("Solicitadas", "Entregues"):
        ent_hist[c] = pd.to_numeric(ent_hist[c], errors="coerce").fillna(0)
    ent_hist["Taxa_%"] = ent_hist["Taxa"].map(lambda x: float(str(x).replace(",", "."))) * 100

    tot_sol = ent_hist.Solicitadas.sum()
    tot_ent = ent_hist.Entregues.sum()
    tx_global = tot_ent / tot_sol * 100 if tot_sol else 0
    sla_medio = sla_hist["No_prazo_%"].mean()
    na_meta = int((sla_hist["No_prazo_%"] >= META_SLA).sum())
    n_per = max(len(ent_hist), len(sla_hist))
    sec["sub"] = f"{n_per} período(s) acompanhado(s)"

    sec["blocos"].append({
        "t": "hero", "titulo": "Histórico do contrato",
        "sub": f"{n_per} período(s) acompanhado(s) · evolução de prazo e volume",
        "chip": "Fonte: histórico acumulado do contrato",
        "tiles": [
            {"lb": "Diárias solicitadas", "vl": ui.fmt(tot_sol), "sb": "acumulado do histórico",
             "spark": ui.sparkline(ent_hist.Solicitadas)},
            {"lb": "Diárias entregues", "vl": ui.fmt(tot_ent),
             "sb": f"{ui.pc(tx_global)} de atendimento",
             "spark": ui.sparkline(ent_hist.Entregues)},
            {"lb": "SLA médio", "vl": ui.pc(sla_medio), "sb": "média dos períodos do histórico",
             "spark": ui.sparkline(sla_hist["No_prazo_%"]),
             "badge": f"meta {ui.pc(META_SLA, 0)}"},
            {"lb": "Períodos com SLA integral", "vl": f"{na_meta} de {len(sla_hist)}",
             "sb": "sem nenhuma vaga fora do prazo"}]})

    cores = [ui.GOOD if v >= META_SLA else (ui.WARN if v >= 90 else ui.CRIT)
             for v in sla_hist["No_prazo_%"]]
    fig1 = go.Figure(go.Bar(
        x=sla_hist.Periodo, y=sla_hist["No_prazo_%"],
        marker=dict(color=cores, line=dict(color=ui.SURF, width=1)),
        text=[f"<b>{ui.pc(v)}</b>" for v in sla_hist["No_prazo_%"]],
        textposition="outside", textfont=dict(size=12, color=ui.INK), cliponaxis=False,
        hovertemplate="%{x}<br>SLA %{y:.1f}%<extra></extra>"))
    fig1.add_hline(y=META_SLA, line=dict(color=ui.INK2, width=1.2, dash="dash"),
                   annotation_text=f"meta {ui.pc(META_SLA, 0)}",
                   annotation_position="top left", annotation_yshift=9,
                   annotation_font=dict(size=10.5, color=ui.MUTED))
    ui.layout(fig1, 330, legenda=False, ytitulo="% no prazo", hover="closest")
    fig1.update_layout(bargap=0.42,
                       yaxis=dict(range=[0, 124], gridcolor=ui.GRID,
                                  tickfont=dict(color=ui.MUTED, size=10.5),
                                  title=dict(text="% no prazo",
                                             font=dict(size=10.5, color=ui.MUTED))))
    sec["blocos"].append({"t": "fig", "titulo": "Evolução do SLA", "kicker": "prazo",
                          "desc": "Percentual de vagas fechadas no prazo em cada período. "
                                  "Linha tracejada: meta contratual.",
                          "fig": fig1, "altura": 330})

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=ent_hist.Periodo, y=ent_hist.Solicitadas, name="Solicitadas",
                          marker=dict(color=ui.S1, line=dict(color=ui.SURF, width=1)),
                          text=[ui.fmt(v) for v in ent_hist.Solicitadas],
                          textposition="outside", textfont=dict(size=11, color=ui.INK2),
                          cliponaxis=False,
                          hovertemplate="Solicitadas: %{y:,.0f}<extra></extra>"))
    fig2.add_trace(go.Bar(x=ent_hist.Periodo, y=ent_hist.Entregues, name="Entregues",
                          marker=dict(color=ui.S3, line=dict(color=ui.SURF, width=1)),
                          text=[ui.fmt(v) for v in ent_hist.Entregues],
                          textposition="outside", textfont=dict(size=11, color=ui.INK2),
                          cliponaxis=False,
                          hovertemplate="Entregues: %{y:,.0f}<extra></extra>"))
    ui.layout(fig2, 340, ytitulo="diárias")
    fig2.update_layout(barmode="group", bargap=0.3, bargroupgap=0.06,
                       yaxis=dict(range=[0, ent_hist.Solicitadas.max() * 1.25],
                                  gridcolor=ui.GRID,
                                  tickfont=dict(color=ui.MUTED, size=10.5),
                                  title=dict(text="diárias",
                                             font=dict(size=10.5, color=ui.MUTED))))
    sec["blocos"].append({"t": "fig", "titulo": "Evolução do volume de diárias",
                          "kicker": "volume",
                          "desc": "Solicitadas e entregues em cada período do histórico.",
                          "fig": fig2, "altura": 340})

    cores = [ui.GOOD if v >= META_DIARIA else (ui.WARN if v >= 90 else ui.CRIT)
             for v in ent_hist["Taxa_%"]]
    fig3 = go.Figure(go.Bar(
        x=ent_hist.Periodo, y=ent_hist["Taxa_%"],
        marker=dict(color=cores, line=dict(color=ui.SURF, width=1)),
        text=[f"<b>{ui.pc(v)}</b>" for v in ent_hist["Taxa_%"]],
        textposition="outside", textfont=dict(size=11.5, color=ui.INK), cliponaxis=False,
        customdata=np.stack([ent_hist.Entregues, ent_hist.Solicitadas], axis=-1),
        hovertemplate="%{x}<br>%{y:.1f}% · %{customdata[0]:,.0f} de "
                      "%{customdata[1]:,.0f}<extra></extra>"))
    fig3.add_hline(y=META_DIARIA, line=dict(color=ui.INK2, width=1.2, dash="dash"))
    ui.layout(fig3, 250, legenda=False, ytitulo="% de atendimento", hover="closest")
    fig3.update_layout(bargap=0.48,
                       yaxis=dict(range=[0, 118], gridcolor=ui.GRID,
                                  tickfont=dict(color=ui.MUTED, size=10.5),
                                  title=dict(text="% de atendimento",
                                             font=dict(size=10.5, color=ui.MUTED))))
    sec["blocos"].append({"t": "fig", "titulo": "Taxa de atendimento ao longo do contrato",
                          "kicker": "aderência", "fig": fig3, "altura": 250})

    sec["blocos"].append({
        "t": "texto", "titulo": "Leitura do histórico", "kicker": "análise",
        "html": _texto_historico(sla_hist, ent_hist, tot_sol, tot_ent, tx_global)})
    return sec


def _texto_visao_geral(tot_v, no_p, fora, t_sla, sol_d, ent_d, t_dia, sla_det, ped_det):
    gap = sol_d - ent_d
    if fora == 0:
        sla_txt = (f"Todas as <b>{ui.fmt(tot_v)}</b> vagas do período fecharam dentro do prazo "
                   f"acordado. O SLA fica em <b>{ui.pc(t_sla)}</b>, na meta contratual.")
    else:
        sla_txt = (f"Das <b>{ui.fmt(tot_v)}</b> vagas solicitadas, <b>{ui.fmt(no_p)}</b> fecharam "
                   f"no prazo e <b>{ui.fmt(fora)}</b> ultrapassaram o limite acordado — SLA de "
                   f"<b>{ui.pc(t_sla)}</b> contra meta de {ui.pc(META_SLA, 0)}. Cada vaga fora do "
                   f"prazo é um posto que ficou descoberto até ser suprido.")

    if gap > 0:
        dia_txt = (f"Foram entregues <b>{ui.fmt(ent_d)}</b> das <b>{ui.fmt(sol_d)}</b> diárias "
                   f"contratadas — <b>{ui.pc(t_dia)}</b> de atendimento. As {ui.fmt(gap)} diárias "
                   f"não cobertas correspondem a postos que o cliente planejou ter e não teve.")
    else:
        dia_txt = (f"Foram entregues <b>{ui.fmt(ent_d)}</b> diárias sobre <b>{ui.fmt(sol_d)}</b> "
                   f"contratadas — <b>{ui.pc(t_dia)}</b>. A demanda foi coberta integralmente.")

    extra = ""
    if len(ped_det) > 1:
        ped_det = ped_det.copy()
        ped_det["Gap"] = ped_det.Solicitado - ped_det.Entregue
        cobertas = int((ped_det.Gap <= 0).sum())
        abaixo = ped_det[ped_det.Gap > 0]
        if len(abaixo):
            pior = abaixo.loc[abaixo.Gap.idxmax()]
            det_pior = (f" O maior déficit ficou em <b>{pior.Periodo}</b>, com "
                        f"{ui.fmt(pior.Gap)} diárias não cobertas.")
        else:
            det_pior = ""
        n = len(ped_det)
        if cobertas == 0:
            frase = (f"Nenhuma das {n} semanas do período fechou com a demanda coberta "
                     f"integralmente.")
        elif cobertas == n:
            frase = f"As {n} semanas do período fecharam com a demanda coberta integralmente."
        else:
            frase = (f"Das {n} semanas do período, <b>{cobertas}</b> "
                     f"{'fechou' if cobertas == 1 else 'fecharam'} com a demanda coberta "
                     f"integralmente e <b>{n - cobertas}</b> "
                     f"{'ficou' if n - cobertas == 1 else 'ficaram'} abaixo do pedido.")
        extra = f"<li><b>Semana a semana.</b> {frase}{det_pior}</li>"

    foco = ("Manter o banco de candidatos ativo nas funções de maior volume, que são as "
            "que mais pressionam o prazo quando a demanda sobe." if fora == 0 else
            "Reforçar a captação nas funções que concentraram atraso e acompanhar "
            "diariamente as vagas em aberto, para não repetir o estouro no próximo ciclo.")

    return (f'<span class="hd">Resumo do período · {_rotulo_periodo()}</span><ul>'
            f"<li><b>Prazo.</b> {sla_txt}</li>"
            f"<li><b>Volume.</b> {dia_txt}</li>"
            f"{extra}"
            f"<li><b>Foco para o próximo ciclo.</b> {foco}</li></ul>")


def _texto_sla(total, dentro, fora, p_dentro, det):
    if fora == 0:
        cabeca = (f"As <b>{ui.fmt(total)}</b> vagas do período fecharam integralmente dentro do "
                  f"prazo. O SLA fica em <b>{ui.pc(p_dentro)}</b> e cumpre a meta contratual.")
        risco = ("Sem atraso registrado, o ponto de atenção deixa de ser corretivo e passa a ser "
                 "preventivo: sustentar o mesmo prazo quando o volume de pedidos subir.")
    else:
        cabeca = (f"<b>{ui.fmt(dentro)}</b> das <b>{ui.fmt(total)}</b> vagas fecharam no prazo — "
                  f"SLA de <b>{ui.pc(p_dentro)}</b>, {ui.num(META_SLA - p_dentro)} pontos abaixo "
                  f"da meta.")
        risco = (f"As <b>{ui.fmt(fora)}</b> vagas fora do prazo representam postos descobertos "
                 f"durante a operação. O impacto não é apenas contratual: recai sobre a escala "
                 f"da área que abriu a requisição. Como as requisições chegam com cerca de "
                 f"{ANTECEDENCIA_PEDIDO_DIAS} dias de antecedência, o prazo de aviso não é o "
                 f"gargalo — o que alonga o fechamento é a oferta de candidato na função e a "
                 f"etapa de admissão (documentação e exame admissional).")

    comp = ""
    if len(det) > 1:
        pior = det.loc[det["Taxa_%"].idxmin()]
        melhor = det.loc[det["Taxa_%"].idxmax()]
        if pior["Taxa_%"] < melhor["Taxa_%"]:
            comp = (f"<li><b>Comparativo.</b> O melhor período foi <b>{melhor.Periodo}</b>, "
                    f"com as {ui.fmt(melhor.Solicitado)} vagas fechadas no prazo. O mais "
                    f"crítico foi <b>{pior.Periodo}</b>: {ui.fmt(pior.Fora_prazo)} de "
                    f"{ui.fmt(pior.Solicitado)} vagas fora do prazo, {ui.pc(pior['Taxa_%'])} "
                    f"de SLA. A diferença entre as duas semanas está no volume pedido e na "
                    f"oferta de candidato para as funções envolvidas.</li>")
        else:
            comp = (f"<li><b>Comparativo.</b> Os {len(det)} períodos avaliados mantiveram o mesmo "
                    f"patamar de prazo, sem oscilação relevante.</li>")

    acao = ("Manter o banco de candidatos ativo nas funções de maior volume e sustentar o "
            "ritmo de admissão quando o volume de pedidos subir." if fora == 0 else
            "Manter cadastro reserva proporcional ao quadro nas funções que atrasaram, "
            "ampliar os canais de captação dessas funções e acompanhar diariamente as vagas "
            "em aberto, para agir antes de o prazo estourar e não depois.")

    return (f'<span class="hd">Desempenho de prazo · {_rotulo_periodo()}</span><ul>'
            f"<li><b>Resultado.</b> {cabeca}</li>"
            f"<li><b>Risco operacional.</b> {risco}</li>"
            f"{comp}"
            f"<li><b>Encaminhamento.</b> {acao}</li></ul>")


def _texto_diarias(sol, ent, taxa, saldo, det):
    if saldo >= 0:
        cabeca = (f"Entregamos <b>{ui.fmt(ent)}</b> diárias sobre <b>{ui.fmt(sol)}</b> "
                  f"contratadas — <b>{ui.pc(taxa)}</b> de atendimento, com {ui.fmt(saldo)} "
                  f"diárias acima do pedido.")
        leitura = ("O excedente vem de reforço em postos de pico. Não gera custo adicional ao "
                   "cliente e funciona como amortecedor quando alguma função fica descoberta.")
    else:
        cabeca = (f"Entregamos <b>{ui.fmt(ent)}</b> diárias sobre <b>{ui.fmt(sol)}</b> "
                  f"contratadas — <b>{ui.pc(taxa)}</b> de atendimento, com déficit de "
                  f"<b>{ui.fmt(abs(saldo))} diárias</b>.")
        leitura = (f"Essas {ui.fmt(abs(saldo))} diárias correspondem a postos que a operação do "
                   f"cliente planejou ter e não teve. É o número que a área usuária sente na "
                   f"escala do dia.")

    comp = ""

    acao = ("Manter o patamar e acompanhar semana a semana para que o excedente não vire "
            "custo ocioso." if saldo >= 0 else
            f"Zerar o déficit exige somar {ui.fmt(abs(saldo))} diárias ao período — na prática, "
            f"reforçar o quadro nas funções de maior volume e reduzir a perda por ausência.")

    return (f'<span class="hd">Volume de diárias · {_rotulo_periodo()}</span><ul>'
            f"<li><b>Resultado.</b> {cabeca}</li>"
            f"<li><b>Como ler.</b> {leitura}</li>"
            f"{comp}"
            f"<li><b>Encaminhamento.</b> {acao}</li></ul>")


def _texto_historico(sla_hist, ent_hist, tot_sol, tot_ent, tx_global):
    n = len(ent_hist)
    atual_e = ent_hist.iloc[-1]
    atual_s = sla_hist.iloc[-1]
    gap = tot_sol - tot_ent

    if n == 1:
        fortes = (f"<li><b>Primeira medição.</b> O período de abertura ({atual_e.Periodo}) "
                  f"fechou com <b>{ui.pc(atual_e['Taxa_%'])}</b> de atendimento — "
                  f"{ui.fmt(atual_e.Entregues)} de {ui.fmt(atual_e.Solicitadas)} diárias.</li>"
                  f"<li><b>Prazo.</b> O SLA ficou em <b>{ui.pc(atual_s['No_prazo_%'])}</b>. "
                  f"Ainda não há série para falar em tendência: este número passa a ser a "
                  f"linha de base do contrato.</li>")
        if gap > 0:
            gargalos = (f"<li><b>Pendência.</b> Faltaram {ui.fmt(gap)} diárias para cobrir a "
                        f"demanda integralmente.</li>"
                        f"<li><b>O que observar.</b> Com um único ciclo medido, a prioridade é "
                        f"confirmar se o gap se repete ou se foi efeito da curva de partida.</li>")
        else:
            gargalos = ("<li><b>Sem pendência de volume.</b> A demanda foi coberta "
                        "integralmente no primeiro ciclo.</li>"
                        "<li><b>O que observar.</b> Sustentar o patamar quando o volume de "
                        "pedidos crescer.</li>")
    else:
        m_e = ent_hist.loc[ent_hist["Taxa_%"].idxmax()]
        p_e = ent_hist.loc[ent_hist["Taxa_%"].idxmin()]
        m_s = sla_hist.loc[sla_hist["No_prazo_%"].idxmax()]
        p_s = sla_hist.loc[sla_hist["No_prazo_%"].idxmin()]
        delta = atual_e["Taxa_%"] - ent_hist.iloc[0]["Taxa_%"]
        na_meta = int((sla_hist["No_prazo_%"] >= META_SLA).sum())

        if delta > 1:
            tend = f"em alta de {ui.num(delta)} pontos desde o primeiro período medido"
        elif delta < -1:
            tend = f"em queda de {ui.num(abs(delta))} pontos desde o primeiro período medido"
        else:
            tend = "estável em relação ao primeiro período medido"

        fortes = (f"<li><b>Acumulado.</b> {ui.fmt(tot_ent)} de {ui.fmt(tot_sol)} diárias "
                  f"entregues em {n} períodos — <b>{ui.pc(tx_global)}</b> de atendimento "
                  f"global, {tend}.</li>"
                  f"<li><b>Melhor volume.</b> <b>{m_e.Periodo}</b>, com "
                  f"<b>{ui.pc(m_e['Taxa_%'])}</b> de atendimento.</li>"
                  f"<li><b>Prazo.</b> {na_meta} de {len(sla_hist)} períodos fecharam com SLA "
                  f"integral; o melhor foi <b>{m_s.Periodo}</b> "
                  f"({ui.pc(m_s['No_prazo_%'])}).</li>")

        if p_s["Fora_%"] > 0:
            obs = (f"<b>{p_s.Periodo}</b> concentrou o maior atraso do contrato, com "
                   f"<b>{ui.pc(p_s['Fora_%'])}</b> das vagas fora do prazo.")
        else:
            obs = ("Nenhum período do histórico registrou vaga fora do prazo — o prazo "
                   "acordado foi cumprido integralmente em todo o contrato.")

        gargalos = (f"<li><b>Volume mais baixo.</b> <b>{p_e.Periodo}</b>, com "
                    f"<b>{ui.pc(p_e['Taxa_%'])}</b> de atendimento "
                    f"({ui.fmt(p_e.Solicitadas - p_e.Entregues)} diárias não cobertas).</li>"
                    f"<li><b>Prazo.</b> {obs}</li>"
                    f"<li><b>Situação atual.</b> A medição mais recente ({atual_e.Periodo}) "
                    f"fechou com <b>{ui.pc(atual_e['Taxa_%'])}</b> de atendimento e SLA de "
                    f"<b>{ui.pc(atual_s['No_prazo_%'])}</b>.</li>")
        if gap > 0:
            gargalos += (f"<li><b>Pendência acumulada.</b> {ui.fmt(gap)} diárias não entregues "
                         f"desde o início do contrato.</li>")

    return (f'<div class="duo">'
            f'<div class="note good"><span class="hd">Desempenho</span><ul>{fortes}</ul></div>'
            f'<div class="note warn"><span class="hd">Pontos de atenção</span>'
            f'<ul>{gargalos}</ul></div></div>')


# ============================================================== EXPORTAÇÃO PDF
SECOES_DISPONIVEIS = ["Visão Geral", "Análise SLA", "Diárias", "Histórico Mensal"]
if MOSTRAR_TEMPORADA:
    SECOES_DISPONIVEIS.append(ABA_TEMPORADA)
if MOSTRAR_PESQUISA:
    SECOES_DISPONIVEIS.append(ABA_PESQUISA)


def construir_secao(nome, alvos):
    if nome == "Visão Geral":
        return construir_visao_geral(alvos)
    if nome == "Análise SLA":
        return construir_analise_sla(alvos)
    if nome == "Diárias":
        return construir_diarias(alvos)
    if nome == "Histórico Mensal":
        return construir_historico(alvos)
    if nome == ABA_TEMPORADA:
        from aba_temporada import construir_temporada
        return construir_temporada()
    if nome == ABA_PESQUISA:
        from aba_pesquisa import construir_pesquisa
        return construir_pesquisa()
    return {"titulo": nome, "sub": "", "blocos": []}


def painel_exportacao(alvos):
    with st.expander("Exportar relatório", expanded=False):
        st.caption("O conteúdo é o mesmo da tela, incluindo os filtros aplicados. "
                   "O formato HTML abre no navegador e salva em PDF pelo Ctrl+P — "
                   "é o caminho mais rápido e não depende de biblioteca extra.")
        c1, c2 = st.columns([3, 1.6])
        with c1:
            escolhidas = st.multiselect("Seções", SECOES_DISPONIVEIS,
                                        default=SECOES_DISPONIVEIS,
                                        placeholder="Selecione as seções",
                                        key="exp_secoes")
        with c2:
            formato = st.radio("Formato",
                               ["HTML (imprime em PDF com Ctrl+P)", "PDF direto"],
                               key="exp_formato")
        eh_pdf = formato.startswith("PDF")

        pdf_ok, pdf_msg = relatorio_pdf.disponivel()
        if eh_pdf and not pdf_ok:
            st.warning(f"O PDF direto não está disponível: {pdf_msg}")
            st.code('pip install reportlab "kaleido==0.2.1"', language="bat")

        b1, b2 = st.columns([1, 1])
        gerar = b1.button("Gerar arquivo", type="primary", use_container_width=True)
        diag = b2.button("Testar geração de PDF", use_container_width=True,
                         help="Renderiza um gráfico de teste e mostra as versões "
                              "instaladas. Serve para descobrir por que o PDF falha.")

        if diag:
            with st.spinner("Testando…"):
                d = relatorio_pdf.diagnostico()
            versoes = " · ".join(f"{k}: {v}" for k, v in d.items()
                                 if k in ("python", "plotly", "kaleido", "reportlab"))
            if d.get("ok"):
                st.success("Renderização de gráficos funcionando. " + versoes)
            elif d.get("travou"):
                st.error("O kaleido travou neste computador — é o motivo do PDF não sair.")
                st.markdown("Duas saídas, nesta ordem:\n\n"
                            "1. Use o formato **HTML** e salve em PDF com Ctrl+P "
                            "(resultado equivalente, sai na hora).\n"
                            "2. Se quiser insistir no PDF direto, troque a versão do "
                            "motor de imagem — você já tem o Chrome instalado:")
                st.code('pip install "kaleido>=1.0"', language="bat")
            else:
                st.error(f"Falhou: {d.get('erro', 'erro desconhecido')}")
                st.caption(versoes)

        if gerar:
            if not escolhidas:
                st.info("Selecione ao menos uma seção.")
                return
            logo_path = Path(__file__).resolve().parent / "images" / "Logo_Parceria.png"
            logo_bytes = logo_path.read_bytes() if logo_path.exists() else None
            sub = f"{_rotulo_periodo()} · Mendes RH · Aviva / Rio Quente Resorts"
            nome_base = ("Relatorio_Temporarios_"
                         + _rotulo_periodo().replace(" ", "_").replace("/", "-"))
            with st.spinner("Montando o relatório…"):
                try:
                    secoes = [construir_secao(n, alvos) for n in escolhidas]
                    secoes = [x for x in secoes if x["blocos"]]
                except Exception as e:
                    st.error(f"Não foi possível montar as seções: {e}")
                    return

                if eh_pdf:
                    if not pdf_ok:
                        st.error("Instale as bibliotecas acima para gerar em PDF.")
                        return
                    dados, erro = relatorio_pdf.gerar_em_processo(
                        secoes, "Relatório de Gestão de Temporários", sub, logo_bytes)
                    if erro:
                        st.error(f"Falha ao gerar o PDF: {erro}")
                        st.info("Troque o formato para **HTML** — o arquivo sai em "
                                "segundos e o Ctrl+P do navegador salva em PDF com "
                                "o mesmo layout.")
                        return
                    st.session_state["exp_bytes"] = dados
                    st.session_state["exp_nome"] = nome_base + ".pdf"
                    st.session_state["exp_mime"] = "application/pdf"
                else:
                    try:
                        html = relatorio_pdf.gerar_html(
                            secoes, "Relatório de Gestão de Temporários", sub, _logo)
                    except Exception as e:
                        st.error(f"Falha ao gerar o HTML: {e}")
                        return
                    st.session_state["exp_bytes"] = html.encode("utf-8")
                    st.session_state["exp_nome"] = nome_base + ".html"
                    st.session_state["exp_mime"] = "text/html"

        if st.session_state.get("exp_bytes"):
            nome = st.session_state.get("exp_nome", "relatorio")
            st.success(f"Pronto: {nome}")
            st.download_button(f"Baixar {nome}", st.session_state["exp_bytes"], nome,
                               st.session_state.get("exp_mime", "application/octet-stream"),
                               use_container_width=True)
            if nome.endswith(".html"):
                st.caption("Abra o arquivo no navegador e pressione Ctrl+P → destino "
                           "“Salvar como PDF”. O layout já está preparado para A4 "
                           "paisagem, com uma seção por página.")


# ------------------------------------------------------------------ roteamento
aba_ativa = st.session_state.current_tab
alvos_ativos = obter_caminhos_alvo()

if aba_ativa == ABA_TEMPORADA:
    from aba_temporada import render_temporada
    render_temporada()
elif aba_ativa == ABA_PESQUISA:
    from aba_pesquisa import render_pesquisa
    render_pesquisa()
else:
    ui.desenhar(construir_secao(aba_ativa, alvos_ativos))

painel_exportacao(alvos_ativos)
