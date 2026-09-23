# Resultados — RQ1 (tempo) e RQ2 (defeitos)

Issue [#47](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/47) · Sprint 3 · Reprodução: `python scripts/analyze_rq1_rq2.py`

Hipóteses conforme [`scripts/hypotheses.py`](../scripts/hypotheses.py) (issue #27); desenho e pareamento conforme [`desenho_experimental.md`](desenho_experimental.md) (issue #29).

## Método

**Dados.** Os 12 trials da Sprint 2 (`data/trials.csv`): 3 participantes × 4 katas, 6 trials em geração integral por IA e 6 manuais.

**Censura.** Um trial não chegou ao verde dentro do time-box (Gabriel, kata 03, manual). Conforme o enunciado, foi **imputado em 2100s e mantido na análise**, não descartado — descartá-lo enviesaria a comparação a favor do tratamento com mais falhas. O valor imputado é um piso (o tempo real seria ≥ 2100s), então a diferença entre tratamentos aparece **subestimada**, nunca inflada.

**Pareamento.** Cada participante contribui com **um par**: a mediana dos seus 2 trials de IA contra a mediana dos seus 2 trials manuais. É o pareamento within-subject definido na issue #29 — cada pessoa é seu próprio controle, o que remove a variação individual de habilidade da comparação. Resulta em **n = 3 pares**.

**Testes.** Wilcoxon signed-rank pareado. Unilateral em RQ1 (H1 é direcional: "menor no tratamento IA") e bilateral em RQ2 (H1 apenas afirma que difere). Descritivas em mediana e IQR, não média e desvio-padrão, por causa do N pequeno e do valor censurado, que dominaria a média.

## RQ1 — Tempo

**H0:** não há diferença na mediana do time-to-green entre os tratamentos.
**H1:** a mediana do time-to-green é menor no tratamento de geração integral por IA.

| Tratamento | n | Mediana | IQR | Min | Max |
|---|---|---|---|---|---|
| Geração integral por IA | 6 | **35,9s** | 25,6 | 10,3 | 72,0 |
| Manual | 6 | **339,9s** | 389,4 | 159,2 | 2100,0 |

Pares por participante (segundos):

| Participante | IA | Manual | Diferença |
|---|---|---|---|
| gabrielchagas13 | 41,15 | 1387,10 | −1345,95 |
| gguilhermelana | 22,35 | 241,05 | −218,70 |
| marcusvv12 | 40,85 | 268,75 | −227,90 |

**Wilcoxon pareado unilateral, n = 3: W = 0, p = 0,1250.** A α = 0,05, **não se rejeita H0**.

A mediana sob IA foi **9,5× menor** e as três diferenças apontam no mesmo sentido — nenhum participante foi mais rápido à mão.

## RQ2 — Defeitos

**H0:** não há diferença na mediana da taxa de sucesso entre os tratamentos.
**H1:** a mediana da taxa de sucesso difere entre os tratamentos.

| Tratamento | n | Mediana | Min | Trials com 100% |
|---|---|---|---|---|
| Geração integral por IA | 6 | 1,00 | 1,00 | 6/6 |
| Manual | 6 | 1,00 | 0,00 | 5/6 |

**Wilcoxon pareado bilateral, n = 3: W = 0, p = 1,0000.** A α = 0,05, **não se rejeita H0**.

Dois dos três participantes têm diferença exatamente zero (100% nos dois tratamentos); o Wilcoxon descarta empates, então o n efetivo do teste é **1**.

Observação qualitativa que o número não mostra: o único trial abaixo de 100% é o censurado. No tratamento manual a falha não apareceu como *código errado*, e sim como *não terminou no tempo*. Com um time-box de 35 minutos e katas desta dificuldade, a taxa de sucesso satura em 1,0 e praticamente não discrimina os tratamentos — RQ2 acabou medindo o time-box, não a qualidade funcional.

## Limitação central: o teste não tem poder para nada

Com n pares, o Wilcoxon tem 2ⁿ combinações de sinais sob H0, e o caso mais extremo tem probabilidade 1/2ⁿ. Com **n = 3**, o menor p-valor unilateral alcançável é **0,125**.

Ou seja: **mesmo com um efeito perfeito e unânime, o teste não conseguiria chegar a p < 0,05.** O p = 0,1250 do RQ1 é exatamente esse piso — é o resultado mais forte que este desenho é capaz de produzir. "Não rejeita H0" aqui significa *a amostra não consegue detectar efeito nenhum*, e não *não há efeito*. Ler como ausência de efeito seria erro de interpretação.

A causa é o desenho, não a execução: 3 participantes é o tamanho do grupo. Detectar significância a α = 0,05 num Wilcoxon pareado exigiria **pelo menos 5 pares** (1/2⁵ = 0,031), isto é, 5 participantes.

**Verificação exploratória.** Tratando os 12 trials como amostras independentes (Mann-Whitney U, 6 vs 6, unilateral): **U = 0, p = 0,0011**, significativo. Esse teste ignora o pareamento e portanto não responde as RQs — não substitui o Wilcoxon. Serve para mostrar que o não-rejeitar acima vem do número de pares, não da ausência de diferença nos dados.

## Como reportar isso

1. A resposta formal das duas RQs é **não se rejeita H0**.
2. Reportar junto o tamanho do efeito descritivo (9,5×) e a unanimidade das 3 diferenças — sem isso o leitor conclui que IA não fez diferença.
3. Declarar o piso de p = 0,125 explicitamente. É o que separa "testamos e não achamos" de "não era possível achar".
4. Levar o N insuficiente para as ameaças à validade (validade de conclusão) em [`hipoteses_ameacas.md`](hipoteses_ameacas.md), que hoje não lista essa ameaça.

## Arquivos gerados

| Arquivo | Conteúdo |
|---|---|
| `data/rq01_rq02_descritivas.csv` | mediana, IQR, min e max por tratamento |
| `data/rq01_rq02_pares.csv` | os 3 pares (IA, manual) por participante |
| `data/rq01_rq02_testes.csv` | estatística, p-valor e decisão de cada teste |
