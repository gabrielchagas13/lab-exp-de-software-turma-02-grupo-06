# Hipóteses e ameaças à validade (issue #27)

Hipóteses formais (H0/H1) definidas como código em [`lab02/scripts/hypotheses.py`](../scripts/hypotheses.py) — para serem reaproveitadas pelo script de análise estatística e pela geração do relatório final na Sprint 3, sem duplicar o texto.

## Variável independente: método de desenvolvimento

- **Tratamento A (manual):** o integrante escreve o código do zero, sem IA.
- **Tratamento B (geração integral por IA):** o integrante **não escreve o código base**. Ele formula um prompt descrevendo o kata, a IA gera a solução inteira, e o código é colado no ambiente. Falhas identificadas pelos testes são corrigidas por **novos prompts** (não por edição manual linha a linha). O tempo do trial inclui geração + toda a depuração.

Ver `TREATMENT_B_RULE` em [`lab02/scripts/hypotheses.py`](../scripts/hypotheses.py) para o texto exato da regra.

## Hipóteses por RQ

### RQ1 — Tempo
- **H0:** não há diferença na mediana do time-to-green (geração + depuração) entre o tratamento manual e o de geração integral por IA.
- **H1:** a mediana do time-to-green é menor no tratamento de geração integral por IA.
- Trials não concluídos no time-box (35 min) são censurados em 35 min, não descartados.

### RQ2 — Defeitos
- **H0:** não há diferença na mediana da taxa de sucesso (% testes passando) entre os dois tratamentos.
- **H1:** a mediana da taxa de sucesso difere entre o tratamento manual e o de geração integral por IA.

### RQ3 — Estrutura do código
- **H0:** não há diferença na mediana da complexidade ciclomática média, no LOC (verbosidade) nem na duplicação entre os dois tratamentos.
- **H1:** a mediana da complexidade ciclomática, do LOC e/ou da duplicação difere entre os tratamentos.
- LOC é métrica de controle obrigatória: código gerado por IA tende a ser mais verboso.

Teste estatístico único para as três RQs: **Wilcoxon signed-rank** (pareado, consistente com o desenho within-subject), com mediana e IQR nas descritivas.

## Ameaças à validade

| Ameaça | Mitigação |
|---|---|
| Efeito de aprendizado entre katas | Ordem de katas e tratamento contrabalanceada entre integrantes (issue #29, `trial_plan.py`) |
| Familiaridade prévia com a ferramenta de IA | Mesma ferramenta de IA para todos os trials (issue #30); familiaridade prévia registrada como limitação no relatório final |
| Vazamento de solução já vista / memorização | Katas autorais, não publicados (issue #26, ver `katas_escolhidos.md`) |
| Alucinações da IA e tempo iterando prompts de correção | Tempo registrado é sempre o total do trial (geração + depuração via prompt); nº de prompts de correção pode ser registrado como métrica exploratória |
| Variação individual de habilidade (programação e formulação de prompts) | Desenho crossover/within-subject — cada integrante é seu próprio controle (issue #29) |
| Trial não concluído no time-box | Censura em 35 min, não descarte (evita enviesar a favor do tratamento com mais falhas) |

Detalhamento de cada ameaça e sua mitigação em [`lab02/scripts/hypotheses.py`](../scripts/hypotheses.py) (lista `THREATS_TO_VALIDITY`).
