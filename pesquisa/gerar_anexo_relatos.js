// ============================================================================
//  ANEXO — relatos abertos da rodada 2, na integra
//  Escrito em primeira pessoa, da Mendes RH para quem conduzir a apuracao,
//  dos dois lados. Circulacao restrita.
// ----------------------------------------------------------------------------
//  Mesmas regras de escrita do relatorio principal: primeira pessoa, nenhum
//  travessao, nenhuma orientacao interna, sem linguagem promocional.
//  Os textos dos respondentes ficam VERBATIM, sem nenhuma edicao.
// ============================================================================
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
        Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
        PageBreak, LevelFormat, Header, Footer, PageNumber } = require('docx');
const fs = require('fs');

const AZUL = "1C5CAB", AZUL_ESC = "0D366B", CINZA = "52514E", MUT = "898781";
const VERDE = "0C7A3E", VERM = "A32020", AMBAR = "8A5A00";
const LARG = 9360;

const dados = JSON.parse(fs.readFileSync(__dirname + "/_relatos.json", "utf8"));
const M = dados.meta || {};
const pc1 = n => (n === null || n === undefined) ? "—"
  : Number(n).toFixed(1).replace(".", ",") + "%";

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
const H1 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1, spacing: { before: 340, after: 170 } });
const H2 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 120 } });
const LIR = (runs, n = 0) => new Paragraph({ numbering: { reference: "bul", level: n },
  spacing: { after: 80, line: 280 },
  children: runs.map(r => new TextRun({ text: r.t, bold: r.b, italics: r.i, size: 21,
    color: r.c ?? "0B0B0B", font: "Calibri" })) });
const QUEBRA = () => new Paragraph({ children: [new PageBreak()] });

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

// cartao de relato: cabecalho com funcao e nivel, depois o texto verbatim
function relato(n, r) {
  const grave = r.respeito === "Poucas vezes" || r.respeito === "Nunca";
  const c = grave ? VERM : AMBAR;
  return [
    new Paragraph({ spacing: { before: 240, after: 40 }, indent: { left: 200 },
      shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
      border: { left: { style: BorderStyle.SINGLE, size: 18, color: c, space: 8 } },
      children: [
        new TextRun({ text: `Relato ${String(n).padStart(2, "0")}   `, bold: true, size: 20, color: c, font: "Calibri" }),
        new TextRun({ text: r.funcao, bold: true, size: 20, color: "0B0B0B", font: "Calibri" }),
        new TextRun({ text: `   respondeu que se sentiu respeitado(a) ${r.respeito.toLowerCase()}`,
                      size: 19, color: CINZA, font: "Calibri" }),
      ] }),
    new Paragraph({ spacing: { before: 0, after: 220, line: 280 }, indent: { left: 200 },
      shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
      border: { left: { style: BorderStyle.SINGLE, size: 18, color: c, space: 8 } },
      children: [new TextRun({ text: '"' + r.texto + '"', italics: true, size: 20, color: "0B0B0B", font: "Calibri" })] }),
  ];
}

const f = [];
const N = dados.relatos.length;

// ================================================================== CAPA
f.push(new Paragraph({ spacing: { before: 900, after: 0 },
  children: [new TextRun({ text: "CIRCULAÇÃO RESTRITA", bold: true, size: 20, color: VERM, font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 60 },
  children: [new TextRun({ text: "Relatos abertos", bold: true, size: 50, color: "0B0B0B", font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 100 },
  children: [new TextRun({ text: "Anexo ao relatório da escuta do temporário", bold: true, size: 28, color: AZUL_ESC, font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 340 },
  children: [new TextRun({ text: "Temporada de julho de 2026 · Mendes RH e Aviva / Rio Quente Resorts", size: 24, color: CINZA, font: "Calibri" })] }));

f.push(P("Este anexo é para quem for conduzir a apuração dos casos, dos dois lados. Ele reproduz " +
  "sem cortes o que as pessoas escreveram no campo aberto da segunda pesquisa, quando " +
  "perguntamos se queriam contar alguma situação em que não se sentiram respeitadas.", { color: CINZA }));
f.push(P("Separei estes textos do relatório principal porque eles pedem uma ação diferente. O " +
  "relatório mede padrão; aqui há episódios com pessoa, posto e data aproximada, e episódio se " +
  "resolve conversando com quem estava envolvido.", { color: CINZA }));
f.push(QUEBRA());

// ============================================================== ABERTURA
f.push(H1("O que você vai ler"));

f.push(...CAIXA("Sobre o anonimato",
  "A pesquisa não coletou nome, telefone nem qualquer identificador de quem respondeu, e o " +
  "cadastro do sorteio ficou em formulário e planilha separados. Não tenho como dizer quem " +
  "escreveu cada texto, e não quero ter. A função e o nível de respeito aparecem abaixo porque " +
  "vieram do próprio questionário e ajudam a situar o contexto. Quando o relato menciona outra " +
  "pessoa, mantive o nome como foi escrito, porque é a informação necessária para apurar.", AZUL));

f.push(...CAIXA("Sobre a contagem",
  `${M.escreveram} pessoas escreveram algo no campo. ${M.sem_ocorrencia} usaram o espaço para dizer que não tinham nada a ` +
  `relatar, com respostas como "nada", "não tenho" e "fui respeitada em toda situação". Sobraram ` +
  `${N} textos que descrevem alguma situação, e são estes. A separação entre os dois grupos é ` +
  `feita por regra escrita, não a olho, então ela se repete igual quando chegarem novas respostas.`,
  AZUL));

f.push(...CAIXA("Sobre o que fazer com isto",
  "Não classifiquei nada como denúncia formal, porque não é meu papel decidir isso sozinho e " +
  "porque a pesquisa não foi desenhada como canal de denúncia. O que fiz foi ler tudo, agrupar " +
  "por tipo e propor um encaminhamento para cada grupo na segunda parte do documento. A decisão " +
  "sobre abrir apuração é de quem tem essa competência em cada empresa.", AMBAR));
f.push(QUEBRA());

// =========================================================== OS RELATOS
f.push(H1("1. Os textos, na íntegra"));
f.push(P("Coloquei primeiro quem marcou \"poucas vezes\" na pergunta de respeito, depois os " +
  "demais. A barra vermelha marca o primeiro grupo. Nenhum texto foi editado, nem para corrigir " +
  "ortografia.", { size: 19, color: MUT }));

const ordem = { "Nunca": 0, "Poucas vezes": 1, "Na maior parte do tempo": 2, "Sempre": 3 };
const lista = [...dados.relatos].sort((a, b) =>
  (ordem[a.respeito] ?? 9) - (ordem[b.respeito] ?? 9) || b.texto.length - a.texto.length);
lista.forEach((r, i) => f.push(...relato(i + 1, r)));

if (dados.comentarios && dados.comentarios.length) {
  f.push(H2("1.1 Menção que veio de outro campo"));
  f.push(P("Esta apareceu no campo de comentário livre, no fim do questionário, e não no campo de " +
    "relato. O teor é bem mais brando, mas cita uma pessoa e por isso trago junto."));
  dados.comentarios.forEach(c => f.push(new Paragraph({
    spacing: { before: 60, after: 160, line: 264 }, indent: { left: 340 },
    children: [new TextRun({ text: '"' + c.trim() + '"', italics: true, size: 19, color: CINZA, font: "Calibri" })] })));
}
f.push(QUEBRA());

// =========================================================== ENCAMINHAMENTO
f.push(H1("2. O que eu proponho para cada caso"));

f.push(H2("2.1 Os três que precisam de apuração"));

f.push(...CAIXA("Conduta de uma pessoa em função de treinamento",
  "Um relato cita, com nome e função, alguém que grita e trata colegas com grosseria. A conduta " +
  "descrita coincide com um relato anônimo que recebemos na primeira rodada, quando ainda não " +
  "havia nome. São dois respondentes diferentes, em pesquisas diferentes, com semanas de " +
  "intervalo, descrevendo o mesmo comportamento. Proponho abrir apuração pelo canal de conduta e " +
  "segurar qualquer promoção dessa pessoa a função de treinamento até a conclusão.", VERM));

f.push(...CAIXA("Nome social ignorado de forma repetida",
  "Uma pessoa em transição de gênero relata ter sido chamada pelo nome de registro mesmo depois " +
  "de informar o nome social, e tratada no gênero errado de forma continuada. Aqui a falha é " +
  "nossa e é de política, não de conduta de uma pessoa específica: nosso cadastro de contratação " +
  "não tem campo de nome social, então o nome de registro é o que chega ao posto. Vou criar o " +
  "campo e incluir orientação no material dos supervisores antes da próxima temporada.", VERM));

f.push(...CAIXA("Ameaça de agressão",
  "Um relato menciona um colaborador que \"veio me intimidar e de certa forma querer me agredir\". " +
  "O texto não dá nome nem posto, então não consigo apurar com o que tenho. Registro aqui para " +
  "que fique documentado, e vou incluir um campo opcional de posto ou área no relato da próxima " +
  "rodada, para que um caso assim não fique sem destino de novo.", VERM));

f.push(H2("2.2 O padrão que aparece mais de uma vez"));

f.push(...CAIXA("Fronteira entre efetivo e temporário",
  "Cinco relatos descrevem a mesma dinâmica: serviço transferido para o temporário, comentários " +
  "sobre aparência e sobre o corpo, recepção hostil ao entrar em determinados espaços. Dois deles " +
  "citam o mesmo posto, o PDV do Pier, sem que as pessoas se conheçam. Quando o mesmo " +
  "comportamento aparece em relatos independentes sobre o mesmo lugar, o problema passou a ser " +
  "da área e não de quem trabalha nela. Proponho tratar como pauta de gestão da área, com " +
  "orientação aos líderes de turno, e não como caso de conduta de ninguém em particular.", AMBAR));

f.push(...CAIXA("Segurança e portaria",
  "Um relato descreve constrangimento na entrada da rodoviária por não ter recebido crachá na " +
  "contratação nem orientação sobre a necessidade dele. São duas falhas somadas. A entrega do " +
  "crachá é nossa e já está sendo corrigida no processo de contratação. O tratamento recebido na " +
  "portaria vale conversar com a equipe de segurança.", AMBAR));

f.push(H2("2.3 O que sugiro registrar"));
f.push(P("Para que o assunto não recomece do zero na próxima temporada:"));
f.push(LIR([{ t: "Data de abertura, responsável e desfecho de cada apuração, ", b: true },
  { t: "em planilha própria de cada empresa. Isso não entra no painel nem em relatório de " +
       "resultado." }]));
f.push(LIR([{ t: "Repetição das mesmas duas perguntas na próxima rodada, ", b: true },
  { t: `sem mudar uma palavra do texto, para saber se os ${pc1(M.respeito_sempre)} de respeito pleno se movem.` }]));
f.push(LIR([{ t: "Campo opcional de posto ou área no relato aberto. ", b: true },
  { t: "Sem ele, parte dos casos fica inapurável, como o de ameaça acima." }]));
f.push(LIR([{ t: "Retorno para quem respondeu. ", b: true },
  { t: "Essas pessoas escreveram achando que alguém leria. Se a próxima temporada começar sem " +
       `nenhuma sinalização de que algo mudou, a terceira pesquisa não terá os ${pc1(M.taxa_r2)} de retorno desta.` }]));

f.push(new Paragraph({ spacing: { before: 500 },
  children: [new TextRun({ text: "Mendes RH · agosto de 2026 · circulação restrita",
    size: 18, color: CINZA, font: "Calibri" })] }));

// ------------------------------------------------------------------ build
const doc = new Document({
  creator: "Mendes RH",
  title: "Relatos abertos — anexo restrito",
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
        new TextRun({ text: "Relatos abertos · anexo restrito", size: 16, color: MUT, font: "Calibri" }),
        new TextRun({ text: "\t\tMendes RH · temporada de julho de 2026", size: 16, color: MUT, font: "Calibri" }),
      ] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT, spacing: { before: 0 },
      children: [new TextRun({ children: ["Página ", PageNumber.CURRENT], size: 16, color: MUT, font: "Calibri" })] })] }) },
    children: f
  }]
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(__dirname + "/Anexo_Relatos_Abertos.docx", b);
  console.log("ok", b.length, "bytes");
});
