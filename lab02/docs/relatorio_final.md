# Relatório de Laboratório

| Campo | Valor |
|---|---|
| **Curso** | Engenharia de Software |
| **Disciplina** | Laboratório de Experimentação de Software |
| **Turno / Período** | Noite / 6º |
| **Professor(a)** | Danilo Maia |
| **Laboratório** | Lab02: Geração integral por IA vs. codificação manual |
| **Grupo (trio)** | Gabriel Chagas · Guilherme Lana · Marcus Vinicius |
| **Link do repositório / GitHub Projects** | https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06 |
| **Status deste documento** | ✅ **Versão final** — 12/12 trials coletados; RQ1–RQ3 testadas com Wilcoxon pareado (issues #47, #48); dashboard em `lab02/dashboard.html` (#49). |

---

## 1. Introdução

Assistentes de geração integral de código por IA prometem reduzir o tempo de desenvolvimento, mas a um custo pouco discutido: quem delega a escrita inteira do código deixa de escolher a estrutura da solução, apenas revisa (ou nem isso) o que a IA produziu. Este laboratório compara, dentro do mesmo participante (desenho crossover/within-subject), a **geração integral por IA** contra a **codificação manual tradicional** na resolução de katas de programação equivalentes, quanto a tempo total, defeitos remanescentes e qualidade estrutural do código.

Questões de pesquisa (GQM) e hipóteses formais, detalhadas em [`scripts/hypotheses.py`](../scripts/hypotheses.py) e [`docs/hipoteses_ameacas.md`](hipoteses_ameacas.md):

- **RQ1:** Delegar a geração total do código para a IA reduz o tempo total (geração + correção) necessário para resolver uma tarefa de programação, em comparação à codificação manual?
  H0: não há diferença na mediana do time-to-green entre os tratamentos. H1: a mediana é menor no tratamento IA.
- **RQ2:** O código gerado integralmente por IA apresenta mais ou menos defeitos (testes que falham) do que o código feito à mão ao final do tempo limite?
  H0: não há diferença na mediana de success_rate entre os tratamentos. H1: há diferença.
- **RQ3:** O código gerado por IA apresenta maior complexidade ciclomática, verbosidade (LOC) ou duplicação em comparação ao código desenvolvido manualmente?
  H0: não há diferença na mediana de CC, LOC ou duplicação entre os tratamentos. H1: há diferença.

Teste estatístico definido a priori para as três RQs: **Wilcoxon signed-rank pareado** (within-subject — compara, por participante, a mediana IA vs. Manual), issues #47 (RQ1/RQ2) e #48 (RQ3).

---

## 2. Contexto

Este é o **Lab02**, segundo dos cinco laboratórios do semestre. O board **GitHub Projects (v2)** ("KANBAN - Lab Grupo 06") é o mesmo herdado do Lab01, mantendo o mesmo processo (colunas, WIP, snapshots).

O objeto de estudo são **4 katas de programação autorais do grupo** (não publicados, para reduzir o risco de a IA reproduzir uma solução memorizada do treinamento), todos em Python, com a mesma "forma": função pura, sem I/O, 15–30min de esforço estimado, cada um exercitando um conceito diferente de estrutura de dados/algoritmo (agregação, normalização de string, grafo, hashing) — ver [`docs/katas_escolhidos.md`](katas_escolhidos.md).

**Ferramentas fixadas para todo o grupo** ([`docs/ambiente.md`](ambiente.md), issue #30): Python 3.10+, GitHub Copilot como assistente de IA (mesma ferramenta em todos os trials, condição de controle exigida pelo enunciado), VS Code, `pytest` para os testes de aceitação, `radon` (LOC + complexidade ciclomática) e `jscpd` (duplicação) para as métricas estáticas de RQ3.

---

## 3. Metodologia

### 3.1 Desenho experimental

Cada um dos 3 integrantes resolve os 4 katas na ordem 01→02→03→04: 2 sob tratamento IA, 2 sob tratamento Manual, contrabalanceados para que (i) cada participante fique com exatamente 2 katas em cada tratamento e (ii) cada kata seja resolvido tanto com IA quanto sem IA por integrantes diferentes. Tabela completa de atribuição e a lógica de contrabalanceamento em [`docs/desenho_experimental.md`](desenho_experimental.md) (issue #29). **12 trials no total** (6 IA / 6 Manual) — dentro da faixa 4–6 trials/integrante sugerida no enunciado para o Wilcoxon pareado, no limite inferior.

- **Tratamento A (Manual):** participante resolve sem nenhum assistente de IA (autocomplete e chat desligados), dentro do time-box.
- **Tratamento B (IA, geração integral):** participante não escreve o código base — formula um prompt descrevendo o kata, cola a solução gerada pela IA, e corrige falhas apontadas pelos testes com novos prompts, nunca reescrevendo manualmente do zero. Regra normativa completa em `TREATMENT_B_RULE` ([`scripts/hypotheses.py`](../scripts/hypotheses.py)).
- **Time-box fixo:** 35 minutos (2100s) por trial, em ambos os tratamentos. Trial que não termina a tempo é registrado como **censurado em 2100s**, não descartado (descartar enviesaria a amostra a favor do tratamento com mais falhas).

### 3.2 Coleta de dados

- **RQ1/RQ2 (tempo e defeitos):** [`scripts/timer.py`](../scripts/timer.py) (issue #28) roda pytest em polling a cada 5s no kata do participante, cronometrando automaticamente até todos os testes passarem (ou o time-box estourar). Grava uma linha por trial em `data/trials.csv`: `time_to_green_seconds`, `censored`, `success_rate`, `n_tests_passing`/`n_tests_total`, e o caminho do código final arquivado.
- **RQ3 (qualidade estrutural):** o código final de cada trial é arquivado em `data/trials/<trial_id>/`. [`scripts/analyze_rq3.py`](../scripts/analyze_rq3.py) (issue #48) extrai de cada arquivo, via Radon, LOC, SLOC, complexidade ciclomática média e índice de manutenibilidade, além da duplicação, consolidando em `data/rq03_trials_metricas.csv`. [`scripts/aggregate_static_metrics.py`](../scripts/aggregate_static_metrics.py) (issue #49) gera o recorte usado pelo dashboard (`data/metrics.csv`, LOC/CC/duplicação via [`collect_metrics.py`](../scripts/collect_metrics.py), issue #31) — os valores coincidem com os da análise.
- **Correções nos dados brutos:** dois trials manuais do Marcus foram gravados como IA por erro de digitação e corrigidos com evidência; o vocabulário de `participant`/`treatment` foi padronizado. Tudo registrado em [`data/correcoes.md`](../data/correcoes.md).
- **Rastreabilidade:** cada uma das 12 combinações kata×participante×tratamento é uma Issue individual no board (#35–#46), Assignee = participante responsável, exigido pelo enunciado.

### 3.3 Análise estatística

- **Pareamento:** cada participante contribui com **um par** — mediana dos seus 2 trials IA vs. mediana dos seus 2 trials manuais → **n = 3 pares**.
- **Teste:** Wilcoxon signed-rank pareado (`scipy.stats.wilcoxon`). Unilateral em RQ1 (H1 direcional: IA mais rápida); bilateral em RQ2 e RQ3. α = 0,05.
- **Descritivas:** mediana e IQR (não média/desvio-padrão, por causa do N pequeno e do valor censurado).
- **Censura:** o trial não concluído entra com tempo imputado em 2100s. É um piso (o tempo real seria maior), então a diferença entre tratamentos em RQ1 fica **subestimada**, nunca inflada.

### 3.4 Etapas

| Sprint | Entregas | Responsável(is) | Issues | Status |
|---|---|---|---|---|
| Lab02S01 | Desenho do experimento (hipóteses, katas, ambiente, scripts de tempo/métricas) | Gabriel (katas, hipóteses), Marcus (cronometragem, desenho experimental), Guilherme (ambiente, métricas estáticas) | #26–#31 | ✅ Concluída |
| Lab02S02 | Execução dos 12 trials + coleta de dados | Todo o grupo, 4 trials cada | #35–#46 | ✅ 12/12 trials |
| Lab02S03 | Análise estatística + dashboard | Marcus (RQ1/RQ2, #47), Guilherme (RQ3, #48), Gabriel (dashboard, #49) | #47–#49 | ✅ Concluída |
| Relatório Final | Documento consolidado | Todo o grupo | #50 | ✅ Este documento |

### 3.5 Ferramentas

- **Cronometragem e execução:** Python (stdlib) + `pytest`, script próprio (`timer.py`).
- **Métricas estáticas:** `radon` (LOC, SLOC, complexidade ciclomática, índice de manutenibilidade), `jscpd` (duplicação).
- **Análise estatística:** `scipy.stats` (Wilcoxon pareado; Mann-Whitney exploratório) — [`analyze_rq1_rq2.py`](../scripts/analyze_rq1_rq2.py), [`analyze_rq3.py`](../scripts/analyze_rq3.py).
- **Visualização:** dashboard HTML autocontido (Chart.js + SVG), gerado por [`scripts/dashboard.py`](../scripts/dashboard.py) a partir de `data/trials.csv`, `data/metrics.csv` e `data/rq*_testes.csv` — ver `lab02/dashboard.html`.
- **Processo:** GitHub Projects (v2), mesmo board do Lab01.

### 3.6 Tabela de métricas

| RQ | Métrica | Definição operacional | Unidade | Ferramenta |
|---|---|---|---|---|
| RQ1 | `time_to_green_seconds` | Tempo até passar em todos os testes (geração + depuração); censurado em 2100s | Segundos | `timer.py` |
| RQ2 | `success_rate` | Testes passando / testes totais ao fim do trial | Proporção [0,1] | `timer.py` |
| RQ3 | `cyclomatic_complexity_mean` | Complexidade ciclomática média por bloco | Adimensional | Radon `cc` |
| RQ3 | `duplication_pct` | % de código duplicado | Percentual | jscpd |
| RQ3 | `loc` / `sloc` | Linhas totais / linhas de código efetivas (controle de verbosidade) | Contagem | Radon `raw` |
| RQ3 | `maintainability_index` | Índice de manutenibilidade (complementar) | 0–100 | Radon `mi` |

### 3.7 Achados de processo

- **Bug corrigido em `collect_metrics.py` (#49):** `get_radon_cc` filtrava `isinstance(file_blocks, dict)`, mas o radon retorna uma **lista** de blocos por arquivo — o filtro zerava a complexidade ciclomática de todos os trials. Corrigido antes de qualquer análise.
- **Relabel de tratamento (#36, #38):** ver [`data/correcoes.md`](../data/correcoes.md). Para evitar repetição, `timer.py` passou a validar a combinação (participante, kata, tratamento) contra o plano oficial.
- **Pilotos descartados:** as duas primeiras execuções do Marcus (katas 01 e 03) foram tratadas como piloto (tempo dominado por aprender a usar o `timer.py`) e refeitas; ficam em disco só como rastro e não entram na análise.

---

## 4. Resultados

### 4.1 Coleta de dados

**12 de 12 trials coletados** (3 participantes × 4 katas; 6 IA / 6 manual). **1 trial censurado:** Gabriel, kata 03 (escalonador de tarefas), manual — time-box de 35 min esgotado com 0/5 testes passando. Nenhum trial com IA foi censurado.

| Participante | Kata 01 | Kata 02 | Kata 03 | Kata 04 |
|---|---|---|---|---|
| Gabriel Chagas | Manual · 674,2s | IA · 72,0s | Manual · **2100s (censurado, 0/5)** | IA · 10,3s |
| Guilherme Lana | IA · 33,7s | Manual · 180,7s | Manual · 301,4s | IA · 11,0s |
| Marcus Vinicius | IA · 38,1s | Manual · 378,3s | IA · 43,6s | Manual · 159,2s |

Todos os trials não censurados terminaram com 5/5 testes.

### 4.2 RQ1 — Tempo (issue #47)

| Tratamento | n | Mediana | IQR | Mín | Máx |
|---|---|---|---|---|---|
| IA (geração integral) | 6 | **35,9s** | 25,6 | 10,3 | 72,0 |
| Manual | 6 | **339,9s** | 389,4 | 159,2 | 2100,0* |

\* valor censurado imputado.

| Participante | Mediana IA (s) | Mediana Manual (s) | Diferença (IA − Manual) |
|---|---|---|---|
| Gabriel Chagas | 41,2 | 1387,1 | −1346,0 |
| Guilherme Lana | 22,4 | 241,1 | −218,7 |
| Marcus Vinicius | 40,9 | 268,8 | −227,9 |

**Wilcoxon pareado unilateral, n = 3: W = 0, p = 0,125 → não se rejeita H0.**

A mediana com IA foi **~9,5× menor** e os três participantes foram mais rápidos com IA. O p = 0,125 é exatamente o **menor p possível** com 3 pares — o resultado mais forte que este desenho consegue produzir (ver 4.5). Como verificação exploratória, tratando os 12 trials como independentes (Mann-Whitney U, 6 vs. 6, unilateral): U = 0, p = 0,0011. Esse teste ignora o pareamento e não responde à RQ; serve só para mostrar que o "não rejeita" vem do número de pares, não da ausência de diferença nos dados.

### 4.3 RQ2 — Defeitos (issue #47)

| Tratamento | n | Mediana success_rate | Mín | Trials com 100% |
|---|---|---|---|---|
| IA (geração integral) | 6 | 1,00 | 1,00 | 6/6 |
| Manual | 6 | 1,00 | 0,00 | 5/6 |

**Wilcoxon pareado bilateral, n = 3: W = 0, p = 1,0 → não se rejeita H0.** Dois dos três pares têm diferença exatamente zero; como o Wilcoxon descarta empates, o n efetivo do teste é 1.

A única falha é o trial manual censurado: no tratamento manual a falha apareceu como *não terminar no tempo*, não como *código errado*. Com katas desta dificuldade e 35 min de time-box, a taxa de sucesso satura em 1,0 e praticamente não discrimina os tratamentos.

### 4.4 RQ3 — Qualidade estrutural (issue #48)

| Métrica | Mediana IA | Mediana Manual | IQR IA | IQR Manual | W | p (bilateral) | Decisão |
|---|---|---|---|---|---|---|---|
| LOC | 16,0 | 21,0 | 3,0 | 12,3 | 3,0 | 1,00 | Não rejeita H0 |
| SLOC | 8,0 | 9,5 | 3,0 | 4,8 | 3,0 | 1,00 | Não rejeita H0 |
| Complexidade ciclomática média | 2,5 | 2,5 | 1,0 | 1,8 | 3,0 | 1,00 | Não rejeita H0 |
| Índice de manutenibilidade | 98,7 | 97,1 | 4,0 | 5,2 | 2,0 | 0,75 | Não rejeita H0 |
| Duplicação (%) | 0,0 | 0,0 | 0,0 | 0,0 | — | 1,00 | Não rejeita H0 (empate total) |

Diferenças por participante (IA − Manual, mediana dos 2 trials):

| Participante | LOC | CC média | MI |
|---|---|---|---|
| Gabriel Chagas | +4,5 | +1,0 | +0,6 |
| Guilherme Lana | −25,0 | −5,0 | +11,6 |
| Marcus Vinicius | +7,0 | +4,0 | −6,4 |

Ao contrário de RQ1, **não há direção consistente**: para Gabriel e Marcus o código da IA foi mais longo e mais complexo; para Guilherme, o inverso. O que mais pesa em LOC/CC é **qual kata** caiu em qual tratamento, não o tratamento: o kata 03 (escalonador) concentra os picos de complexidade (CC = 12) tanto com IA (Marcus) quanto à mão (Guilherme). A duplicação foi 0% nos 12 trials — soluções de 13 a 52 linhas não têm tamanho para gerar blocos repetidos. O código de IA foi mais **uniforme** (IQR de LOC 3,0 vs. 12,3).

### 4.5 Poder estatístico

Com n pares, o Wilcoxon tem 2ⁿ combinações de sinais sob H0; o caso mais extremo tem probabilidade 1/2ⁿ. Com **n = 3**, o menor p alcançável é **0,125 unilateral** e **0,25 bilateral**. Ou seja: **mesmo com um efeito perfeito e unânime, nenhum teste deste experimento conseguiria chegar a p < 0,05.** Seriam necessários pelo menos 5 pares (1/2⁵ = 0,031) — 5 participantes. "Não rejeita H0" aqui significa *a amostra não consegue detectar efeito*, e não *não há efeito*.

### 4.6 Visualização

O dashboard [`lab02/dashboard.html`](../dashboard.html) (issue #49) mostra: KPIs de coleta; gráficos pareados por participante (dumbbell) para RQ1 e RQ2 — exatamente a diferença que o Wilcoxon testa; medianas por tratamento para tempo, sucesso, LOC, CC e duplicação; perfil normalizado de RQ3 (radar); a tabela de testes inferenciais; e a tabela completa dos 12 trials. É regenerado por `python scripts/dashboard.py`.

---

## 5. Discussão e ameaças à validade

**Hipóteses informais vs. resultados.**

- *"IA é mais rápida"* (RQ1): os dados apontam fortemente nessa direção (≈9,5×, 3/3 participantes), mas a confirmação formal é impossível com n = 3.
- *"Código de IA tem mais defeitos"* (RQ2): não se observou. O único defeito ficou no tratamento manual — e por falta de tempo, não por código errado.
- *"Código de IA é mais verboso/complexo"* (RQ3): não se observou. A mediana de LOC da IA foi até menor, a CC foi igual e a manutenibilidade ficou na faixa mais alta nos dois tratamentos.

**Ameaças à validade** — as previstas no desenho e as observadas na análise estão em [`docs/hipoteses_ameacas.md`](hipoteses_ameacas.md). As que mais afetam as conclusões:

1. **Validade de conclusão — N insuficiente:** 3 pares não dão poder para rejeitar H0 em nenhuma RQ (seção 4.5).
2. **Construto — efeito teto em RQ2:** 11/12 trials com 100% dos testes; a métrica mediu o time-box, não a qualidade funcional.
3. **Construto — trial censurado em RQ3:** o código incompleto do trial censurado (13 LOC, CC = 1) entra na mediana manual do Gabriel e puxa LOC/CC para baixo.
4. **Interna — confusão kata × tratamento:** com 4 katas de complexidades diferentes e só 2 por tratamento por pessoa, a variação entre katas (sobretudo o kata 03) domina as métricas de RQ3.
5. **Interna — rotulagem:** relabel de 2 trials do Marcus, corrigido e documentado em [`data/correcoes.md`](../data/correcoes.md).
6. **Externa:** katas pequenos (funções puras, ≤ 52 linhas), um único assistente (GitHub Copilot) e participantes estudantes — os resultados não se generalizam para tarefas maiores, com dependências ou em código legado.

---

## 6. Conclusão

Formalmente, **nenhuma das três hipóteses nulas foi rejeitada** a α = 0,05. Isso decorre sobretudo do desenho: com 3 participantes o Wilcoxon pareado não tem como produzir p < 0,05.

Descritivamente, o experimento sugere que, em katas pequenos e bem especificados, **delegar integralmente a escrita do código à IA reduziu o tempo de resolução em cerca de uma ordem de grandeza (RQ1), sem aumentar defeitos (RQ2) nem piorar complexidade, verbosidade, duplicação ou manutenibilidade (RQ3)**. O efeito de tempo é consistente nos três participantes; os efeitos estruturais não têm direção definida e parecem depender mais do kata do que do tratamento.

**Para uma replicação:** (i) pelo menos 5 participantes (ou mais katas por pessoa, com pareamento por kata); (ii) katas maiores ou testes ocultos, para que a taxa de sucesso volte a discriminar; (iii) registrar o número de prompts de correção no tratamento IA, como métrica de esforço; (iv) tratar o código de trials censurados à parte na análise estrutural.

---

## Referências

- Enunciado do Lab02 (Laboratório de Experimentação de Software, prof. Danilo Maia).
- [`scripts/hypotheses.py`](../scripts/hypotheses.py) — hipóteses formais (H0/H1) e ameaças à validade.
- [`docs/desenho_experimental.md`](desenho_experimental.md) — desenho crossover, contrabalanceamento (issue #29).
- [`docs/resultados_rq01_rq02.md`](resultados_rq01_rq02.md) — análise detalhada de RQ1/RQ2 (issue #47).
- [`docs/resultados_rq03.md`](resultados_rq03.md) — análise detalhada de RQ3 (issue #48).
- [`data/correcoes.md`](../data/correcoes.md) — registro de correções nos dados brutos.
- Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin*, 1(6), 80–83.
