# Pesquisa da Temporada — pacote de aplicação

## O que mudou nesta versão

1. **A divisão não é mais “ativo × demitido”.** Como praticamente todo mundo já
   foi desligado no fim da temporada, essa quebra ficou vazia de sentido. Agora
   os dois grupos são:
   - **cumpriu** — ficou até o fim do contrato da temporada de julho;
   - **saiu** — saiu antes do fim, tanto por pedido de demissão quanto por
     desligamento pela empresa.

   Voluntária × involuntária deixou de separar formulários e virou a **primeira
   pergunta** do questionário de saída — assim dá para ler os dois casos juntos
   ou separados.

2. **O incentivo deixou de ser sorteio.** Todo mundo que responder ganha **um
   par de ingressos do Hot Park**. Para emitir, o cadastro pede **nome completo,
   CPF e e-mail** — em formulário separado, com planilha própria. A planilha das
   respostas continua sem nome, sem CPF e sem contato.

## Arquivos

| Arquivo | O que é |
|---|---|
| `Pesquisa_Temporada_Mendes_RH.docx` | Documento com o diagnóstico da pesquisa anterior, os dois questionários completos e o plano de aplicação. É o material para aprovar internamente e mostrar ao cliente. |
| `criar_formularios.gs` | Script que cria (ou atualiza) os 3 formulários do Google e a planilha de respostas. |
| `disparador_whatsapp.html` | Painel de disparo. Abre no navegador, lê sua lista e envia um a um pelo WhatsApp. |
| `cabecalho_formulario.png` | Imagem de cabeçalho para aplicar no tema dos formulários. |

## Passo a passo

### 1. Atualizar os formulários que já existem (5 minutos)

Você já rodou `criarTudo()` — os três formulários existem na sua conta. Para
aplicar as mudanças **sem perder o tema, a imagem e os links**:

1. Abra o projeto em **script.google.com** e substitua o conteúdo pelo novo
   `criar_formularios.gs`.
2. Pegue os três IDs na URL de edição de cada formulário
   (`docs.google.com/forms/d/`**`ID`**`/edit`) e cole no topo do arquivo:
   - o formulário **Pesquisa da Temporada** → `ID_CUMPRIU`
   - o formulário **Pesquisa de Saída** → `ID_SAIU`
   - o formulário do **sorteio** → `ID_INGRESSOS`
3. Ajuste, se quiser, `PREMIO`, `PREMIO_CURT` e `PRAZO`.
4. No menu suspenso de funções escolha **atualizarTudo** e clique em
   **Executar**.
5. Abra o log com **Ctrl+Enter** e confira os links.

> `atualizarTudo()` **apaga e recria as perguntas**. Faça isso antes de começar
> a coletar respostas. Se já houver respostas, as colunas antigas ficam
> desalinhadas.

Se preferir começar do zero, use `criarTudo()` — mas o tema e a imagem terão de
ser aplicados de novo, à mão.

### 2. Revisar (15 minutos)

Abra os links de edição e ajuste o que quiser — em especial as opções de
**local de moradia** e **local de trabalho**. A estrutura já vem pronta: seções,
tipos de pergunta, opções, escalas com rótulo e mensagem de conclusão.

### 3. Separar a lista

Monte um arquivo com três colunas:

```
Nome; Telefone; Grupo
Maria da Silva; 64992345678; cumpriu
João Pereira; 64 99876-5432; saiu
```

O grupo aceita `cumpriu` ou `saiu` (também valem `saiu antes`, `desligado`,
`demitido`, `pediu`). Em branco entra como `cumpriu`.

Como classificar: quem tem ponto até o último dia do pedido **cumpriu**; quem
tem data de saída anterior ao fim do contrato entra em **saiu**. O espelho de
ponto e o controle de STH já dão essa separação.

### 4. Disparar

1. Abra `disparador_whatsapp.html` (duplo clique — abre no navegador).
2. Cole os **dois links de pesquisa** no campo 1.
3. Cole ou importe a lista no campo 2 e clique em **Carregar lista**.
4. Revise a mensagem no campo 3.
5. No campo 4, clique em **Abrir WhatsApp** (ou aperte Enter). Abre a conversa
   com o texto pronto — você envia e volta. O próximo já está na fila.

Antes de fechar o navegador, clique em **Baixar controle de envios** para não
perder o progresso.

> **Não envie o link do cadastro de ingressos por WhatsApp.** Ele aparece
> sozinho na tela final de quem termina a pesquisa. Se circular solto, gente que
> não respondeu se cadastra e o número de ingressos deixa de bater com o de
> respostas.

> Na primeira vez o navegador pode bloquear a abertura da aba. Clique no ícone
> de bloqueio na barra de endereço e permita pop-ups para a página.

### 5. Reforço

4 dias depois, dispare de novo só para quem não respondeu. Use o controle de
envios como base. A segunda mensagem costuma render metade das respostas.

### 6. Emitir os ingressos

1. Abra a planilha do cadastro de retirada.
2. Confira **CPF duplicado** — cadastro em duplicidade é cancelado, e o
   formulário avisa isso.
3. Confira o total: cadastros não podem passar do total de respostas das duas
   pesquisas somadas. Se passar, o link vazou — troque o formulário.
4. Emita e envie os vouchers para o e-mail informado.
5. Depois da entrega e do prazo de conferência, **apague a coluna de CPF**.
   Nome e e-mail bastam como comprovação.

### 7. Ligar no dashboard

1. Abra a planilha de respostas.
2. **Arquivo → Compartilhar → Publicar na web**.
3. Escolha a aba de respostas e o formato **CSV**. Publique e copie o link.
4. Me mande o link — a aba de pesquisa do dashboard passa a ler os resultados em
   tempo real.

## Regras que não devem ser quebradas

- Não enviar pelo número pessoal de quem gere a equipe — usar o número
  institucional do RH.
- Nunca responder individualmente a uma resposta da pesquisa. Quebra o
  anonimato prometido e derruba a confiança nas próximas rodadas.
- Não apresentar recorte com menos de 5 respostas por função: nesse volume,
  quem respondeu é identificável.
- O cadastro dos ingressos fica em planilha separada. Nunca juntar com as
  respostas — é isso que sustenta a promessa de anonimato quando alguém
  perguntar por que pedimos o CPF.
- O CPF serve só para emitir o ingresso. Não vai para banco de talentos, não vai
  para o cliente, não entra em comunicação futura.
