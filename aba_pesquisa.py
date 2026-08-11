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

Relatos nominais (assedio, conduta individual) NAO entram no painel. Eles
constam do relatorio em Word, secao 10, e seguem pelo canal de conduta. Em tela
de apresentacao um relato nominal vira o assunto da reuniao inteira e desloca a
discussao do que e estrutural para o que e individual.
================================================================================
"""
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
        x=list(valores), y=list(rotulos), orientation="h",
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
        curto = rot.split(" (")[0]
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
    rot = [f"{f}  ·  n {n}" for f, _, n in linhas]
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
        dados.append((f"{rot}  ·  n {len(g)}", f, p))
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
        f"<p>A pesquisa reuniu <b>{rs['n_total']} respostas em {rs['convites']} convites</b> "
        f"({_p(rs['taxa_total'])}), contra 76 respostas na rodada do ano passado. As duas metas do "
        f"plano foram superadas: {_p(rs['taxa_cumpriu'])} no grupo que cumpriu a temporada e "
        f"{_p(rs['taxa_saiu'])} no grupo que saiu antes do fim.</p>"]
    if tot:
        partes.append(
            f"<p>Entre as {tot} pessoas que declararam ao menos uma ausência, as três causas mais "
            f"citadas — {', '.join(top.index[:3])} — concentram <b>{soma3}% das citações</b>, "
            f"enquanto desânimo, trabalho paralelo e insatisfação com o valor pago somam "
            f"{_p(pdesengaj)}. O absenteísmo desta temporada é um problema de saúde e de "
            f"logística, não de engajamento.</p>")
    voz = "Você se sentiu à vontade para falar quando algo estava errado?"
    if voz in base:
        g1, g2 = base[base[voz] == "Sim"], base[base[voz] == "Não"]
        if len(g1) >= MIN_RECORTE and len(g2) >= MIN_RECORTE:
            t1 = round(g1.faltou.sum() / len(g1) * 100)
            t2 = round(g2.faltou.sum() / len(g2) * 100)
            partes.append(
                f"<p>O corte mais forte da pesquisa é a voz. Quem se sentiu à vontade para "
                f"falar quando algo estava errado faltou <b>{t1}%</b>; quem não se sentiu, "
                f"<b>{t2}%</b>. Não é um problema que se resolva com investimento — resolve-se "
                f"com presença.</p>")
    if ec and es:
        partes.append(
            f"<p>O vínculo com a Mendes RH permanece alto e agora é comparável entre temporadas: "
            f"índice de recomendação de <b>{_n(ec['enps'])}</b> entre quem cumpriu a temporada e "
            f"<b>{_n(es['enps'])}</b> entre quem saiu antes do fim, com "
            f"{_p(rs['voltaria_sim_talvez'])} do total dispostos a voltar ou considerando voltar. "
            f"A diferença de {_n(ec['enps'] - es['enps'])} pontos entre os dois grupos é o custo "
            f"reputacional da saída antecipada — e é modesta.</p>")
    if s is not None and not s.empty:
        cd = "Em que momento você decidiu que ia sair?"
        if cd in s:
            cedo = int(s[cd].isin(["Já nos primeiros dias", "Na primeira semana"]).sum())
            partes.append(
                f"<p>A perda acontece cedo: <b>{cedo} de {len(s)}</b> das saídas respondidas foram "
                f"decididas nos primeiros dias ou na primeira semana. É a janela em que não existe "
                f"hoje nenhuma ação programada, e é onde a próxima temporada tem mais a ganhar.</p>")
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

    t_pag = (f"Quem teve ao menos um erro faltou {err}% contra {ok}% dos demais. "
             if err is not None and ok is not None else "")
    t_voz = (f"Quem não se sente à vontade para falar falta {sem_voz}%, contra {com_voz}% de "
             f"quem se sente. " if sem_voz is not None and com_voz is not None else "")

    t_resp = ""
    if d2 is not None and not d2.empty:
        r2 = pd_src.resumo_r2(d2)
        t_resp = (f"A rodada 2 mede o tamanho disso: só {_p(r2['respeito_sempre'])} se sentiram "
                  f"sempre respeitados, e {_p(r2['respeito_falhou'])} responderam “poucas vezes”. ")

    t_diaria = ""
    if d2 is not None and not d2.empty:
        s, tot = contagem_multipla(d2.alavanca_lista)
        if tot:
            dia = round(s.get("Valor maior da diária", 0) / tot * 100, 1)
            bon = round(max(s.get("Bônus por não faltar", 0),
                            s.get("Bônus por ficar até o fim da temporada", 0)) / tot * 100, 1)
            t_diaria = (f"{_p(dia)} pedem diária maior, mas {_p(bon)} aceitariam bônus "
                        f"condicionado — que custa menos e ataca a falta direto. ")

    return f"""
<div class="duo">
  <div class="note good"><span class="hd">Ação imediata · custo zero</span><ul>
    <li><b>Conversa de 5 minutos no 3º e no 7º dia</b> de cada temporário, com registro de quem
        falou o quê. A decisão de sair é tomada dentro dessa janela.</li>
    <li><b>Zerar erro e atraso de pagamento.</b> {t_pag}Ninguém marcou “teve problema mais de uma
        vez” — é falha pontual, corrigível internamente.</li>
    <li><b>Alinhamento com efetivos e segurança</b> sobre o tratamento dado ao temporário.
        {t_resp}É o tema que aparece nas duas rodadas.</li>
    <li><b>Entregar o crachá na contratação</b> e explicar para que serve — aparece nos relatos
        como causa de constrangimento na portaria.</li>
  </ul></div>
  <div class="note warn"><span class="hd">Ação estruturada · exige planejamento</span><ul>
    <li><b>Canal de escuta ativo durante a temporada</b>, não apenas ao final. {t_voz}</li>
    <li><b>Auditoria do transporte fretado</b>: rota da recepção, horários, estado dos veículos e
        conduta a bordo. 90,0% dependem exclusivamente do fretado.</li>
    <li><b>Diagnóstico dirigido em Camareira e governança</b>, a função com os indicadores
        simultaneamente piores nas duas rodadas.</li>
    <li><b>Bônus por assiduidade e por conclusão de contrato.</b> {t_diaria}Piloto em uma função,
        medindo o efeito contra o histórico desta temporada.</li>
    <li><b>Trilha de efetivação com a Aviva.</b> A demanda existe e é quase unânime — o que falta
        é processo.</li>
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
        [{"t": "fig", "titulo": "Quem respondeu — por função", "kicker": "amostra",
          "desc": "Número de respondentes. Serve para checar se a pesquisa representa a "
                  "operação antes de qualquer leitura.",
          "fig": f_fun}],
        [{"t": "fig", "titulo": "Por local de trabalho", "kicker": "amostra",
          "desc": "89,2% moram na região e 90,0% dependem do transporte fretado — os dois "
                  "números explicam boa parte do resto da aba.",
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
            f"antecipada — e é pequena: mesmo quem interrompeu o contrato segue recontratável."})
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Índice de recomendação da Mendes RH", "kicker": "vínculo",
          "desc": "Nota de 0 a 10 dada à pergunta “o quanto você indicaria a Mendes RH para um "
                  "amigo trabalhar?”. Quem dá 9 ou 10 recomenda, 7 e 8 são indiferentes e ficam "
                  "fora da conta, 0 a 6 não recomenda. O índice é a diferença entre o primeiro e "
                  "o último grupo, de −100 a +100. Acima de 50 é excelente em qualquer "
                  "referência de mercado.",
          "fig": fig_pilha, "extras": extras_enps}],
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
            "desc": f"Calculado apenas sobre quem declarou ao menos uma ausência — {tot_f} "
                    f"pessoas. Cada uma podia marcar até 3 causas, então a soma passa de 100%.",
            "fig": fig_c,
            "extras": [{"html":
                "<span class='hd'>Saúde, transporte e cansaço concentram a explicação</span>"
                "Desânimo, bico no mesmo dia e trabalho pesado demais para o valor pago — as três "
                "causas que a operação costuma presumir — ficam no rodapé da lista. Transporte é a "
                "única causa relevante que a Mendes RH e a Aviva controlam sozinhas: rota, horário, "
                "capacidade e estado dos veículos."}]})

    # ------------------------------------------------------------ 5 preditores
    f_voz = _fig_preditor(base, VOZ, ["Sim", "Mais ou menos", "Não"])
    f_pag = _fig_preditor(base, PGP, ["Sim, sempre", "Teve atraso ou erro uma vez",
                                      "Teve problema mais de uma vez"])
    if f_voz is not None:
        sec["blocos"].append({
            "t": "fig", "titulo": "O que separa quem falta de quem não falta",
            "kicker": "preditor 1",
            "desc": "“Você se sentiu à vontade para falar quando algo estava errado?” — "
                    "o cruzamento não descreve opinião, separa grupos com comportamento diferente.",
            "fig": f_voz})
    if f_pag is not None:
        sec["blocos"].append({
            "t": "fig", "titulo": "Erro de pagamento e falta", "kicker": "preditor 2",
            "desc": "“Você recebeu tudo certo e no prazo (salário, vale, hora extra)?”",
            "fig": f_pag,
            "extras": [{"estilo": "warn", "html":
                "<span class='hd'>É a correção mais barata do relatório</span>"
                "Ninguém marcou “teve problema mais de uma vez”, o que indica falha pontual e não "
                "sistêmica. Depende exclusivamente de processo interno, não envolve negociação com "
                "o cliente e tem efeito medido sobre a falta."}]})

    # --------------------------------------------------------------- 6 janela
    fig_j = _fig_janela(s)
    if fig_j is not None:
        sec["blocos"].append({
            "t": "fig", "titulo": "A janela da saída", "kicker": f"n {len(s)}",
            "desc": "Quando a pessoa decidiu sair (barras em vermelho) contra quanto tempo ficou "
                    "de fato (barras em azul). Grupo que respondeu o questionário de saída — "
                    "leitura indicativa, não conclusiva.",
            "fig": fig_j,
            "extras": [{"html":
                "<span class='hd'>A decisão vem antes do aviso</span>"
                "A maioria decidiu sair na primeira semana e avisou com antecedência. A operação "
                "teve o aviso — o que faltou foi uma conversa antes disso. “Alguém que me ouvisse "
                "quando o problema começou” aparece entre os itens mais citados como o que teria "
                "feito a pessoa ficar."}]})

    # --------------------------------------------------------------- 7 matriz
    mtx = _matriz_funcao(base)
    if not mtx.empty:
        sec["blocos"].append({
            "t": "html", "so_tela": True,
            "html": "<div class='pq-h'><span class='t'>Matriz por função</span>"
                    "<span class='k'>síntese</span></div>"
                    "<div class='pq-d'>Verde é bom, vermelho é atenção. Funções com menos de "
                    f"{MIN_RECORTE} respostas são suprimidas automaticamente. A coluna “pensou em "
                    "sair” só existe no questionário longo, então o denominador dela é menor nas "
                    "funções com muita saída antecipada.</div>" + _matriz_html(mtx)})
        mpdf = mtx.copy()
        mpdf["Recomendação"] = mpdf["Recomendação"].map(lambda v: _n(v) if pd.notna(v) else "—")
        for cc in ("Faltou", "Pensou em sair", "Voltaria"):
            mpdf[cc] = mpdf[cc].map(lambda v: f"{int(v)}%" if pd.notna(v) else "—")
        sec["blocos"].append({"t": "tabela", "so_pdf": True, "titulo": "Matriz por função",
                              "desc": f"Funções com {MIN_RECORTE} ou mais respostas.",
                              "df": mpdf})

    # ------------------------------------------------------------- 8 leitura
    sec["blocos"].append({"t": "texto", "titulo": "Leitura da temporada",
                          "kicker": "análise", "html": _texto_leitura(base, c, s, rs)})

    # --------------------------------------------------------------- 9 plano
    sec["blocos"].append({"t": "texto", "titulo": "Plano de ação",
                          "kicker": "próxima temporada", "html": _plano(base, d2)})

    # ------------------------------------------------------------- 10 ficha
    sec["blocos"].append({"t": "nota", "estilo": "", "html":
        f"<span class='hd'>Ficha técnica</span>"
        f"Coleta de 6 a 10 de agosto de 2026 · {rs['convites']} convites por WhatsApp · "
        f"{rs['n_total']} respostas · dois questionários anônimos, com o cadastro de contato em "
        f"formulário separado. <b>Classificação:</b> o grupo vem da declaração do respondente, não "
        f"da lista de disparo — {rs['reclassificados']} pessoas receberam o questionário de quem "
        f"cumpriu a temporada e informaram que saíram antes do fim; elas contam no grupo de saída. "
        f"<b>Limitações:</b> {round(rs['n_cumpriu'] / rs['n_total'] * 100)}% das respostas vêm de "
        f"quem cumpriu a temporada, então os indicadores de satisfação devem ser lidos como teto; "
        f"recortes com menos de {MIN_RECORTE} respostas não são exibidos."})
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
        dados.append((f"{rot}  ·  n {len(g)}",
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
        f"<p>A rodada 2 foi disparada só para quem já tinha respondido a rodada 1 e trouxe "
        f"<b>{r2['n']} respostas em {r2['convites']} convites</b> ({_p(r2['taxa'])}) em um único "
        f"dia. Uma taxa dessas, numa segunda pesquisa com o mesmo público, é o próprio indicador: "
        f"as pessoas acreditam que responder muda alguma coisa.</p>",

        f"<p><b>Salário não é o problema que se imaginava.</b> A nota média foi "
        f"{_n(r2['media_salario'], 2)} e {_p(r2['expect_atendeu'])} disseram que o valor atendeu ou "
        f"superou o que esperavam quando aceitaram a vaga. Só {_p(r2['expect_abaixo'])} ficaram "
        f"abaixo da expectativa, e apenas {_p(r2['mercado_pior'])} consideram o pagamento pior que "
        f"o de outros temporários da região, contra {_p(r2['mercado_melhor'])} que o consideram "
        f"melhor. O índice de recomendação do salário — {_n(r2['salario']['enps'])} — é o mais "
        f"baixo dos três medidos, mas mede exigência, não revolta.</p>",

        f"<p><b>O que se pede não é só diária maior.</b> {_p(dia)} querem aumento no valor da "
        f"diária, mas {_p(bon_falta)} aceitariam bônus por não faltar e {_p(bon_fim)} bônus por "
        f"ficar até o fim da temporada. Os dois últimos custam menos que um reajuste linear, são "
        f"condicionados a resultado e atacam exatamente os dois problemas da rodada 1: "
        f"absenteísmo e saída antecipada.</p>"]

    if top_me:
        partes.append(
            f"<p><b>Condições de trabalho: nota {_n(r2['media_condicoes'], 2)}, com três frentes "
            f"claras.</b> {', '.join(top_me)} lideram os pedidos de melhoria. Alimentação e local "
            f"para descanso são investimento do cliente; escala é negociação conjunta. "
            f"{_p(trat)} apontam o tratamento dado pelos funcionários efetivos — e esse é o único "
            f"item da lista que não custa dinheiro nenhum para resolver.</p>")

    partes.append(
        f"<p><b>O respeito é o achado mais desconfortável.</b> Apenas {_p(r2['respeito_sempre'])} "
        f"se sentiram sempre respeitados no ambiente de trabalho. {_p(r2['respeito_parcial'])} "
        f"responderam “na maior parte do tempo” e {_p(r2['respeito_falhou'])} responderam “poucas "
        f"vezes”. Somando, quase metade do grupo teve alguma experiência de desrespeito numa "
        f"temporada de poucas semanas. Os relatos abertos apontam sempre na mesma direção: a "
        f"fronteira entre efetivo e temporário.</p>")
    partes.append(
        f"<p><b>A demanda por efetivação é quase unânime.</b> {_p(r2['clt_sim'])} querem ser "
        f"efetivados como CLT na Aviva com certeza e {_p(r2['clt_sim_talvez'])} querem ou "
        f"considerariam. Só {_p(r2['clt_nao'])} descartam. Isso muda a natureza do contrato "
        f"temporário: para a maioria dessas pessoas ele não é um bico de temporada, é uma porta "
        f"de entrada — e hoje não existe trilha formal atrás dessa porta.</p>")
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
        [{"t": "fig", "titulo": "Índice de recomendação do salário", "kicker": "vínculo",
          "desc": "Mesmo método do índice da rodada 1, aplicado à nota do salário: percentual de "
                  "notas 9 e 10 menos percentual de notas 0 a 6.",
          "fig": fig_sal_pilha,
          "extras": [{"html":
              f"<span class='hd'>{_n(r2['salario']['enps'])} é exigência, não revolta</span>"
              f"É o mais baixo dos três índices medidos, e ainda assim positivo. Com "
              f"{_p(r2['expect_atendeu'])} dizendo que o valor atendeu ou superou o esperado, a "
              f"leitura correta é: o salário não afasta, mas também não segura."}]}],
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
          "desc": "Compara o que foi combinado na contratação com o que a pessoa sentiu ao "
                  "receber. Mede promessa cumprida, não generosidade.",
          "fig": fig_exp}],
        [{"t": "fig", "titulo": "Comparação com o mercado da região", "kicker": "posicionamento",
          "desc": "“Comparando com outros trabalhos temporários que você conhece na região, o "
                  "pagamento da Mendes RH é…”",
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
                f"<span class='hd'>Existe uma saída mais barata que o reajuste linear</span>"
                f"{_p(bf)} aceitariam bônus por não faltar e {_p(bt)} bônus por ficar até o fim. "
                f"São os dois problemas da rodada 1 — absenteísmo e saída antecipada — com "
                f"pagamento condicionado a resultado, e não custo fixo sobre toda a folha."}]})

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
            "Pergunta nova nesta rodada. Foi incluída porque a rodada 1 trouxe, num campo aberto, "
            "um relato que exigia apuração formal — e não havia como medir se aquilo era exceção "
            "ou padrão. Agora há.",
        "fig": fig_resp,
        "extras": [
            {"estilo": "warn", "html":
                f"<span class='hd'>Quase metade teve alguma experiência de desrespeito</span>"
                f"Só {_p(r2['respeito_sempre'])} marcaram “sempre”. Numa temporada de poucas "
                f"semanas, {_p(100 - (r2['respeito_sempre'] or 0))} relatarem falha de respeito é "
                f"um número alto — e ele conversa diretamente com o item “tratamento pelos "
                f"funcionários efetivos” do gráfico anterior."},
            {"html":
                f"<span class='hd'>{n_relatos} pessoas descreveram uma situação</span>"
                f"De {n_escreveram} que escreveram no campo aberto — as demais responderam que "
                f"não tinham nada a relatar. Casos individuais são tratados pelo canal de "
                f"conduta, fora do painel. Aqui fica o padrão agregado."}]})

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
                "pessoa relatou. O salário é o mesmo valor para todo mundo na mesma função — "
                "quem se sentiu desrespeitado avalia pior até aquilo que não mudou.",
            "fig": fig_rp,
            "extras": [{"estilo": "warn", "html":
                f"<span class='hd'>Não é uma escada, é um degrau</span>"
                f"Entre “sempre” e “na maior parte do tempo” as notas praticamente não mudam — a "
                f"média dos dois é {_n(m_sal, 2)} no salário e {_n(m_cond, 2)} nas condições. "
                f"Quem marcou “{base_[0].split('  ·')[0].lower()}” cai para {_n(base_[1], 2)} e "
                f"{_n(base_[2], 2)}, mesmo recebendo o mesmo valor que os colegas de função. O "
                f"desrespeito não incomoda um pouco: quando acontece, contamina a avaliação "
                f"inteira. São {base_[0].split('n ')[-1]} pessoas — poucas, e é justamente por "
                f"isso que dá para tratar caso a caso."}]})

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
              f"<span class='hd'>{_p(r2['clt_sim_talvez'])} querem ou considerariam</span>"
              f"Para a maioria dessas pessoas o contrato temporário não é um bico de temporada, é "
              f"uma porta de entrada. Hoje não existe trilha formal atrás dessa porta — e essa é "
              f"uma conversa a ter com a Aviva, não uma ação interna da Mendes RH."}]}],
        [{"t": "fig", "titulo": "O que pesa contra a efetivação", "kicker": f"n {tot_contra}",
          "desc": "Somente quem respondeu “talvez” ou “não”. Base pequena — leitura indicativa, "
                  "não conclusiva.",
          "fig": fig_contra}] if fig_contra is not None else [],
    ]})

    # ---------------------------------------------------------------- 8 matriz
    m2 = _matriz_r2(d2)
    if not m2.empty:
        sec["blocos"].append({
            "t": "html", "so_tela": True,
            "html": "<div class='pq-h'><span class='t'>Matriz por função — rodada 2</span>"
                    "<span class='k'>síntese</span></div>"
                    "<div class='pq-d'>Verde é bom, vermelho é atenção. Funções com menos de "
                    f"{MIN_RECORTE} respostas são suprimidas automaticamente. “Respeito pleno” é o "
                    "percentual que respondeu “sempre”; “quer CLT” é o percentual que respondeu "
                    "“sim, com certeza”.</div>" + _matriz_r2_html(m2)})
        mpdf = m2.copy()
        for cc in ("Nota salário", "Nota condições"):
            mpdf[cc] = mpdf[cc].map(lambda v: _n(v, 2) if pd.notna(v) else "—")
        for cc in ("Respeito pleno", "Quer CLT"):
            mpdf[cc] = mpdf[cc].map(lambda v: f"{int(v)}%" if pd.notna(v) else "—")
        sec["blocos"].append({"t": "tabela", "so_pdf": True,
                              "titulo": "Matriz por função — rodada 2",
                              "desc": f"Funções com {MIN_RECORTE} ou mais respostas.",
                              "df": mpdf})

    # ------------------------------------------------------------- 9 leitura
    sec["blocos"].append({"t": "texto", "titulo": "Leitura da rodada 2",
                          "kicker": "análise", "html": _texto_leitura_r2(d2, r2)})

    # --------------------------------------------------------------- 10 ficha
    sec["blocos"].append({"t": "nota", "estilo": "", "html":
        f"<span class='hd'>Ficha técnica</span>"
        f"Coleta em 10 de agosto de 2026 · disparo por WhatsApp somente para quem respondeu a "
        f"rodada 1 · {r2['n']} respostas em {r2['convites']} convites ({_p(r2['taxa'])}) · "
        f"questionário anônimo, com o cadastro do sorteio em formulário separado. "
        f"<b>Incentivo:</b> sorteio de 10 prêmios de R$ 70 via PIX, pagos no dia de uso do "
        f"ingresso do Hot Park. <b>Limitações:</b> o público é o mesmo da rodada 1, logo herda o "
        f"mesmo viés — {_p(round(d2.grupo.eq(G_CUMPRIU).sum() / len(d2) * 100, 1))} das respostas "
        f"vêm de quem cumpriu a temporada, e os indicadores devem ser lidos como teto. Recortes "
        f"com menos de {MIN_RECORTE} respostas não são exibidos. Relatos nominais não entram no "
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
                "de notas 0 a 6, numa escala de −100 a +100. Acima de 50 é excelente; entre 0 e "
                "30, positivo mas exigente.",
        "fig": fig_idx,
        "extras": [{"html":
            f"<span class='hd'>A ordem é a mensagem</span>"
            f"As pessoas gostam mais da Mendes RH ({_n(e_tot['enps'])}) do que das condições de "
            f"trabalho ({_n(r2['condicoes']['enps'])}), e mais das condições do que do salário "
            f"({_n(r2['salario']['enps'])}). O vínculo com a empresa está sustentando a "
            f"experiência — não o contrário. Isso é um ativo, e é frágil."}]})

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
         "Tema recorrente nos comentários abertos e um relato de assédio",
         f"{trat_r2}% pedem melhora · só {_p(r2['respeito_sempre'])} sempre respeitados",
         "CONFIRMADO", CRIT)
    _lin("Transporte",
         f"{transp_r1}% de quem faltou citou · 90,0% dependem do fretado",
         f"{transp_r2}% pedem melhora",
         "CONFIRMADO", SERIOUS)
    _lin("Escala e folgas",
         "Aparece nos comentários abertos e no que teria feito ficar",
         f"{esc_r2}% pedem melhora · principal freio à efetivação",
         "CONFIRMADO", SERIOUS)
    _lin("Alimentação e descanso",
         "Pedidos pontuais no campo aberto",
         f"{ali_r2}% alimentação · {desc_r2}% cadeiras para descanso",
         "AMPLIADO", WARN)
    _lin("Salário",
         "Baixa presença entre as causas de falta e de saída",
         f"{_p(r2['expect_atendeu'])} tiveram a expectativa atendida",
         "DESCARTADO", GOOD)

    sec["blocos"].append({
        "t": "html", "so_tela": True,
        "html": "<div class='pq-h'><span class='t'>O que as duas rodadas dizem sobre o mesmo "
                "tema</span><span class='k'>convergência</span></div>"
                "<div class='pq-d'>A rodada 1 levantou hipóteses a partir de campos abertos; a "
                "rodada 2 foi desenhada para medi-las. “Confirmado” significa que o tema apareceu "
                "espontaneamente na primeira e foi dimensionado na segunda.</div>"
                + _tabela_html(["Tema", "Rodada 1 · experiência", "Rodada 2 · salário e condições",
                                "Veredito"], linhas)})
    df_conv = pd.DataFrame(
        [[l[0], l[1], l[2], l[3][0]] for l in linhas],
        columns=["Tema", "Rodada 1", "Rodada 2", "Veredito"])
    sec["blocos"].append({"t": "tabela", "so_pdf": True,
                          "titulo": "O que as duas rodadas dizem sobre o mesmo tema",
                          "desc": "Convergência entre as duas coletas.", "df": df_conv})

    # ------------------------------------------------------------- 4 leitura
    sec["blocos"].append({"t": "texto", "titulo": "O retrato conjunto", "kicker": "análise",
                          "html": f"""
<p>As duas rodadas somam <b>{rs['n_total'] + r2['n']} respostas</b> — {rs['n_total']} na primeira e
{r2['n']} na segunda — coletadas em cinco dias junto a um universo de {rs['convites']} pessoas
convidadas. Como a rodada 2 foi disparada só para quem já havia respondido a rodada 1, os dois
públicos se sobrepõem: não são amostras independentes. O retorno de {_p(r2['taxa'])} em um único
dia, numa segunda pesquisa com o mesmo público, é o indicador mais direto de que a escuta tem
credibilidade aqui.</p>

<p><b>A hipótese do salário caiu.</b> Era a suspeita natural para explicar
{_p(rs['faltou_cumpriu'])} de absenteísmo e {rs['n_saiu']} saídas antecipadas. A rodada 2 mostra
{_p(r2['expect_atendeu'])} com a expectativa atendida ou superada e apenas
{_p(r2['mercado_pior'])} considerando o pagamento pior que o do mercado local. O salário é
exigente, não é ferida.</p>

<p><b>O que sobra é relação.</b> Voz — quem não se sente à vontade para falar falta muito mais —
na rodada 1; respeito — {_p(100 - (r2['respeito_sempre'] or 0))} com alguma falha — na rodada 2.
São a mesma coisa vista de dois ângulos: a fronteira entre efetivo e temporário, e a ausência de
alguém escutando durante o contrato, não só no fim dele. Nenhum dos dois se resolve com dinheiro.</p>

<p><b>E há uma oportunidade que ninguém pediu.</b> {_p(r2['clt_sim_talvez'])} querem ou
considerariam efetivação CLT na Aviva. Essas pessoas já foram treinadas, já conhecem a operação e
já demonstraram que ficam até o fim. Uma trilha formal de efetivação transformaria o custo de
captação da próxima temporada em investimento — e é a única ação desta lista que depende mais da
Aviva do que da Mendes RH.</p>"""})

    # --------------------------------------------------------------- 5 plano
    sec["blocos"].append({"t": "texto", "titulo": "Plano de ação consolidado",
                          "kicker": "próxima temporada", "html": _plano(base, d2)})

    # --------------------------------------------------------------- 6 ficha
    sec["blocos"].append({"t": "nota", "estilo": "", "html":
        f"<span class='hd'>Ficha técnica</span>"
        f"Rodada 1: coleta de 6 a 10 de agosto, {rs['n_total']} respostas em {rs['convites']} "
        f"convites ({_p(rs['taxa_total'])}), dois questionários. Rodada 2: coleta em 10 de agosto, "
        f"{r2['n']} respostas em {r2['convites']} convites ({_p(r2['taxa'])}), questionário único "
        f"disparado só para quem respondeu a rodada 1. Ambas anônimas, com dados de contato em "
        f"formulário separado. <b>Limitações:</b> os dois públicos se sobrepõem, então os "
        f"resultados não são amostras independentes; a maioria das respostas vem de quem cumpriu a "
        f"temporada, e os indicadores devem ser lidos como teto. Recortes com menos de "
        f"{MIN_RECORTE} respostas não são exibidos. Relatos nominais não entram no painel."})
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
            st.caption("A visão consolidada usa sempre a base completa das duas rodadas, "
                       "sem filtros — é o quadro de abertura da reunião.")

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
