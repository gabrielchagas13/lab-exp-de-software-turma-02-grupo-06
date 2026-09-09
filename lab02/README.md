# LAB02 — Assistentes de IA vs. codificação manual (20 pontos)

**Curso:** Engenharia de Software · **Disciplina:** Laboratório de Experimentação de Software · **Turno/Período:** Noite / 6º · **Professor(a):** Danilo Maia

Experimento controlado (crossover within-subject) para comparar o uso de um assistente de IA generativa contra codificação manual, na resolução de katas de programação, quanto a tempo, defeitos e qualidade estrutural do código.

Board: mesmo GitHub Projects (v2) do grupo — "KANBAN - Lab Grupo 06" — usado desde o Lab01.

## Questões de Pesquisa (GQM)

**Goal:** Analisar o uso de assistentes de IA generativa na resolução de tarefas de programação, comparando seu efeito frente à codificação manual, quanto a tempo de resolução, qualidade funcional (defeitos) e qualidade estrutural do código, do ponto de vista do grupo pesquisador, em katas de dificuldade equivalente resolvidos sob condições controladas (crossover within-subject, time-boxed).

| RQ | Pergunta | Métricas candidatas |
|---|---|---|
| RQ1 | O uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação? | Time-to-green (mediana por tratamento); trials sem sucesso censurados em 35 min, não descartados |
| RQ2 | O uso de assistente de IA reduz a quantidade de defeitos (testes que falham) no código produzido? | Taxa de sucesso (% testes passando); nº absoluto de testes falhando |
| RQ3 | O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido? | Complexidade ciclomática (CK/Radon); duplicação (PMD CPD/jscpd); LOC (controle obrigatório) |

*(As métricas exatas a usar em cada RQ, e a justificativa da escolha, ainda precisam ser definidas pelo grupo — ver issues #26-#32 abaixo.)*

## Desenho do experimento (a definir pelo grupo)

- **Hipóteses (H0/H1):** ✅ pronto — [`lab02/scripts/hypotheses.py`](scripts/hypotheses.py) + [`lab02/docs/hipoteses_ameacas.md`](docs/hipoteses_ameacas.md) — issue [#27](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/27)
- **Variáveis, tratamentos e crossover:** ✅ pronto — [`lab02/docs/desenho_experimental.md`](docs/desenho_experimental.md) — issue [#29](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/29)
- **Katas escolhidos (4, dificuldade equivalente, autorais):** ✅ pronto — [`lab02/katas/`](katas/) + [`lab02/docs/katas_escolhidos.md`](docs/katas_escolhidos.md) — issue [#26](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/26)
- **Ameaças à validade:** ✅ pronto — [`lab02/scripts/hypotheses.py`](scripts/hypotheses.py) (`THREATS_TO_VALIDITY`) — issue [#27](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/27)
- **Ambiente / assistente de IA / linguagem:** ✅ pronto — [`lab02/docs/ambiente.md`](docs/ambiente.md) — issue [#30](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/30)

## Regras fixas do enunciado

- Time-box: **35 minutos por trial** — só pode ser reduzido, nunca aumentado
- Mesmo assistente de IA em todos os trials do grupo
- Linguagem da kata compatível com a ferramenta de métricas estáticas (CK exige Java; Radon para Python)
- Cada trial (kata × tratamento) é uma Issue individual no board, atribuída ao integrante responsável
- Análise estatística: mediana e IQR nas descritivas; teste de Wilcoxon (pareado) na inferencial
- Commits sem referência ao número da Issue não são considerados na correção

## Processo de desenvolvimento

| Sprint | Entregável | Pontos |
|---|---|---|
| Lab02S01 | Desenho do experimento + preparação (katas, ambiente, scripts de tempo e métricas) | 5 |
| Lab02S02 | Execução do experimento + coleta de dados | 5 |
| Lab02S03 | Análise de resultados (RQ1-RQ3) + Dashboard de visualização | 5 |
| Relatório Final | Documento final | 5 |

**Regra de contribuição individual:** em toda sprint, cada integrante deve ser Assignee de ao menos uma Issue com artefato de código commitado — a ausência disso zera a parcela individual do integrante na sprint.

### Sprint 1 — Lab02S01 (5 pontos)

| Issue | Tarefa | Responsável | Status |
|---|---|---|---|
| [#26](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/26) | Escolher e validar katas (4 ou 6) | Gabriel Chagas | ✅ Pronto (`lab02/katas/`, 4 katas com testes validados) |
| [#27](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/27) | Hipóteses (H0/H1) e ameaças à validade | Gabriel Chagas | ✅ Pronto (`lab02/scripts/hypotheses.py`) |
| [#28](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/28) | Script de cronometragem e coleta de tempo | Marcus Vinicius | ✅ Pronto (`lab02/scripts/timer.py`) |
| [#29](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/29) | Variáveis, tratamentos e desenho experimental | Marcus Vinicius | ✅ Pronto (`lab02/docs/desenho_experimental.md`) |
| [#30](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/30) | Preparar ambiente + escolher assistente de IA | Guilherme Lana | ✅ Pronto (`lab02/docs/ambiente.md`) |
| [#31](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/31) | Script de métricas estáticas (CK/PMD ou Radon) + LOC | Guilherme Lana | ✅ Pronto (`lab02/scripts/collect_metrics.py`) |
| [#32](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/32) | Revisão conjunta do desenho do experimento | Todo o grupo | ⬜ Backlog |

### Sprint 2 — Lab02S02 (5 pontos)

Execução: cada integrante resolve todos os katas (metade com IA, metade sem, ordem contrabalanceada). Cada trial = 1 Issue individual no board. *(Issues serão criadas depois que a Sprint 1 definir katas e ambiente.)*

### Sprint 3 — Lab02S03 (5 pontos)

- Análise estatística RQ1/RQ2 (Wilcoxon)
- Análise RQ3 (métricas estáticas)
- Dashboard de visualização (Pandas + Matplotlib/Seaborn)

### Relatório Final (5 pontos)

Introdução com hipóteses, metodologia reprodutível, resultados por RQ, discussão, link do repositório/board.

## Estrutura da pasta

```
lab02/
  katas/     # 4 katas autorais (kata.md + solution.py stub + test_solution.py)
  scripts/   # hypotheses.py (H0/H1 + ameaças), cronometragem, métricas estáticas, análise, dashboard
  data/      # tempos coletados, métricas estáticas por trial, dados agregados
  docs/      # desenho do experimento (katas, hipóteses), relatório final
```

## Setup

```bash
cd lab02
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```
