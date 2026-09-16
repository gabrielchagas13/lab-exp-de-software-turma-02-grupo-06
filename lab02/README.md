# LAB02 — Geração integral por IA vs. codificação manual (20 pontos)

**Curso:** Engenharia de Software · **Disciplina:** Laboratório de Experimentação de Software · **Turno/Período:** Noite / 6º · **Professor(a):** Danilo Maia

Experimento controlado (crossover within-subject) para comparar a **delegação total da escrita do código a uma IA generativa** contra a codificação manual tradicional, na resolução de katas de programação, quanto a tempo total (geração + depuração), defeitos e qualidade estrutural do código.

Board: mesmo GitHub Projects (v2) do grupo — "KANBAN - Lab Grupo 06" — usado desde o Lab01.

## Variável independente: método de desenvolvimento

- **Tratamento A (manual):** o integrante escreve o código do zero, sem IA.
- **Tratamento B (geração integral por IA):** o integrante **não escreve o código base**. Ele formula um prompt descrevendo o kata, cola no ambiente o código gerado pela IA, e corrige eventuais falhas com **novos prompts** — nunca reescrevendo a solução manualmente do zero. O tempo do trial conta geração + toda a depuração.

Ver `TREATMENT_B_RULE` em [`lab02/scripts/hypotheses.py`](scripts/hypotheses.py) para o texto exato da regra.

## Questões de Pesquisa (GQM)

**Goal:** Analisar a delegação total a assistentes de IA generativa na resolução de tarefas de programação, comparando seu efeito frente à codificação manual, quanto a tempo de resolução (geração + correção), qualidade funcional (defeitos) e qualidade estrutural do código, do ponto de vista do grupo pesquisador, em katas de dificuldade equivalente resolvidos sob condições controladas (crossover within-subject, time-boxed).

| RQ | Pergunta | Métricas candidatas |
|---|---|---|
| RQ1 | Delegar a geração total do código para a IA reduz o tempo total (geração + correção) necessário para resolver uma tarefa de programação, em comparação à codificação manual? | Time-to-green, geração + depuração (mediana por tratamento); trials sem sucesso censurados em 35 min, não descartados |
| RQ2 | O código gerado integralmente por IA apresenta mais ou menos defeitos (testes que falham) do que o código feito à mão ao final do tempo limite? | Taxa de sucesso (% testes passando); nº absoluto de testes falhando |
| RQ3 | O código gerado por IA apresenta maior complexidade ciclomática, verbosidade ou duplicação em comparação ao código desenvolvido manualmente? | Complexidade ciclomática (CK/Radon); duplicação (PMD CPD/jscpd); LOC (controle obrigatório — código de IA tende a ser mais verboso) |

*(As métricas exatas a usar em cada RQ, e a justificativa da escolha, ainda precisam ser definidas pelo grupo — ver issues #26-#32 abaixo.)*

## Desenho do experimento (a definir pelo grupo)

- **Hipóteses (H0/H1):** ✅ pronto — [`lab02/scripts/hypotheses.py`](scripts/hypotheses.py) + [`lab02/docs/hipoteses_ameacas.md`](docs/hipoteses_ameacas.md) — issue [#27](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/27)
- **Variáveis, tratamentos e crossover:** ✅ pronto — [`lab02/docs/desenho_experimental.md`](docs/desenho_experimental.md) — issue [#29](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/29)
- **Katas escolhidos (4, dificuldade equivalente, autorais):** ✅ pronto — [`lab02/katas/`](katas/) + [`lab02/docs/katas_escolhidos.md`](docs/katas_escolhidos.md) — issue [#26](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/26)
- **Ameaças à validade:** ✅ pronto — [`lab02/scripts/hypotheses.py`](scripts/hypotheses.py) (`THREATS_TO_VALIDITY`) — issue [#27](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/27)
- **Ambiente / assistente de IA / linguagem:** ✅ pronto — [`lab02/docs/ambiente.md`](docs/ambiente.md) — issue [#30](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/30)

## Regras fixas do enunciado

- Time-box: **35 minutos por trial** — só pode ser reduzido, nunca aumentado (inclui geração + depuração no tratamento B)
- Mesma ferramenta de IA em todos os trials do grupo
- No tratamento B, o integrante não escreve o código base manualmente — só prompts (geração inicial + correções)
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
| [#26](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/26) | Escolher e validar katas (4 ou 6) | Gabriel Chagas | ✅ Fechada (`lab02/katas/`, 4 katas com testes validados) |
| [#27](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/27) | Hipóteses (H0/H1) e ameaças à validade | Gabriel Chagas | ✅ Fechada (`lab02/scripts/hypotheses.py`) |
| [#28](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/28) | Script de cronometragem e coleta de tempo | Marcus Vinicius | ✅ Pronto (`lab02/scripts/timer.py`) |
| [#29](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/29) | Variáveis, tratamentos e desenho experimental | Marcus Vinicius | ✅ Pronto (`lab02/docs/desenho_experimental.md`) — **fonte de verdade do contrabalanceamento da S02** |
| [#30](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/30) | Preparar ambiente + escolher assistente de IA | Guilherme Lana | ✅ Fechada (`lab02/docs/ambiente.md`) — descrição do Tratamento IA a revisar (assumia uso assistido, não geração integral) |
| [#31](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/31) | Script de métricas estáticas (CK/PMD ou Radon) + LOC | Guilherme Lana | ✅ Fechada (`lab02/scripts/collect_metrics.py`) |
| [#32](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/32) | Revisão conjunta do desenho do experimento | Todo o grupo | ⬜ Backlog |

### Sprint 2 — Lab02S02 (5 pontos)

Execução: cada integrante resolve os 4 katas, na ordem numérica 01→02→03→04 (2 com IA, 2 manual), conforme a tabela de contrabalanceamento oficial em [`lab02/docs/desenho_experimental.md`](docs/desenho_experimental.md) (issue #29). Cada trial é uma Issue individual no board:

| Issue | Trial | Responsável | Status |
|---|---|---|---|
| [#35](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/35) | Kata 01 (com IA) | Marcus Vinicius | ✅ Executado — 38,1s, 5/5 |
| [#36](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/36) | Kata 02 (sem IA) | Marcus Vinicius | ✅ Executado — 378,3s, 5/5 |
| [#37](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/37) | Kata 03 (com IA) | Marcus Vinicius | ✅ Executado — 43,6s, 5/5 |
| [#38](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/38) | Kata 04 (sem IA) | Marcus Vinicius | ✅ Executado — 159,2s, 5/5 |
| [#39](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/39) | Kata 01 (com IA) | Guilherme Lana | ⬜ Backlog |
| [#40](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/40) | Kata 02 (sem IA) | Guilherme Lana | ⬜ Backlog |
| [#41](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/41) | Kata 03 (sem IA) | Guilherme Lana | ⬜ Backlog |
| [#42](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/42) | Kata 04 (com IA) | Guilherme Lana | ⬜ Backlog |
| [#43](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/43) | Kata 02 (com IA) | Gabriel Chagas | ✅ Executado — 72,0s, 5/5 |
| [#44](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/44) | Kata 01 (sem IA) | Gabriel Chagas | ✅ Executado — 674,2s, 5/5 |
| [#45](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/45) | Kata 03 (sem IA) | Gabriel Chagas | ⚠️ Executado — **censurado em 2100s, 0/5** (não concluído a tempo) |
| [#46](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/46) | Kata 04 (com IA) | Gabriel Chagas | ✅ Executado — 10,3s, 5/5 |

Balanceamento por kata (soma do trio): 6 trials com IA / 6 manual no total — ver a tabela de verificação em `desenho_experimental.md`.

O comando de cada trial segue sempre o mesmo formato, trocando kata, participante e tratamento:

```bash
python scripts/timer.py --kata 02_normalizador_tags --participant marcusvv12 --treatment manual
```

#### Protocolo de cada trial

1. Leia o `kata.md` **só depois** de iniciar o cronômetro — ler antes tira do tempo medido a parte de entender o problema, que faz parte da tarefa nos dois tratamentos.
2. Rode o comando acima com o seu kata/tratamento. O `timer.py` confere que o seu `solution_<iniciais>.py` está no stub original e aborta se sobrou código de um trial anterior.
3. Edite **apenas o seu arquivo**: `katas/<kata>/solution_<iniciais>.py` (`_mv` Marcus, `_gc` Gabriel, `_gl` Guilherme). O `timer.py` cria o arquivo a partir do stub na primeira vez e avisa no console qual é. Não edite `solution.py` — ele é gerado a cada polling (o `test_solution.py` importa `from solution`) e o que você escrever nele é sobrescrito. Não altere `test_solution.py` — mexer nos testes de aceitação invalida `success_rate` (RQ2).
4. **Tratamento A (manual):** desligue o assistente de IA de verdade antes de começar — autocomplete inline *e* chat. Autocomplete esquecido ligado contamina o trial de controle e não aparece em nenhum dado depois.
5. **Tratamento B (geração integral por IA):** você **não escreve o código base**. Formula um prompt descrevendo o kata, cola a solução que a IA gerar, e corrige as falhas apontadas pelos testes com **novos prompts** — sem reescrever à mão linha a linha. O tempo do trial conta geração + toda a depuração. Use a ferramenta fixada na issue [#30](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/30), a mesma para todo o grupo. Regra completa em `TREATMENT_B_RULE` ([`scripts/hypotheses.py`](scripts/hypotheses.py)).
6. O cronômetro para sozinho quando os 5 testes passam, ou censura em 2100s. Não interrompa antes: trial que estoura o time-box é dado válido (censurado), não descartado.
7. Ao fim, o código do trial é arquivado em `data/trials/<trial_id>/solution_<iniciais>.py` e o `solution.py` gerado volta ao stub. Commite `data/trials.csv` e a pasta do trial referenciando o número da Issue.

Se um trial for abortado no meio (Ctrl+C), nada é gravado, mas o seu arquivo fica com o código pela metade — restaure antes de recomeçar:

```bash
python scripts/timer.py --reset --kata 01_gastos_semanais --participant marcusvv12
```

### Sprint 3 — Lab02S03 (5 pontos)

| Issue | Tarefa | Responsável | Status |
|---|---|---|---|
| [#47](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/47) | Análise estatística RQ1/RQ2 (Wilcoxon) | Marcus Vinicius | ⬜ Backlog |
| [#48](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/48) | Análise RQ3 (métricas estáticas) | Guilherme Lana | ⬜ Backlog |
| [#49](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/49) | Dashboard de visualização | Gabriel Chagas | ⬜ Backlog |

### Relatório Final (5 pontos)

| Issue | Tarefa | Responsável | Status |
|---|---|---|---|
| [#50](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/50) | Elaborar relatório final | Todo o grupo | ⬜ Backlog |

## Estrutura da pasta

```
lab02/
  katas/           # 4 katas autorais (kata.md + test_solution.py)
    01_.../
      solution_mv.py   # um arquivo por integrante — é o que cada um edita no trial
      solution_gc.py
      solution.py      # GERADO a cada polling (o test importa daqui); volta ao stub no fim
    _stubs/        # cópia canônica do enunciado vazio — origem de todo solution_<iniciais>.py
  scripts/         # hypotheses.py (H0/H1 + ameaças), cronometragem, métricas estáticas, análise, dashboard
  data/
    trials.csv     # uma linha por trial (12 no total): tempo, testes passando, caminho do código
    trials/        # código final de cada trial, um subdir por trial_id — entrada da RQ3
  docs/            # desenho do experimento (katas, hipóteses), relatório final
```

## Setup

```bash
cd lab02
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```
