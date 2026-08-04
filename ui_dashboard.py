# -*- coding: utf-8 -*-
"""
================================================================================
 SISTEMA VISUAL DO DASHBOARD  |  Mendes RH x Aviva / Rio Quente Resorts
================================================================================
Paleta, CSS e componentes compartilhados por todas as abas.

A paleta e validada para daltonismo: separacao CVD >= 8 e visao normal >= 15
em todos os pares em uso (OKLab x100). Nenhum dado depende de cor isolada -
todo mark colorido carrega rotulo ou legenda.
================================================================================
"""
import base64
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------- paleta
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"      # categoricas 1-2-3
S4 = "#4a3aa7"                                     # categorica auxiliar
GOOD, WARN, SERIOUS, CRIT = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURF = "#eceae4", "#c3c2b7", "#ffffff"
SEQ = ["#eef5fe", "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
       "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#0d366b"]

FONTE = 'system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'

CSS = """
<style>
:root{--ink:#0b0b0b;--ink2:#52514e;--mut:#898781;--line:rgba(11,11,11,.08);}
.stApp{background:#f4f5f7;}
section.main > div.block-container{padding-top:1.1rem;max-width:1500px;}
html, body, [class*="css"]{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}

/* cartoes */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:#fff;border-radius:18px;border:1px solid var(--line)!important;
  box-shadow:0 1px 2px rgba(11,11,11,.04),0 10px 30px -14px rgba(11,11,11,.16);
  padding:6px 20px 14px 20px;margin-bottom:16px;}

/* cabecalho */
.app-head h1{margin:0;font-size:1.32rem;font-weight:760;letter-spacing:-.025em;
  color:var(--ink);line-height:1.25;}
.app-head .sub{font-size:.83rem;color:var(--ink2);margin-top:2px;}
.app-logo{display:flex;align-items:center;justify-content:center;height:100%;}
.app-logo img{max-height:70px;max-width:270px;width:auto;height:auto;object-fit:contain;
  display:block;}

/* abas em pilulas */
div[data-testid="stHorizontalBlock"] .stButton>button{
  border-radius:999px!important;padding:9px 18px!important;font-size:.9rem!important;
  font-weight:650!important;border:1px solid var(--line)!important;
  background:#fff!important;color:var(--ink2)!important;box-shadow:none!important;
  transition:background .15s,color .15s,border-color .15s;}
div[data-testid="stHorizontalBlock"] .stButton>button:hover{
  border-color:#2a78d6!important;color:#2a78d6!important;}
div[data-testid="stHorizontalBlock"] .stButton>button[kind="primary"]{
  background:#2a78d6!important;color:#fff!important;border-color:#2a78d6!important;
  box-shadow:0 6px 16px -8px rgba(42,120,214,.9)!important;}

/* faixa hero */
.hero{background:linear-gradient(125deg,#0d366b 0%,#1c5cab 52%,#2a78d6 100%);
  border-radius:20px;padding:22px 26px 20px 26px;color:#fff;margin-bottom:16px;
  box-shadow:0 14px 34px -18px rgba(13,54,107,.75);
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}
.hero .top{display:flex;align-items:flex-end;justify-content:space-between;
  gap:18px;flex-wrap:wrap;margin-bottom:18px;}
.hero h2{margin:0;font-size:1.5rem;font-weight:760;letter-spacing:-.025em;}
.hero .sub{font-size:.86rem;opacity:.78;margin-top:3px;}
.hero .chip{font-size:.72rem;font-weight:700;letter-spacing:.03em;
  background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);
  padding:5px 12px;border-radius:999px;}
.tiles{display:grid;gap:12px;}
.tile{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.16);
  border-radius:14px;padding:13px 15px 12px 15px;display:flex;flex-direction:column;
  min-height:108px;}
.tile .lb{font-size:.68rem;font-weight:700;letter-spacing:.07em;
  text-transform:uppercase;opacity:.72;}
.tile .vl{font-size:1.9rem;font-weight:780;line-height:1.15;margin-top:3px;
  letter-spacing:-.02em;}
.tile .sb{font-size:.72rem;opacity:.74;margin-top:auto;line-height:1.35;}
.tile .bd{display:inline-block;font-size:.66rem;font-weight:750;padding:2px 8px;
  border-radius:999px;margin-top:6px;align-self:flex-start;
  background:rgba(255,255,255,.18);}
.spark{margin-top:6px;opacity:.9;}

/* titulos de secao */
.sec{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:10px 0 2px 0;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}
.sec .t{font-size:1.02rem;font-weight:730;color:var(--ink);letter-spacing:-.012em;}
.sec .k{font-size:.7rem;font-weight:750;letter-spacing:.06em;text-transform:uppercase;
  color:#2a78d6;background:#eaf2fd;padding:2px 9px;border-radius:999px;}
.secd{font-size:.83rem;color:var(--ink2);margin:2px 0 8px 0;line-height:1.5;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}

/* blocos de texto */
.note{border-left:4px solid #2a78d6;background:#fbfcfe;border-radius:0 12px 12px 0;
  padding:14px 18px;font-size:.92rem;color:var(--ink);line-height:1.65;margin-top:6px;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}
.note.good{border-left-color:#0ca30c;background:#f6fcf6;}
.note.warn{border-left-color:#fab219;background:#fffdf7;}
.note.bad{border-left-color:#d03b3b;background:#fffbfb;}
.note .hd{font-weight:750;font-size:.95rem;display:block;margin-bottom:5px;}
.note ul{margin:6px 0 0 0;padding-left:19px;}
.note li{margin-bottom:7px;}
.note b{font-weight:700;}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:6px;}
</style>
"""


def aplicar_css():
    st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------- formatacao
def fmt(n, casas=0):
    return f"{n:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def pc(n, casas=1):
    return f"{n:.{casas}f}".replace(".", ",") + "%"


def num(n, casas=1):
    return f"{n:.{casas}f}".replace(".", ",")


def logo_b64(caminho):
    try:
        return base64.b64encode(Path(caminho).read_bytes()).decode()
    except Exception:
        return ""


# ----------------------------------------------------------------- componentes
def sparkline(vals, cor="#ffffff", w=150, h=26):
    v = [x for x in vals if pd.notna(x)]
    if len(v) < 2:
        return ""
    lo, hi = min(v), max(v)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i / (len(v) - 1) * w:.1f},{h - (x - lo) / rng * (h - 4) - 2:.1f}"
                   for i, x in enumerate(v))
    return (f'<svg class="spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'preserveAspectRatio="none"><polyline points="{pts}" fill="none" '
            f'stroke="{cor}" stroke-width="1.8" stroke-linejoin="round" '
            f'stroke-linecap="round" opacity=".85"/></svg>')


def tile(lb, vl, sb, spark="", badge=None):
    bd = f'<span class="bd">{badge}</span>' if badge else ""
    return (f'<div class="tile"><div class="lb">{lb}</div><div class="vl">{vl}</div>'
            f'{spark}{bd}<div class="sb">{sb}</div></div>')


def hero(titulo, subtitulo, tiles, chip=None):
    c = f'<div><span class="chip">{chip}</span></div>' if chip else ""
    st.markdown(
        f'<div class="hero"><div class="top"><div><h2>{titulo}</h2>'
        f'<div class="sub">{subtitulo}</div></div>{c}</div>'
        f'<div class="tiles" style="grid-template-columns:repeat({len(tiles)},1fr);">'
        + "".join(tiles) + "</div></div>", unsafe_allow_html=True)


def secao(titulo, kicker=None, desc=None):
    k = f'<span class="k">{kicker}</span>' if kicker else ""
    d = f'<div class="secd">{desc}</div>' if desc else ""
    st.markdown(f'<div class="sec"><span class="t">{titulo}</span>{k}</div>{d}',
                unsafe_allow_html=True)


def nota(html, tipo=""):
    st.markdown(f'<div class="note {tipo}">{html}</div>', unsafe_allow_html=True)


def layout(fig, altura=330, legenda=True, ytitulo="", hover="x unified"):
    fig.update_layout(
        height=altura, margin=dict(l=6, r=6, t=8, b=6),
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family=FONTE, size=12, color=INK2),
        hovermode=hover,
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


SEM_BARRA = {"displayModeBar": False}


# ------------------------------------------------------------------ desenho
# Cada aba produz uma "seção": {"titulo", "sub", "blocos"}. Os blocos abaixo
# são desenhados na tela por desenhar() e convertidos em PDF por relatorio_pdf,
# garantindo que painel e relatório nunca divirjam.
#
#   {"t":"hero",   titulo, sub, chip, tiles:[{lb,vl,sb,spark,badge}]}
#   {"t":"fig",    titulo, kicker, desc, fig, altura}
#   {"t":"texto",  titulo, kicker, html}
#   {"t":"nota",   html, estilo}
#   {"t":"tabela", titulo, desc, df}
#   {"t":"html",   html}                      (só tela)
#   {"t":"custom", fn}                        (só tela)
#   {"t":"cards",  itens:[[bloco, ...], ...]} (colunas lado a lado)
#
# Sinalizadores opcionais: so_tela=True / so_pdf=True.

SEM_BARRA_CFG = {"displayModeBar": False}


def _bloco_tela(b):
    t = b.get("t")
    if b.get("so_pdf"):
        return
    if t == "hero":
        hero(b["titulo"], b.get("sub", ""),
             [tile(x["lb"], x["vl"], x.get("sb", ""), x.get("spark", ""), x.get("badge"))
              for x in b["tiles"]], b.get("chip"))
    elif t == "fig":
        with st.container(border=True):
            secao(b.get("titulo", ""), b.get("kicker"), b.get("desc"))
            st.plotly_chart(b["fig"], use_container_width=True, config=SEM_BARRA_CFG)
            for extra in b.get("extras", []):
                nota(extra["html"], extra.get("estilo", ""))
    elif t == "texto":
        with st.container(border=True):
            secao(b.get("titulo", ""), b.get("kicker"))
            st.markdown(b["html"], unsafe_allow_html=True)
    elif t == "nota":
        nota(b["html"], b.get("estilo", ""))
    elif t == "tabela":
        with st.container(border=True):
            secao(b.get("titulo", ""), b.get("kicker"), b.get("desc"))
            st.dataframe(b["df"], use_container_width=True, hide_index=True,
                         height=b.get("altura_tabela", 360))
    elif t == "html":
        st.markdown(b["html"], unsafe_allow_html=True)
    elif t == "custom":
        b["fn"]()
    elif t == "cards":
        cols = st.columns(len(b["itens"]), gap="medium")
        for col, filhos in zip(cols, b["itens"]):
            with col:
                for f in filhos:
                    _bloco_tela(f)


def desenhar(sec):
    for b in sec["blocos"]:
        _bloco_tela(b)
