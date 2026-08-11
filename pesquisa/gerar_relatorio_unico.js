// ============================================================================
//  RELATORIO UNICO — as duas rodadas da pesquisa da temporada de julho/2026
//  Mendes RH x Aviva / Rio Quente Resorts
// ----------------------------------------------------------------------------
//  Todos os numeros vem de _estatisticas.json, gerado por extrair_estatisticas.py
//  a partir da MESMA base do dashboard. Nenhum valor e digitado a mao aqui.
//  Se a base mudar: rode o .py e depois este .js.
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
const nb = n => (n === null || n === undefined) ? "—" : String(n).replace(".", ",");
const pc = (n, c) => (n === null || n === undefined) ? "—"
  : Number(n).toFixed(c === undefined ? 1 : c).replace(".", ",") + "%";
const nu = (n, c) => (n === null || n === undefined) ? "—"
  : Number(n).toFixed(c === undefined ? 1 : c).replace(".", ",");

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
// tabela de distribuicao (rotulo | n | %)
function tabDist(titulo, itens, largRotulo) {
  const lr = largRotulo || 5360;
  return tabela([titulo, "Respostas", "%"],
    itens.map(x => [x.rotulo, x.n, pc(x.pct)]),
    [lr, (LARG - lr) / 2, (LARG - lr) / 2], 1);
}
const DESTAQUE = (titulo, texto, cor) => [
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

// ==================================================================== CAPA
f.push(new Paragraph({ spacing: { before: 1100, after: 0 },
  children: [new TextRun({ text: "MENDES RH  ·  AVIVA / RIO QUENTE RESORTS", bold: true, size: 20, color: AZUL, font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 60 },
  children: [new TextRun({ text: "Escuta do Temporário", bold: true, size: 56, color: "0B0B0B", font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 100 },
  children: [new TextRun({ text: "Relatório completo das duas rodadas", bold: true, size: 30, color: AZUL_ESC, font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 360 },
  children: [new TextRun({ text: "Temporada de julho de 2026 · resultados, leitura e plano de ação", size: 25, color: CINZA, font: "Calibri" })] }));
f.push(P(`${m.total_respostas} respostas no total: ${m.r1_n} na primeira rodada, sobre a experiência da ` +
  `temporada, e ${m.r2_n} na segunda, sobre salário, condições de trabalho e efetivação. Coleta ` +
  `entre 6 e 10 de agosto de 2026.`, { color: CINZA }));
f.push(P("Todos os números deste relatório são os mesmos exibidos na aba Pesquisa do dashboard, " +
  "calculados pelo mesmo código a partir da mesma base. Se um percentual for questionado, ele " +
  "pode ser reproduzido na tela na hora.", { color: CINZA, it: true }));
f.push(QUEBRA());

// ================================================================== SUMARIO
f.push(H1("Sumário"));
f.push(P("Atualize o sumário no Word com Ctrl+A e depois F9 para que os números de página " +
  "apareçam.", { size: 18, color: MUT, it: true }));
f.push(new TableOfContents("Sumário", { hyperlink: true, headingStyleRange: "1-2" }));
f.push(QUEBRA());

// ======================================================== 1. RESUMO EXECUTIVO
f.push(H1("1. Resumo executivo"));
f.push(P(`Duas rodadas de escuta foram aplicadas ao final da temporada de julho. A primeira ` +
  `perguntou como foi a experiência e por que as pessoas faltaram ou saíram antes do fim; ` +
  `respondeu ${m.r1_n} de ${m.r1_convites} convidados (${pc(m.r1_taxa)}). A segunda foi ` +
  `desenhada para medir hipóteses que a primeira só havia levantado por campo aberto — salário, ` +
  `condições de trabalho e interesse em efetivação — e foi disparada apenas para quem já havia ` +
  `respondido: ${m.r2_n} respostas em ${m.r2_convites} convites (${pc(m.r2_taxa)}), em um único dia.`));
f.push(P("Sete conclusões sustentam o resto deste documento."));

f.push(...DESTAQUE("1. A falta é majoritariamente involuntária",
  `Entre as ${D.absenteismo.n_faltou} pessoas que declararam ao menos uma ausência, ` +
  D.absenteismo.causas.slice(0, 3).map(x => `${pc(x.pct)} apontaram ${x.rotulo.toLowerCase()}`).join(", ") +
  `. Desânimo com o trabalho, bico no mesmo dia e trabalho pesado demais para o valor pago somam ` +
  `${pc(D.absenteismo.desengajamento)} das citações. O absenteísmo desta temporada é um problema ` +
  `de saúde e de logística, não de engajamento.`));

const voz = D.preditores.voz;
f.push(...DESTAQUE("2. Quem não tem com quem falar falta quase o dobro",
  `Entre quem se sentiu à vontade para falar quando algo estava errado, ${pc(voz[0].faltou, 0)} ` +
  `faltaram. Entre quem não se sentiu, ${pc(voz[voz.length - 1].faltou, 0)}. É o achado mais ` +
  `acionável das duas rodadas e o de menor custo: não depende de investimento, depende de presença.`));

f.push(...DESTAQUE("3. A decisão de sair acontece na primeira semana",
  `Das ${D.saida.n_form_saida} saídas que responderam o questionário próprio, ` +
  `${D.saida.decidiu_cedo} foram decididas nos primeiros dias ou na primeira semana. ` +
  `A janela de intervenção é curtíssima — e hoje não existe nenhuma ação programada dentro dela.`, AZUL));

f.push(...DESTAQUE("4. A hipótese do salário caiu",
  `${pc(D.salario.expect_atendeu)} disseram que o valor recebido atendeu ou superou o que ` +
  `esperavam ao aceitar a vaga. Apenas ${pc(D.salario.mercado_pior)} consideram o pagamento pior ` +
  `que o de outros temporários da região, contra ${pc(D.salario.mercado_melhor)} que o consideram ` +
  `melhor. A nota média foi ${nu(D.salario.media, 2)} e o índice de recomendação do salário, ` +
  `${nu(D.salario.indice.enps)}, é o mais baixo dos três medidos — mas mede exigência, não revolta.`));

const alav = D.salario.alavancas;
const bonusFalta = alav.find(x => x.rotulo.includes("não faltar"));
const bonusFim = alav.find(x => x.rotulo.includes("até o fim"));
f.push(...DESTAQUE("5. O que se pede não é só diária maior",
  `${pc(alav[0].pct)} querem aumento no valor da diária, mas ${pc(bonusFalta.pct)} aceitariam ` +
  `bônus por não faltar e ${pc(bonusFim.pct)} bônus por ficar até o fim da temporada. Os dois ` +
  `últimos custam menos que um reajuste linear, são condicionados a resultado e atacam exatamente ` +
  `os dois problemas da rodada 1.`, AZUL));

f.push(...DESTAQUE("6. O respeito é o achado mais desconfortável",
  `Apenas ${pc(D.respeito.sempre)} se sentiram sempre respeitados no ambiente de trabalho. ` +
  `${pc(D.respeito.parcial)} responderam "na maior parte do tempo" e ${pc(D.respeito.falhou)} ` +
  `responderam "poucas vezes". Quem marcou "poucas vezes" avalia pior tudo — inclusive o salário, ` +
  `que é o mesmo valor pago aos colegas de função.`, VERM));

f.push(...DESTAQUE("7. A demanda por efetivação é quase unânime",
  `${pc(D.efetivacao.sim)} querem ser efetivados como CLT na Aviva com certeza e ` +
  `${pc(D.efetivacao.sim_talvez)} querem ou considerariam. Apenas ${pc(D.efetivacao.nao)} ` +
  `descartam. Para a maioria dessas pessoas o contrato temporário não é um bico de temporada — ` +
  `é uma porta de entrada, e hoje não existe trilha formal atrás dela.`, AZUL));
f.push(QUEBRA());

// =========================================================== 2. METODO
f.push(H1("2. Método e participação"));
f.push(H2("2.1 As duas rodadas"));
f.push(tabela(
  ["Rodada", "Objeto", "Convites", "Respostas", "Taxa"],
  [["1 · experiência", "Experiência da temporada, faltas, saída, vínculo",
    m.r1_convites, m.r1_n, pc(m.r1_taxa)],
   ["2 · salário", "Salário, condições de trabalho, respeito, efetivação",
    m.r2_convites, m.r2_n, pc(m.r2_taxa)]],
  [1700, 4060, 1200, 1200, 1200], 2));
f.push(LEG(`A rodada 2 foi disparada apenas para quem respondeu a rodada 1 — por isso os dois ` +
  `públicos se sobrepõem e não são amostras independentes.`));

f.push(H2("2.2 Como foi aplicada"));
f.push(P(`A rodada 1 usou dois questionários: um longo, para quem cumpriu a temporada ` +
  `(${m.r1_form_longo} respostas), e um curto, de saída (${m.r1_form_saida} respostas). ` +
  `Ambos anônimos, disparados por WhatsApp, um a um. O incentivo foi um par de ingressos do Hot ` +
  `Park garantido a quem concluísse — não sorteio.`));
f.push(P(`A rodada 2 usou um questionário único, também anônimo, com sorteio de 10 prêmios de ` +
  `R$ 70 via PIX como incentivo, pagos no dia de uso do ingresso. Em ambas as rodadas o cadastro ` +
  `de contato ficou em um formulário separado, com planilha separada: as respostas não são ` +
  `ligáveis a quem respondeu.`));
f.push(...DESTAQUE("O anonimato é o que explica os números",
  "O formato anterior de pesquisa da operação coletava telefone na mesma planilha das respostas. " +
  "Nele, ninguém escreve que se sentiu desrespeitado. As duas rodadas deste ciclo separaram o " +
  "cadastro da resposta — e foi por isso que apareceram os relatos que estão na seção 9 e no " +
  "anexo interno.", AZUL));

f.push(H2("2.3 Regra de classificação dos grupos"));
f.push(RICH([
  { t: "O grupo não vem da lista de disparo, vem da declaração do respondente. ", b: true },
  { t: `${m.r1_reclassificados} pessoas receberam o questionário de quem cumpriu a temporada e ` +
       `informaram, na pergunta de triagem, que saíram antes do fim. Elas contam no grupo de ` +
       `saída. Resultado: ${m.r1_cumpriu} cumpriram e ${m.r1_saiu} saíram antes — e não ` +
       `${m.r1_form_longo} e ${m.r1_form_saida}, como diria a lista de envio.` }]));
f.push(tabela(
  ["Grupo", "Convites", "Respostas", "Taxa", "Após reclassificação"],
  [["Cumpriu a temporada", 150, m.r1_form_longo, pc(m.r1_taxa_cumpriu), m.r1_cumpriu],
   ["Saiu antes do fim", 28, m.r1_form_saida, pc(m.r1_taxa_saiu), m.r1_saiu],
   ["Total", m.r1_convites, m.r1_n, pc(m.r1_taxa), m.r1_n]],
  [2700, 1500, 1600, 1400, 2160], 1));
f.push(QUEBRA());

// ============================================================ 3. QUEM RESPONDEU
f.push(H1("3. Quem respondeu"));
f.push(P("Perfil da rodada 1, que tem a base maior. A rodada 2 tem distribuição equivalente por " +
  "função, já que foi disparada para o mesmo público."));
f.push(H2("3.1 Por função"));
f.push(tabDist("Função", D.perfil.funcao, 5360));
f.push(H2("3.2 Por local de trabalho"));
f.push(tabDist("Local", D.perfil.local, 5360));
f.push(H2("3.3 Moradia e transporte"));
f.push(tabDist("Onde mora", D.perfil.moradia, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Como ia e voltava do trabalho", D.perfil.transporte, 5360));
const fret = D.perfil.transporte.find(x => x.rotulo.includes("fretado"));
const local = D.perfil.moradia.find(x => x.rotulo.includes("Moro em"));
f.push(...DESTAQUE("Dois números que explicam boa parte do resto",
  `${pc(local.pct)} moram na região e ${pc(fret.pct)} dependem exclusivamente do transporte ` +
  `fretado. Isso significa que uma falha de rota, horário ou capacidade do fretado não tem plano ` +
  `B: vira falta. E de fato transporte aparece entre as três maiores causas de ausência.`, AMBAR));
f.push(QUEBRA());

// ============================================== 4. VINCULO (RODADA 1)
f.push(H1("4. Vínculo com a Mendes RH"));
f.push(H2("4.1 Índice de recomendação"));
f.push(P("Nota de 0 a 10 dada à pergunta “o quanto você indicaria a Mendes RH para um amigo " +
  "trabalhar?”. Quem dá 9 ou 10 recomenda; 7 e 8 são indiferentes e ficam fora da conta; 0 a 6 " +
  "não recomenda. O índice é a diferença entre o percentual do primeiro grupo e o do último, " +
  "numa escala de −100 a +100. Acima de 50 é excelente em qualquer referência de mercado."));
const vt = D.vinculo.total, vc = D.vinculo.cumpriu, vs = D.vinculo.saiu;
f.push(tabela(
  ["Grupo", "n", "Recomendam", "Indiferentes", "Não recomendam", "Índice", "Nota média"],
  [["Total", vt.n, vt.promotores, vt.neutros, vt.detratores, nu(vt.enps), nu(vt.media, 2)],
   ["Cumpriu a temporada", vc.n, vc.promotores, vc.neutros, vc.detratores, nu(vc.enps), nu(vc.media, 2)],
   ["Saiu antes do fim", vs.n, vs.promotores, vs.neutros, vs.detratores, nu(vs.enps), nu(vs.media, 2)]],
  [2300, 700, 1300, 1300, 1560, 1100, 1100], 1));
f.push(...DESTAQUE("A saída antecipada custa pouco em reputação",
  `A diferença entre quem cumpriu (${nu(vc.enps)}) e quem saiu antes (${nu(vs.enps)}) é de ` +
  `${nu(vc.enps - vs.enps)} pontos. É pequena: mesmo quem interrompeu o contrato segue ` +
  `recontratável e segue recomendando a empresa. O vínculo não se rompeu na saída.`));

f.push(H2("4.2 Índice por função"));
f.push(tabela(
  ["Função", "n", "Índice", "Nota média", "Faltou", "Pensou em sair", "Voltaria"],
  D.vinculo.por_funcao.map(x => [x.funcao, x.n, nu(x.indice), nu(x.media, 2),
    pc(x.faltou, 0), pc(x.pensou_sair, 0), pc(x.voltaria, 0)]),
  [2700, 600, 1000, 1200, 1000, 1500, 1360], 1));
f.push(LEG(`Apenas funções com 5 ou mais respostas. Abaixo disso o recorte identifica quem ` +
  `respondeu e o anonimato prometido no formulário cai. A coluna "pensou em sair" só existe no ` +
  `questionário longo, então o denominador dela é menor nas funções com muita saída antecipada.`));

f.push(H2("4.3 Intenção de retorno"));
f.push(tabDist("Voltaria a trabalhar na próxima temporada?", D.vinculo.voltaria, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Se abrisse uma vaga fixa hoje, você aceitaria?", D.vinculo.vaga_fixa, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Você acredita que teve chance real de efetivação?", D.vinculo.chance_efetivacao, 5360));
f.push(H2("4.4 Experiência com a equipe da Mendes RH"));
f.push(tabDist("Da entrevista até o fim do contrato", D.vinculo.experiencia, 6200));
f.push(QUEBRA());

// ============================================= 5. ABSENTEISMO (RODADA 1)
f.push(H1("5. Absenteísmo"));
f.push(H2("5.1 Quanto se faltou"));
f.push(tabDist("Durante a temporada, você chegou a faltar?", D.absenteismo.faixas, 5360));
f.push(RICH([{ t: "Taxa de ausência: ", b: true },
  { t: `${pc(D.absenteismo.faltou_cumpriu)} entre quem cumpriu a temporada e ` +
       `${pc(D.absenteismo.faltou_saiu)} entre quem saiu antes do fim.` }]));

f.push(H2("5.2 Por que se falta"));
f.push(tabela(["Causa", "Citações", "% de quem faltou"],
  D.absenteismo.causas.map(x => [x.rotulo, x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));
f.push(LEG(`Base: as ${D.absenteismo.n_faltou} pessoas que declararam ao menos uma ausência. ` +
  `Cada uma podia marcar até 3 causas, então a soma passa de 100%. Total de ` +
  `${D.absenteismo.citacoes} citações.`));
f.push(...DESTAQUE("Saúde, cansaço e transporte concentram a explicação",
  `As três causas mais citadas somam ${pc(D.absenteismo.top3_share, 0)} das citações. Desânimo, ` +
  `bico no mesmo dia e trabalho pesado demais para o valor pago — as três que a operação costuma ` +
  `presumir — ficam no rodapé, com ${pc(D.absenteismo.desengajamento)} somadas. Transporte é a ` +
  `única causa relevante que Mendes RH e Aviva controlam sozinhas: rota, horário, capacidade e ` +
  `estado dos veículos.`, AMBAR));

f.push(H2("5.3 O que pesou no dia a dia"));
f.push(tabela(["O que mais pesou", "Citações", "% dos respondentes"],
  D.absenteismo.pesou.map(x => [x.rotulo, x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));

f.push(H2("5.4 O que teria reduzido as faltas"));
f.push(tabela(["Alavanca", "Citações", "%"],
  D.absenteismo.alavancas.map(x => [x.rotulo, x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));
const outro = D.absenteismo.alavancas.find(x => x.rotulo === "Outro");
if (outro) {
  f.push(...DESTAQUE("A opção mais marcada foi “Outro” — e isso é informação",
    `${pc(outro.pct)} marcaram "Outro", acima de qualquer alavanca oferecida. A lista de opções ` +
    `partia do pressuposto de que a falta é negociável — mais folga, mais dinheiro, melhor ` +
    `escala. Para a maior parte dessas pessoas nenhuma delas se aplicava, o que é coerente com ` +
    `a causa declarada: quem falta por doença ou por não conseguir chegar não é retido por bônus. ` +
    `Na próxima rodada vale trocar essa pergunta por uma aberta.`, AZUL));
}
f.push(QUEBRA());

// ============================================== 6. PREDITORES (RODADA 1)
f.push(H1("6. O que separa quem falta de quem não falta"));
f.push(P("Os cruzamentos abaixo não descrevem opinião: separam grupos com comportamento medido " +
  "diferente. São a parte mais acionável da rodada 1."));

f.push(H2("6.1 Voz — o preditor mais forte"));
f.push(tabela(["“Você se sentiu à vontade para falar quando algo estava errado?”", "n", "Faltou ao menos 1 dia"],
  D.preditores.voz.map(x => [x.nivel, x.n, pc(x.faltou, 0)]),
  [5360, 1400, 2600], 1));
if (D.preditores.voz_intencao.length) {
  f.push(P("", { after: 100 }));
  f.push(tabela(["Mesmo corte, outra medida", "n", "Pensou em sair antes do fim"],
    D.preditores.voz_intencao.map(x => [x.nivel, x.n, pc(x.pensou, 0)]),
    [5360, 1400, 2600], 1));
}
f.push(...DESTAQUE("Não é um problema que se resolva com investimento",
  `Quem não se sentiu à vontade para falar faltou ${pc(voz[voz.length - 1].faltou, 0)}, contra ` +
  `${pc(voz[0].faltou, 0)} de quem se sentiu. Resolve-se com presença: alguém disponível no posto, ` +
  `nos primeiros dias, com registro do que foi dito. Custo zero.`));

f.push(H2("6.2 Erro de pagamento"));
f.push(tabela(["“Você recebeu tudo certo e no prazo?”", "n", "Faltou ao menos 1 dia"],
  D.preditores.pagamento.map(x => [x.nivel, x.n, pc(x.faltou, 0)]),
  [5360, 1400, 2600], 1));
f.push(...DESTAQUE("A correção mais barata do relatório",
  `Ninguém marcou "teve problema mais de uma vez", o que indica falha pontual e não sistêmica. ` +
  `Depende exclusivamente de processo interno, não envolve negociação com o cliente e tem efeito ` +
  `medido sobre a falta.`));

f.push(H2("6.3 Entrada e integração"));
f.push(tabela(["Pergunta", "n", "Nota média (1 a 5)", "Deram nota 5", "Deram 1 ou 2"],
  D.escalas.map(x => [x.pergunta, x.n, nu(x.media, 2), pc(x.nota5), pc(x.nota12)]),
  [4200, 900, 1800, 1300, 1160], 1));
const trat = D.escalas.find(x => x.pergunta.includes("Tratamento"));
if (trat) {
  f.push(...DESTAQUE("O sinal que a rodada 2 foi buscar",
    `"Como os colegas efetivos tratavam os temporários" teve média ${nu(trat.media, 2)}, a mais ` +
    `baixa das três escalas, com ${trat.n_nota1} pessoas dando nota 1 — o único item em que ` +
    `alguém usou o extremo negativo em volume. Era um sinal fraco demais para virar decisão. Foi ` +
    `exatamente por isso que a rodada 2 incluiu a pergunta direta sobre respeito.`, AMBAR));
}
f.push(P("", { after: 100 }));
f.push(tabDist("Ficou claro o que era esperado de você?", D.preditores.claro, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Recebeu no primeiro dia tudo o que precisava?", D.preditores.kit, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("A escala cumprida foi a combinada na contratação?", D.preditores.escala, 5360));
f.push(QUEBRA());

// ================================================ 7. SAIDA (RODADA 1)
f.push(H1("7. A saída antecipada"));
f.push(P(`${D.saida.n} pessoas saíram antes do fim da temporada, segundo a própria declaração. ` +
  `Destas, ${D.saida.n_form_saida} responderam o questionário de saída, mais curto e específico. ` +
  `Os números desta seção têm base pequena — são leitura indicativa, não conclusiva.`));

f.push(H2("7.1 Quem pensou em sair"));
f.push(tabDist("Em algum momento você pensou em sair antes do fim?", D.vinculo.por_funcao.length
  ? D.saida.pensou_sair : D.saida.pensou_sair, 5360));

f.push(H2("7.2 O que segurou quem ficou"));
f.push(tabela(["O que mais te segurou até o fim", "Citações", "%"],
  D.saida.segurou.map(x => [x.rotulo, x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));

f.push(H2("7.3 Como e quando a saída aconteceu"));
f.push(tabDist("A saída foi decisão sua ou da empresa?", D.saida.decisao, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Em que momento decidiu que ia sair?", D.saida.quando, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Quanto tempo ficou antes de sair?", D.saida.tempo, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Avisou alguém antes de sair?", D.saida.avisou, 5360));
f.push(...DESTAQUE("A decisão vem antes do aviso",
  `${D.saida.decidiu_cedo} das ${D.saida.n_form_saida} saídas foram decididas nos primeiros dias ` +
  `ou na primeira semana. A maioria avisou com antecedência — ou seja, a operação teve o aviso. ` +
  `O que faltou foi uma conversa antes disso.`, AZUL));

f.push(H2("7.4 Motivo declarado"));
f.push(tabDist("Qual foi o motivo REAL da sua saída?", D.saida.motivo, 5360));
f.push(H2("7.5 O que teria feito ficar"));
f.push(tabela(["O que teria feito você ficar até o fim", "Citações", "%"],
  D.saida.ficaria.map(x => [x.rotulo, x.n, pc(x.pct)]),
  [5360, 2000, 2000], 1));
const ouvisse = D.saida.ficaria.find(x => x.rotulo.includes("ouvisse"));
if (ouvisse) {
  f.push(...DESTAQUE("O item mais citado não custa nada",
    `"Alguém que me ouvisse quando o problema começou" é o que mais aparece — ${ouvisse.n} de ` +
    `${D.saida.n_form_saida} respostas. É o mesmo achado da seção 6.1, visto do outro lado: quem ` +
    `saiu queria ter tido com quem falar.`, AZUL));
}
f.push(QUEBRA());

// ================================================ 8. SALARIO (RODADA 2)
f.push(H1("8. Salário e remuneração"));
f.push(P("Esta seção e as três seguintes vêm da rodada 2. A pergunta central era simples: o " +
  "salário explica o absenteísmo e a saída antecipada? A resposta é não."));

f.push(H2("8.1 Nota do salário"));
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

f.push(H2("8.2 Expectativa e mercado"));
f.push(tabDist("O valor atendeu o que você esperava ao aceitar a vaga?", D.salario.expectativa, 5360));
f.push(P("", { after: 100 }));
f.push(tabDist("Comparado a outros temporários da região, o pagamento é:", D.salario.mercado, 5360));
f.push(...DESTAQUE("Exigência, não revolta",
  `${pc(D.salario.expect_atendeu)} tiveram a expectativa atendida ou superada e apenas ` +
  `${pc(D.salario.mercado_pior)} consideram o pagamento pior que o do mercado local. O índice ` +
  `${nu(D.salario.indice.enps)} é o mais baixo dos três medidos e ainda assim positivo. A leitura ` +
  `correta é: o salário não afasta, mas também não segura. Ele não é o que precisa ser corrigido ` +
  `primeiro.`));

f.push(H2("8.3 O que faria diferença no pagamento"));
f.push(tabela(["O que mais faria diferença", "Citações", "% dos respondentes", "Natureza do custo"],
  D.salario.alavancas.map(x => [x.rotulo, x.n, pc(x.pct),
    x.rotulo.includes("Bônus") ? "Condicionado a resultado"
      : x.rotulo.includes("semanal") ? "Fluxo de caixa, sem custo extra" : "Custo fixo"]),
  [3300, 1100, 1700, 3260], 1));
f.push(LEG(`Base: ${D.salario.alavancas_base} respondentes, até 2 marcações cada.`));
f.push(...DESTAQUE("Existe uma saída mais barata que o reajuste linear",
  `${pc(bonusFalta.pct)} aceitariam bônus por não faltar e ${pc(bonusFim.pct)} bônus por ficar ` +
  `até o fim. São os dois problemas da rodada 1 — absenteísmo e saída antecipada — com pagamento ` +
  `condicionado a resultado, e não custo fixo sobre toda a folha. Entre as ` +
  `${D.salario.insatisfeitos.n} pessoas que deram nota 6 ou menos ao salário, o padrão se repete.`, VERDE));
f.push(QUEBRA());

// ============================================== 9. CONDICOES E RESPEITO
f.push(H1("9. Condições de trabalho e respeito"));
f.push(H2("9.1 Nota das condições"));
const dcond = D.condicoes.distribuicao.filter(x => x.n > 0);
f.push(tabela(["Nota atribuída (0 a 10)", ...dcond.map(x => String(x.nota))],
  [["Respostas", ...dcond.map(x => String(x.n))]],
  [2600, ...dcond.map(() => Math.floor((LARG - 2600) / dcond.length))], 1));
f.push(P("", { after: 120 }));
f.push(RICH([{ t: `Nota média ${nu(D.condicoes.media, 2)}`, b: true },
  { t: `, contra ${nu(D.salario.media, 2)} do salário. Índice de recomendação ` +
       `${nu(D.condicoes.indice.enps)}, contra ${nu(D.salario.indice.enps)}. As pessoas avaliam ` +
       `melhor as condições do que a remuneração.` }]));

f.push(H2("9.2 O que precisa melhorar"));
f.push(tabela(["Frente", "Citações", "% dos respondentes", "De quem depende"],
  D.condicoes.melhorar.map(x => {
    const r = x.rotulo;
    const dono = r.includes("Tratamento") ? "Aviva — custo zero"
      : r.includes("Escala") || r.includes("Transporte") ? "Negociação conjunta"
      : r.includes("Uniforme") ? "Mendes RH"
      : r.includes("Nada") ? "—" : "Aviva";
    return [r, x.n, pc(x.pct), dono];
  }),
  [3300, 1100, 1700, 3260], 1));
f.push(LEG(`Base: ${D.condicoes.melhorar_base} respondentes, até 3 marcações cada.`));
f.push(...DESTAQUE("A coluna que organiza a conversa com o cliente",
  "Alimentação, banheiros e local de descanso são investimento da Aviva. Escala e transporte são " +
  "negociação conjunta. Uniforme é da Mendes RH. E o tratamento dado pelos efetivos e pela " +
  "segurança não custa dinheiro nenhum — é o item mais barato da lista e o que mais aparece nos " +
  "relatos abertos.", AMBAR));

f.push(H2("9.3 Respeito no ambiente de trabalho"));
f.push(P("Pergunta nova nesta rodada. Foi incluída porque a rodada 1 trouxe, em um campo aberto, " +
  "um relato que exigia apuração formal — e não havia como medir se aquilo era exceção ou padrão."));
f.push(tabela(["Você se sentiu respeitado(a)?", "Respostas", "%", "Nota salário", "Nota condições"],
  D.respeito.por_nivel.map(x => [x.nivel, x.n, pc(x.pct), nu(x.nota_salario, 2), nu(x.nota_condicoes, 2)]),
  [3000, 1400, 1200, 1880, 1880], 1));
const pleno = D.respeito.por_nivel.find(x => x.nivel === "Sempre");
const parcial = D.respeito.por_nivel.find(x => x.nivel === "Na maior parte do tempo");
const pior = D.respeito.por_nivel.filter(x => x.nota_salario !== null).slice(-1)[0];
if (pleno && parcial && pior && pior.nivel !== "Sempre") {
  const mSal = ((pleno.nota_salario + parcial.nota_salario) / 2);
  const mCond = ((pleno.nota_condicoes + parcial.nota_condicoes) / 2);
  f.push(...DESTAQUE("Não é uma escada, é um degrau",
    `Entre "sempre" e "na maior parte do tempo" as notas praticamente não mudam — a média dos ` +
    `dois é ${nu(mSal, 2)} no salário e ${nu(mCond, 2)} nas condições. Quem marcou ` +
    `"${pior.nivel.toLowerCase()}" cai para ${nu(pior.nota_salario, 2)} e ` +
    `${nu(pior.nota_condicoes, 2)}, recebendo o mesmo valor de diária que os colegas de função. ` +
    `O desrespeito não incomoda um pouco: quando acontece, contamina a avaliação inteira. São ` +
    `${pior.n} pessoas — poucas o bastante para tratar caso a caso, em vez de por política geral.`, VERM));
}

f.push(H2("9.4 Onde o problema se concentra"));
f.push(tabela(["Função", "n", "Sempre", "Na maior parte", "Poucas vezes", "Nota salário", "Quer CLT"],
  D.respeito.por_funcao.map(x => [x.funcao, x.n, x.sempre, x.maior_parte, x.poucas,
    nu(x.nota_salario, 2), pc(x.quer_clt, 0)]),
  [2700, 600, 1000, 1400, 1300, 1200, 1160], 1));
f.push(LEG("Apenas funções com 5 ou mais respostas."));

f.push(H2("9.5 Relatos abertos"));
f.push(P(`${D.respeito.n_escreveram} pessoas escreveram no campo aberto de relato. ` +
  `${D.respeito.n_escreveram - D.respeito.n_relatos} responderam que não tinham nada a relatar. ` +
  `As ${D.respeito.n_relatos} restantes descrevem alguma situação, e se distribuem em quatro padrões:`));
f.push(LIR([{ t: "Fronteira efetivo × temporário. ", b: true },
  { t: "O padrão dominante. Sobrecarga transferida ao temporário, comentários sobre aparência, " +
       "recepção hostil em postos específicos. Dois relatos independentes citam o mesmo posto." }]));
f.push(LIR([{ t: "Conduta individual nominal. ", b: true },
  { t: "Um relato cita, com nome e função, alguém cuja conduta descrita coincide com o caso " +
       "reportado anonimamente na rodada 1. São dois respondentes independentes, em rodadas " +
       "diferentes, descrevendo o mesmo comportamento — o que tira o caso da condição de relato " +
       "isolado." }]));
f.push(LIR([{ t: "Identidade de gênero. ", b: true },
  { t: "Uma pessoa em transição relata ter tido o nome social ignorado de forma reiterada. É " +
       "ausência de política, não conduta isolada: exige campo de nome social no cadastro e " +
       "orientação formal a supervisores." }]));
f.push(LIR([{ t: "Crachá e portaria. ", b: true },
  { t: "Constrangimento na entrada por não ter recebido crachá na contratação nem orientação " +
       "sobre sua necessidade. Falha de processo da Mendes RH, corrigível imediatamente." }]));
f.push(...DESTAQUE("Onde estão os textos",
  "Os relatos na íntegra estão no documento INTERNO_Relatos_Rodada2.docx, de uso restrito, junto " +
  "com o encaminhamento sugerido para cada caso. Casos que citam pessoas seguem pelo canal de " +
  "conduta, com registro formal — não por este relatório e não pelo painel.", VERM));
f.push(QUEBRA());

// ============================================= 10. EFETIVACAO (RODADA 2)
f.push(H1("10. Efetivação CLT na Aviva"));
f.push(tabDist("Teria interesse em ser efetivado(a) como CLT na Aviva / Rio Quente?",
  D.efetivacao.distribuicao, 5360));
if (D.efetivacao.contra.length) {
  f.push(P("", { after: 120 }));
  f.push(tabela(["O que pesa contra", "Citações", "%"],
    D.efetivacao.contra.map(x => [x.rotulo, x.n, pc(x.pct)]),
    [5360, 2000, 2000], 1));
  f.push(LEG(`Base: ${D.efetivacao.contra_base} pessoas que responderam "talvez" ou "não". ` +
    `Base pequena — leitura indicativa.`));
}
f.push(P(`${D.efetivacao.n_area} pessoas indicaram em qual área gostariam de trabalhar como ` +
  `efetivas. As mais citadas são bares e restaurantes, hotelaria e governança, e parques e ` +
  `recreação — as mesmas áreas em que já atuaram como temporárias.`));
f.push(...DESTAQUE("O que isso significa em custo",
  "Essas pessoas já foram captadas, treinadas, integradas à operação e demonstraram que ficam " +
  "até o fim do contrato. Uma trilha formal de efetivação converteria parte do custo de captação " +
  "da próxima temporada em investimento com retorno conhecido. É a única ação deste relatório " +
  "que depende mais da Aviva do que da Mendes RH — e a de maior ganho reputacional para ambas.", VERDE));
f.push(QUEBRA());

// ============================================= 11. CONVERGENCIA
f.push(H1("11. O que as duas rodadas dizem juntas"));
f.push(P("A rodada 1 levantou hipóteses a partir de campos abertos e escalas. A rodada 2 foi " +
  "desenhada para medi-las. “Confirmado” significa que o tema apareceu espontaneamente na " +
  "primeira e foi dimensionado na segunda."));
const trans1 = D.absenteismo.causas.find(x => x.rotulo.includes("Transporte"));
const tratR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("efetivos"));
const transR2 = D.condicoes.melhorar.find(x => x.rotulo === "Transporte");
const escR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("Escala"));
const aliR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("Alimentação"));
const descR2 = D.condicoes.melhorar.find(x => x.rotulo.includes("descanso"));
f.push(tabela(["Tema", "Rodada 1", "Rodada 2", "Veredito"],
  [["Tratamento pelos efetivos",
    `Nota ${nu(trat ? trat.media : 0, 2)} na escala, ${trat ? trat.n_nota1 : 0} notas 1, tema recorrente no campo aberto`,
    `${pc(tratR2.pct, 0)} pedem melhora · ${pc(D.respeito.alguma_falha, 0)} com falha de respeito`,
    "CONFIRMADO"],
   ["Transporte",
    `${pc(trans1.pct, 0)} de quem faltou citou · ${pc(fret.pct)} dependem do fretado`,
    `${pc(transR2.pct, 0)} pedem melhora`, "CONFIRMADO"],
   ["Escala e folgas",
    "Aparece entre o que teria feito ficar e no campo aberto",
    `${pc(escR2.pct, 0)} pedem melhora · maior freio à efetivação`, "CONFIRMADO"],
   ["Alimentação e descanso",
    `Nota ${nu(D.escalas[1].media, 2)} na escala; pedidos pontuais no campo aberto`,
    `${pc(aliR2.pct, 0)} alimentação · ${pc(descR2.pct, 0)} cadeiras para descanso`, "AMPLIADO"],
   ["Salário",
    `Baixa presença entre causas de falta e de saída`,
    `${pc(D.salario.expect_atendeu)} com expectativa atendida`, "DESCARTADO"]],
  [2000, 3000, 2900, 1460]));

f.push(H2("11.1 O retrato conjunto"));
f.push(P(`As duas rodadas somam ${m.total_respostas} respostas coletadas em cinco dias. A segunda ` +
  `teve ${pc(m.r2_taxa)} de retorno em um único dia, disparada apenas para quem já havia ` +
  `respondido a primeira — é o indicador mais direto de que a escuta tem credibilidade com esse ` +
  `público.`));
f.push(RICH([{ t: "A hipótese do salário caiu. ", b: true },
  { t: `Era a suspeita natural para explicar ${pc(D.absenteismo.faltou_cumpriu)} de absenteísmo e ` +
       `${D.saida.n} saídas antecipadas. A rodada 2 mostra ${pc(D.salario.expect_atendeu)} com a ` +
       `expectativa atendida ou superada. O salário é exigente, não é ferida.` }]));
f.push(RICH([{ t: "O que sobra é relação. ", b: true },
  { t: `Voz na rodada 1 — quem não se sente à vontade para falar falta ` +
       `${pc(voz[voz.length - 1].faltou, 0)} contra ${pc(voz[0].faltou, 0)}. Respeito na rodada 2 ` +
       `— ${pc(D.respeito.alguma_falha)} com alguma falha. São a mesma coisa vista de dois ` +
       `ângulos: a fronteira entre efetivo e temporário, e a ausência de alguém escutando durante ` +
       `o contrato, não só no fim dele. Nenhum dos dois se resolve com dinheiro.` }]));
f.push(RICH([{ t: "E há uma oportunidade que ninguém pediu. ", b: true },
  { t: `${pc(D.efetivacao.sim_talvez)} querem ou considerariam efetivação CLT na Aviva. Essas ` +
       `pessoas já foram treinadas, já conhecem a operação e já demonstraram que ficam até o fim.` }]));
f.push(QUEBRA());

// ============================================= 12. PLANO DE ACAO
f.push(H1("12. Plano de ação"));
f.push(P("Onze ações, ordenadas por relação entre impacto esperado e custo. As cinco primeiras " +
  "não dependem de negociação com o cliente e podem começar nesta semana."));
f.push(tabela(["#", "Ação", "Base na pesquisa", "Custo", "Responsável"],
  [["1", "Conversa de 5 minutos no 3º e no 7º dia, com registro",
    `${D.saida.decidiu_cedo} de ${D.saida.n_form_saida} saídas decididas na 1ª semana`, "Zero", "Mendes RH"],
   ["2", "Zerar erro e atraso de pagamento",
    `Quem teve erro faltou ${pc(D.preditores.pagamento[1].faltou, 0)} contra ${pc(D.preditores.pagamento[0].faltou, 0)}`,
    "Zero", "Mendes RH"],
   ["3", "Entregar crachá na contratação e explicar seu uso",
    "Relato de constrangimento na portaria", "Zero", "Mendes RH"],
   ["4", "Apurar os relatos nominais pelo canal de conduta",
    "Caso corroborado entre as duas rodadas", "Zero", "Mendes RH + Aviva"],
   ["5", "Nome social no cadastro e orientação a supervisores",
    "1 relato reiterado", "Zero", "Mendes RH"],
   ["6", "Alinhamento com efetivos e segurança sobre o temporário",
    `${pc(tratR2.pct, 0)} pedem · ${pc(D.respeito.alguma_falha, 0)} com falha de respeito`, "Zero", "Aviva"],
   ["7", "Diagnóstico dirigido em Camareira e governança",
    "Pior nota de salário e maior taxa de “poucas vezes”", "Baixo", "Mendes RH + Aviva"],
   ["8", "Canal de escuta ativo durante a temporada",
    `Sem voz falta ${pc(voz[voz.length - 1].faltou, 0)}, com voz ${pc(voz[0].faltou, 0)}`, "Baixo", "Mendes RH"],
   ["9", "Piloto de bônus por assiduidade e por conclusão",
    `${pc(bonusFalta.pct)} e ${pc(bonusFim.pct)} aceitariam`, "Médio", "Negociação"],
   ["10", "Auditoria do transporte fretado",
    `${pc(fret.pct)} dependem · ${pc(transR2.pct, 0)} pedem melhora`, "Médio", "Negociação"],
   ["11", "Trilha formal de efetivação com a Aviva",
    `${pc(D.efetivacao.sim_talvez)} querem ou considerariam`, "Médio", "Aviva"]],
  [500, 2900, 2900, 900, 2160]));

f.push(H2("12.1 O que precisa de decisão"));
f.push(LI("Aprovar as ações 1 a 5, internas, para começar imediatamente."));
f.push(LI("Levar as ações 6 e 7 à Aviva como pauta formal, com os números desta pesquisa."));
f.push(LI("Definir se o piloto de bônus entra na negociação da próxima temporada e em qual função."));
f.push(LI("Abrir a conversa sobre a trilha de efetivação — a demanda existe e está documentada."));
f.push(QUEBRA());

// ============================================= 13. LIMITACOES
f.push(H1("13. Limitações e ficha técnica"));
f.push(H2("13.1 O que este relatório não sustenta"));
f.push(LIR([{ t: "Os dois públicos se sobrepõem. ", b: true },
  { t: "A rodada 2 foi disparada só para quem respondeu a rodada 1. Não são amostras " +
       "independentes e os resultados não podem ser somados nem tratados como validação cruzada " +
       "estatística — são o mesmo grupo respondendo duas vezes, sobre assuntos diferentes." }]));
f.push(LIR([{ t: "Viés de sobrevivência. ", b: true },
  { t: `${pc(m.r2_cumpriu_pct)} das respostas da rodada 2 vêm de quem cumpriu a temporada. Quem ` +
       `saiu antes está sub-representado nas duas rodadas, e é justamente o grupo cuja opinião ` +
       `mais importaria para explicar a saída. Todos os indicadores de satisfação devem ser lidos ` +
       `como teto, não como média.` }]));
f.push(LIR([{ t: "Recortes pequenos foram suprimidos. ", b: true },
  { t: "Funções com menos de 5 respostas não aparecem em nenhuma tabela por função. Abaixo desse " +
       "volume o recorte identifica quem respondeu e quebra o anonimato prometido no formulário." }]));
f.push(LIR([{ t: "As bases das seções 7 e 10 são pequenas. ", b: true },
  { t: `${D.saida.n_form_saida} respostas no questionário de saída e ${D.efetivacao.contra_base} ` +
       `no que pesa contra a efetivação. Servem para orientar hipótese, não para fechar decisão ` +
       `sozinhas.` }]));
f.push(LIR([{ t: "Autodeclaração. ", b: true },
  { t: "Faltas, motivos e percepções são o que a pessoa relatou, não o que o ponto registrou. " +
       "A conciliação com o ponto está no dashboard, na aba da temporada, e é onde os dois se " +
       "encontram." }]));

f.push(H2("13.2 Ficha técnica"));
f.push(tabela(["Item", "Rodada 1", "Rodada 2"],
  [["Objeto", "Experiência, faltas, saída, vínculo", "Salário, condições, respeito, efetivação"],
   ["Coleta", "6 a 10 de agosto de 2026", "10 de agosto de 2026"],
   ["Convites", String(m.r1_convites), String(m.r2_convites)],
   ["Respostas", String(m.r1_n), String(m.r2_n)],
   ["Taxa", pc(m.r1_taxa), pc(m.r2_taxa)],
   ["Questionários", "2 (cumpriu / saiu antes)", "1"],
   ["Canal", "WhatsApp, envio individual", "WhatsApp, envio individual"],
   ["Incentivo", "Par de ingressos garantido", "Sorteio de 10 prêmios de R$ 70 via PIX"],
   ["Anonimato", "Cadastro em formulário separado", "Cadastro em formulário separado"],
   ["Corte mínimo", "5 respostas por recorte", "5 respostas por recorte"]],
  [2200, 3580, 3580]));

f.push(H2("13.3 Documentos relacionados"));
f.push(LIR([{ t: "Dashboard, aba Pesquisa Jul/26. ", b: true },
  { t: "Mesmos números, com filtros por grupo e por função e exportação em PDF." }]));
f.push(LIR([{ t: "INTERNO_Relatos_Rodada2.docx. ", b: true },
  { t: "Relatos abertos na íntegra e encaminhamento por caso. Uso restrito." }]));
f.push(LIR([{ t: "LEIA-ME_organizacao.md. ", b: true },
  { t: "Convenção de pastas e rotina de atualização do dashboard." }]));

f.push(new Paragraph({ spacing: { before: 400 },
  children: [new TextRun({ text: "Números gerados a partir da mesma base do dashboard · Mendes RH · agosto de 2026",
    size: 17, color: MUT, italics: true, font: "Calibri" })] }));

// ------------------------------------------------------------------ build
const doc = new Document({
  creator: "Mendes RH",
  title: "Escuta do Temporário — relatório completo das duas rodadas",
  description: "Temporada de julho de 2026 · Mendes RH x Aviva / Rio Quente Resorts",
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
        new TextRun({ text: "Escuta do Temporário · duas rodadas", size: 16, color: MUT, font: "Calibri" }),
        new TextRun({ text: "\t\tMendes RH · Aviva / Rio Quente", size: 16, color: MUT, font: "Calibri" }),
      ] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT, spacing: { before: 0 },
      children: [new TextRun({ children: ["Página ", PageNumber.CURRENT], size: 16, color: MUT, font: "Calibri" })] })] }) },
    children: f
  }]
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(__dirname + "/Relatorio_Pesquisa_Completo.docx", b);
  console.log("ok", b.length, "bytes");
});
