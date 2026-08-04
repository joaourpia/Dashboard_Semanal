# Aba "Temporada" — entrega diária e absenteísmo

Pacote para `C:\Projetos_Python\Dashboard_Semanal`. Substitui a versão anterior.

## O que mudou nesta versão

- **Escopo corrigido.** O STH passa a ser usado só para *quantidade solicitada* e
  *período*. A entrega vem inteiramente do espelho de ponto, agrupada por função.
  Não há mais vínculo por nome/CPF.
- Classificação dia a dia conferida contra o `Resumo_Ponto` do controle interno:
  **177 de 177 pessoas sem divergência**.
- Gráficos com rótulos em todas as barras.
- Detalhamento reduzido à matriz função × dia (dias 1 a 31 em colunas) e à base
  por data e função. Saíram as abas de faltas nominais, reincidência e qualidade.
- "Alocado" virou **Entregue** = trabalhado + folga + atestado + justificativas.
- Visual novo: fundo neutro, cartões, faixa de indicadores e abas em pílula —
  o padrão que as demais abas vão seguir na fase 2.

## Arquivos

| Arquivo | O que é |
|---|---|
| `processar_temporada.py` | ETL. Lê STH e espelho e gera os CSVs. |
| `aba_temporada.py` | Módulo da aba. |
| `app.py` | Seu app com a aba nova + shell visual atualizado. |
| `.streamlit/config.toml` | Tema. |
| `dados/temporada_julho/entrada/` | Arquivos-fonte do mês. |
| `dados/temporada_julho/*.csv` | Saídas já geradas para julho/2026. |

## Rodar

```bat
pip install streamlit plotly pandas numpy openpyxl
streamlit run app.py
```

Para atualizar o mês: troque os arquivos em `dados\temporada_julho\entrada\`,
ajuste `ANO, MES` no topo de `processar_temporada.py` e rode
`python processar_temporada.py`.

A pasta de entrada aceita três coisas:

- `sth_temporada.xlsx` — demanda.
- `ponto_julho_2026.csv` — espelho de ponto principal.
- `diaristas*.xlsx` — espelhos complementares (contratações pontuais). Qualquer
  arquivo cujo nome comece com `diaristas` é lido automaticamente; pode haver
  mais de um. Nesses espelhos **só entra dia efetivamente trabalhado** — falta e
  atestado são ignorados e não afetam absenteísmo nem escala. Os números somam
  ao total sem qualquer distinção no painel.

## Regras de cálculo

**Entregue no dia** — batida de horário, folga, atestado ou justificativa formal.
**Não entregue** — apenas quando o espelho traz explicitamente *Falta*.
Célula `-` ou vazia = contrato não vigente, fora da conta.

**Solicitado no dia** — vagas do STH com `data inicial ≤ dia ≤ data final`,
recortadas em 01–31/07, excluídas as canceladas.

| Indicador | Fórmula |
|---|---|
| Entregue | Trabalhou + Folga + Atestado + Outras justificativas |
| Escala | Entregue + Falta |
| Absenteísmo % | Falta ÷ Escala |
| Cobertura % | Entregue ÷ Solicitado |
| Presença em posto % | Trabalhou ÷ Solicitado |

Funções que aparecem no ponto sem nenhuma vaga no STH ficam fora do escopo
(no julho: Assistente Administrativo, Coordenador e um registro sem cargo).

## Conciliação STH × ponto

O ETL grava `dados/temporada_julho/CONCILIACAO_STH.csv` e imprime no console as
funções em que o efetivo do ponto supera a demanda registrada no STH. Não entra
no painel — é material de trabalho para corrigir o controle de STH.
