// Anexo interno — relatos abertos da rodada 2, na integra.
// Documento de uso restrito: nao vai ao cliente e nao entra no painel.
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
        Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
        PageBreak, LevelFormat } = require('docx');
const fs = require('fs');

const AZUL = "1C5CAB", AZUL_ESC = "0D366B", CINZA = "52514E", MUT = "898781";
const VERDE = "0C7A3E", VERM = "A32020", AMBAR = "8A5A00";
const LARG = 9360;

const dados = JSON.parse(fs.readFileSync(__dirname + "/_relatos.json", "utf8"));

const P = (t, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 120, line: o.line ?? 276 },
  alignment: o.align, indent: o.indent,
  children: [new TextRun({ text: t, size: o.size ?? 21, bold: o.bold,
                           italics: o.it, color: o.color ?? "0B0B0B", font: "Calibri" })]
});
const RICH = (runs, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 120, line: 276 }, indent: o.indent,
  children: runs.map(r => new TextRun({ text: r.t, bold: r.b, italics: r.i,
    size: r.size ?? 21, color: r.c ?? "0B0B0B", font: "Calibri" }))
});
const H1 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 } });
const H2 = t => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 120 } });
const LIR = (runs, n = 0) => new Paragraph({ numbering: { reference: "bul", level: n },
  spacing: { after: 80, line: 276 },
  children: runs.map(r => new TextRun({ text: r.t, bold: r.b, italics: r.i, size: 21,
    color: r.c ?? "0B0B0B", font: "Calibri" })) });

const DESTAQUE = (titulo, texto, cor) => [
  new Paragraph({ spacing: { before: 220, after: 60 }, indent: { left: 200 },
    shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: cor || VERDE, space: 8 } },
    children: [new TextRun({ text: titulo, bold: true, size: 21, color: cor || VERDE, font: "Calibri" })] }),
  new Paragraph({ spacing: { before: 0, after: 220, line: 276 }, indent: { left: 200 },
    shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: cor || VERDE, space: 8 } },
    children: [new TextRun({ text: texto, size: 20, color: CINZA, font: "Calibri" })] })
];

// cartao de relato: cabecalho com funcao/nivel + texto integral
function relato(n, r, cor) {
  const grave = r.respeito === "Poucas vezes" || r.respeito === "Nunca";
  const c = cor || (grave ? VERM : AMBAR);
  return [
    new Paragraph({ spacing: { before: 240, after: 40 }, indent: { left: 200 },
      shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
      border: { left: { style: BorderStyle.SINGLE, size: 18, color: c, space: 8 } },
      children: [
        new TextRun({ text: `Relato ${String(n).padStart(2, "0")}  ·  `, bold: true, size: 20, color: c, font: "Calibri" }),
        new TextRun({ text: r.funcao, bold: true, size: 20, color: "0B0B0B", font: "Calibri" }),
        new TextRun({ text: `  ·  respeito: ${r.respeito}`, size: 19, color: CINZA, font: "Calibri" }),
      ] }),
    new Paragraph({ spacing: { before: 0, after: 220, line: 276 }, indent: { left: 200 },
      shading: { type: ShadingType.CLEAR, fill: "F4F6F9", color: "auto" },
      border: { left: { style: BorderStyle.SINGLE, size: 18, color: c, space: 8 } },
      children: [new TextRun({ text: "“" + r.texto + "”", italics: true, size: 20, color: "0B0B0B", font: "Calibri" })] }),
  ];
}

const f = [];

// ================================================================== CAPA
f.push(new Paragraph({ spacing: { before: 900, after: 0 },
  children: [new TextRun({ text: "USO INTERNO  ·  NÃO DIVULGAR", bold: true, size: 20, color: VERM, font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 60 },
  children: [new TextRun({ text: "Anexo — relatos abertos", bold: true, size: 46, color: "0B0B0B", font: "Calibri" })] }));
f.push(new Paragraph({ spacing: { after: 300 },
  children: [new TextRun({ text: "Pesquisa 2 · temporada de julho de 2026 · Mendes RH", size: 25, color: CINZA, font: "Calibri" })] }));

f.push(P("Este documento reproduz na íntegra as respostas ao campo aberto “Se quiser, conte uma " +
  "situação em que você não se sentiu respeitado(a)”. Ele existe para dar destino às ocorrências " +
  "individuais — apuração, conversa, registro — que o painel e o relatório de reunião tratam " +
  "apenas de forma agregada.", { color: CINZA }));

f.push(...DESTAQUE("Anonimato",
  "A pesquisa não coleta nome, telefone nem qualquer identificador de quem respondeu. Função e " +
  "nível de respeito aparecem abaixo porque vieram do próprio questionário e ajudam a localizar " +
  "o contexto — não permitem identificar o autor. Onde o relato menciona terceiros, o nome " +
  "aparece como foi escrito: é a informação necessária para apurar.", AZUL));

f.push(...DESTAQUE("Contagem",
  `17 pessoas escreveram algo no campo. 6 responderam que não tinham nada a relatar ` +
  `("nada", "não tenho", "fui respeitada em toda situação") e não constam aqui. ` +
  `Restam ${dados.relatos.length} respostas que descrevem alguma situação — são estas.`, AZUL));

f.push(new Paragraph({ children: [new PageBreak()] }));

// =========================================================== OS RELATOS
f.push(H1("1. Relatos na íntegra"));
f.push(P("Ordenados por gravidade aparente: primeiro quem marcou “poucas vezes” na pergunta de " +
  "respeito, depois os demais. A barra vermelha marca os primeiros.", { size: 19, color: MUT }));

const ordem = { "Nunca": 0, "Poucas vezes": 1, "Na maior parte do tempo": 2, "Sempre": 3 };
const lista = [...dados.relatos].sort((a, b) =>
  (ordem[a.respeito] ?? 9) - (ordem[b.respeito] ?? 9) || b.texto.length - a.texto.length);
lista.forEach((r, i) => f.push(...relato(i + 1, r)));

if (dados.comentarios && dados.comentarios.length) {
  f.push(H2("1.1 Menção nominal fora do campo de relato"));
  f.push(P("Apareceu no campo de comentário livre, não no de relato. Teor bem mais brando, mas " +
    "cita uma pessoa e por isso entra aqui."));
  dados.comentarios.forEach(c => f.push(new Paragraph({
    spacing: { before: 60, after: 160, line: 264 }, indent: { left: 340 },
    children: [new TextRun({ text: "“" + c.trim() + "”", italics: true, size: 19, color: CINZA, font: "Calibri" })] })));
}

f.push(new Paragraph({ children: [new PageBreak()] }));

// =========================================================== ENCAMINHAMENTO
f.push(H1("2. Encaminhamento sugerido"));

f.push(H2("2.1 Apuração formal — antes da próxima temporada"));
f.push(...DESTAQUE("Conduta de uma pessoa em função de treinamento",
  "Um relato descreve, com nome e função, alguém que grita e trata colegas com grosseria. A " +
  "conduta descrita coincide com o relato anônimo da seção 10.1 do relatório da rodada 1 — dois " +
  "respondentes independentes, em rodadas diferentes, descrevendo o mesmo comportamento. Abrir " +
  "apuração pelo canal de conduta e suspender qualquer promoção dessa pessoa a função de " +
  "treinamento até a conclusão.", VERM));
f.push(...DESTAQUE("Nome social ignorado de forma reiterada",
  "Uma pessoa em transição de gênero relata ter sido chamada pelo nome de registro apesar de ter " +
  "informado o nome social, e referida no gênero errado de forma continuada. Não é conduta " +
  "isolada: é ausência de política. Exige (a) campo de nome social no cadastro de contratação, " +
  "(b) orientação formal a supervisores e (c) conversa reservada com a pessoa, se ela ainda " +
  "estiver acessível pelo grupo de temporários.", VERM));
f.push(...DESTAQUE("Intimidação física",
  "Um relato menciona colaborador que “veio me intimidar e de certa forma querer me agredir”. O " +
  "texto não dá nome nem posto. Vale incluir a pergunta no roteiro da próxima rodada — um campo " +
  "opcional de “onde isso aconteceu” tornaria esse tipo de relato apurável.", VERM));

f.push(H2("2.2 Padrão coletivo — vai para a pauta com a Aviva"));
f.push(...DESTAQUE("Fronteira efetivo × temporário",
  "Cinco dos relatos descrevem a mesma dinâmica: sobrecarga transferida ao temporário, " +
  "comentários sobre aparência, recepção hostil. Dois relatos independentes citam o mesmo posto " +
  "— o PDV/Burguer do Pier. Não é conduta de uma pessoa, é clima de área. Entra como pauta " +
  "formal com a Aviva, junto com o dado de que 43,0% não se sentiram sempre respeitados.", AMBAR));
f.push(...DESTAQUE("Segurança e portaria",
  "Um relato descreve constrangimento na entrada da rodoviária por não ter recebido crachá na " +
  "contratação nem orientação sobre a necessidade dele. Duas ações: entregar o crachá no " +
  "processo de contratação (Mendes RH, esta semana) e alinhar o tratamento da equipe de " +
  "segurança ao temporário (Aviva).", AMBAR));

f.push(H2("2.3 Registro"));
f.push(P("Sugestão de controle mínimo, para que o tema não recomece do zero na próxima temporada:"));
f.push(LIR([{ t: "Data de abertura, responsável e desfecho ", b: true },
  { t: "de cada apuração, em planilha própria — não no dashboard." }]));
f.push(LIR([{ t: "Repetir as perguntas 9 e 10 ", b: true },
  { t: "na próxima rodada, sem alteração de texto, para medir se o número de 57,0% de respeito " +
       "pleno se move." }]));
f.push(LIR([{ t: "Acrescentar um campo opcional de posto ou área ", b: true },
  { t: "no relato aberto. Sem ele, parte dos casos fica inapurável, como o de intimidação acima." }]));

f.push(new Paragraph({ spacing: { before: 400 },
  children: [new TextRun({ text: "Documento de uso interno · gerado a partir da base da Pesquisa 2 · Mendes RH · agosto de 2026",
    size: 17, color: MUT, italics: true, font: "Calibri" })] }));

// ------------------------------------------------------------------ build
const doc = new Document({
  creator: "Mendes RH",
  title: "Anexo interno — relatos abertos da Pesquisa 2",
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 220 } } } }] },
  ]},
  styles: { default: {
    heading1: { run: { size: 32, bold: true, color: AZUL_ESC, font: "Calibri" },
                paragraph: { spacing: { before: 320, after: 160 } } },
    heading2: { run: { size: 25, bold: true, color: "0B0B0B", font: "Calibri" },
                paragraph: { spacing: { before: 260, after: 110 } } },
  }},
  sections: [{
    properties: { page: { margin: { top: 1100, right: 1100, bottom: 1100, left: 1100 } } },
    children: f
  }]
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(__dirname + "/INTERNO_Relatos_Rodada2.docx", b);
  console.log("ok", b.length);
});
