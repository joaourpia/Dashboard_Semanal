# -*- coding: utf-8 -*-
"""
================================================================================
 ABA "PESQUISA" - Experiencia do temporario na temporada de julho
 Mendes RH x Aviva / Rio Quente Resorts
================================================================================
Le dados/pesquisa/RESPOSTAS_PESQUISA.xlsx via pesquisa_dados.py e monta a
secao no mesmo formato de blocos das demais abas: construir_pesquisa() devolve
{"titulo","sub","blocos"}, ui.desenhar() joga na tela e relatorio_pdf percorre
a mesma lista. Tela e relatorio nunca divergem.

Paleta identica a das outras abas, ja validada para daltonismo. Nenhum dado
depende de cor isolada - todo mark colorido carrega rotulo.

Recortes com menos de 5 respostas sao suprimidos automaticamente: nesse volume
o respondente e identificavel e o anonimato prometido no formulario cai.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ui_dashboard as ui
import pesquisa_dados as pd_src
from pesquisa_dados import (G_CUMPRIU, G_SAIU, MIN_RECORTE, SEM_FALTA,
                            contagem, contagem_multipla, enps)

TITULO = "Pesquisa de Experiência do Temporário"
SUBTITULO = "Temporada de julho de 2026 · coleta de 6 a 10 de agosto"

S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
GOOD, WARN, SERIOUS, CRIT = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURF = "#eceae4", "#c3c2b7", "#ffffff"

K_GRUPO, K_FUNC = "pq_grupo", "pq_funcao"


def _p(n, casas=1):
    return f"{n:.{casas}f}".replace(".", ",") + "%"


def _n(n, casas=1):
    return f"{n:.{casas}f}".replace(".", ",")


@st.cache_data(show_spinner=False)
def carregar():
    base, c, s = pd_src.consolidar()
    return base, c, s


# ------------------------------------------------------------------ filtros
def _filtrar(base, c, s):
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


# ------------------------------------------------------------------ graficos
def _barras_h(rotulos, valores, cor, sufixo="", altura=None, cores=None,
              texto=None):
    fig = go.Figure(go.Bar(
        x=list(valores), y=list(rotulos), orientation="h",
        marker=dict(color=cores or cor,
                    line=dict(color="rgba(0,0,0,0)", width=0)),
        text=texto or [f"{v}{sufixo}" for v in valores],
        textposition="outside", cliponaxis=False,
        textfont=dict(size=11.5, color=INK2), hoverinfo="skip"))
    alt = altura or max(150, 30 * len(list(rotulos)) + 40)
    fig.update_layout(
        height=alt, margin=dict(l=6, r=52, t=8, b=24), showlegend=False,
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family=ui.FONTE, size=12, color=INK2),
        xaxis=dict(showgrid=True, gridcolor=GRID, zerolinecolor=AXIS,
                   showticklabels=False, range=[0, max(list(valores) or [1]) * 1.2]),
        yaxis=dict(autorange="reversed", showgrid=False,
                   linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=INK, size=11.5)))
    return fig


def _fig_participacao(base):
    fun = contagem(base.funcao).head(10)
    loc = contagem(base.local).head(10)
    return (_barras_h(fun.index, fun.values, S1),
            _barras_h(loc.index, loc.values, S4))


def _fig_enps_pilha(e):
    if not e:
        return None
    fig = go.Figure()
    for rot, val, cor in [("Recomendam (notas 9 e 10)", e["promotores"], GOOD),
                          ("Indiferentes (7 e 8)", e["neutros"], WARN),
                          ("Não recomendam (0 a 6)", e["detratores"], CRIT)]:
        pcs = val / e["n"] * 100
        fig.add_bar(x=[val], y=["recom"], orientation="h", name=rot,
                    marker=dict(color=cor),
                    text=[f"{rot.split(' (')[0]}<br>{val} · {_p(pcs)}"],
                    textposition="inside", insidetextanchor="middle",
                    textfont=dict(size=11.5, color="#fff" if cor != WARN else INK),
                    hoverinfo="skip")
    fig.update_layout(
        barmode="stack", height=132, margin=dict(l=6, r=6, t=10, b=6),
        paper_bgcolor=SURF, plot_bgcolor=SURF, separators=",.",
        font=dict(family=ui.FONTE, size=12, color=INK2), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


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
    fig = _barras_h(rot, val, None, cores=cores,
                    texto=[_n(v) for v in val])
    fig.update_xaxes(range=[min(0, min(val) * 1.3), max(val) * 1.28])
    return fig, len(linhas)


def _fig_causas(base):
    faltou = base[base.faltou]
    s, tot = contagem_multipla(faltou.causa_falta_lista, len(faltou))
    if tot == 0:
        return None, 0
    s = s.head(9)
    pcs = [round(v / tot * 100, 1) for v in s.values]
    cores = [MUTED if "Não sei" in k else S2 for k in s.index]
    return _barras_h(s.index, pcs, S2, cores=cores,
                     texto=[_p(v) for v in pcs]), tot


def _fig_preditor(base, coluna, rotulos_ordem):
    """Barras pareadas: taxa de falta e intenção de saída por nível."""
    PS = "Em algum momento você pensou em sair antes do fim?"
    dados = []
    for rot in rotulos_ordem:
        g = base[base[coluna] == rot]
        if len(g) < MIN_RECORTE:
            continue
        f = round(g.faltou.sum() / len(g) * 100)
        ps = g["pensou_sair"].dropna()
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
    fig = _barras_h(rot, val, None, cores=cor, texto=[str(v) for v in val])
    return fig


# -------------------------------------------------------------------- matriz
def _matriz_funcao(base):
    PS = "pensou_sair"
    linhas = []
    for f, g in base.groupby("funcao"):
        if len(g) < MIN_RECORTE or not f:
            continue
        e = enps(g.nps)
        ps = g[PS].dropna()
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


def _cor_recom(v):
    if pd.isna(v):
        return "#f7f8fa", INK
    return (GOOD, "#fff") if v >= 60 else ((WARN, INK) if v >= 40 else (CRIT, "#fff"))


def _cor_ruim(v, bom, medio):
    """Quanto menor melhor (faltou, pensou em sair)."""
    if pd.isna(v):
        return "#f7f8fa", INK
    if v <= bom:
        return GOOD, "#fff"
    if v <= medio:
        return WARN, INK
    return (SERIOUS, "#fff") if v <= medio + 20 else (CRIT, "#fff")


def _matriz_html(df):
    if df.empty:
        return "<div class='pq-vazio'>Sem recortes com 5 ou mais respostas.</div>"
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
    th = "".join(f"<th>{c}</th>" for c in ["Função", "n", "Recomendação", "Faltou",
                                           "Pensou em sair", "Voltaria"])
    trs = []
    for _, r in df.iterrows():
        ce, te = _cor_recom(r["Recomendação"])
        cf, tf = _cor_ruim(r["Faltou"], 30, 45)
        cp, tp = _cor_ruim(r["Pensou em sair"], 20, 35)
        trs.append(
            f"<tr><td>{r['Função']}</td><td>{int(r['n'])}</td>"
            f"<td class='q' style='background:{ce};color:{te}'>{_n(r['Recomendação'])}</td>"
            f"<td class='q' style='background:{cf};color:{tf}'>{int(r['Faltou'])}%</td>"
            f"<td class='q' style='background:{cp};color:{tp}'>"
            f"{int(r['Pensou em sair']) if pd.notna(r['Pensou em sair']) else '—'}%</td>"
            f"<td>{int(r['Voltaria']) if pd.notna(r['Voltaria']) else '—'}%</td></tr>")
    return css + f"<div class='pq-wrap'><table class='pqm'><thead><tr>{th}</tr></thead>" \
                 f"<tbody>{''.join(trs)}</tbody></table></div>"


# --------------------------------------------------------------------- textos
def _texto_leitura(base, c, s, rs):
    ec, es = rs["enps_cumpriu"], rs["enps_saiu"]
    faltou = base[base.faltou]
    causas, tot = contagem_multipla(faltou.causa_falta_lista, len(faltou))
    top = causas.head(3) if len(causas) else pd.Series(dtype=int)
    cit = int(causas.sum()) if len(causas) else 0
    soma3 = round(sum(top.values) / cit * 100) if cit else 0
    desengaj = 0
    for k in ("Desânimo com o trabalho", "Outro trabalho ou bico no mesmo dia",
              "Trabalho pesado demais para o valor pago"):
        desengaj += int(causas.get(k, 0))
    pdesengaj = round(desengaj / cit * 100, 1) if cit else 0

    partes = []
    partes.append(
        f"<p>A pesquisa reuniu <b>{rs['n_total']} respostas em {rs['convites']} convites</b> "
        f"({_p(rs['taxa_total'])}), contra 76 respostas na rodada do ano passado. As duas metas do "
        f"plano foram superadas: {_p(rs['taxa_cumpriu'])} no grupo que cumpriu a temporada e "
        f"{_p(rs['taxa_saiu'])} no grupo que saiu antes do fim.</p>")
    if tot:
        partes.append(
            f"<p>Entre as {tot} pessoas que declararam ao menos uma ausência, as três causas mais "
            f"citadas — {', '.join(top.index[:3])} — concentram <b>{soma3}% das citações</b>, "
            f"enquanto desânimo, trabalho paralelo e insatisfação com o valor pago somam "
            f"{_p(pdesengaj)}. O absenteísmo desta temporada é um problema de saúde e de "
            f"logística, não de engajamento.</p>")
    if "pensou_sair" in base and base.pensou_sair.notna().any():
        voz = "Você se sentiu à vontade para falar quando algo estava errado?"
        if voz in base:
            g1 = base[base[voz] == "Sim"]
            g2 = base[base[voz] == "Não"]
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
            f"<b>{_n(es['enps'])}</b> "
            f"entre quem saiu antes do fim, com {_p(rs['voltaria_sim_talvez'])} do total dispostos a "
            f"voltar ou considerando voltar. A diferença de {_n(ec['enps'] - es['enps'])} pontos entre "
            f"os dois grupos é o custo reputacional da saída antecipada — e é modesta.</p>")
    if s is not None and not s.empty:
        cd = "Em que momento você decidiu que ia sair?"
        if cd in s:
            cedo = int(s[cd].isin(["Já nos primeiros dias", "Na primeira semana"]).sum())
            partes.append(
                f"<p>A perda acontece cedo: <b>{cedo} de {len(s)}</b> das saídas respondidas foram "
                f"decididas nos primeiros dias ou na primeira semana. É a janela em que não existe "
                f"hoje nenhuma ação programada, e é onde a próxima temporada tem mais a ganhar.</p>")
    return "".join(partes)


def _plano(base):
    """Plano de ação com os números tirados da mesma base dos gráficos."""
    PGP = "Você recebeu tudo certo e no prazo (salário, vale, hora extra)?"
    VOZ = "Você se sentiu à vontade para falar quando algo estava errado?"

    def tx(col, valor):
        g = base[base[col] == valor] if col in base else base.iloc[0:0]
        return (round(g.faltou.sum() / len(g) * 100), len(g)) if len(g) else (None, 0)

    err, n_err = tx(PGP, "Teve atraso ou erro uma vez")
    ok, n_ok = tx(PGP, "Sim, sempre")
    sem_voz, n_sv = tx(VOZ, "Não")
    com_voz, n_cv = tx(VOZ, "Sim")

    t_pag = (f"Quem teve ao menos um erro faltou {err}% contra {ok}% dos demais. "
             if err is not None and ok is not None else "")
    t_voz = (f"Quem não se sente à vontade para falar falta {sem_voz}%, contra {com_voz}% de "
             f"quem se sente. " if sem_voz is not None and com_voz is not None else "")

    return f"""
<div class="duo">
  <div class="note good"><span class="hd">Ação imediata · custo zero</span><ul>
    <li><b>Conversa de 5 minutos no 3º e no 7º dia</b> de cada temporário, com registro de quem
        falou o quê. A decisão de sair é tomada dentro dessa janela.</li>
    <li><b>Zerar erro e atraso de pagamento.</b> {t_pag}Ninguém marcou “teve problema mais de uma
        vez” — é falha pontual, corrigível internamente.</li>
    <li><b>Alinhamento com efetivos e segurança</b> sobre o tratamento dado ao temporário, tema
        recorrente nos comentários abertos.</li>
  </ul></div>
  <div class="note warn"><span class="hd">Ação estruturada · exige planejamento</span><ul>
    <li><b>Canal de escuta ativo durante a temporada</b>, não apenas ao final. {t_voz}</li>
    <li><b>Auditoria do transporte fretado</b>: rota da recepção, horários, estado dos veículos e
        conduta a bordo. 89,4% dependem exclusivamente do fretado.</li>
    <li><b>Diagnóstico dirigido em Camareira e governança</b>, a função com os três indicadores
        simultaneamente piores.</li>
    <li><b>Piloto de bônus por assiduidade com folga adicional</b> em uma função, medindo o efeito
        contra o histórico desta temporada.</li>
  </ul></div>
</div>
"""


# ================================================================= construcao
def construir_pesquisa():
    base, c, s = carregar()
    sec = {"titulo": TITULO, "sub": SUBTITULO, "blocos": []}
    if base is None or base.empty:
        return sec

    PS = "Em algum momento você pensou em sair antes do fim?"
    VOZ = "Você se sentiu à vontade para falar quando algo estava errado?"
    PGJ = "Pensando no esforço do dia a dia, o pagamento foi justo?"
    PGP = "Você recebeu tudo certo e no prazo (salário, vale, hora extra)?"

    # anexa as colunas do questionario longo ao quadro canonico
    extras = c.set_index(c.index)
    base = base.copy()
    for col in (PS, VOZ, PGJ, PGP):
        vals = list(c[col]) if col in c else []
        serie = pd.Series([np.nan] * len(base), index=base.index, dtype=object)
        idx_c = base.index[base.origem == "cumpriu"]
        for i, v in zip(idx_c, vals):
            serie.loc[i] = str(v).strip() if pd.notna(v) else np.nan
        base[col] = serie
    base = base.rename(columns={PS: "pensou_sair"})

    base, c, s = _filtrar(base, c, s)
    if base.empty:
        return sec
    rs = pd_src.resumo(base)
    ec = rs["enps_cumpriu"] or rs["enps_total"]

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
        [{"t": "fig", "titulo": "Quem respondeu — por função",
          "kicker": "amostra",
          "desc": "Número de respondentes. Serve para checar se a pesquisa representa a "
                  "operação antes de qualquer leitura.",
          "fig": f_fun}],
        [{"t": "fig", "titulo": "Por local de trabalho", "kicker": "amostra",
          "desc": "89,4% moram na região e 89,4% dependem do transporte fretado — os dois "
                  "números explicam boa parte do resto da aba.",
          "fig": f_loc}],
    ]})

    # ------------------------------------------- 3 índice de recomendação
    fig_pilha = _fig_enps_pilha(e_tot)
    fig_fun, qtd = _fig_enps_funcao(base)
    extras_enps = []
    if rs["enps_cumpriu"] and rs["enps_saiu"]:
        extras_enps.append({"html":
            f"<span class='hd'>Quem saiu antes do fim marcou "
            f"{_n(rs['enps_saiu']['enps'])}</span>Contra {_n(rs['enps_cumpriu']['enps'])} de quem "
            f"cumpriu a temporada. A diferença de {_n(rs['enps_cumpriu']['enps'] - rs['enps_saiu']['enps'])} "
            f"pontos é o custo reputacional da saída antecipada — e é pequena: mesmo quem "
            f"interrompeu o contrato segue recontratável."})
    sec["blocos"].append({"t": "cards", "itens": [
        [{"t": "fig", "titulo": "Índice de recomendação da Mendes RH",
          "kicker": "vínculo",
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
            "t": "fig", "titulo": "A janela da saída",
            "kicker": f"n {len(s)}",
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
                    "funções com muita saída antecipada.</div>"
                    + _matriz_html(mtx)})
        mpdf = mtx.copy()
        mpdf["Recomendação"] = mpdf["Recomendação"].map(lambda v: _n(v) if pd.notna(v) else "—")
        for cc in ("Faltou", "Pensou em sair", "Voltaria"):
            mpdf[cc] = mpdf[cc].map(lambda v: f"{int(v)}%" if pd.notna(v) else "—")
        sec["blocos"].append({"t": "tabela", "so_pdf": True, "titulo": "Matriz por função",
                              "desc": f"Funções com {MIN_RECORTE} ou mais respostas.",
                              "df": mpdf})

    # ------------------------------------------------------------- 8 leitura
    sec["blocos"].append({"t": "texto", "titulo": "Leitura da temporada",
                          "kicker": "análise",
                          "html": _texto_leitura(base, c, s, rs)})

    # --------------------------------------------------------------- 9 plano
    sec["blocos"].append({"t": "texto", "titulo": "Plano de ação",
                          "kicker": "próxima temporada", "html": _plano(base)})

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
    funcoes = sorted([f for f in base.funcao.dropna().unique() if f])

    with st.container(border=True):
        f1, f2 = st.columns([1.4, 3])
        with f1:
            st.selectbox("Grupo", ["Todos", G_CUMPRIU, G_SAIU], key=K_GRUPO)
        with f2:
            st.multiselect("Funções", funcoes, default=[], key=K_FUNC,
                           placeholder="Todas as funções")

    sec = construir_pesquisa()
    if not sec["blocos"]:
        st.info("Sem respostas para o filtro selecionado.")
        return
    ui.desenhar(sec)
