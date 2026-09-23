# Correções aplicadas aos dados brutos

Registro de toda alteração feita em `trials.csv` depois da coleta. Existe para que o
Relatório Final possa declarar o que foi mexido — dado de experimento corrigido sem
registro não é reproduzível.

## 2026-09-16 — Relabel de tratamento nos trials 02 e 04 do Marcus (#36, #38)

**O que aconteceu:** os trials dos katas `02_normalizador_tags` e `04_clusters_anagramas`
foram executados **manualmente**, mas gravados com `--treatment ai` por erro de digitação
no comando. Os quatro trials do participante ficaram rotulados como IA, o que deixaria o
Marcus sem nenhum trial manual — e, num Wilcoxon pareado, sem par ele não entra na análise.

**Correção:** `treatment` de `ai` → `manual` nas duas linhas, com renomeação das pastas
correspondentes em `data/trials/` e atualização de `trial_id` e `solution_path`.

**Evidência que sustenta o relabel** (o código final arquivado de cada trial):

- Kata 02 e 04 usam identificadores em português (`frequencias`, `ranking`, `grupos`,
  `palavra`, `chave`, `resultado`), preservam o cabeçalho original do stub
  (`"Implemente a funcao abaixo"`) e têm espaços em branco sobrando no fim de linhas.
- Os trials de IA (katas 01 e 03) têm cabeçalho substituído (`Trial: marcus (MV) |
  tratamento: IA`), identificadores em inglês e comentários explicativos.
- O kata 02 em particular passou por uma correção de `tag.strip.lower()` para
  `tag.strip().lower()` durante o trial — erro de digitação característico de código
  escrito à mão.

## 2026-09-16 — Padronização de vocabulário

`participant` de `marcus` → `marcusvv12` e `treatment` de `ai` → `ia_total`, alinhando
`trials.csv` com [`scripts/trial_plan.py`](../scripts/trial_plan.py), o plano oficial de
contrabalanceamento (issue #29). Sem isso, o join entre os dados coletados e o plano
falharia na análise da Sprint 3.

Para evitar a repetição do erro acima, `scripts/timer.py` passou a validar
`(participante, kata, tratamento)` contra `trial_plan.TRIALS` antes de iniciar o
cronômetro, e aborta se a combinação não bater com o plano.

## Trials descartados (piloto)

`data/trials/` contém duas pastas com timestamp `16:45` e `16:53` sem linha correspondente
em `trials.csv`. São as duas primeiras execuções do Marcus (katas 01 e 03), descartadas
como **piloto**: o tempo medido foi dominado pelo participante aprendendo a operar o
`timer.py`, não pela resolução do kata. Foram refeitas às `17:13` e `17:14`, já com o
fluxo conhecido. Mantidas em disco apenas como rastro de procedência; não entram em
nenhuma análise.
