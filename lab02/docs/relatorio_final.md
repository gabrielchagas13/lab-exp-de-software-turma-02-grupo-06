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
| **Status deste documento** | 🟡 **Rascunho — Sprint 2 em andamento, Sprint 3 (issues #47, #48) ainda não iniciada.** Seções 4 e 5 têm apenas estatística descritiva sobre os dados coletados até agora; não substituem o teste de Wilcoxon pareado, que é quem de fato responde H0/H1. |

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
- **RQ3 (qualidade estrutural):** o código final de cada trial é arquivado em `data/trials/<trial_id>/`. [`scripts/aggregate_static_metrics.py`](../scripts/aggregate_static_metrics.py) (novo, issue #49) percorre esse arquivo por trial e roda `radon raw` (LOC), `radon cc` (complexidade ciclomática média) e `jscpd` (duplicação) via [`scripts/collect_metrics.py`](../scripts/collect_metrics.py) (issue #31), consolidando em `data/metrics.csv`.
- **Rastreabilidade:** cada uma das 12 combinações kata×participante×tratamento é uma Issue individual no board (#35–#46), Assignee = participante responsável, exigido pelo enunciado.

### 3.3 Etapas

| Sprint | Entregas | Responsável(is) | Issues | Status |
|---|---|---|---|---|
| Lab02S01 | Desenho do experimento (hipóteses, katas, ambiente, scripts de tempo/métricas) | Gabriel (katas, hipóteses), Marcus (cronometragem, desenho experimental), Guilherme (ambiente, métricas estáticas) | #26–#32 | ✅ Concluída |
| Lab02S02 | Execução dos 12 trials + coleta de dados | Todo o grupo, 4 trials cada | #35–#46 | 🟡 **8/12 trials executados** — faltam os 4 da Guilherme (#39–#42) |
| Lab02S03 | Análise estatística (Wilcoxon, RQ1–RQ3) + dashboard | Marcus (#47), Guilherme (#48), Gabriel (#49) | #47–#49 | 🟡 Dashboard pronto (#49); análise estatística formal (#47, #48) ainda não iniciada |
| Relatório Final | Documento consolidado | Todo o grupo | #50 | 🟡 Este rascunho |

### 3.4 Ferramentas

- **Cronometragem e execução:** Python (stdlib) + `pytest`, script próprio (`timer.py`).
- **Métricas estáticas:** `radon` (LOC, complexidade ciclomática), `jscpd` (duplicação via Node/`npx`).
- **Análise estatística (pendente):** Wilcoxon signed-rank pareado — biblioteca a definir pelo grupo nas issues #47/#48 (ex.: `scipy.stats.wilcoxon`).
- **Visualização:** dashboard HTML autocontido (Chart.js + SVG), gerado por [`scripts/dashboard.py`](../scripts/dashboard.py) a partir de `data/trials.csv` + `data/metrics.csv` — ver `lab02/dashboard.html`.
- **Processo:** GitHub Projects (v2), mesmo board do Lab01.

### 3.5 Tabela de métricas

| RQ | Métrica | Definição operacional | Unidade | Ferramenta |
|---|---|---|---|---|
| RQ1 | `time_to_green_seconds` | Tempo até passar em todos os testes (geração + depuração); censurado em 2100s | Segundos | `timer.py` |
| RQ2 | `success_rate` | Testes passando / testes totais ao fim do time-box | Proporção [0,1] | `timer.py` |
| RQ3 | `cyclomatic_complexity_mean` | Complexidade ciclomática média por função/método | Adimensional | Radon `cc` |
| RQ3 | `duplication_pct` | % de código duplicado | Percentual | jscpd |
| RQ3 | `loc` | Linhas de código (controle, obrigatório) | Contagem | Radon `raw` |

### 3.6 Achados de processo durante a preparação do dashboard (issue #49)

- **Bug corrigido em `collect_metrics.py`:** `get_radon_cc` filtrava `isinstance(file_blocks, dict)`, mas o radon retorna uma **lista** de blocos por arquivo — o filtro descartava todo resultado válido e zerava a complexidade ciclomática de 100% dos trials. Corrigido antes de gerar `data/metrics.csv`.
- **Inconsistência de dados a resolver com o Marcus:** os 4 trials dele em `data/trials.csv` apontam para diretórios em `data/trials/` que não existem (`marcusvv12_ia_total_...`); existem, em vez disso, diretórios órfãos com nomenclatura antiga (`marcus_ai_...`), de uma execução anterior à padronização dos identificadores. Sem o `solution_path` correto, os 4 trials do Marcus **não entram em RQ3** (LOC/CC/duplicação) até isso ser corrigido — não afeta RQ1/RQ2, que vêm direto de `trials.csv`.

---

## 4. Resultados (parciais — 8/12 trials, 2/3 participantes)

### 4.1 Coleta de dados

**8 de 12 trials coletados** (Gabriel: 4/4 completos; Marcus: 4/4 completos; Guilherme: 0/4, issues #39–#42 em backlog). RQ3 (métricas estáticas) só tem cobertura para os 4 trials do Gabriel, pela inconsistência descrita na Seção 3.6 — **n=2 por tratamento** para LOC/CC/duplicação, amostra pequena demais para qualquer leitura conclusiva.

### 4.2 Estatística descritiva por tratamento

| Métrica | IA (geração integral) | Manual |
|---|---|---|
| Time-to-green (mediana, s) | 40,85 (n=4, IQR [31,2–50,7]) | 378,3 (n=3, IQR [268,8–526,3], 1 censurado) |
| Success rate (mediana) | 1,00 (n=4, IQR [1,00–1,00]) | 1,00 (n=4, IQR [0,75–1,00]) |
| LOC (mediana) | 18,0 (n=2) | 13,5 (n=2) |
| Complexidade ciclomática (mediana) | 2,5 (n=2) | 1,5 (n=2) |
| Duplicação % (mediana) | 0,0 (n=2) | 0,0 (n=2) |

### 4.3 Comparação pareada por participante (RQ1/RQ2)

| Participante | Mediana tempo IA (s) | Mediana tempo Manual (s) | Success IA | Success Manual |
|---|---|---|---|---|
| Gabriel Chagas | 41,1 | 674,2 | 1,00 | 0,50 (1 trial censurado em 0/5) |
| Marcus Vinicius | 40,9 | 268,8 | 1,00 | 1,00 |
| Guilherme Lana | — (sem dados) | — (sem dados) | — | — |

Ver `lab02/dashboard.html` para os gráficos pareados por participante (RQ1/RQ2), o perfil normalizado de RQ3 e a tabela completa de trials — gerado por [`scripts/dashboard.py`](../scripts/dashboard.py), reexecutável a qualquer momento conforme mais trials entrarem.

### 4.4 Discussão preliminar

**⚠️ Estes números são descritivos, não testados estatisticamente — nenhuma hipótese pode ser considerada confirmada ou refutada nesta etapa.** Ainda assim, alguns padrões chamam atenção nos 8 trials disponíveis:

- Em ambos os participantes com dados completos, o tratamento IA foi **consistentemente mais rápido** (mediana ~9x menor que o Manual), alinhado com H1 de RQ1 — mas com n=2 pares, qualquer teste teria poder estatístico quase nulo.
- O único trial censurado (0/5 testes, time-box esgotado) ocorreu no tratamento **Manual** (kata 03, Gabriel), o que empurra a mediana de success_rate do Manual para baixo (0,75 no agregado) — contraintuitivo frente à hipótese informal de que IA gera mais defeitos; mas é um único evento, não um padrão.
- RQ3 não tem amostra suficiente (n=2 por tratamento, só o Gabriel) para qualquer leitura — depende da correção dos arquivos do Marcus e da execução dos trials da Guilherme.

---

## 5. Conclusão (preliminar)

Este documento não pode ainda responder RQ1–RQ3 com rigor estatístico: faltam os 4 trials da Guilherme (issues #39–#42), a correção dos arquivos arquivados do Marcus para completar RQ3, e o teste de Wilcoxon pareado em si (issues #47 e #48). O que está pronto é a infraestrutura de análise — `data/trials.csv`, `data/metrics.csv` e `dashboard.html` já consolidam e visualizam automaticamente qualquer trial novo que entrar, sem trabalho manual adicional.

**Pendências para a versão final deste relatório:**
1. Guilherme executar e commitar os 4 trials (#39–#42).
2. Resolver os `solution_path` órfãos do Marcus (Seção 3.6) e re-rodar `aggregate_static_metrics.py`.
3. Marcus rodar o Wilcoxon pareado para RQ1/RQ2 (#47) sobre os 12 trials completos.
4. Guilherme rodar o Wilcoxon pareado para RQ3 (#48).
5. Reescrever a Seção 4 com os resultados formais (estatística de teste, p-valor, decisão sobre H0) e a Seção 5 com a conclusão real, substituindo esta versão descritiva.
6. Discutir ameaças à validade observadas na prática (ver [`docs/hipoteses_ameacas.md`](hipoteses_ameacas.md)) à luz dos dados reais — em especial o trial censurado do tratamento Manual.

---

## Referências

- Enunciado do Lab02 (Laboratório de Experimentação de Software, prof. Danilo Maia).
- [`scripts/hypotheses.py`](../scripts/hypotheses.py) — hipóteses formais (H0/H1) e ameaças à validade.
- [`docs/desenho_experimental.md`](desenho_experimental.md) — desenho crossover, contrabalanceamento (issue #29).
