# -*- coding: utf-8 -*-
"""
Dump de TODOS os numeros do relatorio unico para _estatisticas.json.

O gerador do documento (gerar_relatorio_unico.js) le esse JSON e nao calcula
nada por conta propria. Assim o relatorio, o painel e o PDF saem sempre dos
mesmos numeros: se a base mudar, basta rodar este script de novo.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pesquisa_dados as p   # noqa: E402
from pesquisa_dados import (G_CUMPRIU, G_SAIU, MIN_RECORTE,   # noqa: E402
                            OPC_ALAVANCA, OPC_CONTRA, OPC_MELHORAR,
                            ORDEM_CLT, ORDEM_EXPECT, ORDEM_MERCADO,
                            ORDEM_RESPEITO, contagem, contagem_multipla,
                            descreveu_situacao, enps)

PS = "Em algum momento você pensou em sair antes do fim?"
VOZ = "Você se sentiu à vontade para falar quando algo estava errado?"
PGJ = "Pensando no esforço do dia a dia, o pagamento foi justo?"
PGP = "Você recebeu tudo certo e no prazo (salário, vale, hora extra)?"
REC = "Como foi sua recepção no primeiro dia?"
ALIM = "Como foi a alimentação durante o trabalho?"
TRAT = "Como os colegas efetivos tratavam os temporários?"
CLARO = "Quando você começou, ficou claro o que era esperado de você?"
KIT = ("Você recebeu no primeiro dia tudo o que precisava para trabalhar "
       "(uniforme, EPI, crachá, materiais)?")
ESCALA = "A escala que você cumpriu foi a que combinaram na contratação?"
EFET = "Você acredita que teve chance real de efetivação?"
VAGA = "Se abrisse uma vaga fixa aqui hoje, você aceitaria?"
EXPER = ("Como foi sua experiência com a equipe da Mendes RH, da entrevista "
         "até o fim do contrato?")
SEGUROU = "O que mais te segurou até o fim do contrato?"
PESOU = "Pensando no seu dia de trabalho, o que mais pesou?"
ALAV1 = "O que teria ajudado a reduzir as faltas?"
MUDAR = "Se você pudesse mudar UMA coisa na temporada, o que seria?"
ELOGIO = "Quer deixar algum elogio ou reclamação? (opcional)"

# questionario de saida
MOTIVO = "Qual foi o motivo REAL da sua saída?"
DECISAO = "Sua saída foi decisão sua ou da empresa?"
QUANDO = "Em que momento você decidiu que ia sair?"
TEMPO = "Quanto tempo você ficou antes de sair?"
AVISOU = "Você avisou alguém antes de sair?"
FICARIA = "O que teria feito você ficar até o fim do contrato?"


def pct(parte, total, casas=1):
    return round(parte / total * 100, casas) if total else None


def dist(serie, ordem=None, total=None):
    """Distribuicao [{rotulo, n, pct}] preservando a ordem informada."""
    s = pd.Series([str(x).strip() for x in serie if str(x).strip()])
    tot = total or len(s)
    c = s.value_counts()
    chaves = [o for o in ordem if o in c.index] if ordem else list(c.index)
    if ordem:
        chaves += [k for k in c.index if k not in ordem]
    return [{"rotulo": k, "n": int(c[k]), "pct": pct(int(c[k]), tot)} for k in chaves]


def dist_multipla(listas, ordem=None, limite=None):
    s, tot = contagem_multipla(listas)
    if not tot:
        return [], 0
    itens = [(k, int(v)) for k, v in s.items()]
    if ordem:
        itens = [(k, v) for k, v in itens if k in ordem]
    if limite:
        itens = itens[:limite]
    return [{"rotulo": k, "n": v, "pct": pct(v, tot)} for k, v in itens], tot


def preparar_r1():
    base, c, s = p.consolidar()
    base = base.copy()
    for col in (PS, VOZ, PGJ, PGP, REC, ALIM, TRAT, CLARO, KIT, ESCALA, EFET,
                VAGA, EXPER, SEGUROU, PESOU, ALAV1, MUDAR, ELOGIO):
        vals = list(c[col]) if col in c else []
        serie = pd.Series([None] * len(base), index=base.index, dtype=object)
        for i, v in zip(base.index[base.origem == "cumpriu"], vals):
            serie.loc[i] = str(v).strip() if pd.notna(v) else None
        base[col] = serie
    return base, c, s


def taxa_falta(base, col, valor):
    g = base[base[col] == valor] if col in base else base.iloc[0:0]
    if not len(g):
        return None
    return {"n": len(g), "faltou": pct(int(g.faltou.sum()), len(g), 0)}


def main():
    base, c, s = preparar_r1()
    d2 = p.carregar_r2()
    rs = p.resumo(base)
    r2 = p.resumo_r2(d2, len(base))
    out = {}

    # ------------------------------------------------------------ metodo
    out["metodo"] = {
        "r1_convites": rs["convites"],
        "r1_n": rs["n_total"],
        "r1_taxa": rs["taxa_total"],
        "r1_cumpriu": rs["n_cumpriu"],
        "r1_saiu": rs["n_saiu"],
        "r1_taxa_cumpriu": rs["taxa_cumpriu"],
        "r1_taxa_saiu": rs["taxa_saiu"],
        "r1_reclassificados": rs["reclassificados"],
        "r1_form_longo": int((base.origem == "cumpriu").sum()),
        "r1_form_saida": int((base.origem == "saiu").sum()),
        "r2_convites": r2["convites"],
        "r2_n": r2["n"],
        "r2_taxa": r2["taxa"],
        "r2_cumpriu_pct": pct(int(d2.grupo.eq(G_CUMPRIU).sum()), len(d2)),
        "total_respostas": rs["n_total"] + r2["n"],
    }

    # ------------------------------------------------------------ perfil
    out["perfil"] = {
        "funcao": dist(base.funcao, total=len(base))[:12],
        "local": dist(base.local, total=len(base))[:10],
        "moradia": dist(base.moradia, total=len(base)),
        "transporte": dist(base.transporte, total=len(base)),
    }

    # ------------------------------------------------- vinculo (rodada 1)
    out["vinculo"] = {
        "total": rs["enps_total"], "cumpriu": rs["enps_cumpriu"],
        "saiu": rs["enps_saiu"],
        "voltaria": dist(base.voltaria.dropna()),
        "voltaria_sim": rs["voltaria_sim"],
        "voltaria_sim_talvez": rs["voltaria_sim_talvez"],
        "experiencia": dist(base[EXPER].dropna()),
        "chance_efetivacao": dist(base[EFET].dropna()),
        "vaga_fixa": dist(base[VAGA].dropna()),
    }
    por_funcao = []
    for f, g in base.groupby("funcao"):
        if len(g) < MIN_RECORTE or not f:
            continue
        e = enps(g.nps)
        ps = g[PS].dropna()
        volt = g.voltaria.dropna()
        por_funcao.append({
            "funcao": f, "n": len(g),
            "indice": e["enps"] if e else None,
            "media": e["media"] if e else None,
            "faltou": pct(int(g.faltou.sum()), len(g), 0),
            "pensou_sair": (pct(int((ps != "Não, nunca pensei").sum()), len(ps), 0)
                            if len(ps) else None),
            "voltaria": (pct(int((volt == "Sim").sum()), len(volt), 0)
                         if len(volt) else None),
        })
    out["vinculo"]["por_funcao"] = sorted(por_funcao, key=lambda x: -x["n"])

    # ------------------------------------------------ absenteismo (rodada 1)
    faltou = base[base.faltou]
    causas, tot_c = dist_multipla(faltou.causa_falta_lista, limite=9)
    cit = sum(x["n"] for x in causas)
    out["absenteismo"] = {
        "faltou_cumpriu": rs["faltou_cumpriu"],
        "faltou_saiu": rs["faltou_saiu"],
        "n_faltou": tot_c,
        "causas": causas,
        "citacoes": cit,
        "top3_share": pct(sum(x["n"] for x in causas[:3]), cit, 0),
        "desengajamento": pct(sum(
            x["n"] for x in causas
            if x["rotulo"] in ("Desânimo com o trabalho",
                               "Outro trabalho ou bico no mesmo dia",
                               "Trabalho pesado demais para o valor pago")), cit),
        "faixas": dist(base.faltas.dropna(),
                       ordem=["Não faltei nenhum dia", "Faltei 1 dia",
                              "Faltei 2 ou 3 dias", "Faltei mais de 3 dias",
                              "Prefiro não dizer"]),
    }
    out["absenteismo"]["alavancas"] = dist_multipla(
        [p._multi(v) for v in base[ALAV1].dropna()])[0][:8]
    out["absenteismo"]["pesou"] = dist_multipla(
        [p._multi(v) for v in base[PESOU].dropna()])[0][:8]

    # -------------------------------------------------- preditores (rodada 1)
    out["preditores"] = {
        "voz": [dict(nivel=v, **(taxa_falta(base, VOZ, v) or {}))
                for v in ("Sim", "Mais ou menos", "Não")
                if taxa_falta(base, VOZ, v)],
        "pagamento": [dict(nivel=v, **(taxa_falta(base, PGP, v) or {}))
                      for v in ("Sim, sempre", "Teve atraso ou erro uma vez",
                                "Teve problema mais de uma vez")
                      if taxa_falta(base, PGP, v)],
        "voz_dist": dist(base[VOZ].dropna(), ordem=["Sim", "Mais ou menos", "Não"]),
        "pgp_dist": dist(base[PGP].dropna()),
        "pgj_dist": dist(base[PGJ].dropna()),
        "claro": dist(base[CLARO].dropna()),
        "kit": dist(base[KIT].dropna()),
        "escala": dist(base[ESCALA].dropna()),
    }
    # escalas de 1 a 5 do questionario longo
    def escala5(col, rotulo):
        v = pd.to_numeric(base[col], errors="coerce").dropna()
        if not len(v):
            return None
        return {"pergunta": rotulo, "n": len(v),
                "media": round(float(v.mean()), 2),
                "nota5": pct(int((v == 5).sum()), len(v)),
                "nota12": pct(int((v <= 2).sum()), len(v)),
                "n_nota1": int((v == 1).sum())}

    out["escalas"] = [x for x in (
        escala5(REC, "Recepção no primeiro dia"),
        escala5(ALIM, "Alimentação durante o trabalho"),
        escala5(TRAT, "Tratamento dos efetivos aos temporários"),
    ) if x]

    # intencao de sair por nivel de voz
    isair = []
    for v in ("Sim", "Mais ou menos", "Não"):
        g = base[base[VOZ] == v]
        ps = g[PS].dropna()
        if len(g) >= MIN_RECORTE and len(ps):
            isair.append({"nivel": v, "n": len(ps),
                          "pensou": pct(int((ps != "Não, nunca pensei").sum()), len(ps), 0)})
    out["preditores"]["voz_intencao"] = isair

    # ------------------------------------------------------ saida (rodada 1)
    saiu_todos = base[base.grupo == G_SAIU]
    out["saida"] = {
        "n": len(saiu_todos),
        "n_form_saida": len(s),
        "pensou_sair": dist(base[PS].dropna()),
        "segurou": dist_multipla([p._multi(v) for v in base[SEGUROU].dropna()])[0][:8],
    }
    for chave, col, ordem in [
            ("decisao", DECISAO, None), ("quando", QUANDO, None),
            ("tempo", TEMPO, ["Menos de 7 dias", "De 7 a 15 dias",
                              "De 15 a 30 dias", "Mais de 30 dias"]),
            ("avisou", AVISOU, None), ("motivo", MOTIVO, None)]:
        out["saida"][chave] = dist(s[col].dropna(), ordem=ordem) if col in s else []
    out["saida"]["ficaria"] = dist_multipla(
        [p._multi(v) for v in s[FICARIA].dropna()])[0][:8] if FICARIA in s else []
    if QUANDO in s:
        cedo = int(s[QUANDO].isin(["Já nos primeiros dias", "Na primeira semana"]).sum())
        out["saida"]["decidiu_cedo"] = cedo

    # --------------------------------------------------- salario (rodada 2)
    out["salario"] = {
        "media": r2["media_salario"], "indice": r2["salario"],
        "distribuicao": [{"nota": int(k), "n": int(v)} for k, v in
                         d2.nota_salario.dropna().astype(int)
                         .value_counts().reindex(range(11), fill_value=0).items()],
        "expectativa": dist(d2.expectativa, ordem=ORDEM_EXPECT, total=len(d2)),
        "mercado": dist(d2.mercado, ordem=ORDEM_MERCADO, total=len(d2)),
        "expect_atendeu": r2["expect_atendeu"],
        "expect_abaixo": r2["expect_abaixo"],
        "mercado_melhor": r2["mercado_melhor"],
        "mercado_pior": r2["mercado_pior"],
    }
    alav, tot_a = dist_multipla(d2.alavanca_lista, ordem=OPC_ALAVANCA)
    out["salario"]["alavancas"] = alav
    out["salario"]["alavancas_base"] = tot_a
    baixa = d2[d2.nota_salario <= 6]
    out["salario"]["insatisfeitos"] = {
        "n": len(baixa),
        "alavancas": dist_multipla(baixa.alavanca_lista, ordem=OPC_ALAVANCA)[0],
    }

    # ------------------------------------------------- condicoes (rodada 2)
    mel, tot_m = dist_multipla(d2.melhorar_lista, ordem=OPC_MELHORAR)
    out["condicoes"] = {
        "media": r2["media_condicoes"], "indice": r2["condicoes"],
        "distribuicao": [{"nota": int(k), "n": int(v)} for k, v in
                         d2.nota_condicoes.dropna().astype(int)
                         .value_counts().reindex(range(11), fill_value=0).items()],
        "melhorar": mel, "melhorar_base": tot_m,
    }

    # -------------------------------------------------- respeito (rodada 2)
    respeito_funcao = []
    for f, g in d2.groupby("funcao"):
        if len(g) < MIN_RECORTE or not f:
            continue
        vc = g.respeito.value_counts()
        respeito_funcao.append({
            "funcao": f, "n": len(g),
            "sempre": int(vc.get("Sempre", 0)),
            "maior_parte": int(vc.get("Na maior parte do tempo", 0)),
            "poucas": int(vc.get("Poucas vezes", 0)),
            "nunca": int(vc.get("Nunca", 0)),
            "pleno_pct": pct(int(vc.get("Sempre", 0)), len(g), 0),
            "nota_salario": round(float(g.nota_salario.mean()), 2),
            "nota_condicoes": round(float(g.nota_condicoes.mean()), 2),
            "quer_clt": pct(int(g.clt.eq("Sim, com certeza").sum()), len(g), 0),
        })
    por_nivel = []
    for nivel in ORDEM_RESPEITO:
        g = d2[d2.respeito == nivel]
        if not len(g):
            continue
        por_nivel.append({
            "nivel": nivel, "n": len(g), "pct": pct(len(g), len(d2)),
            "nota_salario": (round(float(g.nota_salario.mean()), 2)
                             if len(g) >= MIN_RECORTE else None),
            "nota_condicoes": (round(float(g.nota_condicoes.mean()), 2)
                               if len(g) >= MIN_RECORTE else None),
        })
    out["respeito"] = {
        "distribuicao": dist(d2.respeito, ordem=ORDEM_RESPEITO, total=len(d2)),
        "sempre": r2["respeito_sempre"],
        "parcial": r2["respeito_parcial"],
        "falhou": r2["respeito_falhou"],
        "alguma_falha": round(100 - (r2["respeito_sempre"] or 0), 1),
        "por_nivel": por_nivel,
        "por_funcao": sorted(respeito_funcao, key=lambda x: -x["n"]),
        "n_escreveram": r2["n_escreveram"],
        "n_relatos": r2["n_relatos"],
    }

    # ------------------------------------------------ efetivacao (rodada 2)
    contra, tot_contra = dist_multipla(d2.contra_lista, ordem=OPC_CONTRA)
    out["efetivacao"] = {
        "distribuicao": dist(d2.clt, ordem=ORDEM_CLT, total=len(d2)),
        "sim": r2["clt_sim"], "sim_talvez": r2["clt_sim_talvez"], "nao": r2["clt_nao"],
        "contra": contra, "contra_base": tot_contra,
        "n_area": int((d2.area.str.strip().str.len() > 1).sum()),
    }

    # ---------------------------------------------------------- comentarios
    out["comentarios"] = {
        "r2_n": r2["n_comentarios"],
        "r1_mudar": int(base[MUDAR].notna().sum()),
        "r1_elogio": int(base[ELOGIO].notna().sum()),
    }

    Path(__file__).resolve().with_name("_estatisticas.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("_estatisticas.json gravado")
    print("  rodada 1: %d respostas | rodada 2: %d respostas"
          % (out["metodo"]["r1_n"], out["metodo"]["r2_n"]))
    print("  blocos:", ", ".join(out.keys()))


if __name__ == "__main__":
    main()
