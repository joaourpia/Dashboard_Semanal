# -*- coding: utf-8 -*-
"""
================================================================================
 LEITURA E CONSOLIDACAO DA PESQUISA DE EXPERIENCIA DO TEMPORARIO
 Mendes RH x Aviva / Rio Quente Resorts
================================================================================
Le dados/pesquisa/RESPOSTAS_PESQUISA.xlsx (exportacao da planilha do Google
Forms, com as duas abas de respostas) e devolve um quadro unico ja tratado.

REGRA DE CLASSIFICACAO
----------------------
O grupo NAO vem da lista de disparo, e sim da declaracao do proprio
respondente. Sete pessoas receberam o questionario de quem cumpriu a temporada
e informaram, na pergunta de triagem, que sairam antes do fim. Elas contam no
grupo "Saiu antes". Resultado: 97 cumpriram e 17 sairam antes.

Perguntas equivalentes nos dois questionarios sao unificadas em colunas
canonicas (funcao, local, faltas, causa, enps, voltaria). O que existe em
apenas um dos formularios permanece separado.
================================================================================
"""
from pathlib import Path

import numpy as np
import pandas as pd

ARQUIVO = Path(__file__).resolve().parent / "dados" / "pesquisa" / "RESPOSTAS_PESQUISA.xlsx"

ABA_CUMPRIU = "Form Responses 1"
ABA_SAIU = "Form Responses 2"

CONVITES = {"Cumpriu a temporada": 150, "Saiu antes do fim": 28}

G_CUMPRIU = "Cumpriu a temporada"
G_SAIU = "Saiu antes do fim"

# --------------------------------------------------------------- colunas
Q_TRIAGEM = "Como foi o fim do seu contrato na temporada de julho?"
Q_NPS = "De 0 a 10, o quanto você indicaria a Mendes RH para um amigo trabalhar?"

# equivalencias entre os dois questionarios: (canonica, coluna aba1, coluna aba2)
EQUIV = [
    ("funcao", "Em qual função você trabalhou nesta temporada?",
     "Em qual função você trabalhou?"),
    ("local", "Onde você trabalhou a maior parte do tempo?",
     "Onde você trabalhou a maior parte do tempo?"),
    ("moradia", "Onde você mora?", "Onde você mora?"),
    ("transporte", "Como você ia e voltava do trabalho?",
     "Como você ia e voltava do trabalho?"),
    ("faltas", "Durante a temporada, você chegou a faltar algum dia?",
     "Antes de sair, você chegou a faltar?"),
    ("causa_falta", "O que mais levou você ou seus colegas a faltar?",
     "O que fez você faltar?"),
    ("pos_falta", "Depois da sua primeira falta, alguém da Mendes RH ou da liderança "
                  "conversou com você?",
     "Depois da sua primeira falta, alguém da Mendes RH ou da liderança conversou com você?"),
    ("voltaria", "Você voltaria a trabalhar na próxima temporada?",
     "Você aceitaria trabalhar de novo com a Mendes RH?"),
]

# "Com certeza" (quem ficou) e "Sim" (quem saiu) medem a mesma disposicao
MAPA_VOLTARIA = {"Com certeza": "Sim", "Sim": "Sim", "Talvez": "Talvez", "Não": "Não"}

SEM_FALTA = {"Não faltei nenhum dia", "Prefiro não dizer", "Não faltei"}
MIN_RECORTE = 5          # abaixo disso o recorte identifica quem respondeu


# ------------------------------------------------------------------ leitura
def _texto(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    return str(v).strip()


def _multi(v):
    """Quebra resposta de multipla escolha do Forms em lista."""
    t = _texto(v)
    return [x.strip() for x in t.split(",") if x.strip()] if t else []


def carregar_bruto(caminho=None):
    caminho = Path(caminho) if caminho else ARQUIVO
    if not caminho.exists():
        return None, None
    c = pd.read_excel(caminho, sheet_name=ABA_CUMPRIU)
    s = pd.read_excel(caminho, sheet_name=ABA_SAIU)
    c.columns = [str(x).strip() for x in c.columns]
    s.columns = [str(x).strip() for x in s.columns]
    c = c.dropna(how="all")
    s = s.dropna(how="all")
    return c, s


def consolidar(caminho=None):
    """Devolve (base, form_cumpriu, form_saiu).

    base ......... um registro por respondente, com as colunas canonicas e o
                   grupo ja reclassificado.
    form_cumpriu . respostas do questionario longo (inclui as 7 reclassificadas,
                   porque as demais perguntas continuam validas).
    form_saiu .... respostas do questionario de saida.
    """
    c, s = carregar_bruto(caminho)
    if c is None:
        return None, None, None

    linhas = []
    for _, r in c.iterrows():
        fim = _texto(r.get(Q_TRIAGEM))
        grupo = G_CUMPRIU if fim.startswith("Fiquei até o fim") else G_SAIU
        linhas.append(_linha(r, grupo, "cumpriu", 0))
    for _, r in s.iterrows():
        linhas.append(_linha(r, G_SAIU, "saiu", 1))

    base = pd.DataFrame(linhas)
    return base, c, s


def _linha(r, grupo, origem, idx_equiv):
    d = {"grupo": grupo, "origem": origem}
    for canon, col1, col2 in EQUIV:
        col = col2 if idx_equiv else col1
        v = r.get(col)
        d[canon] = _texto(v)
    d["causa_falta_lista"] = _multi(r.get(
        EQUIV[5][2] if idx_equiv else EQUIV[5][1]))
    d["voltaria"] = MAPA_VOLTARIA.get(d["voltaria"], d["voltaria"] or None)
    try:
        d["nps"] = float(r.get(Q_NPS))
    except (TypeError, ValueError):
        d["nps"] = np.nan
    d["faltou"] = d["faltas"] not in SEM_FALTA and d["faltas"] != ""
    d["declarou_falta"] = d["faltas"] not in ("", "Prefiro não dizer")
    return d


# --------------------------------------------------------------- indicadores
def enps(serie):
    """Indice de recomendacao (metodo NPS aplicado a empregados).

    Quem da 9 ou 10 recomenda; 7 e 8 sao indiferentes; 0 a 6 nao recomenda.
    O indice e a diferenca entre o percentual do primeiro grupo e o do ultimo,
    de -100 a +100. Nos textos do painel e do relatorio o indicador aparece
    como "indice de recomendacao" - eNPS e so o nome tecnico.
    """
    v = pd.Series(serie).dropna().astype(float)
    if len(v) == 0:
        return None
    prom = int((v >= 9).sum())
    detr = int((v <= 6).sum())
    return {"enps": round(prom / len(v) * 100 - detr / len(v) * 100, 1),
            "promotores": prom, "neutros": len(v) - prom - detr,
            "detratores": detr, "n": len(v), "media": round(float(v.mean()), 2)}


def contagem(serie, ordem_desc=True):
    c = pd.Series([x for x in serie if str(x).strip()]).value_counts()
    return c if ordem_desc else c.sort_index()


def contagem_multipla(listas, universo):
    """Frequencia de cada opcao sobre o total de respondentes do recorte."""
    total = sum(1 for l in listas if l)
    if not total:
        return pd.Series(dtype=float), 0
    c = {}
    for l in listas:
        for x in l:
            c[x] = c.get(x, 0) + 1
    s = pd.Series(c).sort_values(ascending=False)
    return s, total


def taxa(sub, cond):
    n = len(sub)
    return (round(sum(1 for _, r in sub.iterrows() if cond(r)) / n * 100), n) if n else (None, 0)


def resumo(base):
    """Números de capa, já reclassificados."""
    cum = base[base.grupo == G_CUMPRIU]
    sai = base[base.grupo == G_SAIU]
    conv = sum(CONVITES.values())
    volt = base.voltaria.dropna()
    return {
        "n_total": len(base), "n_cumpriu": len(cum), "n_saiu": len(sai),
        "convites": conv,
        "taxa_total": round(len(base) / conv * 100, 1),
        "taxa_cumpriu": round(104 / CONVITES[G_CUMPRIU] * 100, 1),
        "taxa_saiu": round(10 / CONVITES[G_SAIU] * 100, 1),
        "enps_total": enps(base.nps), "enps_cumpriu": enps(cum.nps),
        "enps_saiu": enps(sai.nps),
        "faltou_cumpriu": round(cum.faltou.sum() / len(cum) * 100, 1) if len(cum) else None,
        "faltou_saiu": round(sai.faltou.sum() / len(sai) * 100, 1) if len(sai) else None,
        "voltaria_sim": round((volt == "Sim").sum() / len(volt) * 100, 1),
        "voltaria_sim_talvez": round(volt.isin(["Sim", "Talvez"]).sum() / len(volt) * 100, 1),
        "reclassificados": int((base.origem.eq("cumpriu") & base.grupo.eq(G_SAIU)).sum()),
    }


if __name__ == "__main__":
    base, c, s = consolidar()
    if base is None:
        raise SystemExit("Arquivo não encontrado: %s" % ARQUIVO)
    import json
    print(json.dumps(resumo(base), ensure_ascii=False, indent=2))
