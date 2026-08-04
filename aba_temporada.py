# -*- coding: utf-8 -*-
"""
================================================================================
 ABA "TEMPORADA" - Entrega diaria e absenteismo por funcao
 Mendes RH x Aviva / Rio Quente Resorts
================================================================================
Consome os CSVs gerados por processar_temporada.py em dados/temporada_julho/.

Paleta validada para daltonismo (separacao CVD >= 8 / visao normal >= 15 em
todos os pares em uso). Nenhuma informacao depende de cor isolada: todo mark
colorido carrega rotulo ou legenda.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ui_dashboard as ui

PASTA = Path(__file__).resolve().parent / "dados" / "temporada_julho"
TITULO = "Temporada de Julho"
SUBTITULO = "01 a 31 de julho de 2026 · Rio Quente Resorts"

# ------------------------------------------------------------------- paleta
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
GOOD, WARN, SERIOUS, CRIT = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURF = "#eceae4", "#c3c2b7", "#ffffff"
SEQ = ["#eef5fe", "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
       "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#0d366b"]

META_ABS = 5.0
META_COB = 95.0

CSS = """
<style>
:root{--tj-ink:#0b0b0b;--tj-ink2:#52514e;--tj-mut:#898781;}
section.main > div.block-container{padding-top:1.2rem;max-width:1500px;}
.stApp{background:#f4f5f7;}

/* cartoes (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:#fff;border-radius:18px;
  border:1px solid rgba(11,11,11,.07)!important;
  box-shadow:0 1px 2px rgba(11,11,11,.04),0 10px 30px -14px rgba(11,11,11,.16);
  padding:6px 20px 14px 20px;margin-bottom:16px;}

.tj{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}

/* faixa hero */
.tj-hero{background:linear-gradient(125deg,#0d366b 0%,#1c5cab 52%,#2a78d6 100%);
  border-radius:20px;padding:22px 26px 20px 26px;color:#fff;margin-bottom:16px;
  box-shadow:0 14px 34px -18px rgba(13,54,107,.75);}
.tj-hero .top{display:flex;align-items:flex-end;justify-content:space-between;
  gap:18px;flex-wrap:wrap;margin-bottom:18px;}
.tj-hero h2{margin:0;font-size:1.5rem;font-weight:760;letter-spacing:-.025em;}
.tj-hero .sub{font-size:.86rem;opacity:.78;margin-top:3px;}
.tj-hero .chip{font-size:.72rem;font-weight:700;letter-spacing:.03em;
  background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);
  padding:5px 12px;border-radius:999px;}
.tj-tiles{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;}
.tj-tile{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);
  border-radius:14px;padding:13px 15px 12px 15px;backdrop-filter:blur(2px);
  display:flex;flex-direction:column;min-height:112px;}
.tj-tile .lb{font-size:.68rem;font-weight:700;letter-spacing:.07em;
  text-transform:uppercase;opacity:.72;}
.tj-tile .vl{font-size:1.85rem;font-weight:780;line-height:1.15;margin-top:3px;
  letter-spacing:-.02em;}
.tj-tile .sb{font-size:.72rem;opacity:.74;margin-top:auto;line-height:1.35;}
.tj-tile .bd{display:inline-block;font-size:.66rem;font-weight:750;
  padding:2px 8px;border-radius:999px;margin-top:6px;align-self:flex-start;}
.tj-spark{margin-top:6px;opacity:.9;}

/* titulos de secao dentro do cartao */
.tj-h{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
  margin:10px 0 2px 0;}
.tj-h .t{font-size:1.02rem;font-weight:730;color:var(--tj-ink);letter-spacing:-.012em;}
.tj-h .k{font-size:.7rem;font-weight:750;letter-spacing:.06em;text-transform:uppercase;
  color:#2a78d6;background:#eaf2fd;padding:2px 9px;border-radius:999px;}
.tj-d{font-size:.83rem;color:var(--tj-ink2);margin:2px 0 8px 0;line-height:1.5;}

/* blocos de texto analitico */
.tj-note{border-left:4px solid #2a78d6;background:#fbfcfe;border-radius:0 12px 12px 0;
  padding:14px 18px;font-size:.92rem;color:var(--tj-ink);line-height:1.65;
  margin-top:6px;}
.tj-note.warn{border-left-color:#fab219;background:#fffdf7;}
.tj-note.bad{border-left-color:#d03b3b;background:#fffbfb;}
.tj-note .hd{font-weight:750;font-size:.95rem;display:block;margin-bottom:5px;}
.tj-note ul{margin:6px 0 0 0;padding-left:19px;}
.tj-note li{margin-bottom:7px;}
</style>
"""


# ---------------------------------------------------------------- utilidades
def _fmt(n, casas=0):
    return f"{n:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def _p(n, casas=1):
    return f"{n:.{casas}f}".replace(".", ",") + "%"


def _n(n, casas=1):
    return f"{n:.{casas}f}".replace(".", ",")


@st.cache_data(show_spinner=False)
def carregar():
    def ler(nome):
        p = PASTA / f"{nome}.csv"
        return pd.read_csv(p, sep=";", decimal=",", encoding="utf-8-sig") if p.exists() else None
    d = {n: ler(n) for n in ["ABSENTEISMO_DIA_FUNCAO", "ABSENTEISMO_DIA_TOTAL",
                             "ABSENTEISMO_FUNCAO", "RESUMO_TEMPORADA", "CONCILIACAO_STH"]}
    if d["ABSENTEISMO_DIA_FUNCAO"] is not None:
        d["ABSENTEISMO_DIA_FUNCAO"]["Dia"] = pd.to_datetime(d["ABSENTEISMO_DIA_FUNCAO"]["Dia"])
    return d


def _sparkline(vals, cor="#ffffff", w=150, h=26):
    """Mini serie em SVG inline para os tiles do hero."""
    v = [x for x in vals if pd.notna(x)]
    if len(v) < 2:
        return ""
    lo, hi = min(v), max(v)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i / (len(v) - 1) * w:.1f},{h - (x - lo) / rng * (h - 4) - 2:.1f}"
                   for i, x in enumerate(v))
    return (f'<svg class="tj-spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'preserveAspectRatio="none"><polyline points="{pts}" fill="none" '
            f'stroke="{cor}" stroke-width="1.8" stroke-linejoin="round" '
            f'stroke-linecap="round" opacity=".85"/></svg>')


def _tile(lb, vl, sb, spark="", badge=None):
    bd = ""
    if badge:
        txt, bg, fg = badge
        bd = f'<span class="bd" style="background:{bg};color:{fg}">{txt}</span>'
    return (f'<div class="tj-tile"><div class="lb">{lb}</div><div class="vl">{vl}</div>'
            f'{spark}{bd}<div class="sb">{sb}</div></div>')


def _titulo(t, kicker=None, desc=None):
    k = f'<span class="k">{kicker}</span>' if kicker else ""
    d = f'<div class="tj-d">{desc}</div>' if desc else ""
    st.markdown(f'<div class="tj"><div class="tj-h"><span class="t">{t}</span>{k}</div>{d}</div>',
                unsafe_allow_html=True)


def _layout(fig, altura=340, legenda=True, ytitulo=""):
    fig.update_layout(
        height=altura, margin=dict(l=6, r=6, t=8, b=6),
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family='system-ui,-apple-system,"Segoe UI",sans-serif', size=12, color=INK2),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#fff", bordercolor=AXIS, font=dict(color=INK, size=12)),
        showlegend=legenda,
        legend=dict(orientation="h", y=1.16, x=0, xanchor="left",
                    font=dict(size=11.5, color=INK2), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, linecolor=AXIS, ticks="outside", ticklen=3,
                   tickcolor=AXIS, tickfont=dict(color=MUTED, size=10.5)),
        yaxis=dict(title=dict(text=ytitulo, font=dict(size=10.5, color=MUTED)),
                   gridcolor=GRID, zerolinecolor=AXIS, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=MUTED, size=10.5)),
    )
    return fig


# ------------------------------------------------------------------- render
K_FUNC, K_PER = "tj_funcoes", "tj_periodo"


def construir_temporada(sel=None, d_ini=None, d_fim=None):
    """Monta a seção da temporada. Sem argumentos, usa os filtros da tela."""
    sec = {"titulo": TITULO, "sub": SUBTITULO, "blocos": []}
    dados = carregar()
    if dados["ABSENTEISMO_DIA_FUNCAO"] is None:
        return sec

    base = dados["ABSENTEISMO_DIA_FUNCAO"]
    if sel is None:
        sel = st.session_state.get(K_FUNC) or sorted(base["Funcao"].dropna().unique())
    if d_ini is None or d_fim is None:
        d_ini, d_fim = st.session_state.get(K_PER, (1, 31))

    det = base.copy()
    if sel:
        det = det[det["Funcao"].isin(sel)]
    det = det[(det["DiaNum"] >= d_ini) & (det["DiaNum"] <= d_fim)]
    if det.empty or det["Solicitado"].sum() == 0:
        return sec

    SOM = ["Solicitado", "Entregue", "Escala", "Trabalhou", "Folga", "Atestado",
           "Outra justificativa", "Falta"]
    t = det[SOM].sum()
    cob = t.Entregue / t.Solicitado * 100
    absent = t.Falta / t.Escala * 100 if t.Escala else 0
    posto = t.Trabalhou / t.Solicitado * 100

    dia = det.groupby(["DiaNum", "DiaSemana", "FimDeSemana"])[SOM].sum().reset_index()
    dia = dia.sort_values("DiaNum")
    dia["Absenteismo_%"] = dia.Falta / dia.Escala.replace(0, np.nan) * 100
    dia["Cobertura_%"] = dia.Entregue / dia.Solicitado.replace(0, np.nan) * 100

    fun = det.groupby("Funcao")[SOM].sum().reset_index()
    fun["Absenteismo_%"] = fun.Falta / fun.Escala.replace(0, np.nan) * 100
    fun["Cobertura_%"] = fun.Entregue / fun.Solicitado.replace(0, np.nan) * 100

    dias_ok = int((dia["Cobertura_%"] >= META_COB).sum())
    sec["sub"] = f"{SUBTITULO} · dias {d_ini} a {d_fim}"

    # ------------------------------------------------------------------ hero
    sec["blocos"].append({
        "t": "hero", "titulo": TITULO,
        "sub": f"{SUBTITULO} · {det['Funcao'].nunique()} funções · {d_fim - d_ini + 1} dias",
        "chip": "Fonte: STH (demanda) × espelho de ponto (entrega)",
        "tiles": [
            {"lb": "Diárias solicitadas", "vl": _fmt(t.Solicitado),
             "sb": "vagas do STH ativas no período", "spark": _sparkline(dia.Solicitado)},
            {"lb": "Diárias entregues", "vl": _fmt(t.Entregue),
             "sb": f"{_fmt(t.Trabalhou)} em posto · "
                   f"{_fmt(t.Folga + t.Atestado + t['Outra justificativa'])} folga e afastamento",
             "spark": _sparkline(dia.Entregue)},
            {"lb": "Cobertura da demanda", "vl": _p(cob),
             "sb": f"{dias_ok} de {len(dia)} dias na meta",
             "spark": _sparkline(dia["Cobertura_%"]), "badge": f"meta {_p(META_COB, 0)}"},
            {"lb": "Absenteísmo", "vl": _p(absent, 2),
             "sb": f"{_fmt(t.Falta)} faltas em {_fmt(t.Escala)} diárias de escala",
             "spark": _sparkline(dia["Absenteismo_%"]), "badge": f"meta ate {_p(META_ABS, 0)}"},
            {"lb": "Presença em posto", "vl": _p(posto),
             "sb": "ponto batido sobre a demanda contratada",
             "spark": _sparkline(dia.Trabalhou)}]})

    x = dia["DiaNum"]
    rot = [f"{d}<br><span style='font-size:9px'>{s}</span>"
           for d, s in zip(dia.DiaNum, dia.DiaSemana)]

    # ------------------------------------------- solicitado x entregue diario
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=dia.Entregue, name="Entregue",
        marker=dict(color=S3, line=dict(color=SURF, width=1)),
        text=[f"<b>{v:.0f}</b>" for v in dia.Entregue], textposition="inside",
        insidetextanchor="middle", textangle=0, constraintext="none",
        textfont=dict(size=10, color="#fff"),
        cliponaxis=False, hovertemplate="Entregue: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=x, y=dia.Solicitado, name="Solicitado (STH)", mode="lines+markers",
        line=dict(color=S1, width=2.4),
        marker=dict(size=6, color=S1, line=dict(color=SURF, width=1.5)),
        hovertemplate="Solicitado: %{y:,.0f}<extra></extra>"))
    topo = np.maximum(dia.Solicitado.values, dia.Entregue.values)
    fig.add_trace(go.Scatter(
        x=x, y=topo, mode="text", showlegend=False, hoverinfo="skip",
        text=[f"{v:.0f}" for v in dia.Solicitado], textposition="top center",
        textfont=dict(size=10, color=S1), cliponaxis=False))
    _layout(fig, 360, ytitulo="diárias")
    fig.update_layout(bargap=0.28,
                      xaxis=dict(tickmode="array", tickvals=list(x), ticktext=rot,
                                 showgrid=False, linecolor=AXIS,
                                 tickfont=dict(color=MUTED, size=10)),
                      yaxis=dict(range=[0, max(dia.Solicitado.max(),
                                               dia.Entregue.max()) * 1.22],
                                 gridcolor=GRID, tickfont=dict(color=MUTED, size=10.5),
                                 title=dict(text="diárias", font=dict(size=10.5, color=MUTED))))
    sec["blocos"].append({"t": "fig", "titulo": "Solicitado × entregue, dia a dia",
                          "kicker": "entrega",
                          "desc": "Barras: diárias entregues (ponto batido, folga, atestado e "
                                  "demais justificativas). Linha: demanda contratada no dia.",
                          "fig": fig, "altura": 360})

    # ------------------------------------------------------ absenteismo diario
    cores = [CRIT if v > 15 else (SERIOUS if v > META_ABS else S1) for v in dia["Absenteismo_%"]]
    fig = go.Figure(go.Bar(
        x=x, y=dia["Absenteismo_%"],
        marker=dict(color=cores, line=dict(color=SURF, width=1)),
        text=[f"<b>{_p(v, 0)}</b>" for v in dia["Absenteismo_%"]],
        textposition="outside", textfont=dict(size=10, color=INK), cliponaxis=False,
        customdata=np.stack([dia.Falta, dia.Escala], axis=-1),
        hovertemplate="Absenteísmo: %{y:.1f}%<br>%{customdata[0]:,.0f} faltas em "
                      "%{customdata[1]:,.0f} de escala<extra></extra>"))
    fig.add_hline(y=META_ABS, line=dict(color=MUTED, width=1.2, dash="dash"))
    _layout(fig, 320, legenda=False, ytitulo="% de absenteísmo")
    fig.update_layout(bargap=0.3,
                      xaxis=dict(tickmode="array", tickvals=list(x), ticktext=rot,
                                 showgrid=False, linecolor=AXIS,
                                 tickfont=dict(color=MUTED, size=10)),
                      yaxis=dict(range=[0, max(dia["Absenteismo_%"].max() * 1.3, 12)],
                                 gridcolor=GRID, tickfont=dict(color=MUTED, size=10.5),
                                 title=dict(text="% de absenteísmo",
                                            font=dict(size=10.5, color=MUTED))))
    sec["blocos"].append({"t": "fig", "titulo": "Absenteísmo diário", "kicker": "faltas",
                          "desc": f"Faltas sobre a escala do dia (entregues + faltas). "
                                  f"Linha tracejada: meta de {_p(META_ABS, 0)}.",
                          "fig": fig, "altura": 320})

    # ----------------------------------------------------------- por função
    fv = fun.sort_values("Solicitado")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=fv.Funcao, x=fv.Solicitado, orientation="h", name="Solicitado (STH)",
        marker=dict(color=S1, line=dict(color=SURF, width=1)),
        text=[f"{v:.0f}" for v in fv.Solicitado], textposition="outside",
        textfont=dict(size=10, color=INK2), cliponaxis=False,
        hovertemplate="%{y} · solicitado %{x:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(
        y=fv.Funcao, x=fv.Entregue, orientation="h", name="Entregue",
        marker=dict(color=S3, line=dict(color=SURF, width=1)),
        text=[f"{v:.0f}" for v in fv.Entregue], textposition="outside",
        textfont=dict(size=10, color=INK2), cliponaxis=False,
        hovertemplate="%{y} · entregue %{x:,.0f}<extra></extra>"))
    alt_f = max(280, 30 * len(fv) + 70)
    _layout(fig, alt_f, ytitulo="")
    fig.update_layout(barmode="group", bargap=0.24, bargroupgap=0.06, hovermode="closest",
                      legend=dict(orientation="h", y=1.05, x=0, xanchor="left",
                                  font=dict(size=11.5, color=INK2)),
                      margin=dict(l=6, r=6, t=34, b=6),
                      xaxis=dict(title=dict(text="diárias", font=dict(size=10.5, color=MUTED)),
                                 gridcolor=GRID, tickfont=dict(color=MUTED, size=10.5),
                                 range=[0, max(fv.Solicitado.max(), fv.Entregue.max()) * 1.12]),
                      yaxis=dict(showgrid=False, tickfont=dict(color=INK2, size=11.5)))
    sec["blocos"].append({"t": "fig", "titulo": "Solicitado × entregue por função",
                          "kicker": "funções",
                          "desc": "Ordenado pelo volume de diárias solicitadas no período.",
                          "fig": fig, "altura": alt_f})

    # ranking de absenteísmo + composição do dia
    rk = fun[fun["Escala"] > 0].sort_values("Absenteismo_%")
    cores = [CRIT if v > 15 else (SERIOUS if v > META_ABS else S1) for v in rk["Absenteismo_%"]]
    fig_rk = go.Figure(go.Bar(
        y=rk.Funcao, x=rk["Absenteismo_%"], orientation="h",
        marker=dict(color=cores, line=dict(color=SURF, width=1)),
        text=[f"<b>{_p(v)}</b>" for v in rk["Absenteismo_%"]],
        textposition="outside", textfont=dict(size=10.5, color=INK), cliponaxis=False,
        customdata=np.stack([rk.Falta, rk.Escala], axis=-1),
        hovertemplate="%{y}<br>%{x:.1f}% · %{customdata[0]:,.0f} faltas em "
                      "%{customdata[1]:,.0f}<extra></extra>"))
    fig_rk.add_vline(x=META_ABS, line=dict(color=MUTED, width=1.2, dash="dash"))
    alt_rk = max(300, 32 * len(rk) + 70)
    _layout(fig_rk, alt_rk, legenda=False)
    fig_rk.update_layout(hovermode="closest", bargap=0.34,
                         xaxis=dict(title=dict(text="% de absenteísmo",
                                               font=dict(size=10.5, color=MUTED)),
                                    gridcolor=GRID, tickfont=dict(color=MUTED, size=10.5),
                                    range=[0, rk["Absenteismo_%"].max() * 1.3]),
                         yaxis=dict(showgrid=False, tickfont=dict(color=INK2, size=11)))

    comp = [("Em posto (ponto batido)", t.Trabalhou, S3),
            ("Folga de escala", t.Folga, S1),
            ("Atestado e justificativas", t.Atestado + t["Outra justificativa"], S2),
            ("Falta", t.Falta, CRIT)]
    tot = sum(v for _, v, _ in comp)
    fig_cp = go.Figure(go.Pie(
        labels=[c[0] for c in comp], values=[c[1] for c in comp],
        hole=0.62, sort=False, direction="clockwise",
        marker=dict(colors=[c[2] for c in comp], line=dict(color=SURF, width=2)),
        texttemplate="<b>%{percent:.0%}</b>", textposition="inside",
        insidetextorientation="horizontal", textfont=dict(color="#fff", size=13),
        hovertemplate="%{label}: %{value:,.0f} diárias (%{percent:.1%})<extra></extra>"))
    fig_cp.add_annotation(
        text=f"<b>{_fmt(tot)}</b><br>"
             f"<span style='font-size:11px;color:{MUTED}'>diárias de escala</span>",
        showarrow=False, font=dict(size=22, color=INK), x=0.5, y=0.5)
    _layout(fig_cp, alt_rk, legenda=True)
    fig_cp.update_layout(hovermode="closest",
                         legend=dict(orientation="v", y=0.5, x=1.0, xanchor="left",
                                     yanchor="middle", traceorder="normal",
                                     font=dict(size=11.5, color=INK2)),
                         margin=dict(l=6, r=6, t=20, b=20),
                         xaxis=dict(visible=False), yaxis=dict(visible=False))

    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Absenteísmo por função", "kicker": "ranking",
          "fig": fig_rk, "altura": alt_rk}],
        [{"t": "fig", "titulo": "Perfil do dia entregue", "kicker": "composição",
          "desc": "Como as diárias entregues se distribuem.",
          "fig": fig_cp, "altura": alt_rk}]]})

    # ------------------------------------------------------------- heatmap
    f_ = det.pivot_table(index="Funcao", columns="DiaNum", values="Falta", aggfunc="sum")
    e_ = det.pivot_table(index="Funcao", columns="DiaNum", values="Escala", aggfunc="sum")
    pct = f_ / e_.replace(0, np.nan) * 100
    ordem = [f for f in fun.sort_values("Absenteismo_%", ascending=False).Funcao
             if f in pct.index]
    pct = pct.loc[ordem]
    zmax = float(np.nanpercentile(pct.values, 95)) if np.isfinite(pct.values).any() else 50
    fig = go.Figure(go.Heatmap(
        z=pct.values, x=[str(c) for c in pct.columns], y=list(pct.index),
        colorscale=[[i / (len(SEQ) - 1), c] for i, c in enumerate(SEQ)],
        zmin=0, zmax=max(zmax, 10), xgap=2, ygap=2, hoverongaps=False,
        colorbar=dict(title=dict(text="%", font=dict(size=10, color=MUTED)),
                      thickness=9, len=0.8, outlinewidth=0,
                      tickfont=dict(size=10, color=MUTED)),
        hovertemplate="%{y} · dia %{x}<br>absenteísmo %{z:.0f}%<extra></extra>"))
    alt_hm = max(300, 32 * len(pct) + 80)
    _layout(fig, alt_hm, legenda=False)
    fig.update_layout(margin=dict(l=6, r=6, t=26, b=6),
                      xaxis=dict(side="top", showgrid=False, linecolor="rgba(0,0,0,0)",
                                 tickmode="array", tickvals=[str(c) for c in pct.columns],
                                 tickfont=dict(color=MUTED, size=9.5)),
                      yaxis=dict(showgrid=False, autorange="reversed",
                                 tickfont=dict(color=INK2, size=11)))
    sec["blocos"].append({"t": "fig", "titulo": "Mapa de calor · absenteísmo por função e dia",
                          "kicker": "concentração",
                          "desc": "Quanto mais escuro, maior o percentual de faltas da função "
                                  "naquele dia. Célula em branco: função sem escala no dia.",
                          "fig": fig, "altura": alt_hm})

    # ------------------------------------------------------ leitura executiva
    sec["blocos"].append({"t": "texto", "titulo": "Leitura da operação", "kicker": "análise",
                          "html": _texto(t, cob, absent, posto, dia, fun, d_ini, d_fim)})

    # -------------------------------------------------------------- matriz
    sec["blocos"].append({"t": "html", "so_tela": True,
                          "html": '<div class="tj"><div class="tj-h">'
                                  '<span class="t">Matriz função × dia</span>'
                                  '<span class="k">detalhamento</span></div>'
                                  '<div class="tj-d">Solicitado, entregue e absenteísmo de cada '
                                  'função em cada dia do mês. Role na horizontal para ver os '
                                  '31 dias.</div></div>' + _matriz_html(det)})
    exp = _matriz_longa(det)
    sec["blocos"].append({"t": "custom", "so_tela": True,
                          "fn": lambda: st.download_button(
                              "Baixar matriz completa (CSV)",
                              exp.to_csv(sep=";", decimal=",", index=False).encode("utf-8-sig"),
                              "matriz_funcao_dia.csv", "text/csv", key="dl_matriz")})

    # resumo por função — entra no PDF no lugar da matriz de 31 colunas
    res = fun[["Funcao", "Solicitado", "Entregue", "Trabalhou", "Folga", "Atestado",
               "Falta", "Absenteismo_%", "Cobertura_%"]].copy()
    res = res.sort_values("Solicitado", ascending=False)
    res.columns = ["Função", "Solicitado", "Entregue", "Em posto", "Folga", "Atestado",
                   "Faltas", "Absenteísmo %", "Cobertura %"]
    for c in ("Absenteísmo %", "Cobertura %"):
        res[c] = res[c].map(lambda v: _p(v) if pd.notna(v) else "—")
    for c in ("Solicitado", "Entregue", "Em posto", "Folga", "Atestado", "Faltas"):
        res[c] = res[c].map(_fmt)
    sec["blocos"].append({"t": "tabela", "so_pdf": True, "titulo": "Resumo por função",
                          "desc": "A matriz dia a dia (31 colunas) está no painel e no CSV "
                                  "para download.",
                          "df": res})
    return sec


def render_temporada():
    st.markdown(CSS, unsafe_allow_html=True)
    dados = carregar()
    if dados["ABSENTEISMO_DIA_FUNCAO"] is None:
        st.warning("Base não gerada. Rode `python processar_temporada.py`.")
        return
    base = dados["ABSENTEISMO_DIA_FUNCAO"]
    funcoes = sorted(base["Funcao"].dropna().unique())

    with st.container(border=True):
        f1, f2 = st.columns([3, 1.4])
        with f1:
            st.multiselect("Funções", funcoes, default=funcoes,
                           placeholder="Todas as funções", key=K_FUNC)
        with f2:
            st.select_slider("Período (dia do mês)", options=list(range(1, 32)),
                             value=(1, 31), key=K_PER)

    sec = construir_temporada()
    if not sec["blocos"]:
        st.info("Sem dados para o filtro selecionado.")
        return
    ui.desenhar(sec)


# --------------------------------------------------------------------- matriz
def _matriz_longa(det: pd.DataFrame) -> pd.DataFrame:
    """Formato longo para exportação: uma linha por função × indicador."""
    linhas = []
    for f, g in det.groupby("Funcao"):
        g = g.set_index("DiaNum")
        for rot, serie, total in [
            ("Solicitado", g["Solicitado"], g["Solicitado"].sum()),
            ("Entregue", g["Entregue"], g["Entregue"].sum()),
            ("Falta", g["Falta"], g["Falta"].sum()),
            ("Absenteísmo %", (g["Falta"] / g["Escala"].replace(0, np.nan) * 100).round(1),
             round(g["Falta"].sum() / max(g["Escala"].sum(), 1) * 100, 1)),
        ]:
            linha = {"Função": f, "Indicador": rot, "Mês": total}
            linha.update({str(d): serie.get(d, np.nan) for d in sorted(det.DiaNum.unique())})
            linhas.append(linha)
    return pd.DataFrame(linhas)


def _matriz_html(det: pd.DataFrame) -> str:
    dias = sorted(det.DiaNum.unique())
    sem = (det.drop_duplicates("DiaNum").set_index("DiaNum")["DiaSemana"].to_dict())
    ordem = (det.groupby("Funcao")["Solicitado"].sum().sort_values(ascending=False).index)

    css = """<style>
.mtx-wrap{max-height:560px;overflow:auto;border:1px solid rgba(11,11,11,.09);
  border-radius:14px;background:#fff;}
table.mtx{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:11.5px;
  font-variant-numeric:tabular-nums;color:#0b0b0b;}
table.mtx th,table.mtx td{padding:5px 8px;text-align:center;white-space:nowrap;
  border-bottom:1px solid #f0efec;}
table.mtx thead th{position:sticky;top:0;z-index:3;background:#f7f8fa;color:#52514e;
  font-weight:700;font-size:10.5px;letter-spacing:.02em;border-bottom:1px solid #e1e0d9;}
table.mtx thead th .wd{display:block;font-weight:600;font-size:9px;color:#898781;}
table.mtx .c0{position:sticky;left:0;z-index:2;background:#fff;text-align:left;
  font-weight:650;min-width:212px;max-width:212px;white-space:normal;line-height:1.25;}
table.mtx .c1{position:sticky;left:212px;z-index:2;background:#fff;text-align:left;
  color:#52514e;min-width:104px;font-size:11px;}
table.mtx thead .c0,table.mtx thead .c1{z-index:4;background:#f7f8fa;}
table.mtx .tt{font-weight:750;background:#f7f8fa;border-left:1px solid #e1e0d9;
  border-right:1px solid #e1e0d9;}
table.mtx tr.grp td{border-top:2px solid #e6e5df;}
table.mtx tr.grp td.c0,table.mtx tr.grp td.c1{border-top:2px solid #e6e5df;}
table.mtx td.z{color:#c3c2b7;}
table.mtx .ent-ok{background:#eef8f3;}   table.mtx .ent-lo{background:#fdf0f0;}
table.mtx .ab0{background:#f2f9f5;}      table.mtx .ab1{background:#fdf5e8;}
table.mtx .ab2{background:#fbeaea;font-weight:700;}
table.mtx .sol{color:#1c5cab;font-weight:650;}
table.mtx tbody tr:hover td{background:#f6f9fe;}
table.mtx tbody tr:hover td.c0,table.mtx tbody tr:hover td.c1{background:#f6f9fe;}
</style>"""

    cab = ('<tr><th class="c0">Função</th><th class="c1">Indicador</th>'
           '<th class="tt">Mês</th>'
           + "".join(f'<th>{d}<span class="wd">{sem.get(d, "")}</span></th>' for d in dias)
           + "</tr>")

    corpo = []
    for f in ordem:
        g = det[det.Funcao == f].set_index("DiaNum")
        sol = g["Solicitado"].reindex(dias).fillna(0)
        ent = g["Entregue"].reindex(dias).fillna(0)
        fal = g["Falta"].reindex(dias).fillna(0)
        esc = g["Escala"].reindex(dias).fillna(0)
        abs_ = np.where(esc > 0, fal / esc.replace(0, np.nan) * 100, np.nan)

        t_sol, t_ent, t_esc, t_fal = sol.sum(), ent.sum(), esc.sum(), fal.sum()
        t_abs = t_fal / t_esc * 100 if t_esc else np.nan

        c_sol = "".join(f'<td class="sol{" z" if v == 0 else ""}">{v:.0f}</td>' for v in sol)
        c_ent = "".join(
            f'<td class="{"ent-lo" if (s > 0 and v < s) else ("ent-ok" if v > 0 else "")}'
            f'{" z" if v == 0 else ""}">{v:.0f}</td>' for v, s in zip(ent, sol))

        def _cls(a):
            if not np.isfinite(a):
                return ""
            return "ab0" if a <= META_ABS else ("ab1" if a <= 15 else "ab2")
        c_abs = "".join(
            f'<td class="{_cls(a)}">{"—" if not np.isfinite(a) else _p(a, 0)}</td>' for a in abs_)

        corpo.append(
            f'<tr class="grp"><td class="c0" rowspan="3">{f}</td>'
            f'<td class="c1">Solicitado</td><td class="tt">{t_sol:.0f}</td>{c_sol}</tr>'
            f'<tr><td class="c1">Entregue</td><td class="tt">{t_ent:.0f}</td>{c_ent}</tr>'
            f'<tr><td class="c1">Absenteísmo</td>'
            f'<td class="tt">{"—" if not np.isfinite(t_abs) else _p(t_abs, 1)}</td>{c_abs}</tr>')

    return (css + '<div class="mtx-wrap"><table class="mtx"><thead>' + cab
            + "</thead><tbody>" + "".join(corpo) + "</tbody></table></div>"
            + '<div style="font-size:.78rem;color:#898781;margin-top:8px;">'
            'Entregue com fundo claro-verde: igual ou acima do solicitado no dia; '
            'rosa: abaixo. Absenteísmo: verde até 5%, âmbar até 15%, vermelho acima. '
            '“—” indica função sem escala no dia.</div>')


# ------------------------------------------------------------ texto analitico
def _texto(t, cob, absent, posto, dia, fun, d_ini, d_fim):
    per = f"{d_ini:02d} a {d_fim:02d}/07"
    fds, sem = dia[dia.FimDeSemana], dia[~dia.FimDeSemana]
    a_fds = fds.Falta.sum() / fds.Escala.sum() * 100 if fds.Escala.sum() else 0
    a_sem = sem.Falta.sum() / sem.Escala.sum() * 100 if sem.Escala.sum() else 0

    meio = dia.DiaNum.median()
    q1, q2 = dia[dia.DiaNum <= meio], dia[dia.DiaNum > meio]
    a1 = q1.Falta.sum() / q1.Escala.sum() * 100 if q1.Escala.sum() else 0
    a2 = q2.Falta.sum() / q2.Escala.sum() * 100 if q2.Escala.sum() else 0
    tend = a2 - a1

    pior = dia.loc[dia["Absenteismo_%"].idxmax()]
    crit = fun[fun.Escala >= 30].sort_values("Absenteismo_%", ascending=False).head(3)
    l_crit = ", ".join(f"<b>{r.Funcao}</b> ({_p(r['Absenteismo_%'])})" for _, r in crit.iterrows())
    peso = crit.Falta.sum() / t.Falta * 100 if t.Falta else 0

    deficit = fun[(fun.Solicitado > 0) & (fun["Cobertura_%"] < 100)].sort_values("Cobertura_%")
    l_def = ", ".join(f"<b>{r.Funcao}</b> ({_p(r['Cobertura_%'], 0)})"
                      for _, r in deficit.head(3).iterrows())

    if cob >= 100:
        entrega = (f"A operação entregou <b>{_fmt(t.Entregue)}</b> diárias contra "
                   f"<b>{_fmt(t.Solicitado)}</b> solicitadas via STH — cobertura de "
                   f"<b>{_p(cob)}</b>, com saldo positivo de {_fmt(t.Entregue - t.Solicitado)} "
                   f"diárias. O contrato foi honrado em volume.")
    else:
        entrega = (f"A operação entregou <b>{_fmt(t.Entregue)}</b> diárias contra "
                   f"<b>{_fmt(t.Solicitado)}</b> solicitadas via STH — cobertura de "
                   f"<b>{_p(cob)}</b>, um déficit de {_fmt(t.Solicitado - t.Entregue)} diárias.")

    if tend > 1.5:
        curva = (f"O indicador piora ao longo do mês: {_p(a1)} na primeira metade contra "
                 f"{_p(a2)} na segunda (+{_n(tend)} p.p.). É o desgaste típico de temporário "
                 f"em pico de operação e antecipa risco de saída antes do fim do contrato.")
    elif tend < -1.5:
        curva = (f"O indicador cede ao longo do mês: {_p(a1)} na primeira metade contra "
                 f"{_p(a2)} na segunda ({_n(tend)} p.p.), sinal de que integração e ajuste "
                 f"de escala surtiram efeito.")
    else:
        curva = (f"O indicador é estável no mês ({_p(a1)} na primeira metade contra {_p(a2)} "
                 f"na segunda), o que aponta causa estrutural e não evento isolado.")

    dif = a_fds - a_sem
    if abs(dif) >= 2:
        lado = "fins de semana" if dif > 0 else "dias úteis"
        semana = (f"As faltas se concentram nos <b>{lado}</b>: {_p(a_fds)} em sábado e domingo "
                  f"contra {_p(a_sem)} de segunda a sexta. Como o pico de ocupação do resort é "
                  f"no fim de semana, o impacto percebido pelo cliente é maior que o número.")
    else:
        semana = (f"Não há diferença relevante entre fim de semana ({_p(a_fds)}) e dias úteis "
                  f"({_p(a_sem)}): o absenteísmo é distribuído.")

    diag = f"""<div class="tj-note"><span class="hd">Diagnóstico · {per}</span><ul>
<li><b>Entrega.</b> {entrega} Desse total, {_fmt(t.Trabalhou)} diárias foram de presença
física em posto ({_p(posto)} da demanda); o restante são folgas de escala e afastamentos
legais, previstos no dimensionamento e sem impacto contratual.</li>
<li><b>Absenteísmo.</b> {_p(absent, 2)} no período — {_fmt(t.Falta)} faltas sobre
{_fmt(t.Escala)} diárias de escala. {curva}</li>
<li><b>Onde dói.</b> {l_crit} concentram {_p(peso, 0)} das faltas do período. O pico foi
no dia {int(pior.DiaNum)}/07 ({pior.DiaSemana}), com {_p(pior['Absenteismo_%'])}.</li>
<li><b>Ritmo semanal.</b> {semana}</li>
{f"<li><b>Cobertura abaixo do pedido.</b> {l_def} ficaram sob 100% de cobertura no período — são as funções em que a demanda do STH não foi integralmente suprida.</li>" if len(deficit) else ""}
</ul></div>"""

    acoes = []
    if len(crit):
        acoes.append(f"<li><b>Ação focada nas três funções críticas.</b> {l_crit}. "
                     f"Revisar escala e deslocamento, conferir se o horário praticado bate com "
                     f"o horário do STH e abrir feedback com a liderança da área nas duas "
                     f"primeiras semanas de contrato — é quando a falta começa.</li>")
    if absent > META_ABS:
        acoes.append(f"<li><b>Rotina de consequência.</b> Com {_p(absent, 2)} contra meta de "
                     f"{_p(META_ABS, 0)}: advertência formal na primeira falta não justificada, "
                     f"comunicação ao gestor da área no mesmo dia e substituição a partir da "
                     f"terceira ocorrência.</li>")
    if dif >= 2:
        acoes.append("<li><b>Reforço de fim de semana.</b> Escalar cadastro reserva "
                     "especificamente para sábado e domingo, quando a falta custa mais "
                     "caro em experiência do hóspede.</li>")
    if len(deficit):
        acoes.append("<li><b>Fechar o déficit por função.</b> Antecipar o corte de "
                     "recrutamento das funções listadas acima para 15 dias antes do início "
                     "do STH e manter banco de reserva ativo durante toda a temporada.</li>")
    acoes.append("<li><b>Medir durante, não depois.</b> Publicar este painel semanalmente "
                 "ao longo da temporada — cobertura perdida só é recuperável com o mês "
                 "em curso.</li>")

    plano = f"""<div class="tj-note bad" style="margin-top:12px;">
<span class="hd">Plano de ação</span><ul>{''.join(acoes)}</ul></div>"""
    return diag + plano
