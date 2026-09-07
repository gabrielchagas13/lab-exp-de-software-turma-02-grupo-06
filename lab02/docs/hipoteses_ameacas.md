# Hipóteses e ameaças à validade (issue #27)

Hipóteses formais (H0/H1) definidas como código em [`lab02/scripts/hypotheses.py`](../scripts/hypotheses.py) — para serem reaproveitadas pelo script de análise estatística e pela geração do relatório final na Sprint 3, sem duplicar o texto.

## Hipóteses por RQ

### RQ1 — Tempo
- **H0:** não há diferença na mediana do time-to-green entre trials com e sem assistente de IA.
- **H1:** a mediana do time-to-green é menor nos trials com assistente de IA.
- Trials não concluídos no time-box (35 min) são censurados em 35 min, não descartados.

### RQ2 — Defeitos
- **H0:** não há diferença na mediana da taxa de sucesso (% testes passando) entre os dois tratamentos.
- **H1:** a mediana da taxa de sucesso é maior nos trials com assistente de IA.

### RQ3 — Estrutura do código
- **H0:** não há diferença na mediana da complexidade ciclomática média nem na duplicação (normalizadas por LOC) entre os dois tratamentos.
- **H1:** a mediana da complexidade ciclomática e/ou da duplicação difere entre os tratamentos.

Teste estatístico único para as três RQs: **Wilcoxon signed-rank** (pareado, consistente com o desenho within-subject), com mediana e IQR nas descritivas.

## Ameaças à validade

| Ameaça | Mitigação |
|---|---|
| Efeito de aprendizado entre katas | Ordem de katas e tratamento contrabalanceada entre integrantes (issue #29) |
| Familiaridade prévia com a ferramenta de IA | Mesmo assistente de IA para todos os trials (issue #30); familiaridade prévia registrada como limitação no relatório final |
| Vazamento de solução já vista / memorização | Katas autorais, não publicados (issue #26, ver `katas_escolhidos.md`) |
| Variação individual de habilidade | Desenho crossover/within-subject — cada integrante é seu próprio controle (issue #29) |
| Trial não concluído no time-box | Censura em 35 min, não descarte (evita enviesar a favor do tratamento com mais falhas) |

Detalhamento de cada ameaça e sua mitigação em [`lab02/scripts/hypotheses.py`](../scripts/hypotheses.py) (lista `THREATS_TO_VALIDITY`).
