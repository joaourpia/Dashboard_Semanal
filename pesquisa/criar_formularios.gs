/**
 * =============================================================================
 *  PESQUISAS DA TEMPORADA  ·  Mendes RH x Aviva / Rio Quente Resorts
 * =============================================================================
 *  Gera 3 formulários do Google e 1 planilha de respostas:
 *
 *    1. PESQUISA — CUMPRIU A TEMPORADA   (ficou até o fim do contrato)
 *    2. PESQUISA — SAIU ANTES DO FIM     (saída voluntária ou involuntária)
 *    3. RETIRADA DOS INGRESSOS           (separado, para preservar o anonimato)
 *
 *  A DIVISÃO NÃO É "ativo x demitido"
 *  ---------------------------------
 *  Quase todo mundo já foi desligado — o contrato temporário acabou. O que
 *  separa os dois públicos é OUTRA COISA: quem chegou até o fim da temporada
 *  e quem saiu antes, seja porque pediu para sair, seja porque foi desligado.
 *  É essa quebra que explica a curva de absenteísmo e é ela que interessa ao
 *  cliente.
 *
 *  INCENTIVO
 *  ---------
 *  Todo mundo que responder ganha um par de ingressos do Hot Park — não é
 *  sorteio, é garantido. Para emitir os ingressos precisamos de nome completo,
 *  CPF e e-mail, e esses dados ficam em um formulário SEPARADO: a planilha das
 *  respostas continua sem nome, sem CPF e sem contato.
 *
 *  COMO USAR
 *  ---------
 *  PRIMEIRA VEZ .....: selecione  criarTudo  e clique em Executar.
 *  DEPOIS DA PRIMEIRA: cole os três IDs no topo e use  atualizarTudo()  —
 *                      ela edita os MESMOS formulários, preservando tema,
 *                      imagem de cabeçalho, links já enviados e planilha.
 *
 *  Se você já rodou criarTudo() antes desta versão, o de-para dos IDs é:
 *      formulário "Pesquisa da Temporada" -> ID_CUMPRIU
 *      formulário "Pesquisa de Saída" ....-> ID_SAIU
 *      formulário do sorteio ............-> ID_INGRESSOS
 * =============================================================================
 */

// ----------------------------------------------------------------- ajustes
var PREMIO      = 'um par de ingressos do Hot Park';   // incentivo garantido
var PREMIO_CURT = 'par de ingressos do Hot Park';
var PRAZO       = '15 de agosto';                      // data limite

var LINK_INGRESSOS = '';                // preenchido automaticamente

// -------------------------------------------------------------------- IDs
// Deixe em branco na PRIMEIRA execução. Depois copie os três IDs que aparecem
// no registro e cole aqui — a partir daí use sempre atualizarTudo().
var ID_CUMPRIU   = '';
var ID_SAIU      = '';
var ID_INGRESSOS = '';


// ------------------------------------------------------------------ listas
var FUNCOES = [
  'Garçom', 'Atendente de Parque', 'Camareira',
  'Auxiliar de Serviços Gerais / Limpeza', 'Recepcionista de Parques',
  'Auxiliar de Cozinha', 'Auxiliar de Lavanderia', 'Atendente de Hotelaria',
  'Monitor de Lazer e Recreação', 'Roupeiro', 'Atendente de Portaria',
  'Vendedor Interno', 'Operador de Lava-Jato', 'Guia de Férias', 'Outra'
];

var LOCAIS = [
  'Hot Park', 'Parque das Fontes', 'Bares e restaurantes',
  'Hotéis (governança / camararia)', 'Lavanderia', 'Recepção / portaria',
  'Loja / vendas', 'Outro'
];

var MORADIA = [
  'Moro em Rio Quente ou Caldas Novas',
  'Venho de outra cidade todo dia',
  'Me mudei para a região por causa da temporada'
];

var TRANSPORTE = [
  'Transporte fretado da empresa', 'Por conta própria (moto ou carro)',
  'A pé ou de bicicleta', 'Transporte público', 'Carona com colegas'
];

var CAUSAS_FALTA = [
  'Cansaço físico acumulado',
  'Problema de saúde',
  'Transporte — não consegui chegar',
  'Problema em casa ou com filhos',
  'Escala em domingo ou feriado',
  'Desânimo com o trabalho',
  'Trabalho pesado demais para o valor pago',
  'Outro trabalho ou bico no mesmo dia',
  'Não sei dizer'
];

var ALAVANCAS = [
  'Escala mais previsível',
  'Mais folgas',
  'Transporte garantido',
  'Alimentação melhor',
  'Reconhecimento da liderança',
  'Bônus por assiduidade',
  'Pagamento maior',
  'Outro'
];


// =============================================================================
//  >>>  EXECUTE ESTA FUNÇÃO  <<<
// =============================================================================
//  As funções que começam com underline (_montarCumpriu, _escala5, ...) são
//  auxiliares e NÃO devem ser executadas sozinhas: esperam receber um
//  formulário como parâmetro e travam se rodarem isoladas.
// =============================================================================
function criarTudo() {
  var ingressos = FormApp.create('Retirada dos ingressos — Mendes RH');
  LINK_INGRESSOS = ingressos.shortenFormUrl(ingressos.getPublishedUrl());
  _montarIngressos(ingressos);

  var cumpriu = FormApp.create('Pesquisa da Temporada — Mendes RH');
  _montarCumpriu(cumpriu);
  var saiu = FormApp.create('Pesquisa de Saída — Mendes RH');
  _montarSaiu(saiu);

  var plan = SpreadsheetApp.create('Respostas — Pesquisa Temporada');
  cumpriu.setDestination(FormApp.DestinationType.SPREADSHEET, plan.getId());
  saiu.setDestination(FormApp.DestinationType.SPREADSHEET, plan.getId());

  return _relatorio(cumpriu, saiu, ingressos, plan.getUrl(), true);
}


/**
 * ATUALIZA os formulários que já existem, sem criar novos.
 *
 * Os formulários mantêm o mesmo link (o que você já enviou continua valendo),
 * o tema, a imagem de cabeçalho e a planilha de respostas vinculada.
 *
 * ATENÇÃO: atualizar apaga e recria as perguntas. Faça isso ANTES de começar a
 * coletar respostas — depois disso, as colunas antigas da planilha ficam
 * desalinhadas das novas.
 */
function atualizarTudo() {
  if (!ID_CUMPRIU || !ID_SAIU || !ID_INGRESSOS) {
    throw new Error('Preencha ID_CUMPRIU, ID_SAIU e ID_INGRESSOS no topo do ' +
                    'arquivo. Eles aparecem no registro da primeira execução.');
  }
  var ingressos = FormApp.openById(ID_INGRESSOS);
  LINK_INGRESSOS = ingressos.shortenFormUrl(ingressos.getPublishedUrl());

  var cumpriu = FormApp.openById(ID_CUMPRIU);
  var saiu    = FormApp.openById(ID_SAIU);

  _limparItens(ingressos); _montarIngressos(ingressos);
  _limparItens(cumpriu);   _montarCumpriu(cumpriu);
  _limparItens(saiu);      _montarSaiu(saiu);

  return _relatorio(cumpriu, saiu, ingressos, '(a mesma de antes)', false);
}


function _limparItens(form) {
  var itens = form.getItems();
  for (var i = itens.length - 1; i >= 0; i--) form.deleteItem(itens[i]);
}


function _relatorio(cumpriu, saiu, ingressos, urlPlanilha, primeira) {
  var msg = [
    '',
    '===========================================================',
    primeira ? '  FORMULÁRIOS CRIADOS. Guarde tudo abaixo.'
             : '  FORMULÁRIOS ATUALIZADOS. Os links continuam os mesmos.',
    '===========================================================',
    '',
    'PESQUISA — CUMPRIU A TEMPORADA (ficou até o fim):',
    '  ' + cumpriu.shortenFormUrl(cumpriu.getPublishedUrl()),
    '',
    'PESQUISA — SAIU ANTES DO FIM (voluntária ou involuntária):',
    '  ' + saiu.shortenFormUrl(saiu.getPublishedUrl()),
    '',
    'RETIRADA DOS INGRESSOS (aparece no fim das duas pesquisas):',
    '  ' + LINK_INGRESSOS,
    '',
    'PLANILHA DE RESPOSTAS (alimenta o dashboard):',
    '  ' + urlPlanilha,
    '',
    'EDIÇÃO DOS FORMULÁRIOS (aplique aqui o tema e a imagem):',
    '  Cumpriu ....: ' + cumpriu.getEditUrl(),
    '  Saiu antes .: ' + saiu.getEditUrl(),
    '  Ingressos ..: ' + ingressos.getEditUrl(),
    '',
    '-----------------------------------------------------------',
    'COLE ESTES IDs NO TOPO DO ARQUIVO PARA PODER ATUALIZAR DEPOIS:',
    "  var ID_CUMPRIU   = '" + cumpriu.getId() + "';",
    "  var ID_SAIU      = '" + saiu.getId() + "';",
    "  var ID_INGRESSOS = '" + ingressos.getId() + "';",
    '-----------------------------------------------------------',
    '',
    'IMPORTANTE — NÃO DIVULGUE O LINK DOS INGRESSOS NO WHATSAPP:',
    '  Ele aparece sozinho na tela final de quem termina a pesquisa. Se for',
    '  enviado solto, qualquer pessoa se cadastra sem responder e o número de',
    '  ingressos deixa de bater com o número de respostas.',
    '',
    'CONTROLE DOS INGRESSOS:',
    '  Confira as duas planilhas antes de emitir. O total de cadastros não pode',
    '  passar do total de respostas das duas pesquisas somadas.',
    '',
    'TEMA E IMAGEM DE CABEÇALHO:',
    '  O Google não permite definir tema por script. Abra cada link de edição,',
    '  clique no ícone de paleta (Personalizar tema), envie a imagem',
    '  cabecalho_formulario.png e escolha a cor azul #173162.',
    '  Feito uma vez, o tema permanece mesmo rodando atualizarTudo().',
    '',
    'PRÓXIMO PASSO PARA O DASHBOARD:',
    '  Na planilha de respostas: Arquivo > Compartilhar > Publicar na web,',
    '  escolha a aba e o formato CSV.',
    '==========================================================='
  ].join('\n');
  Logger.log(msg);
  return msg;
}


// ------------------------------------------------------------- utilidades
function _escala5(form, titulo, rotuloBaixo, rotuloAlto, obrigatoria) {
  form.addScaleItem()
      .setTitle(titulo)
      .setBounds(1, 5)
      .setLabels(rotuloBaixo, rotuloAlto)
      .setRequired(obrigatoria !== false);
}

function _unica(form, titulo, opcoes, obrigatoria, ajuda) {
  var it = form.addMultipleChoiceItem().setTitle(titulo).setChoiceValues(opcoes);
  if (ajuda) it.setHelpText(ajuda);
  it.setRequired(obrigatoria !== false);
  return it;
}

function _multipla(form, titulo, opcoes, ajuda, obrigatoria) {
  var it = form.addCheckboxItem().setTitle(titulo).setChoiceValues(opcoes);
  if (ajuda) it.setHelpText(ajuda);
  it.setRequired(obrigatoria === true);
  return it;
}

function _secao(form, titulo, descricao) {
  form.addPageBreakItem().setTitle(titulo).setHelpText(descricao || '');
}

function _configurar(form) {
  form.setProgressBar(true)
      .setCollectEmail(false)          // anonimato: não coleta e-mail
      .setLimitOneResponsePerUser(false)
      .setAllowResponseEdits(false)
      .setShowLinkToRespondAgain(false)
      .setConfirmationMessage(
        'Pronto! Sua resposta foi registrada de forma anônima.\n\n' +
        'Agora garanta o seu ' + PREMIO_CURT + '. ' +
        (LINK_INGRESSOS
          ? 'Preencha o cadastro de retirada aqui: ' + LINK_INGRESSOS
          : 'O link do cadastro de retirada foi enviado junto com esta pesquisa.') +
        '\n\nO cadastro é um formulário separado e pede nome completo, CPF e ' +
        'e-mail apenas para emitir os ingressos no seu nome. Ele não fica ' +
        'ligado às respostas que você acabou de dar.');
}


// =============================================================================
//  CONTEUDO — QUEM CUMPRIU A TEMPORADA
// =============================================================================
function _montarCumpriu(form) {
  form.setTitle('Você foi até o fim da temporada')
      .setDescription(
        'Esta pesquisa é para quem FICOU ATÉ O FIM do contrato da temporada de ' +
        'julho. Se você saiu antes do fim, avise a gente: existe outro ' +
        'formulário, mais curto, para o seu caso.\n\n' +
        'É ANÔNIMA. Não pedimos seu nome e não temos como saber quem respondeu ' +
        'o quê.\n\n' +
        'São cerca de 5 minutos. Sua resposta ajuda a melhorar as condições da ' +
        'próxima temporada — para você e para quem vier depois.\n\n' +
        'QUEM RESPONDER GANHA ' + PREMIO.toUpperCase() + '. Não é sorteio: é ' +
        'para todo mundo que concluir a pesquisa. No fim aparece um cadastro ' +
        'separado, com nome completo, CPF e e-mail, só para emitir os ' +
        'ingressos.\n\n' +
        'Prazo para responder: ' + PRAZO + '.');

  // ---------------------------------------------------------- 0. Triagem
  _secao(form, 'Confirmação',
         'Só para ter certeza de que você está no formulário certo.');
  _unica(form, 'Como foi o fim do seu contrato na temporada de julho?',
         ['Fiquei até o fim da temporada',
          'Saí antes do fim — eu pedi para sair',
          'Saí antes do fim — fui desligado pela empresa'],
         true,
         'Se você saiu antes do fim, feche este formulário e responda o de ' +
         'saída — o link está na mensagem que você recebeu. É mais curto e o ' +
         'brinde é o mesmo.');

  // ---------------------------------------------------------- 1. Perfil
  _secao(form, 'Sobre você',
         'Só para entendermos os resultados por área. Nada aqui identifica você.');
  _unica(form, 'Em qual função você trabalhou nesta temporada?', FUNCOES);
  _unica(form, 'Onde você trabalhou a maior parte do tempo?', LOCAIS);
  _unica(form, 'Quanto tempo durou seu contrato?',
         ['Menos de 15 dias', 'De 15 a 30 dias', 'De 1 a 2 meses', 'Mais de 2 meses']);
  _unica(form, 'Onde você mora?', MORADIA);
  _unica(form, 'Como você ia e voltava do trabalho?', TRANSPORTE);

  // ------------------------------------------------- 2. Entrada e integração
  _secao(form, 'O começo do contrato',
         'Os primeiros dias costumam definir o resto da experiência.');
  _escala5(form, 'Como foi sua recepção no primeiro dia?', 'Muito ruim', 'Muito boa');
  _unica(form, 'Quando você começou, ficou claro o que era esperado de você?',
         ['Sim, totalmente', 'Mais ou menos', 'Não — fui aprendendo sozinho na prática']);
  _unica(form, 'Você recebeu no primeiro dia tudo o que precisava para trabalhar ' +
               '(uniforme, EPI, crachá, materiais)?',
         ['Sim, tudo certo', 'Faltou alguma coisa', 'Não, demorou dias para chegar']);

  // -------------------------------------------------------- 3. O dia a dia
  _secao(form, 'O dia a dia no trabalho', '');
  _multipla(form, 'Pensando no seu dia de trabalho, o que mais pesou?',
            ['Calor e sol', 'Ritmo e volume de trabalho', 'Ficar muito tempo em pé',
             'Escala (dias e horários)', 'Poucas folgas', 'Alimentação',
             'Transporte', 'Tratamento de colegas ou da liderança',
             'Falta de material ou equipamento', 'Nada pesou de forma relevante'],
            'Marque no máximo 3.');
  _unica(form, 'A escala que você cumpriu foi a que combinaram na contratação?',
         ['Sim, foi a mesma', 'Mudou um pouco', 'Mudou bastante']);
  _escala5(form, 'Como foi a alimentação durante o trabalho?', 'Muito ruim', 'Muito boa');
  _escala5(form, 'Como os colegas efetivos tratavam os temporários?',
           'Muito mal', 'Muito bem');
  _unica(form, 'Você se sentiu à vontade para falar quando algo estava errado?',
         ['Sim', 'Mais ou menos', 'Não']);

  // -------------------------------------------------------- 4. Remuneração
  _secao(form, 'Pagamento', '');
  _unica(form, 'Pensando no esforço do dia a dia, o pagamento foi justo?',
         ['Sim, foi justo pelo trabalho que fiz',
          'É pouco perto do que a gente faz',
          'É pouco e existe coisa melhor na região']);
  _unica(form, 'Você recebeu tudo certo e no prazo (salário, vale, hora extra)?',
         ['Sim, sempre', 'Teve atraso ou erro uma vez',
          'Teve problema mais de uma vez']);
  _unica(form, 'Comparando com outros trabalhos na região:',
         ['Paga melhor e o trabalho é mais leve',
          'Paga igual, mas aqui o trabalho é mais pesado',
          'Paga pior do que outros lugares']);

  // ------------------------------------------------------------ 5. Faltas
  _secao(form, 'Sobre faltas',
         'Esta parte é a mais importante para nós. Ninguém será identificado ou ' +
         'cobrado por causa do que responder aqui.');
  _unica(form, 'Durante a temporada, você chegou a faltar algum dia?',
         ['Não faltei nenhum dia', 'Faltei 1 dia', 'Faltei 2 ou 3 dias',
          'Faltei mais de 3 dias', 'Prefiro não dizer']);
  _multipla(form, 'O que mais levou você ou seus colegas a faltar?',
            CAUSAS_FALTA, 'Marque no máximo 3. Vale falar dos colegas também.');
  _multipla(form, 'O que teria ajudado a reduzir as faltas?',
            ALAVANCAS, 'Marque no máximo 2.');

  // --------------------------------------------- 6. Por que você ficou
  _secao(form, 'Por que você ficou',
         'Muita gente saiu antes do fim. Entender por que você ficou vale tanto ' +
         'quanto entender por que os outros saíram.');
  _unica(form, 'Em algum momento você pensou em sair antes do fim?',
         ['Não, nunca pensei', 'Pensei uma vez', 'Pensei várias vezes',
          'Cheguei a decidir sair e mudei de ideia']);
  _multipla(form, 'O que mais te segurou até o fim do contrato?',
            ['Precisava do dinheiro', 'Gostei do trabalho',
             'Bom relacionamento com a equipe', 'Chance de efetivação',
             'Compromisso pessoal — eu assumi e fui até o fim',
             'Não tinha outra opção de trabalho', 'Boa liderança no posto',
             'A escala deu certo para mim'],
            'Marque no máximo 2.');

  // --------------------------------------------------- 7. Vínculo e futuro
  _secao(form, 'Sua relação com a Mendes RH', '');
  form.addScaleItem()
      .setTitle('De 0 a 10, o quanto você indicaria a Mendes RH para um amigo ' +
                'trabalhar?')
      .setBounds(0, 10)
      .setLabels('De jeito nenhum', 'Com certeza')
      .setRequired(true);
  _unica(form, 'Como foi sua experiência com a equipe da Mendes RH, da entrevista ' +
               'até o fim do contrato?',
         ['Ótima — fui bem recebido, as informações foram claras e tive apoio',
          'Boa, mas distante — o processo foi correto, mas depois da contratação ' +
          'me senti sozinho',
          'Confusa — as informações mudavam ou não batiam com o combinado',
          'Ruim — me senti largado no posto de trabalho']);
  _unica(form, 'Você acredita que teve chance real de efetivação?',
         ['Sim, dependia de mim', 'Tive dúvidas', 'Não acreditei nessa possibilidade',
          'Não tinha interesse em ser efetivado']);
  _unica(form, 'Se abrisse uma vaga fixa aqui hoje, você aceitaria?',
         ['Sim, na hora', 'Sim, se melhorasse alguma coisa', 'Não']);
  _unica(form, 'Você voltaria a trabalhar na próxima temporada?',
         ['Com certeza', 'Talvez', 'Não']);

  // ------------------------------------------------------------ 8. Aberta
  _secao(form, 'Por último', '');
  form.addParagraphTextItem()
      .setTitle('Se você pudesse mudar UMA coisa na temporada, o que seria?')
      .setRequired(false);
  form.addParagraphTextItem()
      .setTitle('Quer deixar algum elogio ou reclamação? (opcional)')
      .setRequired(false);

  _configurar(form);
  return form;
}


// =============================================================================
//  CONTEUDO — QUEM SAIU ANTES DO FIM DA TEMPORADA
// =============================================================================
function _montarSaiu(form) {
  form.setTitle('Sua saída antes do fim da temporada')
      .setDescription(
        'Esta pesquisa é para quem SAIU ANTES DO FIM do contrato da temporada de ' +
        'julho — tanto quem pediu para sair quanto quem foi desligado pela ' +
        'empresa. Se você ficou até o fim, existe outro formulário para o seu ' +
        'caso.\n\n' +
        'É ANÔNIMA e leva cerca de 3 minutos.\n\n' +
        'Não é cobrança e não interfere em nada que você já recebeu. Queremos ' +
        'entender de verdade o que fez as pessoas saírem antes do fim, para ' +
        'corrigir o que estiver do nosso lado.\n\n' +
        'QUEM RESPONDER GANHA ' + PREMIO.toUpperCase() + '. Não é sorteio: é ' +
        'para todo mundo que concluir a pesquisa. No fim aparece um cadastro ' +
        'separado, com nome completo, CPF e e-mail, só para emitir os ' +
        'ingressos.\n\n' +
        'Prazo para responder: ' + PRAZO + '.');

  // ------------------------------------------------------ 1. Como terminou
  _secao(form, 'Como terminou',
         'A primeira pergunta é a que mais importa para nós.');
  _unica(form, 'Sua saída foi decisão sua ou da empresa?',
         ['Eu pedi para sair (saída voluntária)',
          'Fui desligado pela empresa (saída involuntária)',
          'Combinamos a saída juntos',
          'Prefiro não dizer']);
  _unica(form, 'Se você foi desligado, sabe qual foi o motivo?',
         ['Faltas', 'Desempenho', 'Comportamento ou conduta',
          'Redução de quadro', 'Não me explicaram', 'Outro motivo',
          'Não fui desligado — eu pedi para sair'], false);
  _unica(form, 'Quanto tempo você ficou antes de sair?',
         ['Menos de 7 dias', 'De 7 a 15 dias', 'De 15 a 30 dias', 'Mais de 30 dias']);

  // ---------------------------------------------------------- 2. Perfil
  _secao(form, 'Sobre você', 'Nada aqui identifica você.');
  _unica(form, 'Em qual função você trabalhou?', FUNCOES);
  _unica(form, 'Onde você trabalhou a maior parte do tempo?', LOCAIS);
  _unica(form, 'Onde você mora?', MORADIA);
  _unica(form, 'Como você ia e voltava do trabalho?', TRANSPORTE);

  // ------------------------------------------------------- 3. Motivo real
  _secao(form, 'O motivo real',
         'Aqui é onde sua resposta mais ajuda. Seja franco.');
  _unica(form, 'Qual foi o motivo REAL da sua saída?',
         ['Salário', 'Trabalho mais pesado do que eu esperava',
          'Escala e falta de folga', 'Transporte ou distância', 'Alimentação',
          'Chefia ou liderança no posto', 'Ambiente e colegas',
          'Problema de saúde', 'Problema pessoal ou familiar',
          'Consegui outro emprego', 'Fui efetivado na Aviva',
          'Demora na efetivação', 'Fui desligado por faltas',
          'Fui desligado por outro motivo', 'Prefiro não dizer']);
  _multipla(form, 'Teve algum outro motivo que também pesou?',
            ['Salário', 'Trabalho pesado', 'Escala e folgas', 'Transporte',
             'Alimentação', 'Chefia ou liderança', 'Ambiente e colegas',
             'Saúde', 'Problema pessoal', 'Outro emprego',
             'Demora na efetivação', 'Não teve outro motivo'],
            'Marque quantos quiser.');
  _unica(form, 'Em que momento você decidiu que ia sair?',
         ['Já nos primeiros dias', 'Na primeira semana',
          'Depois de mais ou menos duas semanas',
          'Perto do fim, quando já estava quase acabando',
          'Não foi decisão minha — fui desligado']);

  // ------------------------------------------------------------ 4. Faltas
  _secao(form, 'Sobre faltas',
         'Ninguém será identificado ou cobrado pelo que responder aqui.');
  _unica(form, 'Antes de sair, você chegou a faltar?',
         ['Não faltei nenhum dia', 'Faltei 1 dia', 'Faltei 2 ou 3 dias',
          'Faltei mais de 3 dias', 'Prefiro não dizer']);
  _multipla(form, 'O que fez você faltar?', CAUSAS_FALTA,
            'Marque no máximo 3. Se não faltou, pode pular.');
  _unica(form, 'Depois da sua primeira falta, alguém da Mendes RH ou da liderança ' +
               'conversou com você?',
         ['Sim, e a conversa ajudou', 'Sim, mas foi só cobrança',
          'Não falaram comigo', 'Não me lembro', 'Não faltei']);

  // -------------------------------------------- 5. O que teria mudado
  _secao(form, 'O que teria mudado sua decisão', '');
  _multipla(form, 'O que teria feito você ficar até o fim do contrato?',
            ['Nada — eu sairia de qualquer forma', 'Salário maior',
             'Escala melhor', 'Mais folgas', 'Transporte garantido',
             'Alimentação melhor', 'Tratamento melhor da liderança',
             'Promessa clara de efetivação', 'Bônus por concluir o contrato',
             'Alguém que me ouvisse quando o problema começou'],
            'Marque no máximo 2.');
  _unica(form, 'Você avisou alguém antes de sair?',
         ['Sim, avisei com antecedência', 'Avisei em cima da hora',
          'Não avisei — só parei de ir',
          'Tentei avisar e não consegui falar com ninguém',
          'Não se aplica — fui desligado']);

  // --------------------------------------------------------- 6. Relação
  _secao(form, 'Sua relação com a Mendes RH', '');
  form.addScaleItem()
      .setTitle('De 0 a 10, o quanto você indicaria a Mendes RH para um amigo ' +
                'trabalhar?')
      .setBounds(0, 10)
      .setLabels('De jeito nenhum', 'Com certeza')
      .setRequired(true);
  _unica(form, 'Você aceitaria trabalhar de novo com a Mendes RH?',
         ['Sim', 'Talvez', 'Não']);
  form.addParagraphTextItem()
      .setTitle('O que você diria para a gente melhorar?')
      .setRequired(false);

  _configurar(form);
  return form;
}


// =============================================================================
//  CONTEUDO — RETIRADA DOS INGRESSOS  (separado, sem nenhuma resposta)
// =============================================================================
function _montarIngressos(form) {
  form.setTitle('Retirada do seu ' + PREMIO_CURT)
      .setDescription(
        'Você respondeu a pesquisa — agora garanta o seu ' + PREMIO_CURT + '.\n\n' +
        'Este cadastro é SEPARADO da pesquisa. Ele existe só para emitir os ' +
        'ingressos no seu nome. Não temos como ligar seus dados às respostas ' +
        'que você deu: são dois formulários diferentes, com planilhas ' +
        'diferentes.\n\n' +
        'Preencha uma vez só. Cadastro em duplicidade é cancelado.\n\n' +
        'Prazo para o cadastro: ' + PRAZO + '.');

  form.addTextItem()
      .setTitle('Nome completo')
      .setHelpText('Igual está no documento — o ingresso é emitido nominal.')
      .setRequired(true);
  form.addTextItem()
      .setTitle('CPF')
      .setHelpText('Só números. É exigência do parque para emitir o ingresso ' +
                   'no seu nome.')
      .setRequired(true);
  form.addTextItem()
      .setTitle('E-mail')
      .setHelpText('É por aqui que o voucher dos ingressos chega. Confira se ' +
                   'está escrito certo.')
      .setRequired(true);
  form.addTextItem()
      .setTitle('WhatsApp com DDD')
      .setHelpText('Exemplo: 64 99999-9999. Só para avisar quando o voucher sair.')
      .setRequired(true);
  form.addCheckboxItem()
      .setTitle('Autorização')
      .setChoiceValues([
        'Autorizo o uso do meu nome, CPF e e-mail exclusivamente para emitir e ' +
        'enviar o par de ingressos do Hot Park. Sei que estes dados não são ' +
        'ligados às minhas respostas da pesquisa.'
      ])
      .setRequired(true);

  form.setProgressBar(false)
      .setCollectEmail(false)
      .setAllowResponseEdits(false)
      .setShowLinkToRespondAgain(false)
      .setConfirmationMessage(
        'Cadastro concluído. Seu ' + PREMIO_CURT + ' será enviado para o ' +
        'e-mail informado até ' + PRAZO + '. Obrigado por responder!');
  return form;
}
