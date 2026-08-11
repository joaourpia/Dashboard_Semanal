# -*- coding: utf-8 -*-
"""
================================================================================
 ABA "PESQUISA" - Duas rodadas de escuta do temporario
 Mendes RH x Aviva / Rio Quente Resorts
================================================================================
Rodada 1 . Experiencia da temporada ....... dados/pesquisa/RESPOSTAS_PESQUISA.xlsx
Rodada 2 . Salario, condicoes e efetivacao  dados/pesquisa/RESPOSTAS_PESQUISA_2.xlsx

A aba tem tres visoes, selecionadas por um seletor no topo:
  Rodada 1        experiencia, absenteismo, vinculo
  Rodada 2        salario, condicoes de trabalho, respeito, efetivacao CLT
  Consolidado     o que as duas rodadas dizem juntas

Cada visao monta uma "secao" no mesmo formato de blocos das demais abas:
construir_*() devolve {"titulo","sub","blocos"}, ui.desenhar() joga na tela e
relatorio_pdf percorre a mesma lista. Tela e relatorio nunca divergem.

Paleta identica a das outras abas, ja validada para daltonismo. Nenhum dado
depende de cor isolada - todo mark colorido carrega rotulo.

Recortes com menos de 5 respostas sao suprimidos automaticamente: nesse volume
o respondente e identificavel e o anonimato prometido no formulario cai.

Relatos nominais (assedio, conduta individual) NAO entram no painel. Eles vao
para o anexo de circulacao restrita e seguem por apuracao formal.

REGRAS DE ESCRITA DOS TEXTOS DESTA ABA
--------------------------------------
Quem escreve e a Mendes RH; quem le e a Aviva, que assiste a apresentacao.
Por isso: primeira pessoa, nenhum travessao, nenhuma orientacao interna do tipo
"levar isso ao cliente", e nada de "o cliente" para se referir a quem esta
lendo. Os mesmos criterios do relatorio em Word.
================================================================================
"""
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ui_dashboard as ui
import pesquisa_dados as pd_src
from pesquisa_dados import (G_CUMPRIU, G_SAIU, MIN_RECORTE,
                            OPC_ALAVANCA, OPC_CONTRA, OPC_MELHORAR,
                            ORDEM_CLT, ORDEM_EXPECT, ORDEM_MERCADO, ORDEM_RESPEITO,
                            contagem, contagem_multipla, enps)

TITULO = "Pesquisa de Experiência do Temporário"
SUBTITULO = "Temporada de julho de 2026 · coleta de 6 a 10 de agosto"

TITULO_R2 = "Pesquisa de Salário, Condições e Efetivação"
SUBTITULO_R2 = "Temporada de julho de 2026 · coleta em 10 de agosto"

TITULO_CONS = "Pesquisa · visão consolidada"
SUBTITULO_CONS = "As duas rodadas lidas em conjunto"

S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
GOOD, WARN, SERIOUS, CRIT = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURF = "#eceae4", "#c3c2b7", "#ffffff"

K_GRUPO, K_FUNC = "pq_grupo", "pq_funcao"
K_VISAO = "pq_visao"
K_FUNC2 = "pq_funcao_r2"

V_R1 = "Rodada 1 · experiência"
V_R2 = "Rodada 2 · salário e efetivação"
V_CONS = "Visão consolidada"


def _rot(t):
    """Normaliza rotulo vindo do Google Forms para exibicao.

    Algumas opcoes do questionario tem travessao no proprio texto, por exemplo
    "Transporte — nao consegui chegar". O travessao e o tique de escrita de IA
    mais facil de reconhecer, entao troco por virgula na hora de mostrar. O
    valor original continua intacto na base: isto e so apresentacao.
    """
    return re.sub(r"\s*[—–]\s*", ", ", str(t))


def _rots(seq):
    return [_rot(x) for x in seq]


def _p(n, casas=1):
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "—"
    return f"{n:.{casas}f}".replace(".", ",") + "%"


def _n(n, casas=1):
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "—"
    return f"{n:.{casas}f}".replace(".", ",")


@st.cache_data(show_spinner=False)
def carregar():
    return pd_src.consolidar()


@st.cache_data(show_spinner=False)
def carregar2():
    return pd_src.carregar_r2()


# ------------------------------------------------------------------ graficos
def _barras_h(rotulos, valores, cor, sufixo="", altura=None, cores=None,
              texto=None, margem_dir=52):
    fig = go.Figure(go.Bar(
        x=list(valores), y=_rots(rotulos), orientation="h",
        marker=dict(color=cores or cor,
                    line=dict(color="rgba(0,0,0,0)", width=0)),
        text=texto or [f"{v}{sufixo}" for v in valores],
        textposition="outside", cliponaxis=False,
        textfont=dict(size=11.5, color=INK2), hoverinfo="skip"))
    alt = altura or max(150, 30 * len(list(rotulos)) + 40)
    fig.update_layout(
        height=alt, margin=dict(l=6, r=margem_dir, t=8, b=24), showlegend=False,
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family=ui.FONTE, size=12, color=INK2),
        xaxis=dict(showgrid=True, gridcolor=GRID, zerolinecolor=AXIS,
                   showticklabels=False, range=[0, max(list(valores) or [1]) * 1.2]),
        yaxis=dict(autorange="reversed", showgrid=False,
                   linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=INK, size=11.5)))
    return fig


MIN_ROTULO_INTERNO = 20.0   # abaixo disso o texto nao cabe dentro da fatia


def _pilha(segmentos, altura=132):
    """Barra empilhada horizontal. segmentos = [(rotulo, valor, cor), ...].

    Fatia estreita nao recebe rotulo interno - o texto sairia girado e
    ilegivel. Quando ha ao menos uma fatia assim, a legenda embaixo passa a
    ser exibida para todas, de modo que nenhuma leitura dependa de cor.
    """
    tot = sum(v for _, v, _ in segmentos)
    if not tot:
        return None
    visiveis = [(r, v, c) for r, v, c in segmentos if v]
    apertado = any(v / tot * 100 < MIN_ROTULO_INTERNO for _, v, _ in visiveis)

    fig = go.Figure()
    for rot, val, cor in visiveis:
        pcs = val / tot * 100
        curto = _rot(rot).split(" (")[0]
        dentro = pcs >= MIN_ROTULO_INTERNO
        fig.add_bar(x=[val], y=["x"], orientation="h",
                    name=f"{curto} · {val} · {_p(pcs)}" if apertado else curto,
                    marker=dict(color=cor),
                    text=[f"{curto}<br>{val} · {_p(pcs)}" if dentro else ""],
                    textposition="inside", insidetextanchor="middle",
                    textfont=dict(size=11.5, color="#fff" if cor != WARN else INK),
                    hoverinfo="skip")
    fig.update_layout(
        barmode="stack", height=altura + (52 if apertado else 0),
        margin=dict(l=6, r=6, t=10, b=6),
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family=ui.FONTE, size=12, color=INK2),
        showlegend=apertado,
        legend=dict(orientation="h", y=-0.08, x=0, xanchor="left",
                    traceorder="normal",
                    font=dict(size=11, color=INK2), bgcolor="rgba(0,0,0,0)",
                    itemclick=False, itemdoubleclick=False),
        xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def _histograma_nota(serie, cor_base=S1):
    """Distribuicao de uma nota 0-10, colorida pela faixa do indice."""
    v = pd.Series(serie).dropna().astype(int)
    if v.empty:
        return None
    cont = v.value_counts().reindex(range(11), fill_value=0)
    cores = [CRIT if i <= 6 else (WARN if i <= 8 else GOOD) for i in cont.index]
    fig = go.Figure(go.Bar(
        x=[str(i) for i in cont.index], y=cont.values,
        marker=dict(color=cores), text=[str(x) if x else "" for x in cont.values],
        textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=INK2), hoverinfo="skip"))
    fig.update_layout(
        height=210, margin=dict(l=6, r=6, t=16, b=24), showlegend=False,
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        bargap=.18, font=dict(family=ui.FONTE, size=12, color=INK2),
        xaxis=dict(showgrid=False, tickfont=dict(color=INK, size=11.5),
                   title=dict(text="nota atribuída", font=dict(size=10.5, color=MUTED))),
        yaxis=dict(showgrid=True, gridcolor=GRID, showticklabels=False,
                   range=[0, max(cont.values) * 1.22]))
    return fig


def _fig_participacao(base):
    fun = contagem(base.funcao).head(10)
    loc = contagem(base.local).head(10)
    return (_barras_h(fun.index, fun.values, S1),
            _barras_h(loc.index, loc.values, S4))


def _fig_enps_pilha(e):
    if not e:
        return None
    return _pilha([("Recomendam (notas 9 e 10)", e["promotores"], GOOD),
                   ("Indiferentes (7 e 8)", e["neutros"], WARN),
                   ("Não recomendam (0 a 6)", e["detratores"], CRIT)])


def _conta_indice(e, oque="o índice"):
    """Escreve a subtracao que produz o indice.

    A barra empilhada mostra tres percentuais, e o indice e a diferenca entre
    dois deles. Sem a conta escrita, quem le ve 49,4% / 31,6% / 19,0% e nao tem
    como chegar sozinho em 30,4. Este bloco fecha essa lacuna.
    """
    if not e:
        return None
    p = e["promotores"] / e["n"] * 100
    d = e["detratores"] / e["n"] * 100
    z = e["neutros"] / e["n"] * 100
    return {"html":
            f"<span class='hd'>Como se chega em {_n(e['enps'])}</span>"
            f"<b>{_p(p)}</b> deram nota 9 ou 10 e contam como quem recomenda. "
            f"<b>{_p(d)}</b> deram de 0 a 6 e contam como quem não recomenda. "
            f"{_p(p)} menos {_p(d)} dá <b>{_n(e['enps'])}</b>, que é {oque}. "
            f"Os {_p(z)} que deram 7 ou 8 ficam fora da conta: o método os trata como "
            f"indiferentes, gente que não faz campanha a favor nem contra. Por isso a "
            f"escala vai de −100 a +100 e não de 0 a 100."}


def _fig_enps_funcao(base):
    linhas = []
    for f, g in base.groupby("funcao"):
        if len(g) < MIN_RECORTE or not f:
            continue
        e = enps(g.nps)
        if e:
            linhas.append((f, e["enps"], e["n"]))
    if not linhas:
        return None, 0
    linhas.sort(key=lambda x: -x[1])
    rot = [f"{_rot(f)}  ·  n {n}" for f, _, n in linhas]
    val = [v for _, v, _ in linhas]
    cores = [GOOD if v >= 60 else (WARN if v >= 40 else CRIT) for v in val]
    fig = _barras_h(rot, val, None, cores=cores, texto=[_n(v) for v in val])
    fig.update_xaxes(range=[min(0, min(val) * 1.3), max(val) * 1.28])
    return fig, len(linhas)


def _fig_causas(base):
    faltou = base[base.faltou]
    s, tot = contagem_multipla(faltou.causa_falta_lista)
    if tot == 0:
        return None, 0
    s = s.head(9)
    pcs = [round(v / tot * 100, 1) for v in s.values]
    cores = [MUTED if "Não sei" in k else S2 for k in s.index]
    return _barras_h(s.index, pcs, S2, cores=cores,
                     texto=[_p(v) for v in pcs]), tot


def _fig_preditor(base, coluna, rotulos_ordem):
    """Barras pareadas: taxa de falta e intenção de saída por nível."""
    dados = []
    for rot in rotulos_ordem:
        g = base[base[coluna] == rot] if coluna in base else base.iloc[0:0]
        if len(g) < MIN_RECORTE:
            continue
        f = round(g.faltou.sum() / len(g) * 100)
        ps = g["pensou_sair"].dropna() if "pensou_sair" in g else pd.Series(dtype=object)
        p = round((ps != "Não, nunca pensei").sum() / len(ps) * 100) if len(ps) else None
        dados.append((f"{_rot(rot)}  ·  n {len(g)}", f, p))
    if not dados:
        return None
    fig = go.Figure()
    fig.add_bar(y=[d[0] for d in dados], x=[d[1] for d in dados], orientation="h",
                name="Faltou ao menos 1 dia", marker=dict(color=S2),
                text=[f"{d[1]}%" for d in dados], textposition="outside",
                cliponaxis=False, textfont=dict(size=11, color=INK2), hoverinfo="skip")
    if any(d[2] is not None for d in dados):
        fig.add_bar(y=[d[0] for d in dados], x=[d[2] or 0 for d in dados],
                    orientation="h", name="Pensou em sair antes do fim",
                    marker=dict(color=S4),
                    text=[f"{d[2]}%" if d[2] is not None else "" for d in dados],
                    textposition="outside", cliponaxis=False,
                    textfont=dict(size=11, color=INK2), hoverinfo="skip")
    fig.update_layout(
        barmode="group", bargap=.28, bargroupgap=.08,
        height=max(150, 62 * len(dados) + 54),
        margin=dict(l=6, r=52, t=8, b=6),
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family=ui.FONTE, size=12, color=INK2),
        legend=dict(orientation="h", y=1.14, x=0, xanchor="left",
                    font=dict(size=11.5, color=INK2), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=True, gridcolor=GRID, showticklabels=False, range=[0, 118]),
        yaxis=dict(autorange="reversed", showgrid=False, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=INK, size=11.5)))
    return fig


def _fig_janela(s):
    if s is None or s.empty:
        return None
    cd = "Em que momento você decidiu que ia sair?"
    tp = "Quanto tempo você ficou antes de sair?"
    ordem_d = ["Já nos primeiros dias", "Na primeira semana",
               "Depois de mais ou menos duas semanas",
               "Perto do fim, quando já estava quase acabando",
               "Não foi decisão minha — fui desligado"]
    ordem_t = ["Menos de 7 dias", "De 7 a 15 dias", "De 15 a 30 dias", "Mais de 30 dias"]
    cd_c = s[cd].value_counts() if cd in s else pd.Series(dtype=int)
    tp_c = s[tp].value_counts() if tp in s else pd.Series(dtype=int)
    rot, val, cor, grp = [], [], [], []
    for o in ordem_d:
        if cd_c.get(o, 0):
            rot.append(o); val.append(int(cd_c[o])); grp.append("d")
    for o in ordem_t:
        if tp_c.get(o, 0):
            rot.append(o); val.append(int(tp_c[o])); grp.append("t")
    if not rot:
        return None
    escala = [CRIT, SERIOUS, WARN, MUTED, MUTED]
    i = 0
    for g in grp:
        if g == "d":
            cor.append(escala[min(i, 4)]); i += 1
        else:
            cor.append(S1)
    return _barras_h(rot, val, None, cores=cor, texto=[str(v) for v in val])


# -------------------------------------------------------------------- tabelas
def _tabela_html(colunas, linhas, largura_1a="auto"):
    """Tabela HTML com celulas coloridas. linhas = [[(txt, bg, fg), ...], ...]."""
    css = """<style>
.pq-wrap{overflow:auto;border:1px solid rgba(11,11,11,.09);border-radius:14px;background:#fff;}
table.pqm{border-collapse:separate;border-spacing:0;width:100%;
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:12.5px;
  font-variant-numeric:tabular-nums;color:#0b0b0b;}
table.pqm th{position:sticky;top:0;background:#2a78d6;color:#fff;font-weight:700;
  font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;padding:9px 11px;
  text-align:right;z-index:2;}
table.pqm th:first-child{text-align:left;}
table.pqm td{padding:8px 11px;text-align:right;border-bottom:1px solid #f0efec;}
table.pqm td:first-child{text-align:left;font-weight:640;}
table.pqm td.q{font-weight:730;}
.pq-vazio{padding:18px;color:#898781;font-size:.88rem;}
</style>"""
    th = "".join(f"<th>{c}</th>" for c in colunas)
    trs = []
    for linha in linhas:
        tds = []
        for cel in linha:
            if isinstance(cel, tuple):
                txt, bg, fg = cel
                tds.append(f"<td class='q' style='background:{bg};color:{fg}'>{txt}</td>")
            else:
                tds.append(f"<td>{cel}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return css + f"<div class='pq-wrap'><table class='pqm'><thead><tr>{th}</tr></thead>" \
                 f"<tbody>{''.join(trs)}</tbody></table></div>"


def _cor_recom(v):
    if pd.isna(v):
        return "#f7f8fa", INK
    return (GOOD, "#fff") if v >= 60 else ((WARN, INK) if v >= 40 else (CRIT, "#fff"))


def _cor_nota(v):
    """Nota 0-10: 9+ verde, 8 amarelo, 7 laranja, abaixo vermelho."""
    if pd.isna(v):
        return "#f7f8fa", INK
    if v >= 8.8:
        return GOOD, "#fff"
    if v >= 8.0:
        return WARN, INK
    if v >= 7.0:
        return SERIOUS, "#fff"
    return CRIT, "#fff"


def _cor_pct_bom(v, bom, medio):
    """Quanto maior melhor."""
    if pd.isna(v):
        return "#f7f8fa", INK
    if v >= bom:
        return GOOD, "#fff"
    if v >= medio:
        return WARN, INK
    return CRIT, "#fff"


def _cor_ruim(v, bom, medio):
    """Quanto menor melhor (faltou, pensou em sair)."""
    if pd.isna(v):
        return "#f7f8fa", INK
    if v <= bom:
        return GOOD, "#fff"
    if v <= medio:
        return WARN, INK
    return (SERIOUS, "#fff") if v <= medio + 20 else (CRIT, "#fff")


def _matriz_funcao(base):
    linhas = []
    for f, g in base.groupby("funcao"):
        if len(g) < MIN_RECORTE or not f:
            continue
        e = enps(g.nps)
        ps = g["pensou_sair"].dropna() if "pensou_sair" in g else pd.Series(dtype=object)
        volt = g.voltaria.dropna()
        linhas.append({
            "Função": f, "n": len(g),
            "Recomendação": e["enps"] if e else np.nan,
            "Faltou": round(g.faltou.sum() / len(g) * 100),
            "Pensou em sair": (round((ps != "Não, nunca pensei").sum() / len(ps) * 100)
                               if len(ps) else np.nan),
            "Voltaria": (round((volt == "Sim").sum() / len(volt) * 100)
                         if len(volt) else np.nan),
        })
    df = pd.DataFrame(linhas)
    return df.sort_values("n", ascending=False) if not df.empty else df


def _matriz_html(df):
    if df.empty:
        return "<div class='pq-vazio'>Sem recortes com 5 ou mais respostas.</div>"
    linhas = []
    for _, r in df.iterrows():
        linhas.append([
            r["Função"], int(r["n"]),
            (_n(r["Recomendação"]), *_cor_recom(r["Recomendação"])),
            (f"{int(r['Faltou'])}%", *_cor_ruim(r["Faltou"], 30, 45)),
            (f"{int(r['Pensou em sair'])}%" if pd.notna(r["Pensou em sair"]) else "—",
             *_cor_ruim(r["Pensou em sair"], 20, 35)),
            f"{int(r['Voltaria'])}%" if pd.notna(r["Voltaria"]) else "—",
        ])
    return _tabela_html(["Função", "n", "Recomendação", "Faltou",
                         "Pensou em sair", "Voltaria"], linhas)


def _matriz_r2(d2):
    """Nota de salário, nota de condições, respeito e efetivação por função."""
    linhas = []
    for f, g in d2.groupby("funcao"):
        if len(g) < MIN_RECORTE or not f:
            continue
        linhas.append({
            "Função": f, "n": len(g),
            "Nota salário": round(float(g.nota_salario.mean()), 2),
            "Nota condições": round(float(g.nota_condicoes.mean()), 2),
            "Respeito pleno": round(g.respeito_pleno.sum() / len(g) * 100),
            "Quer CLT": round(g.clt.eq("Sim, com certeza").sum() / len(g) * 100),
        })
    df = pd.DataFrame(linhas)
    return df.sort_values("n", ascending=False) if not df.empty else df


def _matriz_r2_html(df):
    if df.empty:
        return "<div class='pq-vazio'>Sem recortes com 5 ou mais respostas.</div>"
    linhas = []
    for _, r in df.iterrows():
        linhas.append([
            r["Função"], int(r["n"]),
            (_n(r["Nota salário"], 2), *_cor_nota(r["Nota salário"])),
            (_n(r["Nota condições"], 2), *_cor_nota(r["Nota condições"])),
            (f"{int(r['Respeito pleno'])}%", *_cor_pct_bom(r["Respeito pleno"], 75, 55)),
            (f"{int(r['Quer CLT'])}%", *_cor_pct_bom(r["Quer CLT"], 80, 60)),
        ])
    return _tabela_html(["Função", "n", "Nota salário", "Nota condições",
                         "Respeito pleno", "Quer CLT"], linhas)


# ==================================================================== RODADA 1
def _texto_leitura(base, c, s, rs):
    ec, es = rs["enps_cumpriu"], rs["enps_saiu"]
    faltou = base[base.faltou]
    causas, tot = contagem_multipla(faltou.causa_falta_lista)
    top = causas.head(3) if len(causas) else pd.Series(dtype=int)
    cit = int(causas.sum()) if len(causas) else 0
    soma3 = round(sum(top.values) / cit * 100) if cit else 0
    desengaj = sum(int(causas.get(k, 0)) for k in
                   ("Desânimo com o trabalho", "Outro trabalho ou bico no mesmo dia",
                    "Trabalho pesado demais para o valor pago"))
    pdesengaj = round(desengaj / cit * 100, 1) if cit else 0

    partes = [
        f"<p>Recebemos <b>{rs['n_total']} respostas em {rs['convites']} convites</b> "
        f"({_p(rs['taxa_total'])}), contra 76 na rodada do ano passado. Foram "
        f"{_p(rs['taxa_cumpriu'])} de retorno no grupo que cumpriu a temporada e "
        f"{_p(rs['taxa_saiu'])} no grupo que saiu antes do fim.</p>"]
    if tot:
        partes.append(
            f"<p>Entre as {tot} pessoas que faltaram ao menos um dia, as três causas mais citadas "
            f"({', '.join(_rots(top.index[:3]))}) concentram <b>{soma3}% das citações</b>. Desânimo, "
            f"trabalho paralelo e insatisfação com o valor pago somam {_p(pdesengaj)}. O que "
            f"tiramos disso: o absenteísmo de julho foi um problema de saúde e de logística.</p>")
    voz = "Você se sentiu à vontade para falar quando algo estava errado?"
    if voz in base:
        g1, g2 = base[base[voz] == "Sim"], base[base[voz] == "Não"]
        if len(g1) >= MIN_RECORTE and len(g2) >= MIN_RECORTE:
            t1 = round(g1.faltou.sum() / len(g1) * 100)
            t2 = round(g2.faltou.sum() / len(g2) * 100)
            partes.append(
                f"<p>O corte que mais nos chamou atenção foi o da voz. Quem se sentiu à vontade "
                f"para falar quando algo estava errado faltou <b>{t1}%</b>. Quem não se sentiu, "
                f"<b>{t2}%</b>. Nenhum investimento resolve isso. O que resolve é ter alguém "
                f"presente no posto nos primeiros dias.</p>")
    if ec and es:
        partes.append(
            f"<p>O vínculo com a Mendes RH continua alto: índice de recomendação de "
            f"<b>{_n(ec['enps'])}</b> entre quem cumpriu a temporada e <b>{_n(es['enps'])}</b> "
            f"entre quem saiu antes do fim, com {_p(rs['voltaria_sim_talvez'])} dispostos a voltar "
            f"ou considerando voltar. A diferença de {_n(ec['enps'] - es['enps'])} pontos entre os "
            f"dois grupos é pequena, o que significa que a saída antecipada não queimou a relação.</p>")
    if s is not None and not s.empty:
        cd = "Em que momento você decidiu que ia sair?"
        if cd in s:
            cedo = int(s[cd].isin(["Já nos primeiros dias", "Na primeira semana"]).sum())
            partes.append(
                f"<p>A perda acontece cedo: <b>{cedo} de {len(s)}</b> das saídas respondidas foram "
                f"decididas nos primeiros dias ou na primeira semana. É a janela em que hoje "
                f"nenhum de nós faz nada programado, e é onde a próxima temporada tem mais a "
                f"ganhar.</p>")
    return "".join(partes)


def _plano(base, d2=None):
    """Plano de ação com os números tirados da mesma base dos gráficos."""
    PGP = "Você recebeu tudo certo e no prazo (salário, vale, hora extra)?"
    VOZ = "Você se sentiu à vontade para falar quando algo estava errado?"

    def tx(col, valor):
        g = base[base[col] == valor] if col in base else base.iloc[0:0]
        return (round(g.faltou.sum() / len(g) * 100), len(g)) if len(g) else (None, 0)

    err, _ = tx(PGP, "Teve atraso ou erro uma vez")
    ok, _ = tx(PGP, "Sim, sempre")
    sem_voz, _ = tx(VOZ, "Não")
    com_voz, _ = tx(VOZ, "Sim")

    t_pag = (f"Quem passou por um erro faltou {err}% contra {ok}% dos demais. "
             if err is not None and ok is not None else "")
    t_voz = (f"Sem voz a taxa de falta é {sem_voz}%, com voz é {com_voz}%. "
             if sem_voz is not None and com_voz is not None else "")

    t_resp = ""
    if d2 is not None and not d2.empty:
        r2 = pd_src.resumo_r2(d2)
        t_resp = (f"Na rodada 2, só {_p(r2['respeito_sempre'])} se sentiram sempre respeitados e "
                  f"{_p(r2['respeito_falhou'])} responderam “poucas vezes”. ")

    t_diaria = ""
    if d2 is not None and not d2.empty:
        s, tot = contagem_multipla(d2.alavanca_lista)
        if tot:
            dia = round(s.get("Valor maior da diária", 0) / tot * 100, 1)
            bon = round(max(s.get("Bônus por não faltar", 0),
                            s.get("Bônus por ficar até o fim da temporada", 0)) / tot * 100, 1)
            t_diaria = (f"{_p(dia)} pedem diária maior, mas {_p(bon)} aceitariam bônus "
                        f"condicionado, que sai mais barato porque só é pago quando o resultado "
                        f"aparece. ")

    return f"""
<div class="duo">
  <div class="note good"><span class="hd">O que já começamos do nosso lado</span><ul>
    <li><b>Conversa de 5 minutos no 3º e no 7º dia</b> de cada temporário, com registro do que
        foi dito. A decisão de sair é tomada dentro dessa janela.</li>
    <li><b>Revisão do processo de pagamento.</b> {t_pag}Ninguém marcou “teve problema mais de uma
        vez”, então é erro pontual e a correção é nossa.</li>
    <li><b>Entrega do crachá na contratação</b>, com orientação de uso. Uma pessoa passou por
        constrangimento na portaria por não ter recebido o dela.</li>
    <li><b>Campo de nome social no cadastro</b> e orientação aos supervisores. Hoje o cadastro só
        tem o nome de registro, e é ele que chega ao posto.</li>
    <li><b>Canal de escuta ativo durante a temporada</b>, e não só no encerramento. {t_voz}</li>
  </ul></div>
  <div class="note warn"><span class="hd">O que gostaria de decidir com vocês</span><ul>
    <li><b>Alinhamento com efetivos e segurança</b> sobre o tratamento dado ao temporário.
        {t_resp}É o tema que aparece nas duas rodadas e não custa orçamento.</li>
    <li><b>Diagnóstico dirigido em camareira e governança</b>, a função com os piores indicadores
        nas duas rodadas.</li>
    <li><b>Piloto de bônus por assiduidade e por conclusão de contrato</b> em uma função.
        {t_diaria}Meço o efeito contra o histórico de julho.</li>
    <li><b>Auditoria do transporte fretado</b>: rota da recepção, horários, estado dos veículos e
        conduta a bordo. 90,0% dependem só do fretado e não têm plano B.</li>
    <li><b>Trilha de efetivação.</b> Ao fim de cada temporada indicamos quem se destacou e vocês
        avaliam antes de abrir a vaga para fora.</li>
  </ul></div>
</div>
"""


def _preparar_r1():
    """Base da rodada 1 com as colunas do questionário longo anexadas."""
    base, c, s = carregar()
    if base is None:
        return None, None, None
    PS = "Em algum momento você pensou em sair antes do fim?"
    VOZ = "Você se sentiu à vontade para falar quando algo estava errado?"
    PGJ = "Pensando no esforço do dia a dia, o pagamento foi justo?"
    PGP = "Você recebeu tudo certo e no prazo (salário, vale, hora extra)?"

    base = base.copy()
    for col in (PS, VOZ, PGJ, PGP):
        vals = list(c[col]) if col in c else []
        serie = pd.Series([np.nan] * len(base), index=base.index, dtype=object)
        for i, v in zip(base.index[base.origem == "cumpriu"], vals):
            serie.loc[i] = str(v).strip() if pd.notna(v) else np.nan
        base[col] = serie
    return base.rename(columns={PS: "pensou_sair"}), c, s


def _filtrar_r1(base, c, s):
    grupo = st.session_state.get(K_GRUPO, "Todos")
    funcs = st.session_state.get(K_FUNC) or []
    if grupo != "Todos":
        base = base[base.grupo == grupo]
    if funcs:
        base = base[base.funcao.isin(funcs)]
        c = c[c[pd_src.EQUIV[0][1]].isin(funcs)]
        s = s[s[pd_src.EQUIV[0][2]].isin(funcs)]
    if grupo == G_CUMPRIU:
        c = c[c[pd_src.Q_TRIAGEM].astype(str).str.startswith("Fiquei até o fim")]
        s = s.iloc[0:0]
    elif grupo == G_SAIU:
        c = c[~c[pd_src.Q_TRIAGEM].astype(str).str.startswith("Fiquei até o fim")]
    return base, c, s


def construir_pesquisa():
    """Rodada 1 — experiência da temporada."""
    base, c, s = _preparar_r1()
    sec = {"titulo": TITULO, "sub": SUBTITULO, "blocos": []}
    if base is None or base.empty:
        return sec

    VOZ = "Você se sentiu à vontade para falar quando algo estava errado?"
    PGP = "Você recebeu tudo certo e no prazo (salário, vale, hora extra)?"

    base, c, s = _filtrar_r1(base, c, s)
    if base.empty:
        return sec
    rs = pd_src.resumo(base)
    d2 = carregar2()

    # ---------------------------------------------------------------- 1 hero
    e_tot = rs["enps_total"]
    sec["blocos"].append({
        "t": "hero", "titulo": TITULO,
        "sub": f"{SUBTITULO} · {rs['convites']} convites por WhatsApp",
        "chip": f"{rs['n_total']} respostas",
        "tiles": [
            {"lb": "Respostas", "vl": str(rs["n_total"]),
             "sb": f"{rs['n_cumpriu']} cumpriram · {rs['n_saiu']} saíram antes"},
            {"lb": "Taxa de resposta", "vl": _p(rs["taxa_total"]),
             "sb": f"{_p(rs['taxa_cumpriu'])} e {_p(rs['taxa_saiu'])} por grupo",
             "badge": "metas superadas"},
            {"lb": "Índice de recomendação", "vl": _n(e_tot["enps"]),
             "sb": f"{e_tot['promotores']} recomendam · {e_tot['detratores']} não recomendam"},
            {"lb": "Voltariam", "vl": _p(rs["voltaria_sim_talvez"]),
             "sb": f"{_p(rs['voltaria_sim'])} com certeza"},
            {"lb": "Faltou ao menos 1 dia", "vl": _p(rs["faltou_cumpriu"] or 0),
             "sb": f"{_p(rs['faltou_saiu'] or 0)} entre quem saiu antes"},
        ]})

    # -------------------------------------------------------- 2 quem respondeu
    f_fun, f_loc = _fig_participacao(base)
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Quem respondeu, por função", "kicker": "amostra",
          "desc": "Número de respondentes em cada função. Serve para conferir se a pesquisa "
                  "representa a operação antes de tirar qualquer conclusão dela.",
          "fig": f_fun}],
        [{"t": "fig", "titulo": "Por local de trabalho", "kicker": "amostra",
          "desc": "89,2% moram na região e 90,0% dependem só do transporte fretado. Esses dois "
                  "números explicam boa parte do que vem depois nesta aba.",
          "fig": f_loc}],
    ]})

    # ------------------------------------------- 3 índice de recomendação
    fig_pilha = _fig_enps_pilha(e_tot)
    fig_fun, qtd = _fig_enps_funcao(base)
    extras_enps = []
    if rs["enps_cumpriu"] and rs["enps_saiu"]:
        dif = rs["enps_cumpriu"]["enps"] - rs["enps_saiu"]["enps"]
        extras_enps.append({"html":
            f"<span class='hd'>Quem saiu antes do fim marcou "
            f"{_n(rs['enps_saiu']['enps'])}</span>Contra {_n(rs['enps_cumpriu']['enps'])} de quem "
            f"cumpriu a temporada. A diferença de {_n(dif)} pontos é o custo reputacional da saída "
            f"antecipada, e é pequena: mesmo quem interrompeu o contrato segue recontratável."})
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Índice de recomendação da Mendes RH",
          "kicker": f"índice {_n(e_tot['enps'])}",
          "desc": "Nota de 0 a 10 dada à pergunta “o quanto você indicaria a Mendes RH para um "
                  "amigo trabalhar?”. A barra mostra como as notas se distribuem; o índice é a "
                  "subtração indicada abaixo dela. A escala vai de −100 a +100 e acima de 50 é "
                  "excelente em qualquer referência de mercado.",
          "fig": fig_pilha, "extras": [_conta_indice(e_tot)] + extras_enps}],
        [{"t": "fig", "titulo": "Índice de recomendação por função", "kicker": f"{qtd} funções",
          "desc": f"Apenas funções com {MIN_RECORTE} ou mais respostas. Abaixo disso o "
                  f"recorte identifica quem respondeu.",
          "fig": fig_fun}] if fig_fun else [],
    ]})

    # ----------------------------------------------------------- 4 causa falta
    fig_c, tot_f = _fig_causas(base)
    if fig_c is not None:
        sec["blocos"].append({
            "t": "fig", "titulo": "Por que se falta", "kicker": f"n {tot_f}",
            "desc": f"Calculado só sobre as {tot_f} pessoas que faltaram ao menos um dia. Cada "
                    f"uma podia marcar até 3 causas, então a soma passa de 100%.",
            "fig": fig_c,
            "extras": [{"html":
                "<span class='hd'>Saúde, cansaço e transporte concentram a explicação</span>"
                "Desânimo, bico no mesmo dia e trabalho pesado demais para o valor pago ficam no "
                "rodapé da lista. Eu esperava encontrar essas três no topo e não encontrei. "
                "Entre as causas grandes, transporte é a que nós dois controlamos: rota, horário, "
                "capacidade e estado dos veículos."}]})

    # ------------------------------------------------------------ 5 preditores
    f_voz = _fig_preditor(base, VOZ, ["Sim", "Mais ou menos", "Não"])
    f_pag = _fig_preditor(base, PGP, ["Sim, sempre", "Teve atraso ou erro uma vez",
                                      "Teve problema mais de uma vez"])
    if f_voz is not None:
        sec["blocos"].append({
            "t": "fig", "titulo": "O que separa quem falta de quem não falta",
            "kicker": "preditor 1",
            "desc": "Resposta à pergunta “você se sentiu à vontade para falar quando algo estava "
                    "errado?”, cruzada com a taxa de falta. O cruzamento não mede opinião: separa "
                    "grupos que se comportaram de forma diferente.",
            "fig": f_voz})
    if f_pag is not None:
        sec["blocos"].append({
            "t": "fig", "titulo": "Erro de pagamento e falta", "kicker": "preditor 2",
            "desc": "Resposta à pergunta “você recebeu tudo certo e no prazo (salário, vale, hora "
                    "extra)?”, cruzada com a taxa de falta.",
            "fig": f_pag,
            "extras": [{"estilo": "warn", "html":
                "<span class='hd'>Essa falha é nossa</span>"
                "Ninguém marcou “teve problema mais de uma vez”, o que indica erro pontual e não "
                "sistêmico. Ainda assim é o tipo de coisa que corrigimos sozinhos, sem depender de "
                "negociação com ninguém, e tem efeito medido sobre a falta."}]})

    # --------------------------------------------------------------- 6 janela
    fig_j = _fig_janela(s)
    if fig_j is not None:
        sec["blocos"].append({
            "t": "fig", "titulo": "A janela da saída", "kicker": f"n {len(s)}",
            "desc": "Quando a pessoa decidiu sair, nas barras vermelhas, contra quanto tempo ela "
                    "ficou de fato, nas barras azuis. Só quem respondeu o questionário de saída. "
                    "Base pequena, então leia como indicação e não como conclusão.",
            "fig": fig_j,
            "extras": [{"html":
                "<span class='hd'>A decisão vem antes do aviso</span>"
                "A maioria decidiu sair na primeira semana e avisou com antecedência. Ou seja, "
                "tivemos o aviso. Faltou a conversa que deveria ter vindo antes dele. “Alguém que "
                "me ouvisse quando o problema começou” está entre os itens mais citados como o "
                "que teria feito a pessoa ficar."}]})

    # --------------------------------------------------------------- 7 matriz
    mtx = _matriz_funcao(base)
    if not mtx.empty:
        sec["blocos"].append({
            "t": "html", "so_tela": True,
            "html": "<div class='pq-h'><span class='t'>Matriz por função</span>"
                    "<span class='k'>síntese</span></div>"
                    "<div class='pq-d'>Verde é bom, vermelho pede atenção. Funções com menos de "
                    f"{MIN_RECORTE} respostas ficam de fora: abaixo disso dá para adivinhar quem "
                    "respondeu. A coluna “pensou em sair” só existe no questionário longo, então "
                    "o denominador dela é menor nas funções com muita saída antecipada.</div>"
                    + _matriz_html(mtx)})
        mpdf = mtx.copy()
        mpdf["Recomendação"] = mpdf["Recomendação"].map(lambda v: _n(v) if pd.notna(v) else "—")
        for cc in ("Faltou", "Pensou em sair", "Voltaria"):
            mpdf[cc] = mpdf[cc].map(lambda v: f"{int(v)}%" if pd.notna(v) else "—")
        sec["blocos"].append({"t": "tabela", "so_pdf": True, "titulo": "Matriz por função",
                              "desc": f"Funções com {MIN_RECORTE} ou mais respostas.",
                              "df": mpdf})

    # ------------------------------------------------------------- 8 leitura
    sec["blocos"].append({"t": "texto", "titulo": "O que lemos nesta rodada",
                          "kicker": "análise", "html": _texto_leitura(base, c, s, rs)})

    # --------------------------------------------------------------- 9 plano
    sec["blocos"].append({"t": "texto", "titulo": "O que proponho",
                          "kicker": "próxima temporada", "html": _plano(base, d2)})

    # ------------------------------------------------------------- 10 ficha
    sec["blocos"].append({"t": "nota", "estilo": "", "html":
        f"<span class='hd'>Ficha técnica</span>"
        f"Coleta de 6 a 10 de agosto de 2026 · {rs['convites']} convites por WhatsApp · "
        f"{rs['n_total']} respostas · dois questionários anônimos, com o cadastro de contato em "
        f"formulário separado. <b>Classificação:</b> o grupo veio da declaração de cada pessoa e "
        f"não da nossa lista de envio. {rs['reclassificados']} receberam o questionário de quem "
        f"cumpriu a temporada e informaram que saíram antes do fim, então contei essas no grupo de "
        f"saída. <b>Limitações:</b> {round(rs['n_cumpriu'] / rs['n_total'] * 100)}% das respostas "
        f"vêm de quem cumpriu a temporada, então leia os indicadores de satisfação como teto e não "
        f"como média. Recortes com menos de {MIN_RECORTE} respostas não aparecem."})
    return sec


# ==================================================================== RODADA 2
def _filtrar_r2(d2):
    funcs = st.session_state.get(K_FUNC2) or []
    return d2[d2.funcao.isin(funcs)] if funcs else d2


def _fig_multipla(listas, ordem, cor, destaque=None):
    s, tot = contagem_multipla(listas)
    if not tot:
        return None, 0
    s = s[[k for k in s.index if k in ordem or (destaque and k == destaque)]]
    if s.empty:
        return None, 0
    pcs = [round(v / tot * 100, 1) for v in s.values]
    cores = [MUTED if (destaque and k == destaque) else cor for k in s.index]
    return _barras_h(s.index, pcs, cor, cores=cores,
                     texto=[_p(v) for v in pcs]), tot


def _fig_respeito_preditor(d2):
    """Nota de salario e de condicoes por nivel de respeito percebido.

    E o cruzamento mais forte da rodada 2: quem nao se sentiu respeitado da
    nota mais baixa para tudo, inclusive para o salario - que e o mesmo valor
    recebido por todo mundo na mesma funcao.
    """
    dados = []
    for rot in ORDEM_RESPEITO:
        g = d2[d2.respeito == rot]
        if len(g) < MIN_RECORTE:
            continue
        dados.append((f"{_rot(rot)}  ·  n {len(g)}",
                      round(float(g.nota_salario.mean()), 2),
                      round(float(g.nota_condicoes.mean()), 2)))
    if len(dados) < 2:
        return None, None
    fig = go.Figure()
    fig.add_bar(y=[d[0] for d in dados], x=[d[1] for d in dados], orientation="h",
                name="Nota do salário", marker=dict(color=S3),
                text=[_n(d[1], 2) for d in dados], textposition="outside",
                cliponaxis=False, textfont=dict(size=11, color=INK2), hoverinfo="skip")
    fig.add_bar(y=[d[0] for d in dados], x=[d[2] for d in dados], orientation="h",
                name="Nota das condições", marker=dict(color=S1),
                text=[_n(d[2], 2) for d in dados], textposition="outside",
                cliponaxis=False, textfont=dict(size=11, color=INK2), hoverinfo="skip")
    fig.update_layout(
        barmode="group", bargap=.3, bargroupgap=.08,
        height=max(160, 64 * len(dados) + 56), margin=dict(l=6, r=52, t=8, b=6),
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family=ui.FONTE, size=12, color=INK2),
        legend=dict(orientation="h", y=1.14, x=0, xanchor="left",
                    font=dict(size=11.5, color=INK2), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=True, gridcolor=GRID, showticklabels=False, range=[0, 11.4]),
        yaxis=dict(autorange="reversed", showgrid=False, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=INK, size=11.5)))
    return fig, dados


def _texto_leitura_r2(d2, r2):
    s_al, t_al = contagem_multipla(d2.alavanca_lista)
    s_me, t_me = contagem_multipla(d2.melhorar_lista)
    dia = round(s_al.get("Valor maior da diária", 0) / t_al * 100, 1) if t_al else 0
    bon_falta = round(s_al.get("Bônus por não faltar", 0) / t_al * 100, 1) if t_al else 0
    bon_fim = round(s_al.get("Bônus por ficar até o fim da temporada", 0) / t_al * 100, 1) if t_al else 0
    top_me = s_me.head(3).index.tolist() if len(s_me) else []
    trat = round(s_me.get("Tratamento pelos funcionários efetivos", 0) / t_me * 100, 1) if t_me else 0

    partes = [
        f"<p>Mandamos esta rodada só para quem já tinha respondido a primeira, e voltaram "
        f"<b>{r2['n']} respostas em {r2['convites']} convites</b> ({_p(r2['taxa'])}) em um único "
        f"dia. Gente cansada de pesquisa não responde a segunda em um dia. Elas responderam porque "
        f"acham que muda alguma coisa, o que nos obriga a mostrar que mudou.</p>",

        f"<p><b>O salário não é o problema que eu imaginava.</b> A nota média foi "
        f"{_n(r2['media_salario'], 2)} e {_p(r2['expect_atendeu'])} disseram que o valor atendeu "
        f"ou superou o que esperavam quando aceitaram a vaga. Só {_p(r2['expect_abaixo'])} ficaram "
        f"abaixo da expectativa, e apenas {_p(r2['mercado_pior'])} acham o pagamento pior que o de "
        f"outros temporários da região, contra {_p(r2['mercado_melhor'])} que acham melhor. O "
        f"índice de {_n(r2['salario']['enps'])} é o mais baixo dos três que medimos e ainda assim "
        f"positivo.</p>",

        f"<p><b>O que se pede vai além da diária.</b> {_p(dia)} querem aumento no valor da diária, "
        f"mas {_p(bon_falta)} aceitariam bônus por não faltar e {_p(bon_fim)} bônus por ficar até "
        f"o fim da temporada. Bônus condicionado sai mais barato que reajuste na folha inteira, "
        f"porque só é pago quando o resultado aparece, e ataca justamente os dois problemas da "
        f"primeira rodada.</p>"]

    if top_me:
        partes.append(
            f"<p><b>As condições tiveram nota {_n(r2['media_condicoes'], 2)}.</b> "
            f"{', '.join(top_me)} lideram os pedidos de melhoria. Alimentação e local para "
            f"descanso são investimento de estrutura, escala a gente resolve junto, e "
            f"{_p(trat)} apontam o tratamento dado pelos funcionários efetivos, que é o único item "
            f"da lista que se resolve com orientação em vez de orçamento.</p>")

    partes.append(
        f"<p><b>O respeito é o ponto mais delicado daqui.</b> Apenas {_p(r2['respeito_sempre'])} "
        f"se sentiram sempre respeitados no ambiente de trabalho. {_p(r2['respeito_parcial'])} "
        f"responderam “na maior parte do tempo” e {_p(r2['respeito_falhou'])} responderam “poucas "
        f"vezes”. Somando, quase metade passou por alguma situação de desrespeito em poucas "
        f"semanas de contrato. Os relatos abertos apontam todos para o mesmo lugar: a fronteira "
        f"entre efetivo e temporário.</p>")
    partes.append(
        f"<p><b>E quase todo mundo quer ser efetivado por vocês.</b> {_p(r2['clt_sim'])} querem "
        f"virar CLT na Aviva com certeza e {_p(r2['clt_sim_talvez'])} querem ou considerariam. Só "
        f"{_p(r2['clt_nao'])} descartam. Para essas pessoas o contrato temporário funcionou como "
        f"porta de entrada, e hoje não existe caminho formal depois dessa porta.</p>")
    return "".join(partes)



def construir_pesquisa_r2():
    """Rodada 2 — salário, condições de trabalho e efetivação."""
    sec = {"titulo": TITULO_R2, "sub": SUBTITULO_R2, "blocos": []}
    d2 = carregar2()
    if d2 is None or d2.empty:
        return sec
    base1, _, _ = carregar()
    n_convites = len(base1) if base1 is not None else None

    d2 = _filtrar_r2(d2)
    if d2.empty:
        return sec
    r2 = pd_src.resumo_r2(d2, n_convites)

    # ---------------------------------------------------------------- 1 hero
    sec["blocos"].append({
        "t": "hero", "titulo": TITULO_R2,
        "sub": f"{SUBTITULO_R2} · disparo só para quem respondeu a rodada 1",
        "chip": f"{r2['n']} respostas",
        "tiles": [
            {"lb": "Respostas", "vl": str(r2["n"]),
             "sb": (f"{_p(r2['taxa'])} de {r2['convites']} convites"
                    if r2["taxa"] else "coleta em um único dia"),
             "badge": "1 dia de coleta"},
            {"lb": "Nota do salário", "vl": _n(r2["media_salario"], 2),
             "sb": f"índice {_n(r2['salario']['enps'])} · {r2['salario']['detratores']} abaixo de 7"},
            {"lb": "Nota das condições", "vl": _n(r2["media_condicoes"], 2),
             "sb": f"índice {_n(r2['condicoes']['enps'])} · {r2['condicoes']['promotores']} deram 9 ou 10"},
            {"lb": "Querem efetivação CLT", "vl": _p(r2["clt_sim"]),
             "sb": f"{_p(r2['clt_sim_talvez'])} querem ou considerariam"},
            {"lb": "Sempre se sentiram respeitados", "vl": _p(r2["respeito_sempre"]),
             "sb": f"{_p(r2['respeito_falhou'])} responderam “poucas vezes”"},
        ]})

    # ------------------------------------------------------------ 2 salário
    fig_sal = _histograma_nota(d2.nota_salario)
    fig_sal_pilha = _fig_enps_pilha(r2["salario"])
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Distribuição da nota do salário", "kicker": "0 a 10",
          "desc": "“Que nota você dá para o valor do salário que recebeu na temporada?” "
                  "Verde são notas 9 e 10, amarelo 7 e 8, vermelho 6 ou menos.",
          "fig": fig_sal}],
        [{"t": "fig", "titulo": "Índice de recomendação do salário",
          "kicker": f"índice {_n(r2['salario']['enps'])}",
          "desc": "Mesmo método do índice da rodada 1, aplicado à nota do salário. A barra mostra "
                  "como as 79 notas se distribuem; o índice é a subtração indicada abaixo dela.",
          "fig": fig_sal_pilha,
          "extras": [
              _conta_indice(r2["salario"], "o índice do salário"),
              {"html":
                  f"<span class='hd'>O salário não afasta, mas também não segura</span>"
                  f"{_n(r2['salario']['enps'])} é o mais baixo dos três índices que medimos e "
                  f"ainda assim é positivo. Some a isso {_p(r2['expect_atendeu'])} dizendo que o "
                  f"valor atendeu ou superou o que esperavam: a remuneração está adequada para "
                  f"atrair gente, e não é ela que faz alguém ficar até o fim."}]}],
    ]})

    # ---------------------------------------------- 3 expectativa e mercado
    exp = d2.expectativa.value_counts()
    fig_exp = _pilha([
        ("Foi mais do que eu esperava", int(exp.get("Foi mais do que eu esperava", 0)), GOOD),
        ("Foi o que eu esperava", int(exp.get("Foi o que eu esperava", 0)), S1),
        ("Foi menos do que eu esperava", int(exp.get("Foi menos do que eu esperava", 0)), CRIT)])
    mer = d2.mercado.value_counts()
    fig_mer = _pilha([
        ("Melhor", int(mer.get("Melhor", 0)), GOOD),
        ("Parecido", int(mer.get("Parecido", 0)), S1),
        ("Pior", int(mer.get("Pior", 0)), CRIT),
        ("Não sei comparar", int(mer.get("Não sei comparar", 0)), MUTED)])
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "O valor atendeu a expectativa?", "kicker": "contratação",
          "desc": "Compara o que combinamos na contratação com o que a pessoa sentiu ao receber. "
                  "Mede promessa cumprida, e não generosidade.",
          "fig": fig_exp}],
        [{"t": "fig", "titulo": "Comparação com o mercado da região", "kicker": "posicionamento",
          "desc": "Resposta à pergunta “comparando com outros trabalhos temporários que você "
                  "conhece na região, o pagamento da Mendes RH é…”.",
          "fig": fig_mer}],
    ]})

    # ------------------------------------------------------- 4 alavanca pagto
    fig_al, tot_al = _fig_multipla(d2.alavanca_lista, OPC_ALAVANCA, S3)
    if fig_al is not None:
        s_al, _ = contagem_multipla(d2.alavanca_lista)
        bf = round(s_al.get("Bônus por não faltar", 0) / tot_al * 100, 1)
        bt = round(s_al.get("Bônus por ficar até o fim da temporada", 0) / tot_al * 100, 1)
        sec["blocos"].append({
            "t": "fig", "titulo": "O que mais faria diferença no pagamento",
            "kicker": f"n {tot_al}",
            "desc": "Cada pessoa podia marcar até 2 opções, então a soma passa de 100%. "
                    "Percentual sobre o total de respondentes.",
            "fig": fig_al,
            "extras": [{"estilo": "good", "html":
                f"<span class='hd'>Uma proposta concreta</span>"
                f"{_p(bf)} aceitariam bônus por não faltar e {_p(bt)} bônus por ficar até o fim. "
                f"São exatamente os dois problemas da primeira rodada, e um bônus condicionado sai "
                f"mais barato que reajuste na folha inteira porque só é pago quando o resultado "
                f"aparece. Gostaria de testar isso em uma função na próxima temporada."}]})

    # ------------------------------------------------------------ 5 condições
    fig_cond = _histograma_nota(d2.nota_condicoes)
    fig_mel, tot_mel = _fig_multipla(d2.melhorar_lista, OPC_MELHORAR,
                                     S2, destaque="Nada, estava bom")
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Distribuição da nota das condições", "kicker": "0 a 10",
          "desc": "“Que nota você dá para as condições de trabalho no dia a dia?” "
                  f"Média {_n(r2['media_condicoes'], 2)}, meio ponto acima da nota do salário.",
          "fig": fig_cond}],
        [{"t": "fig", "titulo": "O que mais precisa melhorar", "kicker": f"n {tot_mel}",
          "desc": "Até 3 marcações por pessoa. “Nada, estava bom” aparece em cinza para não "
                  "competir visualmente com os problemas.",
          "fig": fig_mel}] if fig_mel is not None else [],
    ]})

    # -------------------------------------------------------------- 6 respeito
    resp = d2.respeito.value_counts()
    fig_resp = _pilha([
        ("Sempre", int(resp.get("Sempre", 0)), GOOD),
        ("Na maior parte do tempo", int(resp.get("Na maior parte do tempo", 0)), WARN),
        ("Poucas vezes", int(resp.get("Poucas vezes", 0)), SERIOUS),
        ("Nunca", int(resp.get("Nunca", 0)), CRIT)])
    n_relatos = int(d2.relato.map(pd_src.descreveu_situacao).sum())
    n_escreveram = int((d2.relato.str.strip().str.len() > 0).sum())
    sec["blocos"].append({
        "t": "fig", "titulo": "Você se sentiu respeitado(a) no ambiente de trabalho?",
        "kicker": "clima", "desc":
            "Pergunta nova nesta rodada. Incluí porque a primeira trouxe, num campo aberto, um "
            "relato que exigia apuração formal, e eu não tinha como saber se aquilo era exceção "
            "ou rotina.",
        "fig": fig_resp,
        "extras": [
            {"estilo": "warn", "html":
                f"<span class='hd'>Quase metade passou por alguma situação de desrespeito</span>"
                f"Só {_p(r2['respeito_sempre'])} marcaram “sempre”. Em poucas semanas de contrato, "
                f"{_p(100 - (r2['respeito_sempre'] or 0))} relatarem falha de respeito é muito. "
                f"Esse número conversa diretamente com o item “tratamento pelos funcionários "
                f"efetivos” do gráfico anterior."},
            {"html":
                f"<span class='hd'>{n_relatos} pessoas descreveram uma situação</span>"
                f"De {n_escreveram} que escreveram no campo aberto. As demais usaram o espaço para "
                f"dizer que não tinham nada a relatar. Os casos que citam pessoas seguem por "
                f"apuração formal, em documento de circulação restrita. Aqui fica o padrão."}]})

    # ------------------------------------------- 6b respeito como preditor
    fig_rp, dados_rp = _fig_respeito_preditor(d2)
    if fig_rp is not None:
        base_ = dados_rp[-1]          # o pior nivel exibido
        outros = dados_rp[:-1]
        m_sal = sum(d[1] for d in outros) / len(outros)
        m_cond = sum(d[2] for d in outros) / len(outros)
        sec["blocos"].append({
            "t": "fig", "titulo": "O respeito puxa todas as outras notas",
            "kicker": "preditor", "desc":
                "Nota média do salário e das condições, separadas pelo nível de respeito que a "
                "pessoa relatou. A diária é a mesma para todo mundo na mesma função, então quem "
                "se sentiu desrespeitado avalia pior até aquilo que não mudou para ele.",
            "fig": fig_rp,
            "extras": [{"estilo": "warn", "html":
                f"<span class='hd'>O desrespeito contamina a avaliação inteira</span>"
                f"Entre “sempre” e “na maior parte do tempo” as notas quase não mudam: a média das "
                f"duas é {_n(m_sal, 2)} no salário e {_n(m_cond, 2)} nas condições. Quem marcou "
                f"“{base_[0].split('  ·')[0].lower()}” cai para {_n(base_[1], 2)} e "
                f"{_n(base_[2], 2)}, recebendo exatamente a mesma diária que os colegas da mesma "
                f"função. São {base_[0].split('n ')[-1]} pessoas, poucas o bastante para tratar "
                f"caso a caso."}]})

    # ------------------------------------------------------------ 7 efetivação
    clt = d2.clt.value_counts()
    fig_clt = _pilha([
        ("Sim, com certeza", int(clt.get("Sim, com certeza", 0)), GOOD),
        ("Talvez, depende das condições", int(clt.get("Talvez, depende das condições", 0)), WARN),
        ("Não", int(clt.get("Não", 0)), CRIT)])
    fig_contra, tot_contra = _fig_multipla(d2.contra_lista, OPC_CONTRA, S4)
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Interesse em efetivação CLT na Aviva", "kicker": "futuro",
          "desc": "Pergunta feita a todos os respondentes, com ramificação: quem respondeu "
                  "“talvez” ou “não” foi levado a dizer o que pesa contra.",
          "fig": fig_clt,
          "extras": [{"estilo": "good", "html":
              f"<span class='hd'>Por que isso vale dinheiro para vocês</span>"
              f"{_p(r2['clt_sim_talvez'])} querem ou considerariam. São pessoas já captadas, "
              f"treinadas, integradas à operação, e que demonstraram que ficam até o fim do "
              f"contrato. Contratar alguém desse grupo custa menos e tem risco menor do que abrir "
              f"vaga no mercado. Gostaria de propor um processo simples: ao fim de cada temporada "
              f"nós indicamos quem se destacou e vocês avaliam antes de abrir a vaga para fora."}]}],
        [{"t": "fig", "titulo": "O que pesa contra a efetivação", "kicker": f"n {tot_contra}",
          "desc": "Somente quem respondeu “talvez” ou “não”, num total de "
                  f"{tot_contra} pessoas. Base pequena, então leia como indicação.",
          "fig": fig_contra}] if fig_contra is not None else [],
    ]})

    # ---------------------------------------------------------------- 8 matriz
    m2 = _matriz_r2(d2)
    if not m2.empty:
        sec["blocos"].append({
            "t": "html", "so_tela": True,
            "html": "<div class='pq-h'><span class='t'>Matriz por função na rodada 2</span>"
                    "<span class='k'>síntese</span></div>"
                    "<div class='pq-d'>Verde é bom, vermelho pede atenção. Funções com menos de "
                    f"{MIN_RECORTE} respostas ficam de fora. “Respeito pleno” é o percentual que "
                    "respondeu “sempre” e “quer CLT” é o percentual que respondeu “sim, com "
                    "certeza”.</div>" + _matriz_r2_html(m2)})
        mpdf = m2.copy()
        for cc in ("Nota salário", "Nota condições"):
            mpdf[cc] = mpdf[cc].map(lambda v: _n(v, 2) if pd.notna(v) else "—")
        for cc in ("Respeito pleno", "Quer CLT"):
            mpdf[cc] = mpdf[cc].map(lambda v: f"{int(v)}%" if pd.notna(v) else "—")
        sec["blocos"].append({"t": "tabela", "so_pdf": True,
                              "titulo": "Matriz por função na rodada 2",
                              "desc": f"Funções com {MIN_RECORTE} ou mais respostas.",
                              "df": mpdf})

    # ------------------------------------------------------------- 9 leitura
    sec["blocos"].append({"t": "texto", "titulo": "O que lemos nesta rodada",
                          "kicker": "análise", "html": _texto_leitura_r2(d2, r2)})

    # --------------------------------------------------------------- 10 ficha
    sec["blocos"].append({"t": "nota", "estilo": "", "html":
        f"<span class='hd'>Ficha técnica</span>"
        f"Coleta em 10 de agosto de 2026 · envio por WhatsApp somente para quem respondeu a "
        f"rodada 1 · {r2['n']} respostas em {r2['convites']} convites ({_p(r2['taxa'])}) · "
        f"questionário anônimo, com o cadastro do sorteio em formulário separado. "
        f"<b>Incentivo:</b> sorteio de 10 prêmios de R$ 70 via PIX, pagos no dia de uso do "
        f"ingresso do Hot Park. <b>Limitações:</b> o público é o mesmo da rodada 1 e herda o mesmo "
        f"viés. {_p(round(d2.grupo.eq(G_CUMPRIU).sum() / len(d2) * 100, 1))} das respostas vêm de "
        f"quem cumpriu a temporada, então leia os indicadores como teto. Recortes com menos de "
        f"{MIN_RECORTE} respostas não aparecem, e os relatos que citam pessoas ficam fora do "
        f"painel."})
    return sec


# ================================================================ CONSOLIDADO
def construir_pesquisa_consolidado():
    """As duas rodadas lidas em conjunto."""
    sec = {"titulo": TITULO_CONS, "sub": SUBTITULO_CONS, "blocos": []}
    base, c, s = _preparar_r1()
    d2 = carregar2()
    if base is None or base.empty or d2 is None or d2.empty:
        return sec
    rs = pd_src.resumo(base)
    r2 = pd_src.resumo_r2(d2, len(base))
    e_tot = rs["enps_total"]

    # ---------------------------------------------------------------- 1 hero
    sec["blocos"].append({
        "t": "hero", "titulo": "Duas rodadas de escuta, um retrato",
        "sub": "Temporada de julho de 2026 · Mendes RH x Aviva / Rio Quente Resorts",
        "chip": f"{rs['n_total']} + {r2['n']} respostas",
        "tiles": [
            {"lb": "Rodada 1 · experiência", "vl": str(rs["n_total"]),
             "sb": f"{_p(rs['taxa_total'])} de {rs['convites']} convites"},
            {"lb": "Rodada 2 · salário", "vl": str(r2["n"]),
             "sb": f"{_p(r2['taxa'])} de {r2['convites']} convites", "badge": "1 dia"},
            {"lb": "Recomendam a Mendes RH", "vl": _n(e_tot["enps"]),
             "sb": "índice de recomendação, −100 a +100"},
            {"lb": "Voltariam à próxima temporada", "vl": _p(rs["voltaria_sim_talvez"]),
             "sb": f"{_p(rs['voltaria_sim'])} com certeza"},
            {"lb": "Querem efetivação CLT", "vl": _p(r2["clt_sim_talvez"]),
             "sb": f"{_p(r2['clt_sim'])} com certeza"},
        ]})

    # ------------------------------------------------------- 2 três índices
    idx = [("Recomendação da Mendes RH", e_tot["enps"], rs["n_total"]),
           ("Condições de trabalho", r2["condicoes"]["enps"], r2["n"]),
           ("Valor do salário", r2["salario"]["enps"], r2["n"])]
    rot = [f"{k}  ·  n {n}" for k, _, n in idx]
    val = [v for _, v, _ in idx]
    cores = [GOOD if v >= 60 else (WARN if v >= 40 else SERIOUS) for v in val]
    fig_idx = _barras_h(rot, val, None, cores=cores, texto=[_n(v) for v in val])
    fig_idx.update_xaxes(range=[0, max(val) * 1.25])
    sec["blocos"].append({
        "t": "fig", "titulo": "Os três índices lado a lado", "kicker": "síntese",
        "desc": "Todos calculados pelo mesmo método: percentual de notas 9 e 10 menos percentual "
                "de notas 0 a 6, numa escala de −100 a +100. Acima de 50 é excelente. Entre 0 e "
                "30 é positivo, mas com público exigente.",
        "fig": fig_idx,
        "extras": [{"html":
            f"<span class='hd'>A ordem dos três diz alguma coisa</span>"
            f"Eles avaliam melhor a Mendes RH ({_n(e_tot['enps'])}) do que as condições de "
            f"trabalho ({_n(r2['condicoes']['enps'])}), e melhor as condições do que o salário "
            f"({_n(r2['salario']['enps'])}). Quem está segurando a experiência hoje é o vínculo "
            f"com a empresa. Isso é um ativo real e é frágil: depende de continuarmos presentes "
            f"no posto."}]})

    # --------------------------------------------------- 3 temas que se repetem
    s_me, t_me = contagem_multipla(d2.melhorar_lista)
    faltou = base[base.faltou]
    s_ca, t_ca = contagem_multipla(faltou.causa_falta_lista)
    linhas = []

    def _lin(tema, r1txt, r2txt, veredito, cor):
        linhas.append([tema, r1txt, r2txt, (veredito, cor, "#fff")])

    transp_r2 = round(s_me.get("Transporte", 0) / t_me * 100) if t_me else 0
    transp_r1 = round(s_ca.get("Transporte — não consegui chegar", 0) / t_ca * 100) if t_ca else 0
    trat_r2 = round(s_me.get("Tratamento pelos funcionários efetivos", 0) / t_me * 100) if t_me else 0
    esc_r2 = round(s_me.get("Escala e folgas", 0) / t_me * 100) if t_me else 0
    ali_r2 = round(s_me.get("Alimentação e refeitório", 0) / t_me * 100) if t_me else 0
    desc_r2 = round(s_me.get("Local para descanso e cadeiras", 0) / t_me * 100) if t_me else 0

    _lin("Tratamento pelos efetivos",
         "Recorrente no campo aberto, mais um relato que exigia apuração",
         f"{trat_r2}% pedem melhora · só {_p(r2['respeito_sempre'])} sempre respeitados",
         "CONFIRMADO", CRIT)
    _lin("Transporte",
         f"{transp_r1}% de quem faltou citou · 90,0% dependem do fretado",
         f"{transp_r2}% pedem melhora",
         "CONFIRMADO", SERIOUS)
    _lin("Escala e folgas",
         "Aparece no campo aberto e no que teria feito ficar",
         f"{esc_r2}% pedem melhora · maior freio à efetivação",
         "CONFIRMADO", SERIOUS)
    _lin("Alimentação e descanso",
         "Pedidos pontuais no campo aberto",
         f"{ali_r2}% alimentação · {desc_r2}% cadeiras para descanso",
         "AMPLIADO", WARN)
    _lin("Salário",
         "Pouco presente entre as causas de falta e de saída",
         f"{_p(r2['expect_atendeu'])} tiveram a expectativa atendida",
         "DESCARTADO", GOOD)

    sec["blocos"].append({
        "t": "html", "so_tela": True,
        "html": "<div class='pq-h'><span class='t'>O que as duas rodadas dizem sobre o mesmo "
                "tema</span><span class='k'>convergência</span></div>"
                "<div class='pq-d'>A rodada 1 levantou hipóteses a partir de campos abertos e "
                "escalas. A rodada 2 foi feita para medir essas hipóteses. “Confirmado” quer dizer "
                "que o tema apareceu sozinho na primeira e ganhou tamanho na segunda.</div>"
                + _tabela_html(["Tema", "Rodada 1 · experiência", "Rodada 2 · salário e condições",
                                "Veredito"], linhas)})
    df_conv = pd.DataFrame(
        [[l[0], l[1], l[2], l[3][0]] for l in linhas],
        columns=["Tema", "Rodada 1", "Rodada 2", "Veredito"])
    sec["blocos"].append({"t": "tabela", "so_pdf": True,
                          "titulo": "O que as duas rodadas dizem sobre o mesmo tema",
                          "desc": "Convergência entre as duas coletas.", "df": df_conv})

    # ------------------------------------------------------------- 4 leitura
    sec["blocos"].append({"t": "texto", "titulo": "Como eu leio tudo isso", "kicker": "análise",
                          "html": f"""
<p>As duas rodadas somaram <b>{rs['n_total'] + r2['n']} respostas</b>, {rs['n_total']} na primeira e
{r2['n']} na segunda, coletadas em cinco dias junto a {rs['convites']} pessoas convidadas. Como a
segunda foi enviada só para quem já tinha respondido a primeira, os dois públicos se sobrepõem e não
são amostras independentes. Gente cansada de pesquisa não responde a segunda em um dia. Elas
responderam porque acham que muda alguma coisa, o que nos obriga a mostrar que mudou.</p>

<p><b>A hipótese do salário caiu.</b> Era a explicação natural para {_p(rs['faltou_cumpriu'])} de
absenteísmo e {rs['n_saiu']} saídas antecipadas. A rodada 2 mostra {_p(r2['expect_atendeu'])} com a
expectativa atendida ou superada e apenas {_p(r2['mercado_pior'])} achando o pagamento pior que o do
mercado local. Continuo achando que a diária merece revisão, mas ela não explica o que aconteceu em
julho.</p>

<p><b>O que sobra é relação.</b> Na rodada 1, quem não se sente à vontade para falar falta bem mais.
Na rodada 2, {_p(100 - (r2['respeito_sempre'] or 0))} relatam alguma falha de respeito. São o mesmo
problema visto de dois ângulos: a fronteira entre efetivo e temporário, e a falta de alguém
escutando durante o contrato em vez de só no fim dele. Nenhum dos dois se resolve com dinheiro.</p>

<p><b>E apareceu uma oportunidade que ninguém tinha pedido.</b> {_p(r2['clt_sim_talvez'])} querem ou
considerariam ser efetivados por vocês. Essas pessoas já foram treinadas, já conhecem a operação e já
demonstraram que ficam até o fim. É um funil de recrutamento pronto, testado em operação real.</p>"""})

    # --------------------------------------------------------------- 5 plano
    sec["blocos"].append({"t": "texto", "titulo": "O que proponho",
                          "kicker": "próxima temporada", "html": _plano(base, d2)})

    # --------------------------------------------------------------- 6 ficha
    sec["blocos"].append({"t": "nota", "estilo": "", "html":
        f"<span class='hd'>Ficha técnica</span>"
        f"Rodada 1: coleta de 6 a 10 de agosto, {rs['n_total']} respostas em {rs['convites']} "
        f"convites ({_p(rs['taxa_total'])}), dois questionários. Rodada 2: coleta em 10 de agosto, "
        f"{r2['n']} respostas em {r2['convites']} convites ({_p(r2['taxa'])}), questionário único "
        f"enviado só para quem respondeu a rodada 1. Ambas anônimas, com dados de contato em "
        f"formulário separado. <b>Limitações:</b> os dois públicos se sobrepõem, então não são "
        f"amostras independentes. A maioria das respostas vem de quem cumpriu a temporada, então "
        f"leia os indicadores como teto. Recortes com menos de {MIN_RECORTE} respostas não "
        f"aparecem, e os relatos que citam pessoas ficam fora do painel."})
    return sec


# ==================================================================== render
CSS = """
<style>
.pq-h{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:14px 0 2px 0;}
.pq-h .t{font-size:1.02rem;font-weight:730;color:#0b0b0b;letter-spacing:-.012em;}
.pq-h .k{font-size:.7rem;font-weight:750;letter-spacing:.06em;text-transform:uppercase;
  color:#2a78d6;background:#eaf2fd;padding:2px 9px;border-radius:999px;}
.pq-d{font-size:.83rem;color:#52514e;margin:2px 0 10px 0;line-height:1.5;}
</style>
"""


def render_pesquisa():
    st.markdown(CSS, unsafe_allow_html=True)
    base, c, s = carregar()
    if base is None:
        st.warning("Base da pesquisa não encontrada em dados/pesquisa/"
                   "RESPOSTAS_PESQUISA.xlsx.")
        return
    d2 = carregar2()

    visoes = [V_R1]
    if d2 is not None and not d2.empty:
        visoes += [V_R2, V_CONS]

    with st.container(border=True):
        st.radio("Visão", visoes, key=K_VISAO, horizontal=True,
                 label_visibility="collapsed")
        visao = st.session_state.get(K_VISAO, V_R1)
        if visao == V_R1:
            f1, f2 = st.columns([1.4, 3])
            with f1:
                st.selectbox("Grupo", ["Todos", G_CUMPRIU, G_SAIU], key=K_GRUPO)
            with f2:
                st.multiselect("Funções",
                               sorted([f for f in base.funcao.dropna().unique() if f]),
                               default=[], key=K_FUNC,
                               placeholder="Todas as funções")
        elif visao == V_R2:
            st.multiselect("Funções",
                           sorted([f for f in d2.funcao.dropna().unique() if f]),
                           default=[], key=K_FUNC2,
                           placeholder="Todas as funções")
        else:
            st.caption("A visão consolidada usa sempre a base completa das duas rodadas, sem "
                       "filtro de grupo ou de função.")

    visao = st.session_state.get(K_VISAO, V_R1)
    if visao == V_R2:
        sec = construir_pesquisa_r2()
    elif visao == V_CONS:
        sec = construir_pesquisa_consolidado()
    else:
        sec = construir_pesquisa()

    if not sec["blocos"]:
        st.info("Sem respostas para o filtro selecionado.")
        return
    ui.desenhar(sec)
