# -*- coding: utf-8 -*-
"""
================================================================================
 LEITURA E CONSOLIDACAO DAS PESQUISAS DO TEMPORARIO
 Mendes RH x Aviva / Rio Quente Resorts
================================================================================
Duas rodadas, dois arquivos, dois publicos parcialmente sobrepostos.

RODADA 1 - EXPERIENCIA DA TEMPORADA
  dados/pesquisa/RESPOSTAS_PESQUISA.xlsx
  Duas abas ("Form Responses 1" = questionario de quem cumpriu a temporada,
  "Form Responses 2" = questionario de saida). Disparo para 178 pessoas.

RODADA 2 - SALARIO, CONDICOES E EFETIVACAO
  dados/pesquisa/RESPOSTAS_PESQUISA_2.xlsx
  Aba unica. Disparo so para quem respondeu a rodada 1.

REGRA DE CLASSIFICACAO (rodada 1)
---------------------------------
O grupo NAO vem da lista de disparo, e sim da declaracao do proprio
respondente: quem recebeu o questionario longo mas informou na pergunta de
triagem que saiu antes do fim conta no grupo "Saiu antes".

Perguntas equivalentes nos dois questionarios da rodada 1 sao unificadas em
colunas canonicas (funcao, local, faltas, causa, nps, voltaria). O que existe
em apenas um dos formularios permanece separado.
================================================================================
"""
from pathlib import Path

import numpy as np
import pandas as pd

_DIR = Path(__file__).resolve().parent / "dados" / "pesquisa"

ARQUIVO = _DIR / "RESPOSTAS_PESQUISA.xlsx"
ARQUIVO_R2 = _DIR / "RESPOSTAS_PESQUISA_2.xlsx"

ABA_CUMPRIU = "Form Responses 1"
ABA_SAIU = "Form Responses 2"
ABA_R2 = "Form Responses 1"

CONVITES = {"Cumpriu a temporada": 150, "Saiu antes do fim": 28}

G_CUMPRIU = "Cumpriu a temporada"
G_SAIU = "Saiu antes do fim"

MIN_RECORTE = 5          # abaixo disso o recorte identifica quem respondeu

# --------------------------------------------------------------- rodada 1
Q_TRIAGEM = "Como foi o fim do seu contrato na temporada de julho?"
Q_NPS = "De 0 a 10, o quanto você indicaria a Mendes RH para um amigo trabalhar?"

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

MAPA_VOLTARIA = {"Com certeza": "Sim", "Sim": "Sim", "Talvez": "Talvez", "Não": "Não"}

SEM_FALTA = {"Não faltei nenhum dia", "Prefiro não dizer", "Não faltei"}

# --------------------------------------------------------------- rodada 2
R2 = {
    "funcao": "Em qual função você trabalhou na temporada de julho?",
    "ficou": "Você ficou até o fim da temporada?",
    "nota_salario": "De 0 a 10, que nota você dá para o valor do salario que "
                    "recebeu na temporada?",
    "expectativa": "O valor recebido atendeu o que você esperava quando aceitou a vaga?",
    "mercado": "Comparando com outros trabalhos temporários que você conhece na "
               "região, o pagamento da Mendes RH é:",
    "alavanca_pag": "O que mais faria diferença para você no pagamento?",
    "nota_condicoes": "De 0 a 10, que nota você dá para as condições de trabalho "
                      "no dia a dia?",
    "melhorar": "O que mais precisa melhorar?",
    "respeito": "Você se sentiu respeitado(a) no ambiente de trabalho?",
    "relato": "Se quiser, conte uma situação em que você não se sentiu respeitado(a).",
    "clt": "Você teria interesse em ser efetivado(a) como CLT na Aviva / Rio Quente?",
    "area_sim": "Em qual área você gostaria de trabalhar como efetivo?",
    "contra_talvez": "O que pesa contra?",
    "area_talvez": "Em qual área você gostaria de trabalhar, se as condições fossem boas?",
    "contra_nao": "O que pesa contra? ",      # o espaco final e proposital
    "comentario": "Quer deixar mais algum comentário, sugestão ou elogio?",
}

# opcoes fechadas na ordem em que devem aparecer nos graficos
OPC_MELHORAR = [
    "Transporte", "Alimentação e refeitório", "Escala e folgas",
    "Local para descanso e cadeiras", "Tratamento pelos funcionários efetivos",
    "Tratamento pela segurança", "Uniforme e equipamentos",
    "Banheiros e vestiários", "Nada, estava bom",
]
OPC_ALAVANCA = [
    "Valor maior da diária", "Pagamento semanal", "Bônus por não faltar",
    "Bônus por ficar até o fim da temporada",
    "Ajuda de custo para transporte ou alimentação",
]
OPC_CONTRA = [
    "Salário", "Distância ou transporte", "Escala e horários",
    "Já tenho outro trabalho ou estudo", "Não gostei do ambiente",
    "Prefiro trabalho temporário mesmo",
]
ORDEM_RESPEITO = ["Sempre", "Na maior parte do tempo", "Poucas vezes", "Nunca"]

# O campo de relato e opcional e muita gente preenche para dizer que nao tem
# nada a relatar. Contar por tamanho de texto infla o numero. Estas expressoes
# marcam a resposta como "sem ocorrencia"; o resto conta como situacao descrita.
SEM_OCORRENCIA = (
    "nada", "nao tenho", "não tenho", "nao teve", "não teve",
    "nao houve", "não houve", "fui respeitad", "sempre fui respeitad",
    "nenhuma", "nenhum", "sem ocorrencia", "sem ocorrência", "n/a", "na",
)


def descreveu_situacao(texto):
    """True quando o relato aberto descreve de fato alguma situacao."""
    t = str(texto or "").strip().lower()
    if len(t) < 4:
        return False
    for p in SEM_OCORRENCIA:
        if t.startswith(p):
            return False
    return True
ORDEM_EXPECT = ["Foi mais do que eu esperava", "Foi o que eu esperava",
                "Foi menos do que eu esperava"]
ORDEM_MERCADO = ["Melhor", "Parecido", "Pior", "Não sei comparar"]
ORDEM_CLT = ["Sim, com certeza", "Talvez, depende das condições", "Não"]


# ------------------------------------------------------------------ leitura
def _texto(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    return str(v).strip()


def _multi(v, validas=None):
    """Quebra resposta de multipla escolha do Forms em lista.

    O Forms junta as opcoes com virgula, e algumas opcoes do questionario tem
    virgula no proprio texto ("Nada, estava bom"). Quando a lista de opcoes
    validas e informada, elas sao extraidas antes da quebra por virgula, o que
    evita partir a opcao no meio.
    """
    t = _texto(v)
    if not t:
        return []
    if validas:
        achados, resto = [], t
        for opc in sorted(validas, key=len, reverse=True):
            if opc in resto:
                achados.append(opc)
                resto = resto.replace(opc, "", 1)
        extras = [x.strip() for x in resto.split(",") if x.strip()]
        return achados + extras
    return [x.strip() for x in t.split(",") if x.strip()]


def carregar_bruto(caminho=None):
    caminho = Path(caminho) if caminho else ARQUIVO
    if not caminho.exists():
        return None, None
    c = pd.read_excel(caminho, sheet_name=ABA_CUMPRIU)
    s = pd.read_excel(caminho, sheet_name=ABA_SAIU)
    c.columns = [str(x).strip() for x in c.columns]
    s.columns = [str(x).strip() for x in s.columns]
    return c.dropna(how="all"), s.dropna(how="all")


def consolidar(caminho=None):
    """Rodada 1. Devolve (base, form_cumpriu, form_saiu)."""
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

    return pd.DataFrame(linhas), c, s


def _linha(r, grupo, origem, idx_equiv):
    d = {"grupo": grupo, "origem": origem}
    for canon, col1, col2 in EQUIV:
        d[canon] = _texto(r.get(col2 if idx_equiv else col1))
    d["causa_falta_lista"] = _multi(r.get(EQUIV[5][2] if idx_equiv else EQUIV[5][1]))
    d["voltaria"] = MAPA_VOLTARIA.get(d["voltaria"], d["voltaria"] or None)
    try:
        d["nps"] = float(r.get(Q_NPS))
    except (TypeError, ValueError):
        d["nps"] = np.nan
    d["faltou"] = d["faltas"] not in SEM_FALTA and d["faltas"] != ""
    d["declarou_falta"] = d["faltas"] not in ("", "Prefiro não dizer")
    return d


# --------------------------------------------------------- rodada 2
def carregar_r2(caminho=None):
    """Rodada 2. Devolve um DataFrame ja com colunas canonicas, ou None."""
    caminho = Path(caminho) if caminho else ARQUIVO_R2
    if not caminho.exists():
        return None
    d = pd.read_excel(caminho, sheet_name=ABA_R2)
    d.columns = [str(x).strip() if str(x).strip() != R2["contra_nao"].strip()
                 else str(x) for x in d.columns]
    d = d.dropna(how="all")

    out = pd.DataFrame(index=d.index)
    col = {k: v for k, v in R2.items()}

    def _get(nome):
        c = col[nome]
        if c in d.columns:
            return d[c]
        # tolera diferenca de espaco em branco no fim do cabecalho
        alvo = c.strip()
        for x in d.columns:
            if str(x).strip() == alvo:
                return d[x]
        return pd.Series([np.nan] * len(d), index=d.index)

    out["funcao"] = _get("funcao").map(_texto)
    out["ficou"] = _get("ficou").map(_texto)
    out["grupo"] = np.where(out.ficou.str.startswith("Sim"), G_CUMPRIU, G_SAIU)
    out["nota_salario"] = pd.to_numeric(_get("nota_salario"), errors="coerce")
    out["nota_condicoes"] = pd.to_numeric(_get("nota_condicoes"), errors="coerce")
    out["expectativa"] = _get("expectativa").map(_texto)
    out["mercado"] = _get("mercado").map(_texto)
    out["respeito"] = _get("respeito").map(_texto)
    out["clt"] = _get("clt").map(_texto)
    out["relato"] = _get("relato").map(_texto)
    out["comentario"] = _get("comentario").map(_texto)

    out["alavanca_lista"] = [_multi(v, OPC_ALAVANCA) for v in _get("alavanca_pag")]
    out["melhorar_lista"] = [_multi(v, OPC_MELHORAR) for v in _get("melhorar")]

    # "o que pesa contra" existe em duas colunas (caminho Talvez e caminho Nao)
    ct = [_multi(v, OPC_CONTRA) for v in _get("contra_talvez")]
    cn = [_multi(v, OPC_CONTRA) for v in _get("contra_nao")]
    out["contra_lista"] = [a + b for a, b in zip(ct, cn)]

    area = []
    for a, b in zip(_get("area_sim"), _get("area_talvez")):
        area.append(_texto(a) or _texto(b))
    out["area"] = area

    # respeito: "Sempre" vs qualquer coisa abaixo disso
    out["respeito_pleno"] = out.respeito.eq("Sempre")
    out["respeito_falhou"] = out.respeito.isin(["Poucas vezes", "Nunca"])
    return out.reset_index(drop=True)


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


def contagem_multipla(listas, universo=None):
    """Frequencia de cada opcao sobre o total de respondentes do recorte."""
    listas = list(listas)
    total = sum(1 for l in listas if l)
    if not total:
        return pd.Series(dtype=float), 0
    c = {}
    for l in listas:
        for x in l:
            c[x] = c.get(x, 0) + 1
    return pd.Series(c).sort_values(ascending=False), total


def taxa(sub, cond):
    n = len(sub)
    return (round(sum(1 for _, r in sub.iterrows() if cond(r)) / n * 100), n) if n else (None, 0)


def _pct(parte, total):
    return round(parte / total * 100, 1) if total else None


def resumo(base):
    """Numeros de capa da rodada 1, ja reclassificados."""
    cum = base[base.grupo == G_CUMPRIU]
    sai = base[base.grupo == G_SAIU]
    conv = sum(CONVITES.values())
    volt = base.voltaria.dropna()
    n_form_longo = int((base.origem == "cumpriu").sum())
    n_form_saida = int((base.origem == "saiu").sum())
    return {
        "n_total": len(base), "n_cumpriu": len(cum), "n_saiu": len(sai),
        "convites": conv,
        "taxa_total": _pct(len(base), conv),
        "taxa_cumpriu": _pct(n_form_longo, CONVITES[G_CUMPRIU]),
        "taxa_saiu": _pct(n_form_saida, CONVITES[G_SAIU]),
        "enps_total": enps(base.nps), "enps_cumpriu": enps(cum.nps),
        "enps_saiu": enps(sai.nps),
        "faltou_cumpriu": _pct(cum.faltou.sum(), len(cum)),
        "faltou_saiu": _pct(sai.faltou.sum(), len(sai)),
        "voltaria_sim": _pct((volt == "Sim").sum(), len(volt)),
        "voltaria_sim_talvez": _pct(volt.isin(["Sim", "Talvez"]).sum(), len(volt)),
        "reclassificados": int((base.origem.eq("cumpriu") & base.grupo.eq(G_SAIU)).sum()),
    }


def resumo_r2(d2, n_convites=None):
    """Numeros de capa da rodada 2.

    n_convites: quantas pessoas receberam o disparo. Por padrao usa o total de
    respondentes da rodada 1, que foi o publico escolhido para o disparo.
    """
    if d2 is None or d2.empty:
        return None
    sal = d2.nota_salario.dropna()
    cond = d2.nota_condicoes.dropna()
    n = len(d2)
    clt_sim = int(d2.clt.eq("Sim, com certeza").sum())
    clt_talvez = int(d2.clt.eq("Talvez, depende das condições").sum())
    return {
        "n": n,
        "convites": n_convites,
        "taxa": _pct(n, n_convites) if n_convites else None,
        "salario": enps(sal),
        "condicoes": enps(cond),
        "media_salario": round(float(sal.mean()), 2) if len(sal) else None,
        "media_condicoes": round(float(cond.mean()), 2) if len(cond) else None,
        "expect_atendeu": _pct(d2.expectativa.isin(
            ["Foi o que eu esperava", "Foi mais do que eu esperava"]).sum(), n),
        "expect_abaixo": _pct(d2.expectativa.eq("Foi menos do que eu esperava").sum(), n),
        "mercado_melhor": _pct(d2.mercado.eq("Melhor").sum(), n),
        "mercado_pior": _pct(d2.mercado.eq("Pior").sum(), n),
        "respeito_sempre": _pct(d2.respeito_pleno.sum(), n),
        "respeito_falhou": _pct(d2.respeito_falhou.sum(), n),
        "respeito_parcial": _pct(d2.respeito.eq("Na maior parte do tempo").sum(), n),
        "clt_sim": _pct(clt_sim, n),
        "clt_sim_talvez": _pct(clt_sim + clt_talvez, n),
        "clt_nao": _pct(d2.clt.eq("Não").sum(), n),
        "n_escreveram": int((d2.relato.str.strip().str.len() > 0).sum()),
        "n_relatos": int(d2.relato.map(descreveu_situacao).sum()),
        "n_comentarios": int((d2.comentario.str.len() > 3).sum()),
    }


if __name__ == "__main__":
    import json
    base, c, s = consolidar()
    if base is None:
        raise SystemExit("Arquivo não encontrado: %s" % ARQUIVO)
    print("=== RODADA 1 ===")
    print(json.dumps(resumo(base), ensure_ascii=False, indent=2, default=str))
    d2 = carregar_r2()
    if d2 is not None:
        print("=== RODADA 2 ===")
        print(json.dumps(resumo_r2(d2, len(base)), ensure_ascii=False,
                         indent=2, default=str))
