# -*- coding: utf-8 -*-
"""
================================================================================
 EXPORTACAO EM PDF  |  Mendes RH x Aviva / Rio Quente Resorts
================================================================================
Monta um PDF A4 paisagem a partir das mesmas secoes que alimentam a tela,
para que relatorio impresso e painel nunca divirjam.

Dependencias:
    pip install reportlab "kaleido==0.2.1"

kaleido 0.2.1 e autocontido (nao exige Chrome instalado). Se voce ja tiver
kaleido >= 1.0 junto com o Google Chrome, tambem funciona.
================================================================================
"""
import html as _html
import io
import re
from datetime import datetime

FALHA_IMPORT = None
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                    PageBreak, PageTemplate, Paragraph, Spacer,
                                    Table, TableStyle)
except Exception as e:                                   # pragma: no cover
    FALHA_IMPORT = f"reportlab não instalado ({e})"

INK = colors.HexColor("#0b0b0b") if not FALHA_IMPORT else None
INK2 = colors.HexColor("#52514e") if not FALHA_IMPORT else None
MUT = colors.HexColor("#898781") if not FALHA_IMPORT else None
AZUL = colors.HexColor("#2a78d6") if not FALHA_IMPORT else None
AZUL_ESC = colors.HexColor("#0d366b") if not FALHA_IMPORT else None
VERDE = colors.HexColor("#1baf7a") if not FALHA_IMPORT else None
LINHA = colors.HexColor("#e1e0d9") if not FALHA_IMPORT else None

LARG, ALT = landscape(A4)
MARGEM = 14 * mm
UTIL = LARG - 2 * MARGEM


def disponivel():
    """(ok, mensagem) — checagem BARATA, chamada a cada rerun da tela.

    Nao aciona o kaleido aqui de proposito: cada chamada de to_image sobe um
    processo do chromium, o que travava o painel a cada clique. A renderizacao
    dos graficos so acontece dentro do processo separado de geracao.
    """
    if FALHA_IMPORT:
        return False, FALHA_IMPORT
    try:
        import importlib.util
        if importlib.util.find_spec("kaleido") is None:
            return False, ('a biblioteca kaleido não está instalada. Instale com:  '
                           'pip install "kaleido==0.2.1"')
    except Exception:
        pass
    return True, ""


# ------------------------------------------------------------------ gráficos
def _fig_png(fig, largura_px=1500, altura_px=None, escala=2):
    """Converte a figura plotly em PNG, com fonte segura para impressão."""
    import copy
    f = copy.deepcopy(fig)
    alt = altura_px or (f.layout.height or 340)

    # Na tela o Streamlit redimensiona e o plotly expande as margens sozinho.
    # Na exportacao o tamanho e fixo, entao garantimos folga para os rotulos
    # dos eixos nao serem cortados.
    m = f.layout.margin
    f.update_layout(
        font=dict(family="Arial, Helvetica, sans-serif"),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        width=largura_px, height=int(alt),
        margin=dict(l=max(m.l or 0, 58), r=max(m.r or 0, 24),
                    t=max(m.t or 0, 34), b=max(m.b or 0, 46)))
    try:
        f.update_xaxes(automargin=True)
        f.update_yaxes(automargin=True)
    except Exception:
        pass
    return f.to_image(format="png", scale=escala)


# --------------------------------------------------------------------- texto
def _limpar(t):
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"</?(span|div)[^>]*>", "", t)
    t = re.sub(r"<(?!/?[bi]\b)[^>]+>", "", t)
    return _html.unescape(re.sub(r"\s+", " ", t)).strip()


def _html_para_flowables(bruto, estilos):
    """Converte os blocos de análise (HTML simples) em parágrafos do PDF."""
    saida = []
    for bloco in re.split(r'(?=<div class=["\']note)', bruto):
        if not bloco.strip():
            continue
        cab = re.search(r'<span class=["\']hd["\']>(.*?)</span>', bloco, re.S)
        if cab:
            saida.append(Paragraph(_limpar(cab.group(1)), estilos["sub"]))
            bloco = bloco.replace(cab.group(0), "")
        itens = re.findall(r"<li>(.*?)</li>", bloco, re.S)
        if itens:
            for it in itens:
                saida.append(Paragraph(f"\u2022 {_limpar(it)}", estilos["corpo"]))
        else:
            for par in re.split(r"</p>", bloco):
                txt = _limpar(par)
                if txt:
                    saida.append(Paragraph(txt, estilos["corpo"]))
        saida.append(Spacer(1, 3 * mm))
    return saida


def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("t", parent=base["Normal"], fontName="Helvetica-Bold",
                                 fontSize=17, leading=21, textColor=INK, spaceAfter=2),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontName="Helvetica-Bold",
                              fontSize=10.5, leading=14, textColor=INK, spaceBefore=2,
                              spaceAfter=3),
        "secao": ParagraphStyle("se", parent=base["Normal"], fontName="Helvetica-Bold",
                                fontSize=12, leading=15, textColor=INK, spaceBefore=4,
                                spaceAfter=1),
        "desc": ParagraphStyle("d", parent=base["Normal"], fontName="Helvetica",
                               fontSize=8.5, leading=11.5, textColor=MUT, spaceAfter=4),
        "corpo": ParagraphStyle("c", parent=base["Normal"], fontName="Helvetica",
                                fontSize=9, leading=13, textColor=INK,
                                alignment=TA_LEFT, spaceAfter=2, leftIndent=4),
        "rodape": ParagraphStyle("r", parent=base["Normal"], fontName="Helvetica",
                                 fontSize=7.5, leading=10, textColor=MUT),
    }


# ------------------------------------------------------------------- tabelas
def _tabela_kpis(tiles, est):
    dados = [[], []]
    for t in tiles:
        dados[0].append(Paragraph(f"<b>{_limpar(t['lb']).upper()}</b>",
                                  ParagraphStyle("k", fontName="Helvetica-Bold",
                                                 fontSize=7, leading=9,
                                                 textColor=colors.white)))
        sub = _limpar(t.get("sb", ""))
        badge = t.get("badge")
        if badge:
            sub = f"{sub} · {_limpar(badge)}"
        dados[1].append(Paragraph(
            f"<b>{_limpar(t['vl'])}</b><br/><font size=7>{sub}</font>",
            ParagraphStyle("v", fontName="Helvetica-Bold", fontSize=15, leading=17,
                           textColor=colors.white)))
    larg = UTIL / max(len(tiles), 1)
    tb = Table(dados, colWidths=[larg] * len(tiles), rowHeights=[9 * mm, 15 * mm])
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL_ESC),
        ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("LINEAFTER", (0, 0), (-2, -1), 0.6, colors.HexColor("#2a5f9e")),
    ]))
    return tb


def _tabela_df(df, est, max_linhas=40, largura=None):
    df = df.head(max_linhas)
    cab = [Paragraph(f"<b>{c}</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                                                   fontSize=7.5, leading=9.5,
                                                   textColor=colors.white))
           for c in df.columns]
    linhas = [cab]
    for _, r in df.iterrows():
        linhas.append([Paragraph(str(v), ParagraphStyle("td", fontName="Helvetica",
                                                        fontSize=7.5, leading=9.5,
                                                        textColor=INK))
                       for v in r.tolist()])
    larg = (largura or UTIL) / len(df.columns)
    tb = Table(linhas, colWidths=[larg] * len(df.columns), repeatRows=1)
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f8fa")]),
        ("GRID", (0, 0), (-1, -1), 0.3, LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tb


# --------------------------------------------------------------------- capa
def _cabecalho_rodape(canvas, doc, titulo, logo_bytes, quando):
    canvas.saveState()
    canvas.setFillColor(AZUL_ESC)
    canvas.rect(0, ALT - 11 * mm, LARG, 11 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGEM, ALT - 7.6 * mm, titulo)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(LARG - MARGEM, ALT - 7.6 * mm, "Mendes RH · Aviva / Rio Quente")
    canvas.setStrokeColor(LINHA)
    canvas.setLineWidth(0.5)
    canvas.line(MARGEM, 11 * mm, LARG - MARGEM, 11 * mm)
    canvas.setFillColor(MUT)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGEM, 7 * mm, f"Gerado em {quando}")
    canvas.drawRightString(LARG - MARGEM, 7 * mm, f"Página {doc.page}")
    canvas.restoreState()


# ------------------------------------------------------------------- geração
def gerar_pdf(secoes, titulo="Relatório de Gestão de Temporários",
              subtitulo="", logo_bytes=None):
    """
    secoes: lista de {"titulo": str, "blocos": [...]} no mesmo formato usado
            para desenhar na tela.
    Retorna os bytes do PDF.
    """
    ok, msg = disponivel()
    if not ok:
        raise RuntimeError(msg)

    est = _estilos()
    quando = datetime.now().strftime("%d/%m/%Y às %H:%M")
    buf = io.BytesIO()

    doc = BaseDocTemplate(buf, pagesize=landscape(A4),
                          leftMargin=MARGEM, rightMargin=MARGEM,
                          topMargin=16 * mm, bottomMargin=15 * mm,
                          title=titulo, author="Mendes RH")
    frame = Frame(MARGEM, 15 * mm, UTIL, ALT - 31 * mm, id="f", showBoundary=0)
    doc.addPageTemplates([PageTemplate(
        id="p", frames=[frame],
        onPage=lambda c, d: _cabecalho_rodape(c, d, titulo, logo_bytes, quando))])

    hist = []
    # ---- capa
    if logo_bytes:
        try:
            img = Image(io.BytesIO(logo_bytes))
            r = img.imageWidth / img.imageHeight
            img.drawHeight = 22 * mm
            img.drawWidth = 22 * mm * r
            img.hAlign = "LEFT"
            hist += [Spacer(1, 6 * mm), img]
        except Exception:
            pass
    hist += [Spacer(1, 8 * mm),
             Paragraph(titulo, ParagraphStyle("cap", fontName="Helvetica-Bold",
                                              fontSize=26, leading=30, textColor=INK)),
             Spacer(1, 2 * mm),
             Paragraph(subtitulo, ParagraphStyle("cap2", fontName="Helvetica",
                                                 fontSize=12, leading=16, textColor=INK2)),
             Spacer(1, 6 * mm),
             Paragraph("Conteúdo: " + " · ".join(s["titulo"] for s in secoes), est["desc"]),
             PageBreak()]

    for i, sec in enumerate(secoes):
        hist.append(Paragraph(sec["titulo"], est["titulo"]))
        if sec.get("sub"):
            hist.append(Paragraph(_limpar(sec["sub"]), est["desc"]))
        hist.append(Spacer(1, 3 * mm))

        for b in sec["blocos"]:
            tipo = b.get("t")
            if tipo == "hero":
                hist.append(_tabela_kpis(b["tiles"], est))
                hist.append(Spacer(1, 5 * mm))
            elif tipo == "fig":
                partes = []
                if b.get("titulo"):
                    partes.append(Paragraph(b["titulo"], est["secao"]))
                if b.get("desc"):
                    partes.append(Paragraph(_limpar(b["desc"]), est["desc"]))
                try:
                    png = _fig_png(b["fig"], largura_px=1150,
                                   altura_px=b.get("altura") or b["fig"].layout.height)
                    im = Image(io.BytesIO(png))
                    r = im.imageWidth / im.imageHeight
                    im.drawWidth = UTIL
                    im.drawHeight = UTIL / r
                    lim = ALT - 62 * mm
                    if im.drawHeight > lim:
                        im.drawHeight, im.drawWidth = lim, lim * r
                    im.hAlign = "CENTER"
                    partes.append(im)
                except Exception as e:
                    partes.append(Paragraph(f"[gráfico não renderizado: {e}]", est["desc"]))
                for extra in b.get("extras", []):
                    partes += _html_para_flowables(extra["html"], est)
                partes.append(Spacer(1, 4 * mm))
                hist.append(KeepTogether(partes))
            elif tipo in ("texto", "nota"):
                partes = []
                if b.get("titulo"):
                    partes.append(Paragraph(b["titulo"], est["secao"]))
                partes += _html_para_flowables(b["html"], est)
                hist.append(KeepTogether(partes))
            elif tipo == "tabela":
                partes = []
                if b.get("titulo"):
                    partes.append(Paragraph(b["titulo"], est["secao"]))
                if b.get("desc"):
                    partes.append(Paragraph(_limpar(b["desc"]), est["desc"]))
                partes.append(_tabela_df(b["df"], est))
                partes.append(Spacer(1, 4 * mm))
                hist.append(KeepTogether(partes))
            elif tipo == "cards":
                n = max(len(b["itens"]), 1)
                larg = UTIL / n
                celulas = []
                for filho in b["itens"]:
                    conteudo = []
                    for sub_b in filho:
                        conteudo += _blocos_simples(sub_b, est, larg - 6)
                    celulas.append(conteudo)
                tb = Table([celulas], colWidths=[larg] * n)
                tb.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                hist.append(tb)
                hist.append(Spacer(1, 4 * mm))
        if i < len(secoes) - 1:
            hist.append(PageBreak())

    doc.build(hist)
    return buf.getvalue()


def _blocos_simples(b, est, larg=None):
    """Trata um bloco isolado vindo de um agrupamento em colunas."""
    larg = larg or UTIL
    saida = []
    tipo = b.get("t")
    if tipo == "fig":
        if b.get("titulo"):
            saida.append(Paragraph(b["titulo"], est["secao"]))
        if b.get("desc"):
            saida.append(Paragraph(_limpar(b["desc"]), est["desc"]))
        try:
            png = _fig_png(b["fig"], largura_px=700,
                           altura_px=b.get("altura") or b["fig"].layout.height)
            im = Image(io.BytesIO(png))
            r = im.imageWidth / im.imageHeight
            im.drawWidth = larg
            im.drawHeight = im.drawWidth / r
            lim = ALT - 78 * mm
            if im.drawHeight > lim:
                im.drawHeight, im.drawWidth = lim, lim * r
            im.hAlign = "CENTER"
            saida.append(im)
        except Exception as e:
            saida.append(Paragraph(f"[gráfico não renderizado: {e}]", est["desc"]))
        for extra in b.get("extras", []):
            saida += _html_para_flowables(extra["html"], est)
        saida.append(Spacer(1, 3 * mm))
    elif tipo in ("texto", "nota"):
        if b.get("titulo"):
            saida.append(Paragraph(b["titulo"], est["secao"]))
        saida += _html_para_flowables(b["html"], est)
    elif tipo == "tabela":
        if b.get("titulo"):
            saida.append(Paragraph(b["titulo"], est["secao"]))
        saida.append(_tabela_df(b["df"], est, largura=larg))
        saida.append(Spacer(1, 4 * mm))
    return saida



# =============================================================================
# EXPORTACAO EM HTML (sempre disponivel, sem dependencia externa)
# =============================================================================
# Alternativa a prova de falhas: gera um arquivo unico que abre em qualquer
# navegador e pode ser impresso em PDF com Ctrl+P. Nao usa kaleido nem
# reportlab; os graficos vao interativos, ja com quebra de pagina por secao.

CSS_HTML = """
*{box-sizing:border-box}
body{margin:0;background:#f4f5f7;color:#0b0b0b;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}
.pg{max-width:1180px;margin:0 auto;padding:24px 22px 40px 22px;}
.capa{background:linear-gradient(125deg,#0d366b,#1c5cab 52%,#2a78d6);color:#fff;
  border-radius:18px;padding:30px 30px 26px 30px;margin-bottom:22px;}
.capa h1{margin:0;font-size:1.9rem;font-weight:780;letter-spacing:-.02em;}
.capa .s{opacity:.82;margin-top:6px;font-size:.95rem;}
.capa img{max-height:56px;margin-bottom:16px;display:block;background:#fff;
  padding:6px 10px;border-radius:10px;}
h2.sec{font-size:1.45rem;font-weight:770;margin:34px 0 4px 0;letter-spacing:-.02em;}
h2.sec + .s{color:#52514e;font-size:.9rem;margin-bottom:14px;}
.card{background:#fff;border:1px solid rgba(11,11,11,.08);border-radius:16px;
  padding:16px 20px 12px 20px;margin-bottom:16px;
  box-shadow:0 1px 2px rgba(11,11,11,.04),0 10px 30px -16px rgba(11,11,11,.18);}
.card h3{margin:2px 0 2px 0;font-size:1.02rem;font-weight:730;}
.card .d{color:#52514e;font-size:.83rem;margin-bottom:8px;}
.kpis{display:grid;gap:10px;margin-bottom:16px;}
.kpi{background:#0d366b;color:#fff;border-radius:14px;padding:14px 16px;}
.kpi .l{font-size:.66rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  opacity:.75;}
.kpi .v{font-size:1.75rem;font-weight:780;margin-top:2px;line-height:1.15;}
.kpi .s{font-size:.72rem;opacity:.78;margin-top:4px;}
.note{border-left:4px solid #2a78d6;background:#fbfcfe;border-radius:0 12px 12px 0;
  padding:13px 17px;font-size:.92rem;line-height:1.65;}
.note.good{border-left-color:#0ca30c;background:#f6fcf6;}
.note.warn{border-left-color:#fab219;background:#fffdf7;}
.note.bad{border-left-color:#d03b3b;background:#fffbfb;}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
table.tb{width:100%;border-collapse:collapse;font-size:.8rem;}
table.tb th{background:#2a78d6;color:#fff;text-align:left;padding:6px 8px;font-weight:700;}
table.tb td{padding:5px 8px;border-bottom:1px solid #f0efec;}
table.tb tr:nth-child(even) td{background:#f7f8fa;}
.rodape{color:#898781;font-size:.78rem;text-align:center;margin-top:26px;}
@media print{
  body{background:#fff;}
  .pg{max-width:none;padding:0;}
  h2.sec{page-break-before:always;}
  h2.sec:first-of-type{page-break-before:auto;}
  .card,.note,.kpi{break-inside:avoid;page-break-inside:avoid;}
  @page{size:A4 landscape;margin:12mm;}
}
"""


def gerar_html(secoes, titulo="Relatório de Gestão de Temporários",
               subtitulo="", logo_b64=None):
    from datetime import datetime as _dt
    import plotly.io as pio

    partes, primeiro = [], True

    def fig_html(fig):
        nonlocal primeiro
        import copy
        fig = copy.deepcopy(fig)
        m = fig.layout.margin
        fig.update_layout(margin=dict(l=max(m.l or 0, 52), r=max(m.r or 0, 18),
                                      t=max(m.t or 0, 30), b=max(m.b or 0, 42)),
                          autosize=True, width=None)
        try:
            fig.update_xaxes(automargin=True)
            fig.update_yaxes(automargin=True)
        except Exception:
            pass
        h = pio.to_html(fig, full_html=False,
                        include_plotlyjs=("inline" if primeiro else False),
                        config={"displayModeBar": False},
                        default_width="100%")
        primeiro = False
        return h

    def bloco(b, dentro_card=True):
        t = b.get("t")
        if b.get("so_pdf"):
            return ""
        if t == "hero":
            k = "".join(f'<div class="kpi"><div class="l">{x["lb"]}</div>'
                        f'<div class="v">{x["vl"]}</div>'
                        f'<div class="s">{x.get("sb","")}'
                        f'{" · " + x["badge"] if x.get("badge") else ""}</div></div>'
                        for x in b["tiles"])
            n = len(b["tiles"])
            return (f'<div class="kpis" style="grid-template-columns:repeat({n},1fr)">'
                    f'{k}</div>')
        if t == "fig":
            d = f'<div class="d">{b["desc"]}</div>' if b.get("desc") else ""
            extras = "".join(f'<div class="note {e.get("estilo","")}">{e["html"]}</div>'
                             for e in b.get("extras", []))
            return (f'<div class="card"><h3>{b.get("titulo","")}</h3>{d}'
                    f'{fig_html(b["fig"])}{extras}</div>')
        if t in ("texto", "nota"):
            corpo = b["html"]
            if not corpo.strip().startswith("<div"):
                corpo = f'<div class="note {b.get("estilo","")}">{corpo}</div>'
            tit = f'<h3>{b["titulo"]}</h3>' if b.get("titulo") else ""
            return f'<div class="card">{tit}{corpo}</div>'
        if t == "tabela":
            df = b["df"]
            cab = "".join(f"<th>{c}</th>" for c in df.columns)
            linhas = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>"
                             for r in df.itertuples(index=False))
            d = f'<div class="d">{b["desc"]}</div>' if b.get("desc") else ""
            return (f'<div class="card"><h3>{b.get("titulo","")}</h3>{d}'
                    f'<table class="tb"><thead><tr>{cab}</tr></thead>'
                    f'<tbody>{linhas}</tbody></table></div>')
        if t == "html":
            return f'<div class="card">{b["html"]}</div>'
        if t == "cards":
            return ('<div class="duo">'
                    + "".join("".join(bloco(f) for f in filhos) for filhos in b["itens"])
                    + "</div>")
        return ""

    for s in secoes:
        partes.append(f'<h2 class="sec">{s["titulo"]}</h2>')
        if s.get("sub"):
            partes.append(f'<div class="s">{s["sub"]}</div>')
        partes += [bloco(b) for b in s["blocos"]]

    logo = (f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else "")
    quando = _dt.now().strftime("%d/%m/%Y às %H:%M")
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<title>{titulo}</title><style>{CSS_HTML}</style></head><body><div class="pg">
<div class="capa">{logo}<h1>{titulo}</h1><div class="s">{subtitulo}</div></div>
{''.join(partes)}
<div class="rodape">Gerado em {quando} · Mendes RH · Aviva / Rio Quente Resorts<br>
Para salvar em PDF: Ctrl+P e escolha “Salvar como PDF”.</div>
</div></body></html>"""


# =============================================================================
# GERACAO EM PROCESSO SEPARADO
# =============================================================================
# O kaleido (motor que transforma o grafico em imagem) sobe um chromium proprio
# e nao convive bem com o loop de eventos do Streamlit no Windows - o app pode
# ficar preso sem erro. Por isso a montagem do PDF roda em um processo a parte:
# a tela serializa as secoes, chama o interpretador de novo e le o arquivo
# pronto. Se algo falhar, o erro volta em texto em vez de travar o painel.

def serializar(secoes):
    """Converte as secoes em estrutura simples (sem objetos plotly/pandas)."""
    def bloco(b):
        if b.get("so_tela") or b.get("t") in ("custom", "html"):
            return None
        novo = {k: v for k, v in b.items() if k not in ("fig", "df", "fn")}
        if b.get("t") == "fig":
            novo["fig_json"] = b["fig"].to_json()
        elif b.get("t") == "tabela":
            df = b["df"]
            novo["colunas"] = [str(c) for c in df.columns]
            novo["linhas"] = [[str(v) for v in r] for r in df.itertuples(index=False)]
        elif b.get("t") == "cards":
            novo["itens"] = [[x for x in (bloco(f) for f in filhos) if x]
                             for filhos in b["itens"]]
        return novo

    saida = []
    for s in secoes:
        blocos = [x for x in (bloco(b) for b in s["blocos"]) if x]
        if blocos:
            saida.append({"titulo": s["titulo"], "sub": s.get("sub", ""), "blocos": blocos})
    return saida


def _reidratar(secoes):
    import pandas as pd
    import plotly.io as pio

    def bloco(b):
        if b.get("t") == "fig":
            b = dict(b)
            b["fig"] = pio.from_json(b.pop("fig_json"))
        elif b.get("t") == "tabela":
            b = dict(b)
            b["df"] = pd.DataFrame(b.pop("linhas"), columns=b.pop("colunas"))
        elif b.get("t") == "cards":
            b = dict(b)
            b["itens"] = [[bloco(f) for f in filhos] for filhos in b["itens"]]
        return b
    return [{**s, "blocos": [bloco(b) for b in s["blocos"]]} for s in secoes]


def diagnostico(timeout=90):
    """Roda um teste curto de renderizacao em processo separado.

    Devolve um dicionario com as versoes instaladas e o resultado. Serve para
    descobrir rapidamente por que o PDF falha, sem esperar a geracao inteira.
    """
    import json
    import subprocess
    import sys
    from pathlib import Path as _P
    aqui = _P(__file__).resolve()
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(aqui), "--diag"],
                           cwd=str(aqui.parent), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "erro": f"o teste não respondeu em {timeout}s — "
                                     f"o kaleido está travando neste computador.",
                "travou": True}
    saida = (r.stdout or b"").decode("utf-8", "replace").strip()
    for linha in reversed(saida.splitlines()):
        if linha.startswith("{"):
            try:
                return json.loads(linha)
            except Exception:
                pass
    err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
    return {"ok": False, "erro": " | ".join(err[-4:]) if err else "sem resposta"}


def _diag():
    import json
    import importlib.metadata as md
    info = {"python": __import__("sys").version.split()[0]}
    for nome in ("plotly", "kaleido", "reportlab"):
        try:
            info[nome] = md.version(nome)
        except Exception:
            info[nome] = "não instalado"
    try:
        import plotly.graph_objects as go
        go.Figure(go.Bar(x=[1, 2], y=[2, 1])).to_image(format="png", width=300, height=200)
        info["ok"] = True
    except Exception as e:
        info["ok"] = False
        info["erro"] = " ".join(str(e).split())[:400]
    print(json.dumps(info, ensure_ascii=False))


def gerar_em_processo(secoes, titulo, subtitulo, logo_bytes=None, timeout=300):
    """Monta o PDF em um processo separado. Retorna (bytes, erro)."""
    import json
    import subprocess
    import sys
    import tempfile
    from pathlib import Path as _P

    tmp = _P(tempfile.mkdtemp(prefix="relatorio_"))
    entrada, saida, logo = tmp / "in.json", tmp / "out.pdf", tmp / "logo.png"
    if logo_bytes:
        logo.write_bytes(logo_bytes)
    entrada.write_text(json.dumps({
        "secoes": serializar(secoes), "titulo": titulo, "subtitulo": subtitulo,
        "logo": str(logo) if logo_bytes else None, "saida": str(saida)},
        ensure_ascii=False), encoding="utf-8")

    aqui = str(_P(__file__).resolve().parent)
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(_P(__file__).resolve()), str(entrada)],
            cwd=aqui, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, (f"o processo de geração não respondeu em {timeout // 60} minutos. "
                      f"Use o formato HTML (Ctrl+P salva em PDF) e rode o diagnóstico "
                      f"para ver o que está travando.")
    if r.returncode != 0 or not saida.exists():
        err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
        detalhe = " | ".join(err[-4:]) if err else "erro desconhecido"
        return None, detalhe
    return saida.read_bytes(), None


def _cli():
    import json
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--diag":
        _diag()
        return
    cfg = json.loads(open(sys.argv[1], encoding="utf-8").read())
    logo = open(cfg["logo"], "rb").read() if cfg.get("logo") else None
    pdf = gerar_pdf(_reidratar(cfg["secoes"]), cfg["titulo"], cfg["subtitulo"], logo)
    open(cfg["saida"], "wb").write(pdf)


if __name__ == "__main__":
    _cli()
