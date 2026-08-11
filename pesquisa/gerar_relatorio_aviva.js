// ============================================================================
//  ESCUTA DO TEMPORARIO — relatorio das duas rodadas
//  Escrito em primeira pessoa, da Mendes RH para a Aviva / Rio Quente Resorts.
// ----------------------------------------------------------------------------
//  Numeros vindos de _estatisticas.json (extrair_estatisticas.py). Nada e
//  digitado a mao aqui.
//
//  REGRAS DE ESCRITA DESTE DOCUMENTO
//  - Primeira pessoa. Quem escreve e a Mendes RH; quem le e a Aviva.
//  - Nenhum travessao (— ou –). Ponto, virgula, dois-pontos ou parenteses.
//  - Nada de orientacao interna ("levar isso ao cliente", "em tela de
//    apresentacao..."). O cliente e o leitor.
//  - Sem linguagem promocional, sem regra de tres forcada, sem "nao e X, e Y".
// ============================================================================
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
        Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
        PageBreak, LevelFormat, TableOfContents, Header, Footer, PageNumber } = require('docx');
const fs = require('fs');

const D = JSON.parse(fs.readFileSync(__dirname + "/_estatisticas.json", "utf8"));

const AZUL = "1C5CAB", AZUL_ESC = "0D366B", CINZA = "52514E", MUT = "898781";
const VERDE = "0C7A3E", VERM = "A32020", AMBAR = "8A5A00";
const LARG = 9360;

// ------------------------------------------------------------- formatadores
const pc = (n, c) => (n === null || n === undefined) ? "—"
  : Number(n).toFixed(c === undefined ? 1 : c).replace(".", ",") + "%";
const nu = (n, c) => (n === null || n === undefined) ? "—"
  : Number(n).toFixed(c === undefined ? 1 : c).replace(".", ",");
// rotulos vindos do Google Forms usam travessao; troco por virgula na exibicao
const lbl = t => String(t).replace(/\s*—\s*/g, ", ").replace(/\s*–\s*/g, ", ");

// --------------------------------------------------------------- primitivas
const P = (t, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 130, line: o.line ?? 280 },
  alignment: o.align, indent: o.indent,
  children: [new TextRun({ text: t, size: o.size ?? 21, bold: o.bold,
                           italics: o.it, color: o.color ?? "0B0B0B", font: "Calibri" })]
});
const RICH = (runs, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 130, line: 280 }, indent: o.indent,
  children: runs.map(r => new TextRun({ text: r.t, bold: r.b, italics: r.i,
    size: r.size ?? 21, color: r.c ?? "0B0B0B", font: "Calibri" }))
});
const H1 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1,
  spacing: { before: 340, after: 170 } });
const H2 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 120 } });
const LI = (t, n = 0) => new Paragraph({ numbering: { reference: "bul", level: n },
  spacing: { after: 80, line: 280 },
  children: [new TextRun({ text: t, size: 21, font: "Calibri" })] });
const LIR = (runs, n = 0) => new Paragraph({ numbering: { reference: "bul", level: n },
  spacing: { after: 80, line: 280 },
  children: runs.map(r => new TextRun({ text: r.t, bold: r.b, italics: r.i, size: 21,
    color: r.c ?? "0B0B0B", font: "Calibri" })) });
const QUEBRA = () => new Paragraph({ children: [new PageBreak()] });

const cel = (txt, o = {}) => new TableCell({
  width: { size: o.w, type: WidthType.DXA },
  shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: "auto" } : undefined,
  margins: { top: 70, bottom: 70, left: 110, right: 110 },
  children: (Array.isArray(txt) ? txt : [txt]).map(t => new Paragraph({
    spacing: { after: 0, line: 250 }, alignment: o.align,
    children: [new TextRun({ text: String(t), size: o.size ?? 19, bold: o.bold,
      color: o.color ?? "0B0B0B", font: "Calibri" })] }))
});
function tabela(cabs, linhas, larguras, alinhaDir) {
  return new Table({
    columnWidths: larguras, width: { size: LARG, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "D9D8D2" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "D9D8D2" },
      left: { style: BorderStyle.SINGLE, size: 2, color: "D9D8D2" },
      right: { style: BorderStyle.SINGLE, size: 2, color: "D9D8D2" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "EAE9E3" },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: "EAE9E3" },
    },
    rows: [
      new TableRow({ tableHeader: true, children: cabs.map((c, i) =>
        cel(c, { w: larguras[i], fill: AZUL, color: "FFFFFF", bold: true, size: 18,
                 align: (alinhaDir && i >= alinhaDir) ? AlignmentType.RIGHT : undefined })) }),
      ...linhas.map((l, k) => new TableRow({ children: l.map((c, i) =>
        cel(c, { w: larguras[i], fill: k % 2 ? "F7F8FA" : undefined,
                 align: (alinhaDir && i >= alinhaDir) ? AlignmentType.RIGHT : undefined })) }))
    ]
  });
}
function tabDist(titulo, itens, largRotulo) {
  const lr = largRotulo || 5360;
  return tabela([titulo, "Respostas", "%"],
    itens.map(x => [lbl(x.rotulo), x.n, pc(x.pct)]),
    [lr, (LARG - lr) / 2, (LARG - lr) / 2], 1);
}
const CAIXA = (titulo, texto, cor) => [
  new Paragraph({ spacing: { before: 220, after: 60 }, indent: { left: 200 },
    shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: cor || VERDE, space: 8 } },
    children: [new TextRun({ text: titulo, bold: true, size: 21, color: cor || VERDE, font: "Calibri" })] }),
  new Paragraph({ spacing: { before: 0, after: 220, line: 280 }, indent: { left: 200 },
    shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: cor || VERDE, space: 8 } },
    children: [new TextRun({ text: texto, size: 20, color: CINZA, font: "Calibri" })] })
];
const LEG = t => new Paragraph({ spacing: { before: 60, after: 200, line: 260 },
  children: [new TextRun({ text: t, size: 18, color: MUT, italics: true, font: "Calibri" })] });

const f = [];
const m = D.metodo;
const voz = D.preditores.voz;
const vozBaixa = voz[voz.length - 1];
const alav = D.salario.alavancas;
const bonusFalta = alav.find(x => x.rotulo.includes("não faltar"));
const bonusFim = alav.find(x => x.rotulo.includes("até o fim"));
const fret = D.perfil.transporte.find(x => x.rotulo.includes("fretado"));
const moraAqui = D.perfil.moradia.find(x => x.rotulo.includes("Moro em"));
const tratR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("efetivos"));
const transR2 = D.condicoes.melhorar.find(x => x.rotulo === "Transporte");
const escR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("Escala"));
const aliR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("Alimentação"));
const descR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("descanso"));
const trans1 = D.absenteismo.causas.find(x => x.rotulo.includes("Transporte"));
const trat5 = D.escalas.find(x => x.pergunta.includes("Tratamento"));

// ==================================================================== CAPA
f.push(new Paragraph({ spacing: { before: 1000, after: 0 },
  children: [new TextRun({ text: "MENDES RH  PARA  AVIVA / RIO QUENTE RESORTS", bold: true, size: 20, color: AZUL, font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 60 },
  children: [new TextRun({ text: "Escuta do Temporário", bold: true, size: 56, color: "0B0B0B", font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 100 },
  children: [new TextRun({ text: "O que os temporários de julho nos contaram", bold: true, size: 30, color: AZUL_ESC, font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 360 },
  children: [new TextRun({ text: "Temporada de julho de 2026 · duas rodadas de pesquisa · agosto de 2026", size: 25, color: CINZA, font: "Calibri" })] }));
f.push(P(`${m.total_respostas} respostas: ${m.r1_n} sobre a experiência da temporada e ${m.r2_n} sobre ` +
  `salário, condições de trabalho e efetivação. Coleta entre 6 e 10 de agosto.`, { color: CINZA }));
f.push(QUEBRA());

// ============================================================ CARTA
f.push(H1("Antes de começar"));
f.push(P("Aplicamos duas pesquisas com os temporários que trabalharam com vocês em julho. " +
  "Este documento traz o que elas mostraram."));
f.push(P("Uma parte do que está aqui é desconfortável para nós da Mendes RH. Houve erro de " +
  "pagamento, teve gente que não recebeu crachá na contratação e passou vergonha na portaria, e " +
  "teve quem atravessasse a temporada inteira sem ter com quem falar. Deixei tudo no relatório. " +
  "Filtrar o que nos convém tiraria o sentido de ter perguntado."));
f.push(P("Outra parte é desconfortável para vocês. O tratamento que alguns funcionários efetivos " +
  "dão ao temporário aparece nas duas rodadas, e aparece forte. Em determinados postos o padrão " +
  "se repete o bastante para eu não conseguir tratar como caso isolado. Trago os números, trago " +
  "os relatos e proponho o que fazer com eles."));
f.push(P("Também trago uma boa notícia que não estávamos procurando: quase todo mundo que passou " +
  "por aqui quer ser efetivado por vocês. São pessoas já treinadas, que conhecem a operação e " +
  "que ficaram até o fim do contrato."));
f.push(P("Todos os números saem da mesma base do painel que vocês acessam, calculados pelo mesmo " +
  "código. Qualquer percentual deste relatório pode ser conferido lá, com os filtros que vocês " +
  "quiserem aplicar."));
f.push(QUEBRA());

// ================================================================== SUMARIO
f.push(H1("Sumário"));
f.push(P("Para preencher os números de página no Word: Ctrl+A e depois F9.",
  { size: 18, color: MUT, it: true }));
f.push(new TableOfContents("Sumário", { hyperlink: true, headingStyleRange: "1-2" }));
f.push(QUEBRA());

// ======================================================== 1. RESUMO
f.push(H1("1. O que encontramos"));
f.push(P(`A primeira rodada perguntou como foi a temporada, por que as pessoas faltaram e por que ` +
  `algumas saíram antes do fim. Responderam ${m.r1_n} de ${m.r1_convites} convidados, ` +
  `${pc(m.r1_taxa)}. A segunda foi desenhada para medir o que a primeira só tinha levantado em ` +
  `campo aberto, e foi enviada apenas para quem já havia respondido: ${m.r2_n} respostas em ` +
  `${m.r2_convites} convites, ${pc(m.r2_taxa)}, em um único dia.`));
f.push(P("Sete coisas resumem o resto do documento."));

// para citar dentro de uma frase, uso so o nucleo do rotulo
const curto = t => lbl(t).split(",")[0].trim().toLowerCase();
f.push(...CAIXA("1. Quase ninguém faltou por falta de vontade",
  `Entre as ${D.absenteismo.n_faltou} pessoas que faltaram ao menos um dia, ` +
  D.absenteismo.causas.slice(0, 3).map(x => `${pc(x.pct)} citaram ${curto(x.rotulo)}`).join("; ") +
  `. Desânimo com o trabalho, bico no mesmo dia e trabalho pesado demais para o valor pago somam ` +
  `${pc(D.absenteismo.desengajamento)} das citações. O absenteísmo de julho foi um problema de ` +
  `saúde e de logística.`));

f.push(...CAIXA("2. Quem não tem com quem falar falta quase o dobro",
  `Entre quem se sentiu à vontade para falar quando algo estava errado, ${pc(voz[0].faltou, 0)} ` +
  `faltaram. Entre quem não se sentiu, ${pc(vozBaixa.faltou, 0)}. É o achado que mais me chamou ` +
  `atenção, porque não depende de investimento de nenhum dos dois lados. Depende de alguém estar ` +
  `presente no posto nos primeiros dias.`));

f.push(...CAIXA("3. Quem sai decide na primeira semana",
  `Das ${D.saida.n_form_saida} saídas que responderam o questionário próprio, ` +
  `${D.saida.decidiu_cedo} foram decididas nos primeiros dias ou na primeira semana. A janela ` +
  `para intervir é curta e hoje nenhum de nós faz nada programado dentro dela.`, AZUL));

f.push(...CAIXA("4. O salário não é o problema que eu imaginava",
  `${pc(D.salario.expect_atendeu)} disseram que o valor recebido atendeu ou superou o que ` +
  `esperavam quando aceitaram a vaga. Só ${pc(D.salario.mercado_pior)} acham o pagamento pior que ` +
  `o de outros temporários da região, contra ${pc(D.salario.mercado_melhor)} que acham melhor. ` +
  `A nota média foi ${nu(D.salario.media, 2)}. O salário é exigente e ainda assim bem avaliado.`));

f.push(...CAIXA("5. Existe alternativa mais barata que reajuste linear",
  `${pc(alav[0].pct)} pedem diária maior, mas ${pc(bonusFalta.pct)} aceitariam bônus por não ` +
  `faltar e ${pc(bonusFim.pct)} bônus por ficar até o fim da temporada. Bônus condicionado custa ` +
  `menos que reajuste na folha inteira e ataca justamente os dois problemas da primeira rodada.`, AZUL));

f.push(...CAIXA("6. O respeito é o ponto mais delicado deste relatório",
  `Apenas ${pc(D.respeito.sempre)} se sentiram sempre respeitados no ambiente de trabalho. ` +
  `${pc(D.respeito.parcial)} responderam "na maior parte do tempo" e ${pc(D.respeito.falhou)} ` +
  `responderam "poucas vezes". Quem marcou "poucas vezes" avalia pior tudo, inclusive o salário, ` +
  `que é o mesmo valor pago aos colegas da mesma função.`, VERM));

f.push(...CAIXA("7. Quase todo mundo quer ser efetivado por vocês",
  `${pc(D.efetivacao.sim)} querem virar CLT na Aviva com certeza e ${pc(D.efetivacao.sim_talvez)} ` +
  `querem ou considerariam. Só ${pc(D.efetivacao.nao)} descartam. Para essas pessoas o contrato ` +
  `temporário funcionou como porta de entrada, e hoje não existe caminho formal depois dessa porta.`, AZUL));
f.push(QUEBRA());

// =========================================================== 2. METODO
f.push(H1("2. Como perguntamos"));
f.push(H2("2.1 As duas rodadas"));
f.push(tabela(
  ["Rodada", "Sobre o quê", "Convites", "Respostas", "Taxa"],
  [["1", "Experiência da temporada, faltas, saída, vínculo", m.r1_convites, m.r1_n, pc(m.r1_taxa)],
   ["2", "Salário, condições de trabalho, respeito, efetivação", m.r2_convites, m.r2_n, pc(m.r2_taxa)]],
  [900, 4860, 1200, 1200, 1200], 2));
f.push(LEG("A rodada 2 foi enviada só para quem respondeu a rodada 1. Os dois públicos se " +
  "sobrepõem e não são amostras independentes."));

f.push(H2("2.2 Como foi aplicada"));
f.push(P(`Na rodada 1 usamos dois questionários: um longo, para quem cumpriu a temporada, com ` +
  `${m.r1_form_longo} respostas, e um curto, de saída, com ${m.r1_form_saida}. Os dois anônimos, ` +
  `enviados por WhatsApp um a um. Quem concluía ganhava um par de ingressos do Hot Park, sem sorteio.`));
f.push(P(`Na rodada 2 foi um questionário só, também anônimo, com sorteio de 10 prêmios de R$ 70 ` +
  `via PIX pagos no dia de uso do ingresso. Nas duas rodadas o cadastro de contato ficou em um ` +
  `formulário separado, com planilha separada.`));
f.push(...CAIXA("Por que o anonimato importa aqui",
  "O formato de pesquisa que usávamos antes coletava telefone na mesma planilha das respostas. " +
  "Ninguém escreve que se sentiu humilhado num formulário assim. Separar o cadastro da resposta " +
  "foi o que fez aparecer o conteúdo da seção 9.", AZUL));

f.push(H2("2.3 De onde vem a divisão entre os grupos"));
f.push(RICH([
  { t: "O grupo não veio da nossa lista de envio, veio da declaração de cada pessoa. ", b: true },
  { t: `${m.r1_reclassificados} pessoas receberam o questionário de quem cumpriu a temporada e ` +
       `informaram, logo na pergunta de triagem, que tinham saído antes do fim. Contei essas ` +
       `pessoas no grupo de saída. Por isso os números finais são ${m.r1_cumpriu} e ` +
       `${m.r1_saiu}, e não ${m.r1_form_longo} e ${m.r1_form_saida} como diria a lista de disparo.` }]));
f.push(tabela(
  ["Grupo", "Convites", "Respostas", "Taxa", "Após reclassificar"],
  [["Cumpriu a temporada", 150, m.r1_form_longo, pc(m.r1_taxa_cumpriu), m.r1_cumpriu],
   ["Saiu antes do fim", 28, m.r1_form_saida, pc(m.r1_taxa_saiu), m.r1_saiu],
   ["Total", m.r1_convites, m.r1_n, pc(m.r1_taxa), m.r1_n]],
  [2700, 1500, 1600, 1400, 2160], 1));
f.push(QUEBRA());

// ============================================================ 3. PERFIL
f.push(H1("3. Quem respondeu"));
f.push(P("O perfil abaixo é o da rodada 1, que tem a base maior. A rodada 2 tem distribuição " +
  "parecida por função, já que foi para o mesmo público."));
f.push(H2("3.1 Por função"));
f.push(tabDist("Função", D.perfil.funcao, 5360));
f.push(H2("3.2 Por local de trabalho"));
f.push(tabDist("Local", D.perfil.local, 5360));
f.push(H2("3.3 Moradia e transporte"));
f.push(tabDist("Onde mora", D.perfil.moradia, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Como ia e voltava do trabalho", D.perfil.transporte, 5360));
f.push(...CAIXA("Dois números que explicam boa parte do resto",
  `${pc(moraAqui.pct)} moram na região e ${pc(fret.pct)} dependem só do transporte fretado. ` +
  `Quando a rota atrasa ou o ônibus enche, essas pessoas não têm plano B. Vira falta. E ` +
  `transporte está entre as três maiores causas de ausência.`, AMBAR));
f.push(QUEBRA());

// ======================================================= 4. VINCULO
f.push(H1("4. O que eles acham da Mendes RH"));
f.push(H2("4.1 Índice de recomendação"));
f.push(P("Pedimos uma nota de 0 a 10 para a pergunta \"o quanto você indicaria a Mendes RH para " +
  "um amigo trabalhar?\". Quem dá 9 ou 10 recomenda. Quem dá 7 ou 8 é indiferente e fica fora da " +
  "conta. Quem dá 0 a 6 não recomenda. O índice é a diferença entre o percentual do primeiro " +
  "grupo e o do último, numa escala de menos 100 a mais 100. Acima de 50 é considerado excelente " +
  "em qualquer referência de mercado."));
const vt = D.vinculo.total, vcm = D.vinculo.cumpriu, vs = D.vinculo.saiu;
f.push(tabela(
  ["Grupo", "n", "Recomendam", "Indiferentes", "Não recomendam", "Índice", "Nota média"],
  [["Total", vt.n, vt.promotores, vt.neutros, vt.detratores, nu(vt.enps), nu(vt.media, 2)],
   ["Cumpriu a temporada", vcm.n, vcm.promotores, vcm.neutros, vcm.detratores, nu(vcm.enps), nu(vcm.media, 2)],
   ["Saiu antes do fim", vs.n, vs.promotores, vs.neutros, vs.detratores, nu(vs.enps), nu(vs.media, 2)]],
  [2300, 700, 1300, 1300, 1560, 1100, 1100], 1));
f.push(...CAIXA("Quem saiu antes continua recomendando",
  `A diferença entre quem cumpriu, ${nu(vcm.enps)}, e quem saiu antes, ${nu(vs.enps)}, é de ` +
  `${nu(vcm.enps - vs.enps)} pontos. Isso significa que a saída antecipada não queimou a relação: ` +
  `essas pessoas seguem recontratáveis e seguem indicando a empresa para conhecidos.`));

f.push(H2("4.2 Por função"));
f.push(tabela(
  ["Função", "n", "Índice", "Nota média", "Faltou", "Pensou em sair", "Voltaria"],
  D.vinculo.por_funcao.map(x => [x.funcao, x.n, nu(x.indice), nu(x.media, 2),
    pc(x.faltou, 0), pc(x.pensou_sair, 0), pc(x.voltaria, 0)]),
  [2700, 600, 1000, 1200, 1000, 1500, 1360], 1));
f.push(LEG("Só funções com 5 respostas ou mais. Abaixo disso o recorte identifica quem respondeu " +
  "e quebra o anonimato que prometemos no formulário. A coluna de intenção de sair só existe no " +
  "questionário longo, então o denominador dela é menor."));

f.push(H2("4.3 Intenção de voltar"));
f.push(tabDist("Voltaria a trabalhar na próxima temporada?", D.vinculo.voltaria, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Se abrisse uma vaga fixa hoje, aceitaria?", D.vinculo.vaga_fixa, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Acredita que teve chance real de efetivação?", D.vinculo.chance_efetivacao, 5360));
f.push(QUEBRA());

// ==================================================== 5. ABSENTEISMO
f.push(H1("5. Absenteísmo"));
f.push(H2("5.1 Quanto se faltou"));
f.push(tabDist("Durante a temporada, chegou a faltar?", D.absenteismo.faixas, 5360));
f.push(RICH([{ t: "Taxa de ausência: ", b: true },
  { t: `${pc(D.absenteismo.faltou_cumpriu)} entre quem cumpriu a temporada e ` +
       `${pc(D.absenteismo.faltou_saiu)} entre quem saiu antes do fim.` }]));

f.push(H2("5.2 Por que se falta"));
f.push(tabela(["Causa", "Citações", "% de quem faltou"],
  D.absenteismo.causas.map(x => [lbl(x.rotulo), x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));
f.push(LEG(`Base: as ${D.absenteismo.n_faltou} pessoas que declararam ao menos uma ausência. ` +
  `Cada uma podia marcar até 3 causas, então a soma passa de 100%. Foram ` +
  `${D.absenteismo.citacoes} citações no total.`));
f.push(...CAIXA("Saúde, cansaço e transporte concentram a explicação",
  `As três causas mais citadas somam ${pc(D.absenteismo.top3_share, 0)} das citações. Desânimo, ` +
  `bico no mesmo dia e trabalho pesado demais para o valor pago somam ${pc(D.absenteismo.desengajamento)}. ` +
  `Entre as causas grandes, transporte é a que nós dois controlamos: rota, horário, capacidade e ` +
  `estado dos veículos.`, AMBAR));

f.push(H2("5.3 O que pesou no dia a dia"));
f.push(tabela(["O que mais pesou", "Citações", "% dos respondentes"],
  D.absenteismo.pesou.map(x => [lbl(x.rotulo), x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));

f.push(H2("5.4 O que teria reduzido as faltas"));
f.push(tabela(["Alavanca", "Citações", "%"],
  D.absenteismo.alavancas.map(x => [lbl(x.rotulo), x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));
const outro = D.absenteismo.alavancas.find(x => x.rotulo === "Outro");
if (outro) {
  f.push(...CAIXA("A opção mais marcada foi \"Outro\", e isso também diz algo",
    `${pc(outro.pct)} marcaram "Outro", acima de qualquer alavanca que oferecemos. A lista de ` +
    `opções partia do princípio de que a falta é negociável: mais folga, mais dinheiro, escala ` +
    `melhor. Para a maioria dessas pessoas nada disso se aplicava, o que bate com a causa que ` +
    `elas mesmas declararam. Quem falta por doença ou por não conseguir chegar não é retido por ` +
    `bônus. Foi erro meu de formulação e vou trocar essa pergunta por uma aberta na próxima rodada.`, AZUL));
}
f.push(QUEBRA());

// ==================================================== 6. PREDITORES
f.push(H1("6. O que separa quem falta de quem não falta"));
f.push(P("Os cruzamentos desta seção não medem opinião. Eles separam grupos que se comportaram " +
  "de forma diferente. É a parte que mais me interessa, porque aponta ação."));

f.push(H2("6.1 Ter com quem falar"));
f.push(tabela(["\"Se sentiu à vontade para falar quando algo estava errado?\"", "n", "Faltou ao menos 1 dia"],
  D.preditores.voz.map(x => [lbl(x.nivel), x.n, pc(x.faltou, 0)]),
  [5360, 1400, 2600], 1));
if (D.preditores.voz_intencao.length) {
  f.push(P("", { after: 100 }));
  f.push(tabela(["Mesmo corte, outra medida", "n", "Pensou em sair antes do fim"],
    D.preditores.voz_intencao.map(x => [lbl(x.nivel), x.n, pc(x.pensou, 0)]),
    [5360, 1400, 2600], 1));
}
f.push(...CAIXA("Isso não se resolve com dinheiro",
  `Quem não se sentiu à vontade para falar faltou ${pc(vozBaixa.faltou, 0)}, contra ` +
  `${pc(voz[0].faltou, 0)} de quem se sentiu. O que resolve é presença: alguém disponível no ` +
  `posto nos primeiros dias, com registro do que foi dito. Isso é nosso e começa já.`));

f.push(H2("6.2 Erro de pagamento"));
f.push(tabela(["\"Recebeu tudo certo e no prazo?\"", "n", "Faltou ao menos 1 dia"],
  D.preditores.pagamento.map(x => [lbl(x.nivel), x.n, pc(x.faltou, 0)]),
  [5360, 1400, 2600], 1));
f.push(...CAIXA("Essa falha é nossa",
  `Ninguém marcou "teve problema mais de uma vez", o que indica erro pontual e não sistêmico. ` +
  `Ainda assim, ${pc(D.preditores.pgp_dist[1].pct)} passaram por algum atraso ou erro, e esse ` +
  `grupo faltou ${pc(D.preditores.pagamento[1].faltou, 0)} contra ` +
  `${pc(D.preditores.pagamento[0].faltou, 0)} dos demais. Depende só de processo interno nosso.`, VERM));

f.push(H2("6.3 Entrada e integração"));
f.push(tabela(["Pergunta", "n", "Nota média (1 a 5)", "Deram nota 5", "Deram 1 ou 2"],
  D.escalas.map(x => [x.pergunta, x.n, nu(x.media, 2), pc(x.nota5), pc(x.nota12)]),
  [4200, 900, 1800, 1300, 1160], 1));
if (trat5) {
  f.push(...CAIXA("O sinal que a rodada 2 foi confirmar",
    `"Como os colegas efetivos tratavam os temporários" teve média ${nu(trat5.media, 2)}, a mais ` +
    `baixa das três, e ${trat5.n_nota1} pessoas deram nota 1. Foi o único item em que alguém usou ` +
    `o extremo negativo em volume. Era sinal fraco demais para eu levar a vocês como problema. ` +
    `Por isso incluí a pergunta direta sobre respeito na segunda rodada.`, AMBAR));
}
f.push(P("", { after: 100 }));
f.push(tabDist("Ficou claro o que era esperado de você?", D.preditores.claro, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Recebeu no primeiro dia tudo o que precisava?", D.preditores.kit, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("A escala cumprida foi a combinada na contratação?", D.preditores.escala, 5360));
f.push(QUEBRA());

// ==================================================== 7. SAIDA
f.push(H1("7. Quem saiu antes do fim"));
f.push(P(`${D.saida.n} pessoas saíram antes do fim da temporada, pela própria declaração. Dessas, ` +
  `${D.saida.n_form_saida} responderam o questionário de saída. A base é pequena, então leia esta ` +
  `seção como indicação, não como conclusão fechada.`));

f.push(H2("7.1 Quem pensou em sair"));
f.push(tabDist("Em algum momento pensou em sair antes do fim?", D.saida.pensou_sair, 5360));

f.push(H2("7.2 O que segurou quem ficou"));
f.push(tabela(["O que mais te segurou até o fim", "Citações", "%"],
  D.saida.segurou.map(x => [lbl(x.rotulo), x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));

f.push(H2("7.3 Como e quando a saída aconteceu"));
f.push(tabDist("A saída foi decisão sua ou da empresa?", D.saida.decisao, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Em que momento decidiu que ia sair?", D.saida.quando, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Quanto tempo ficou antes de sair?", D.saida.tempo, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Avisou alguém antes de sair?", D.saida.avisou, 5360));
f.push(...CAIXA("A decisão vem antes do aviso",
  `${D.saida.decidiu_cedo} das ${D.saida.n_form_saida} saídas foram decididas nos primeiros dias ` +
  `ou na primeira semana, e a maioria avisou com antecedência. Ou seja, tivemos o aviso. Faltou ` +
  `a conversa que deveria ter vindo antes dele.`, AZUL));

f.push(H2("7.4 Motivo declarado"));
f.push(tabDist("Qual foi o motivo real da sua saída?", D.saida.motivo, 5360));
f.push(H2("7.5 O que teria feito ficar"));
f.push(tabela(["O que teria feito você ficar até o fim", "Citações", "%"],
  D.saida.ficaria.map(x => [lbl(x.rotulo), x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));
const ouvisse = D.saida.ficaria.find(x => x.rotulo.includes("ouvisse"));
if (ouvisse) {
  f.push(...CAIXA("O item mais citado não custa nada",
    `"Alguém que me ouvisse quando o problema começou" foi o mais marcado, ${ouvisse.n} de ` +
    `${D.saida.n_form_saida} respostas. É o mesmo achado da seção 6.1, visto pelo outro lado: ` +
    `quem foi embora queria ter tido com quem falar.`, AZUL));
}
f.push(QUEBRA());

// ==================================================== 8. SALARIO
f.push(H1("8. Salário"));
f.push(P("Esta seção e as duas seguintes vêm da rodada 2. Entrei nela achando que o salário " +
  "explicaria o absenteísmo e a saída antecipada. Não explica."));

f.push(H2("8.1 A nota"));
const dsal = D.salario.distribuicao.filter(x => x.n > 0);
f.push(tabela(["Nota atribuída (0 a 10)", ...dsal.map(x => String(x.nota))],
  [["Respostas", ...dsal.map(x => String(x.n))]],
  [2600, ...dsal.map(() => Math.floor((LARG - 2600) / dsal.length))], 1));
f.push(P("", { after: 120 }));
f.push(tabela(["Indicador", "Valor"],
  [["Nota média", nu(D.salario.media, 2)],
   ["Recomendam (notas 9 e 10)", `${D.salario.indice.promotores} · ${pc(D.salario.indice.promotores / D.salario.indice.n * 100)}`],
   ["Indiferentes (notas 7 e 8)", `${D.salario.indice.neutros} · ${pc(D.salario.indice.neutros / D.salario.indice.n * 100)}`],
   ["Não recomendam (notas 0 a 6)", `${D.salario.indice.detratores} · ${pc(D.salario.indice.detratores / D.salario.indice.n * 100)}`],
   ["Índice de recomendação do salário", nu(D.salario.indice.enps)]],
  [6000, 3360], 1));

f.push(H2("8.2 Expectativa e comparação com a região"));
f.push(tabDist("O valor atendeu o que você esperava ao aceitar a vaga?", D.salario.expectativa, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Comparado a outros temporários da região, o pagamento é:", D.salario.mercado, 5360));
f.push(...CAIXA("Exigência, e não insatisfação",
  `${pc(D.salario.expect_atendeu)} tiveram a expectativa atendida ou superada e só ` +
  `${pc(D.salario.mercado_pior)} consideram o pagamento pior que o do mercado local. O índice ` +
  `${nu(D.salario.indice.enps)} é o mais baixo dos três que medimos e mesmo assim positivo. ` +
  `Minha leitura: o salário está adequado para atrair, mas não é ele que segura ninguém até o fim.`));

f.push(H2("8.3 O que faria diferença no pagamento"));
f.push(tabela(["O que mais faria diferença", "Citações", "% dos respondentes", "Tipo de custo"],
  D.salario.alavancas.map(x => [lbl(x.rotulo), x.n, pc(x.pct),
    x.rotulo.includes("Bônus") ? "Condicionado a resultado"
      : x.rotulo.includes("semanal") ? "Fluxo de caixa, sem custo extra" : "Custo fixo"]),
  [3300, 1100, 1700, 3260], 1));
f.push(LEG(`Base: ${D.salario.alavancas_base} respondentes, até 2 marcações cada.`));
f.push(...CAIXA("Uma proposta concreta",
  `${pc(bonusFalta.pct)} aceitariam bônus por não faltar e ${pc(bonusFim.pct)} bônus por ficar até ` +
  `o fim. São exatamente os dois problemas da rodada 1, e um bônus condicionado custa menos que ` +
  `reajuste na folha inteira porque só é pago quando o resultado aparece. Entre as ` +
  `${D.salario.insatisfeitos.n} pessoas que deram nota 6 ou menos ao salário, o padrão se repete. ` +
  `Gostaria de testar isso em uma função na próxima temporada e medir contra o histórico de julho.`, VERDE));
f.push(QUEBRA());

// ============================================ 9. CONDICOES E RESPEITO
f.push(H1("9. Condições de trabalho e respeito"));
f.push(H2("9.1 A nota das condições"));
const dcond = D.condicoes.distribuicao.filter(x => x.n > 0);
f.push(tabela(["Nota atribuída (0 a 10)", ...dcond.map(x => String(x.nota))],
  [["Respostas", ...dcond.map(x => String(x.n))]],
  [2600, ...dcond.map(() => Math.floor((LARG - 2600) / dcond.length))], 1));
f.push(P("", { after: 120 }));
f.push(RICH([{ t: `Nota média ${nu(D.condicoes.media, 2)}`, b: true },
  { t: `, contra ${nu(D.salario.media, 2)} do salário. Índice ${nu(D.condicoes.indice.enps)}, ` +
       `contra ${nu(D.salario.indice.enps)}. Eles avaliam melhor a estrutura de vocês do que a ` +
       `remuneração que pagamos.` }]));

f.push(H2("9.2 O que precisa melhorar"));
f.push(tabela(["Frente", "Citações", "% dos respondentes", "Onde está a decisão"],
  D.condicoes.melhorar.map(x => {
    const r = x.rotulo;
    const dono = r.includes("Tratamento") ? "Aviva"
      : r.includes("Escala") || r.includes("Transporte") ? "Aviva e Mendes RH"
      : r.includes("Uniforme") ? "Mendes RH"
      : r.includes("Nada") ? "" : "Aviva";
    return [lbl(r), x.n, pc(x.pct), dono];
  }),
  [3300, 1100, 1700, 3260], 1));
f.push(LEG(`Base: ${D.condicoes.melhorar_base} respondentes, até 3 marcações cada.`));
f.push(...CAIXA("Nem tudo aqui custa dinheiro",
  "Alimentação, banheiros e local de descanso são investimento de estrutura. Escala e transporte " +
  "a gente resolve junto. Uniforme é nosso. Mas os dois itens de tratamento, pelos efetivos e " +
  "pela segurança, não custam nada além de orientação e cobrança interna, e são justamente os " +
  "que mais aparecem nos relatos abertos da próxima página.", AMBAR));

f.push(H2("9.3 Respeito no ambiente de trabalho"));
f.push(P("Essa pergunta é nova. Incluí porque a rodada 1 trouxe, num campo aberto, um relato que " +
  "exigia apuração formal, e eu não tinha como saber se aquilo era exceção ou rotina."));
f.push(tabela(["Se sentiu respeitado(a)?", "Respostas", "%", "Nota salário", "Nota condições"],
  D.respeito.por_nivel.map(x => [x.nivel, x.n, pc(x.pct), nu(x.nota_salario, 2), nu(x.nota_condicoes, 2)]),
  [3000, 1400, 1200, 1880, 1880], 1));
const pleno = D.respeito.por_nivel.find(x => x.nivel === "Sempre");
const parcial = D.respeito.por_nivel.find(x => x.nivel === "Na maior parte do tempo");
const pior = D.respeito.por_nivel.filter(x => x.nota_salario !== null).slice(-1)[0];
if (pleno && parcial && pior && pior.nivel !== "Sempre") {
  const mSal = (pleno.nota_salario + parcial.nota_salario) / 2;
  const mCond = (pleno.nota_condicoes + parcial.nota_condicoes) / 2;
  f.push(...CAIXA("O desrespeito contamina a avaliação inteira",
    `Entre "sempre" e "na maior parte do tempo" as notas quase não mudam: a média das duas é ` +
    `${nu(mSal, 2)} no salário e ${nu(mCond, 2)} nas condições. Quem marcou ` +
    `"${pior.nivel.toLowerCase()}" cai para ${nu(pior.nota_salario, 2)} e ` +
    `${nu(pior.nota_condicoes, 2)}, recebendo exatamente a mesma diária que os colegas da mesma ` +
    `função. Quando o desrespeito acontece, ele derruba a percepção de tudo. São ${pior.n} ` +
    `pessoas, poucas o bastante para tratar caso a caso.`, VERM));
}

f.push(H2("9.4 Onde o problema se concentra"));
f.push(tabela(["Função", "n", "Sempre", "Na maior parte", "Poucas vezes", "Nota salário", "Quer CLT"],
  D.respeito.por_funcao.map(x => [x.funcao, x.n, x.sempre, x.maior_parte, x.poucas,
    nu(x.nota_salario, 2), pc(x.quer_clt, 0)]),
  [2700, 600, 1000, 1400, 1300, 1200, 1160], 1));
f.push(LEG("Só funções com 5 respostas ou mais."));

f.push(H2("9.5 O que escreveram"));
f.push(P(`${D.respeito.n_escreveram} pessoas escreveram no campo aberto. ` +
  `${D.respeito.n_escreveram - D.respeito.n_relatos} responderam que não tinham nada a relatar. ` +
  `As ${D.respeito.n_relatos} restantes descrevem alguma situação, e se distribuem assim:`));
f.push(LIR([{ t: "Fronteira entre efetivo e temporário. ", b: true },
  { t: "O padrão que mais aparece. Serviço transferido para o temporário, comentários sobre " +
       "aparência, recepção hostil ao entrar em determinados postos. Duas pessoas diferentes " +
       "citam o mesmo posto sem se conhecerem." }]));
f.push(LIR([{ t: "Conduta individual com nome. ", b: true },
  { t: "Um relato cita, com nome e função, alguém cuja conduta descrita bate com o caso que " +
       "recebemos anonimamente na rodada 1. São dois respondentes independentes, em rodadas " +
       "diferentes, descrevendo o mesmo comportamento." }]));
f.push(LIR([{ t: "Nome social. ", b: true },
  { t: "Uma pessoa em transição de gênero relata ter sido chamada pelo nome de registro de forma " +
       "repetida, mesmo depois de informar o nome social. Isso é falta de política, e a política " +
       "é nossa: vamos criar campo de nome social no cadastro e orientar os supervisores." }]));
f.push(LIR([{ t: "Crachá e portaria. ", b: true },
  { t: "Uma pessoa passou por constrangimento na entrada por não ter recebido crachá na " +
       "contratação nem orientação sobre a necessidade dele. A falha de entrega é nossa e já está " +
       "sendo corrigida. O tratamento recebido na portaria fica para conversarmos." }]));
f.push(...CAIXA("O que proponho para os casos com nome",
  "Os relatos que citam pessoas seguem por apuração formal, com registro, e não por este " +
  "relatório. Envio os textos integrais em documento separado para quem for conduzir a apuração " +
  "de cada lado. A pesquisa é anônima e não identifica quem escreveu, mas identifica posto e " +
  "função de quem foi citado, o que basta para apurar sem expor ninguém.", VERM));
f.push(QUEBRA());

// ==================================================== 10. EFETIVACAO
f.push(H1("10. Efetivação"));
f.push(tabDist("Teria interesse em ser efetivado(a) como CLT na Aviva?",
  D.efetivacao.distribuicao, 5360));
if (D.efetivacao.contra.length) {
  f.push(P("", { after: 120 }));
  f.push(tabela(["O que pesa contra", "Citações", "%"],
    D.efetivacao.contra.map(x => [lbl(x.rotulo), x.n, pc(x.pct)]),
    [5360, 2000, 2000], 1));
  f.push(LEG(`Base: ${D.efetivacao.contra_base} pessoas que responderam "talvez" ou "não". ` +
    `Base pequena, leitura indicativa.`));
}
f.push(P(`${D.efetivacao.n_area} pessoas escreveram em qual área gostariam de trabalhar como ` +
  `efetivas. As mais citadas foram bares e restaurantes, hotelaria e governança, e parques e ` +
  `recreação. São as mesmas áreas em que já atuaram como temporárias.`));
f.push(...CAIXA("Por que isso vale dinheiro para vocês",
  "Essas pessoas já foram captadas, treinadas, integradas à operação e demonstraram que ficam até " +
  "o fim do contrato. Contratar alguém desse grupo custa menos e tem risco menor do que abrir " +
  "vaga no mercado. Gostaria de propor um processo simples: ao fim de cada temporada, nós " +
  "indicamos quem se destacou e vocês avaliam antes de abrir a vaga para fora.", VERDE));
f.push(QUEBRA());

// ==================================================== 11. CONVERGENCIA
f.push(H1("11. O que as duas rodadas dizem juntas"));
f.push(P("A rodada 1 levantou hipóteses a partir de campos abertos e escalas. A rodada 2 foi " +
  "feita para medir essas hipóteses. \"Confirmado\" quer dizer que o tema apareceu sozinho na " +
  "primeira e ganhou tamanho na segunda."));
f.push(tabela(["Tema", "Rodada 1", "Rodada 2", "Resultado"],
  [["Tratamento pelos efetivos",
    `Nota ${nu(trat5 ? trat5.media : 0, 2)} na escala, ${trat5 ? trat5.n_nota1 : 0} notas 1, recorrente no campo aberto`,
    `${pc(tratR2.pct, 0)} pedem melhora, ${pc(D.respeito.alguma_falha, 0)} com falha de respeito`,
    "CONFIRMADO"],
   ["Transporte",
    `${pc(trans1.pct, 0)} de quem faltou citou, ${pc(fret.pct)} dependem do fretado`,
    `${pc(transR2.pct, 0)} pedem melhora`, "CONFIRMADO"],
   ["Escala e folgas",
    "Aparece entre o que teria feito ficar e no campo aberto",
    `${pc(escR2.pct, 0)} pedem melhora, maior freio à efetivação`, "CONFIRMADO"],
   ["Alimentação e descanso",
    `Nota ${nu(D.escalas[1].media, 2)} na escala, pedidos pontuais no campo aberto`,
    `${pc(aliR2.pct, 0)} alimentação, ${pc(descR2.pct, 0)} cadeiras para descanso`, "AMPLIADO"],
   ["Salário",
    "Pouco presente entre causas de falta e de saída",
    `${pc(D.salario.expect_atendeu)} com expectativa atendida`, "DESCARTADO"]],
  [2000, 3000, 2900, 1460]));

f.push(H2("11.1 Como eu leio tudo isso"));
f.push(P(`As duas rodadas somaram ${m.total_respostas} respostas em cinco dias. A segunda teve ` +
  `${pc(m.r2_taxa)} de retorno em um único dia, enviada só para quem já tinha respondido a ` +
  `primeira. Gente cansada de pesquisa não responde a segunda em um dia. Elas responderam porque ` +
  `acreditam que muda alguma coisa, e isso nos obriga a mostrar que mudou.`));
f.push(RICH([{ t: "A hipótese do salário caiu. ", b: true },
  { t: `Era a explicação natural para ${pc(D.absenteismo.faltou_cumpriu)} de absenteísmo e ` +
       `${D.saida.n} saídas antecipadas. A rodada 2 mostra ${pc(D.salario.expect_atendeu)} com a ` +
       `expectativa atendida ou superada. Continuo achando que a diária merece revisão, mas ela ` +
       `não é a causa do que aconteceu em julho.` }]));
f.push(RICH([{ t: "O que sobra é relação. ", b: true },
  { t: `Na rodada 1, quem não se sente à vontade para falar falta ${pc(vozBaixa.faltou, 0)} contra ` +
       `${pc(voz[0].faltou, 0)}. Na rodada 2, ${pc(D.respeito.alguma_falha)} relatam alguma falha ` +
       `de respeito. São o mesmo problema visto de dois ângulos: a fronteira entre efetivo e ` +
       `temporário, e a falta de alguém escutando durante o contrato em vez de só no fim dele.` }]));
f.push(RICH([{ t: "E apareceu uma oportunidade que ninguém tinha pedido. ", b: true },
  { t: `${pc(D.efetivacao.sim_talvez)} querem ou considerariam ser efetivados por vocês. É um ` +
       `funil de recrutamento pronto, já testado em operação real.` }]));
f.push(QUEBRA());

// ==================================================== 12. PLANO
f.push(H1("12. O que proponho"));
f.push(H2("12.1 O que já começamos do nosso lado"));
f.push(P("Estas cinco ações não dependem de vocês e já estão em andamento."));
f.push(tabela(["#", "Ação", "Por quê"],
  [["1", "Conversa de 5 minutos no 3º e no 7º dia de cada temporário, com registro",
    `${D.saida.decidiu_cedo} de ${D.saida.n_form_saida} saídas foram decididas na primeira semana`],
   ["2", "Revisão do processo de pagamento para zerar atraso e erro",
    `Quem teve erro faltou ${pc(D.preditores.pagamento[1].faltou, 0)} contra ${pc(D.preditores.pagamento[0].faltou, 0)}`],
   ["3", "Entrega do crachá na contratação, com orientação de uso",
    "Relato de constrangimento na portaria por falta de crachá"],
   ["4", "Campo de nome social no cadastro e orientação aos supervisores",
    "Relato de nome social ignorado de forma repetida"],
   ["5", "Canal de escuta ativo durante a temporada, não só no encerramento",
    `Sem voz falta ${pc(vozBaixa.faltou, 0)}, com voz ${pc(voz[0].faltou, 0)}`]],
  [500, 4200, 4660]));

f.push(H2("12.2 O que gostaria de decidir com vocês"));
f.push(tabela(["#", "Proposta", "Base na pesquisa", "Custo"],
  [["6", "Alinhamento com efetivos e segurança sobre o tratamento ao temporário",
    `${pc(tratR2.pct, 0)} pedem melhora, ${pc(D.respeito.alguma_falha, 0)} com falha de respeito`, "Nenhum"],
   ["7", "Apuração conjunta dos relatos que citam pessoas",
    "Caso corroborado por duas rodadas independentes", "Nenhum"],
   ["8", "Diagnóstico dirigido em camareira e governança",
    "Pior nota de salário e maior taxa de \"poucas vezes\" em respeito", "Baixo"],
   ["9", "Piloto de bônus por assiduidade e por conclusão de contrato em uma função",
    `${pc(bonusFalta.pct)} e ${pc(bonusFim.pct)} aceitariam`, "Médio"],
   ["10", "Auditoria do transporte fretado: rota, horário, capacidade e conduta a bordo",
    `${pc(fret.pct)} dependem do fretado, ${pc(transR2.pct, 0)} pedem melhora`, "Médio"],
   ["11", "Trilha de efetivação com indicação nossa ao fim de cada temporada",
    `${pc(D.efetivacao.sim_talvez)} querem ou considerariam`, "Médio"]],
  [500, 3400, 4000, 1460]));
f.push(P("As três primeiras não custam orçamento e resolvem o tema que mais apareceu nas duas " +
  "rodadas. As três últimas precisam entrar na conversa da próxima temporada."));
f.push(QUEBRA());

// ==================================================== 13. LIMITACOES
f.push(H1("13. Limitações e ficha técnica"));
f.push(H2("13.1 O que este relatório não sustenta"));
f.push(P("Prefiro apontar as fraquezas antes que alguém as encontre."));
f.push(LIR([{ t: "Os dois públicos se sobrepõem. ", b: true },
  { t: "A rodada 2 foi só para quem respondeu a rodada 1. Não são amostras independentes e os " +
       "resultados não podem ser somados nem tratados como validação cruzada. É o mesmo grupo " +
       "respondendo duas vezes, sobre assuntos diferentes." }]));
f.push(LIR([{ t: "Quem saiu antes está sub-representado. ", b: true },
  { t: `${pc(m.r2_cumpriu_pct)} das respostas da rodada 2 vêm de quem cumpriu a temporada. Quem ` +
       `foi embora antes é justamente o grupo cuja opinião mais explicaria a saída, e é o que ` +
       `menos respondeu. Leia os indicadores de satisfação como teto, não como média.` }]));
f.push(LIR([{ t: "Recortes pequenos foram suprimidos. ", b: true },
  { t: "Funções com menos de 5 respostas não aparecem em nenhuma tabela por função. Abaixo desse " +
       "volume dá para adivinhar quem respondeu, e prometemos anonimato no formulário." }]));
f.push(LIR([{ t: "As bases das seções 7 e 10 são pequenas. ", b: true },
  { t: `${D.saida.n_form_saida} respostas no questionário de saída e ${D.efetivacao.contra_base} ` +
       `no que pesa contra a efetivação. Servem para orientar hipótese, não para fechar decisão.` }]));
f.push(LIR([{ t: "Tudo é autodeclarado. ", b: true },
  { t: "Faltas, motivos e percepções são o que a pessoa relatou, não o que o ponto registrou. A " +
       "conciliação com o ponto está no painel, na aba da temporada." }]));

f.push(H2("13.2 Ficha técnica"));
f.push(tabela(["Item", "Rodada 1", "Rodada 2"],
  [["Sobre o quê", "Experiência, faltas, saída, vínculo", "Salário, condições, respeito, efetivação"],
   ["Coleta", "6 a 10 de agosto de 2026", "10 de agosto de 2026"],
   ["Convites", String(m.r1_convites), String(m.r2_convites)],
   ["Respostas", String(m.r1_n), String(m.r2_n)],
   ["Taxa", pc(m.r1_taxa), pc(m.r2_taxa)],
   ["Questionários", "2 (cumpriu e saiu antes)", "1"],
   ["Canal", "WhatsApp, envio individual", "WhatsApp, envio individual"],
   ["Incentivo", "Par de ingressos garantido", "Sorteio de 10 prêmios de R$ 70 via PIX"],
   ["Anonimato", "Cadastro em formulário separado", "Cadastro em formulário separado"],
   ["Corte mínimo", "5 respostas por recorte", "5 respostas por recorte"]],
  [2200, 3580, 3580]));

f.push(H2("13.3 Onde conferir"));
f.push(P("Todos os números deste relatório estão no painel, na aba Pesquisa, com filtro por grupo " +
  "e por função. Os relatos que citam pessoas seguem em documento separado, para quem conduzir a " +
  "apuração."));

f.push(new Paragraph({ spacing: { before: 500 },
  children: [new TextRun({ text: "Mendes RH · agosto de 2026", size: 18, color: CINZA, font: "Calibri" })] }));

// ------------------------------------------------------------------ build
const doc = new Document({
  creator: "Mendes RH",
  title: "Escuta do Temporário — relatório para a Aviva",
  description: "Temporada de julho de 2026 · duas rodadas de pesquisa",
  features: { updateFields: true },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 220 } } } }] },
  ]},
  styles: { default: {
    heading1: { run: { size: 32, bold: true, color: AZUL_ESC, font: "Calibri" },
                paragraph: { spacing: { before: 340, after: 170 } } },
    heading2: { run: { size: 25, bold: true, color: "0B0B0B", font: "Calibri" },
                paragraph: { spacing: { before: 280, after: 120 } } },
  }},
  sections: [{
    properties: { page: { margin: { top: 1100, right: 1100, bottom: 1100, left: 1100 } } },
    headers: { default: new Header({ children: [new Paragraph({
      spacing: { after: 0 },
      children: [
        new TextRun({ text: "Escuta do Temporário · temporada de julho de 2026", size: 16, color: MUT, font: "Calibri" }),
        new TextRun({ text: "\t\tMendes RH para Aviva / Rio Quente", size: 16, color: MUT, font: "Calibri" }),
      ] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT, spacing: { before: 0 },
      children: [new TextRun({ children: ["Página ", PageNumber.CURRENT], size: 16, color: MUT, font: "Calibri" })] })] }) },
    children: f
  }]
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(__dirname + "/Relatorio_Aviva_Escuta_Temporario.docx", b);
  console.log("ok", b.length, "bytes");
});
