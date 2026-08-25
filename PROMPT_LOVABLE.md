# Dashboard Operacional Mendes RH — migração do Streamlit para app web completo

## 1. Contexto e objetivo

Sou a Mendes RH, agência de trabalho temporário. Atendo a Aviva / Rio Quente Resorts fornecendo trabalhadores temporários (garçons, atendentes, auxiliares de limpeza, cozinha etc.). Hoje acompanho a operação num dashboard Streamlit que lê arquivos CSV/XLSX de pastas por semana. Quero migrar esse sistema para um app web com banco de dados de verdade, telas de importação e controle de acesso.

O app tem duas audiências: eu (administrador, que importo dados e gerencio períodos) e o cliente Aviva (somente leitura, acompanha os indicadores). Todo o texto do sistema é em português do Brasil.

## 2. Autenticação e papéis

- Login com Supabase Auth (e-mail e senha).
- Dois papéis: `admin` (eu) e `viewer` (cliente Aviva).
- Admin: importa dados, cria/edita períodos, gerencia usuários viewer, vê tudo.
- Viewer: só visualiza os painéis. Não vê telas de importação nem configurações.
- IMPORTANTE (privacidade): a rodada 2 da pesquisa tem uma pergunta aberta com relatos de situações de desrespeito. Esses textos verbatim NUNCA aparecem para viewer nem em nenhum painel — ficam numa área restrita só do admin, protegida por RLS no banco. Nos painéis aparecem apenas as contagens agregadas.

## 3. Modelo de dados (Supabase / Postgres)

Estruture com boas chaves e RLS. Sugestão de tabelas:

**semanas** — o período é a unidade central.
- id, ano (int), mes (int), semana_no (int), rotulo (ex.: "01 a 06/07/2026"), data_inicio, data_fim

**sla_semanal** — fechamento de vagas no prazo, uma linha por semana.
- semana_id, solicitado (int), no_prazo (int), fora_prazo (int)
- taxa calculada: no_prazo / solicitado

**diarias_semanais** — diárias contratadas × entregues, uma linha por semana.
- semana_id, solicitado (int), entregue (int)
- taxa calculada: entregue / solicitado (pode passar de 100%)

**temporadas** — eventos sazonais (ex.: "Temporada de Julho de 2026").
- id, nome, data_inicio, data_fim, cliente

**temporada_dia_funcao** — o grão fino da temporada: uma linha por dia × função.
- temporada_id, dia (date), funcao (text), solicitado, trabalhou, folga, atestado, outra_justificativa, falta, fora_do_contrato, entregue, escala (todos int)
- Derivados (views ou colunas calculadas):
  - absenteismo_% = falta / escala × 100
  - cobertura_% = entregue / solicitado × 100
  - em_posto_% = trabalhou / solicitado × 100
  - saldo = entregue − solicitado

**pesquisa_rodadas** — cada rodada de escuta.
- id, numero (1 ou 2), titulo, convites_enviados, data_inicio_coleta, data_fim_coleta

**pesquisa_respostas_r1** — respostas anônimas da rodada 1 (experiência e saída). Colunas canônicas: timestamp, funcao, local, moradia, transporte, decisao_saida, motivo_desligamento, tempo_permanencia, motivo_real_saida, outro_motivo, momento_decisao, faltou (sim/não), causa_falta, alguem_conversou, o_que_faria_ficar, avisou, nps (0–10), voltaria (Sim/Talvez/Não), sugestao (texto livre)

**pesquisa_respostas_r2** — respostas anônimas da rodada 2 (salário, condições, efetivação). Colunas canônicas: timestamp, funcao, cumpriu_temporada, nota_salario (0–10), expectativa (Atendeu/Ficou abaixo/Ficou acima), comparacao_mercado, alavanca_pagamento, nota_condicoes (0–10), o_que_melhorar, respeito (Sim sempre / Na maior parte / Não), relato_desrespeito (TEXTO RESTRITO — RLS: só admin), interesse_clt (Sim/Talvez/Não), area_desejada, o_que_pesa_contra, comentario_final

**importacoes** — log de cada upload: quem, quando, arquivo, tabela destino, linhas inseridas, erros.

Nada de dados pessoais no app: as pesquisas são anônimas por desenho (sem nome, telefone ou CPF).

## 4. Telas de importação (só admin)

Substituem a antiga convenção de pastas. Todas com preview antes de gravar, validação e log em `importacoes`.

1. **Importar semana**: cria/seleciona a semana e recebe dois CSVs (ou digitação manual):
   - SLA: `Mes;Solicitado;No_prazo;Fora_prazo;taxa` (separador `;`, decimal vírgula, encoding latin1 ou utf-8)
   - Diárias: `Mes;Solicitado;Entregue;Taxa`
   - Aceitar também digitar os 5 números direto num formulário — é pouca coisa por semana.
2. **Importar temporada**: upload do CSV dia × função com as colunas: `Dia;Funcao;Solicitado;Trabalhou;Folga;Atestado;Outra justificativa;Falta;Fora do contrato;Entregue;Escala` (demais colunas do arquivo são derivadas, recalcule no banco).
3. **Importar pesquisa**: upload do XLSX exportado do Google Forms (rodada 1 ou 2). Mapear os títulos longos das perguntas para as colunas canônicas acima (traga o mapeamento pronto; os títulos exatos estão na seção 9). Reimportar a mesma rodada substitui os dados dela (a coleta é cumulativa no Forms).

## 5. Estrutura de navegação

Cabeçalho com título "Dashboard Operacional Mendes RH", subtítulo "Gestão de Temporários — Aviva / Rio Quente Resorts", logo da parceria (deixe um placeholder para eu subir a imagem) e um filtro global de período.

Filtro de período: agrupado por mês (ex.: "Agosto/2026 — mês inteiro", depois cada semana) + opção "Ano inteiro (todas as semanas)". Selecionar um mês agrega todas as semanas dele.

Abas (pílulas horizontais):
1. **Visão Geral**
2. **Análise SLA**
3. **Diárias**
4. **Histórico Mensal**
5. **Temporada Jul/26** (só aparece se existir temporada cadastrada; preparada para futuras temporadas)
6. **Pesquisa Jul/26** — com sub-abas **Rodada 1**, **Rodada 2** e **Consolidado**

## 6. Conteúdo de cada aba

Cada aba segue o mesmo padrão: uma faixa hero no topo com KPIs, depois cartões com gráficos, e no fim um cartão "Leitura da operação" com um texto analítico (gere o texto dinamicamente a partir dos números, em primeira pessoa, como se eu, Mendes RH, escrevesse para a Aviva — nunca conselhos internos meus).

### 6.1 Visão Geral
Hero com 4 KPIs (cada um com sparkline da série semanal): Vagas solicitadas, SLA de fechamento (badge "meta 100%"), Diárias entregues, Atendimento de diárias (badge "meta 100%"; subtexto "saldo de +N" ou "déficit de N").
Gráficos lado a lado: rosca do SLA (No prazo × Fora do prazo, furo 62%, total no centro) e barras Solicitadas × Entregues.
Nota de alerta: se faltaram diárias, aviso amarelo "Faltaram N diárias…"; se cobriu, nota verde.

### 6.2 Análise SLA
Hero: Vagas solicitadas, Fechadas no prazo, Fora do prazo (badge "meta: zero").
Gauge do SLA com linha da meta em 100% (cor da barra: verde ≥100, amarelo ≥90, vermelho abaixo) + barras de SLA por período com linha de meta tracejada.
Texto analítico. Contexto para os textos: os pedidos (STH) chegam com ~20 dias de antecedência, então atraso não é falta de aviso, é gargalo de captação/admissão.

### 6.3 Diárias
Hero: Solicitadas, Entregues (saldo/déficit), Taxa de atendimento (meta 100%).
Barras agrupadas Solicitadas × Entregues por período + barras da taxa por período com meta tracejada e cor semáforo.

### 6.4 Histórico Mensal
Série completa do contrato, semana a semana: linha/área da entrega (Solicitado × Entregue) e do SLA ao longo de todas as semanas do banco, agrupável por mês. É a visão "o ano inteiro de uma vez".

### 6.5 Temporada Jul/26
Metas próprias: absenteísmo ≤ 5%, cobertura ≥ 95%.
- Hero com totais da temporada: Solicitado, Entregue, Cobertura %, Absenteísmo %, Saldo.
- Solicitado × entregue dia a dia (barras + linha).
- Absenteísmo diário (linha com meta tracejada em 5%).
- Solicitado × entregue por função.
- Absenteísmo por função (ranking horizontal) + composição do dia entregue (Trabalhou/Folga/Atestado/Falta…).
- Mapa de calor: absenteísmo por função × dia.
- Tabela resumo por função.

### 6.6 Pesquisa Jul/26

Método comum às três sub-abas:
- **Índice de recomendação (método eNPS)**: notas 9–10 = recomenda; 7–8 = neutro (fica fora da conta); 0–6 = não recomenda. Índice = %recomenda − %não recomenda, escala −100 a +100.
- **Anonimato**: qualquer recorte (por função, local etc.) com menos de 5 respostas não é exibido — mostrar "menos de 5 respostas, recorte suprimido".
- Sempre que citar um índice, mostrar a conta: "X% deram 9 ou 10… Y% deram 0 a 6… X − Y = Índice".
- Rótulos vindos do Forms com travessão são normalizados para vírgula na exibição.

**Sub-aba Rodada 1 (experiência e saída)**: hero com n de respostas, taxa de resposta, índice de recomendação, % que voltaria. Quem respondeu por função e por local; índice geral e por função; por que se falta (ranking de causas); preditores de falta (quem se sentiu ouvido falta menos; erro de pagamento e falta); a janela da saída (momento em que decidiu sair); matriz por função; texto "O que lemos nesta rodada" e "O que proponho".

**Sub-aba Rodada 2 (salário, condições, efetivação)**: hero com n, taxa, nota média do salário, índice do salário, nota das condições, % interessados em CLT. Distribuição da nota do salário (0–10) e índice; expectativa × recebido; comparação com o mercado da região; o que mais faria diferença no pagamento; distribuição da nota das condições e o que melhorar; "Você se sentiu respeitado(a)?" (contagens agregadas apenas — ver regra de privacidade); correlação respeito × notas; interesse em efetivação CLT na Aviva e o que pesa contra.

**Sub-aba Consolidado**: hero "Duas rodadas de escuta, um retrato"; os três índices lado a lado (recomendação, salário, condições); o que as duas rodadas dizem sobre os mesmos temas; textos "Como eu leio tudo isso" e "O que proponho". Registrar a limitação: as duas rodadas têm populações sobrepostas mas não idênticas — não são amostras independentes.

## 7. Relatório para reunião

Botão (admin e viewer) "Gerar relatório" que monta uma versão imprimível (print para PDF do navegador) das seções selecionadas, com os mesmos números e gráficos das telas — tela e relatório nunca podem divergir. Cabeçalho com logo, período e data de geração.

## 8. Sistema visual (seguir à risca)

Identidade sóbria, corporativa, clara. Fundo da aplicação `#f4f5f7`, cartões brancos, raio 18px, borda `rgba(11,11,11,.08)`, sombra suave `0 10px 30px -14px rgba(11,11,11,.16)`.

**Paleta (validada para daltonismo — manter):**
- Categóricas: azul `#2a78d6`, laranja `#eb6834`, verde `#1baf7a`, roxo auxiliar `#4a3aa7`
- Semáforo: bom `#0ca30c`, atenção `#fab219`, sério `#ec835a`, crítico `#d03b3b`
- Texto: tinta `#0b0b0b`, secundário `#52514e`, apagado `#898781`
- Grade de gráfico `#eceae4`, eixo `#c3c2b7`, superfície `#ffffff`
- Sequencial (heatmap): de `#eef5fe` até `#0d366b` passando por `#2a78d6`
- Nenhuma informação pode depender só de cor: todo elemento colorido leva rótulo ou legenda.

**Hero**: gradiente `linear-gradient(125deg, #0d366b 0%, #1c5cab 52%, #2a78d6 100%)`, raio 20px, texto branco; KPIs em tiles translúcidos (`rgba(255,255,255,.10)`, borda `rgba(255,255,255,.16)`, raio 14px) com rótulo uppercase pequeno, valor grande (1.9rem, peso 780), sparkline branca e badge em pílula.

**Abas**: pílulas (raio 999px); ativa preenchida de azul `#2a78d6` com sombra, inativas brancas com texto cinza; hover contorna de azul.

**Títulos de seção**: título + "kicker" em pílula azul clara (`#eaf2fd`, texto `#2a78d6`, uppercase, 0.7rem).

**Notas/análises**: bloco com borda esquerda de 4px (azul padrão; verde `#0ca30c` para boa notícia; amarelo `#fab219` para atenção; vermelho `#d03b3b` para problema), fundo quase branco correspondente.

**Tipografia**: system-ui / Segoe UI / Roboto. Títulos com letter-spacing negativo leve.

**Gráficos** (Recharts ou similar): fundo branco, sem moldura, grade horizontal sutil `#eceae4`, rótulos de dados em negrito sobre as barras, linhas de meta tracejadas em `#52514e`, tooltips com fundo branco. Cores semáforo nas barras de taxa contra meta.

**Formato de números pt-BR em TUDO**: vírgula decimal, ponto de milhar (3.600 · 95,4%).

## 9. Mapeamento das perguntas do Google Forms (para o importador)

Rodada 1 (títulos exatos → coluna canônica):
- "Em qual função você trabalhou?" → funcao
- "Onde você trabalhou a maior parte do tempo?" → local
- "Onde você mora?" → moradia
- "Como você ia e voltava do trabalho?" → transporte
- "Sua saída foi decisão sua ou da empresa?" → decisao_saida
- "Se você foi desligado, sabe qual foi o motivo?" → motivo_desligamento
- "Quanto tempo você ficou antes de sair?" → tempo_permanencia
- "Qual foi o motivo REAL da sua saída?" → motivo_real_saida
- "Teve algum outro motivo que também pesou?" → outro_motivo
- "Em que momento você decidiu que ia sair?" → momento_decisao
- "Antes de sair, você chegou a faltar?" → faltou
- "O que fez você faltar?" → causa_falta
- "Depois da sua primeira falta, alguém da Mendes RH ou da liderança conversou com você?" → alguem_conversou
- "O que teria feito você ficar até o fim do contrato?" → o_que_faria_ficar
- "Você avisou alguém antes de sair?" → avisou
- "De 0 a 10, o quanto você indicaria a Mendes RH para um amigo trabalhar?" → nps
- "Você aceitaria trabalhar de novo com a Mendes RH?" → voltaria (normalizar "Com certeza" → "Sim")
- "O que você diria para a gente melhorar?" → sugestao

Rodada 2:
- "Em qual função você trabalhou na temporada de julho?" → funcao
- "Você ficou até o fim da temporada?" → cumpriu_temporada
- "De 0 a 10, que nota você dá para o valor do salario que recebeu na temporada?" → nota_salario
- "O valor recebido atendeu o que você esperava quando aceitou a vaga?" → expectativa
- "Comparando com outros trabalhos temporários que você conhece na região, o pagamento da Mendes RH…" → comparacao_mercado
- "O que mais faria diferença para você no pagamento?" → alavanca_pagamento
- "De 0 a 10, que nota você dá para as condições de trabalho no dia a dia?" → nota_condicoes
- "O que mais precisa melhorar?" → o_que_melhorar
- "Você se sentiu respeitado(a) no ambiente de trabalho?" → respeito
- "Se quiser, conte uma situação em que você não se sentiu respeitado(a)." → relato_desrespeito (RESTRITO)
- "Você teria interesse em ser efetivado(a) como CLT na Aviva / Rio Quente?" → interesse_clt
- "Em qual área você gostaria de trabalhar como efetivo?" / "Em qual área você gostaria de trabalhar, se as condições fossem boas?" → area_desejada (unir as duas colunas)
- "O que pesa contra?" (existe duas vezes, nos caminhos Talvez e Não) → o_que_pesa_contra (unir)
- "Quer deixar mais algum comentário, sugestão ou elogio?" → comentario_final
- Perguntas de múltipla escolha com respostas separadas por ";" no Forms: dividir antes de contar.

## 10. Ordem de construção sugerida

1. Autenticação + papéis + esqueleto de navegação com o sistema visual.
2. Banco (tabelas + RLS) e telas de importação de semana.
3. Abas Visão Geral, Análise SLA, Diárias e Histórico Mensal.
4. Importação e aba da Temporada.
5. Importação e aba da Pesquisa (3 sub-abas, com as regras de anonimato e privacidade).
6. Relatório imprimível.

Comece pela etapa 1 e me mostre antes de seguir.
