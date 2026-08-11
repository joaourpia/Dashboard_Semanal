# Como manter o dashboard organizado o ano inteiro

**Resposta curta: não precisa criar projeto novo, nem duplicar nada.** O
dashboard já foi construído para isso. O que faltava era uma convenção de nome
de pasta que não quebre quando virar o mês — e isso já está resolvido.

---

## Por que um projeto só

O dashboard tem dois tipos de conteúdo, e eles **nunca se misturam**:

| Tipo | Onde mora | Como aparece |
|---|---|---|
| **Operação corrente** — SLA, diárias, entrega | `dados/AAAA-MM-Sn (dd a dd)/` | Abas Visão Geral, Análise SLA, Diárias, Histórico. Respondem ao filtro de período. |
| **Ciclos fechados** — temporada, pesquisas | `dados/temporada_julho/`, `dados/pesquisa/` | Abas próprias. **Ignoram o filtro de período.** |

As pastas do segundo grupo estão em `PASTAS_RESERVADAS` no `app.py`. Elas nunca
entram na lista de períodos, então **julho não contamina agosto** e agosto não
apaga julho. Esse isolamento já existia; só não estava documentado.

Duplicar o projeto criaria dois problemas que você não tem hoje: duas bases de
código para corrigir quando algo mudar, e impossibilidade de comparar julho com
agosto na mesma tela.

---

## A convenção de pastas

```
dados/
├── 2026-07-S1 (01 a 06)/     ← semana de operação
├── 2026-07-S2 (07 a 13)/
├── 2026-07-S3 (14 a 20)/
├── 2026-07-S4 (21 a 27)/
├── 2026-08-S1 (28 a 03)/     ← próxima a criar
├── temporada_julho/          ← ciclo fechado, fora do filtro
└── pesquisa/                 ← ciclo fechado, fora do filtro
```

**Formato:** `AAAA-MM-Sn (dd a dd)`

- `AAAA-MM` no começo faz a ordenação ficar correta para sempre. Com o formato
  antigo (`1- 01 a 06-07`), a semana 1 de agosto apareceria antes da semana 4 de
  julho, e em janeiro de 2027 a lista viraria uma bagunça.
- `Sn` é o número da semana **dentro do mês**, não do ano — recomeça em S1 todo
  mês.
- O trecho entre parênteses é livre; serve só para você reconhecer a semana.
- A semana que cruza o mês (28/07 a 03/08) entra no mês em que **fecha**. A de
  cima é `2026-08-S1`.

Pastas fora dessa convenção continuam funcionando: aparecem como período avulso
no fim da lista, apenas sem agrupamento por mês. Nada quebra.

### O que o filtro passa a mostrar

```
Ano inteiro (todas as semanas)     ← acumulado do ano
Agosto/2026 — mês fechado          ← só aparece com 2+ semanas no mês
  2026-08-S2 (04 a 10)
  2026-08-S1 (28 a 03)
Julho/2026 — mês fechado
  2026-07-S4 (21 a 27)
  ... etc
```

O agrupamento por mês é automático. Você não cadastra nada: o nome da pasta é o
índice.

---

## Rotina semanal

1. Criar `dados/AAAA-MM-Sn (dd a dd)/`
2. Colocar dentro os quatro CSVs de sempre:
   `SLA.csv`, `ANALISE_PEDIDO.csv`, `HISTORICO_SLA.csv`, `HISTORICO_ENTREGA.csv`
3. Recarregar o app. A semana aparece sozinha no filtro.

Não há passo 4. Não precisa editar código.

---

## Rotina de fim de temporada

Quando a temporada de dezembro/janeiro chegar, o padrão é o mesmo que já foi
usado em julho:

1. Criar `dados/temporada_dezembro/` com os CSVs de absenteísmo
2. Criar `dados/pesquisa_dezembro/` com as respostas do Forms
3. Adicionar as duas pastas em `PASTAS_RESERVADAS` no `app.py`
4. Duplicar o bloco de flag da aba (`MOSTRAR_TEMPORADA` / `ABA_TEMPORADA`)

As abas de julho continuam ali, intactas, como histórico.

---

## Ligando e desligando abas sazonais

As abas de julho estão rotuladas **Temporada Jul/26** e **Pesquisa Jul/26** —
com o ano no nome, para não confundir quando houver duas temporadas no ar.

Elas aparecem automaticamente enquanto os arquivos existirem. Para esconder sem
apagar nada, há dois caminhos:

- **Sem mexer em código:** renomear a pasta para começar com `_`
  (`dados/_temporada_julho/`). O app ignora pastas com `_` na frente.
- **No código:** trocar `MOSTRAR_TEMPORADA = "auto"` por `False` no `app.py`.

Para religar, desfazer. Nenhum dado é perdido em nenhum dos casos.

---

## Backup

O único ativo insubstituível é a pasta `dados/`. O código pode ser reescrito; os
CSVs semanais e as respostas das pesquisas, não. Copie a pasta inteira para o
Drive uma vez por mês, no fechamento.

---

## Resumo das mudanças feitas nesta rodada

| O quê | Detalhe |
|---|---|
| Pastas semanais renomeadas | `1- 01 a 06-07` → `2026-07-S1 (01 a 06)` e equivalentes |
| Filtro de período | Agora agrupa por mês e oferece "Ano inteiro" |
| Abas sazonais rotuladas | "Temporada Jul/26", "Pesquisa Jul/26" |
| Aba Pesquisa | Três visões: Rodada 1, Rodada 2, Consolidado |
| Base da pesquisa | Rodada 1 atualizada (120 respostas) e rodada 2 adicionada (79) |
| Exportação | O relatório agora oferece as três seções da pesquisa separadamente |
