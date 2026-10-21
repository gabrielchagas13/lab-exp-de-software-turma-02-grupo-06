# Heurística de release corretiva (CFR b) e F1

Issue [#67](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/67) · código em `metricas/corretiva.py` · avaliação em `validacao/avaliar_heuristica.py`.

Uma release é **corretiva** quando seu objetivo principal é corrigir um defeito recente. O CFR (b) conta as releases seguidas, em até 7 dias, por uma corretiva. A heurística é avaliada contra o consenso da amostra-ouro (267 releases com consenso; classe positiva = corretiva; meta F1 ≥ 0,70). A concordância dos avaliadores nessa dimensão é razoável (kappa de Fleiss = 0,32), o que limita o F1 alcançável.

## Versões testadas

| Versão | Regra | Precisão | Recall | F1 | Meta |
|---|---|---|---|---|---|
| v1 | Versão semver com *patch* > 0 | 0,53 | 0,89 | 0,667 | não |
| v2 | v1, ou *fix/hotfix/bugfix/revert* na tag ou no título | 0,53 | 0,89 | 0,664 | não |
| v3 | Ao menos metade dos commits novos (sem merges) cita correção | 0,68 | 0,45 | 0,541 | não |
| v4 | v1, v2 ou v3 | 0,51 | 0,93 | 0,654 | não |
| **v5** | **Versão com *patch* > 0 E release notes citam *fix/bugfix/hotfix/revert*** | **0,80** | **0,69** | **0,737** | **sim** |

Matriz de confusão da v5: 66 verdadeiros positivos, 17 falsos positivos, 30 falsos negativos e 154 verdadeiros negativos.

## Por que v1 a v4 falham e o que muda na v5
- v1, v2 e v4 acham quase todas as corretivas (recall de 0,89 a 0,93), mas marcam como corretivas muitas releases que só incrementam o *patch* e trazem funcionalidade (74 a 87 falsos positivos em 267). Aqui, 53% das releases com *patch* > 0 são corretivas.
- v3 erra no sentido oposto: a mensagem do commit raramente diz *fix* nas releases corretivas (recall de 0,45).
- A v5 usa as release notes só para desempatar entre as releases com *patch*: elas confirmam ou não que houve correção. Notas sozinhas não servem, porque quase toda release tem uma seção "Bug Fixes". Dentro das releases com *patch*, a condição derruba os falsos positivos de 74 para 17.

## Refinamentos tentados e descartados
Todos partem de "*patch* > 0" e foram avaliados nas mesmas 267 releases:

| Refinamento | F1 |
|---|---|
| *patch* e fração de commits corretivos ≥ 0,2 | 0,631 |
| *patch* e (fração ≥ 0,2 ou ≤ 6 commits) | 0,647 |
| *patch* e nenhum commit de funcionalidade (`feat`, `add`, `support`...) | 0,637 |
| *patch* e notas sem seção de funcionalidades | 0,655 |
| *patch* e notas citam correção e sem seção de funcionalidades | 0,718 |
| ***patch* e notas citam correção (v5)** | **0,737** |

## Limitações (importantes para as ameaças à validade)
- **A v5 foi escolhida olhando as mesmas 267 releases em que foi avaliada.** O F1 de 0,737 é, por isso, otimista. Um bootstrap por repositório dá F1 entre 0,64 e 0,82 (IC 95%), então a meta de 0,70 não está garantida fora da amostra.
- **As release notes da planilha de rotulagem vêm truncadas**, e o pipeline vê o texto completo. O F1 no dataset pode diferir.
- O rótulo de consenso é ruidoso (kappa 0,32). Parte dos "erros" da heurística é desacordo entre avaliadores.
- A coluna `cfr_entrega_v5_patch_e_notas` só aparece no `dataset.csv` quando o pipeline for reexecutado. As variantes v1 a v4 são as que estão no dataset hoje, e as análises RQ5 e RQ6 foram feitas com elas.

## Reproduzir
```bash
python -m validacao.avaliar_heuristica --config config.json
```
Grava `data/validacao/avaliacao_heuristica.csv` (resumo por variante) e `avaliacao_heuristica_itens.csv` (previsão de cada variante por release).
