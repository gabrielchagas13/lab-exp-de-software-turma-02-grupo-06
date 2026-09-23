# Resultados — RQ3 (Métricas Estáticas de Código)

Issue [#48](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/48) · Sprint 3 · Reprodução: `python scripts/analyze_rq3.py`

Hipóteses conforme [`scripts/hypotheses.py`](../scripts/hypotheses.py) (issue #27); desenho e pareamento conforme [`desenho_experimental.md`](desenho_experimental.md) (issue #29).

---

## Método

**Dados.** Os 12 trials executados na Sprint 2 (`data/trials.csv`), mapeados individualmente através de `solution_path` para os arquivos de código arquivados em `data/trials/<trial_id>/solution_*.py`. Foram avaliados 6 trials sob geração integral por IA e 6 sob desenvolvimento manual distribuídos entre os 3 participantes.

**Ferramenta de Métricas.** Extração estática automatizada via **Radon** (v6.0.1):
- `loc` (Linhas brutas de código): métrica de controle e verbosidade.
- `sloc` (Linhas de código fonte efetivas, excluindo comentários e linhas em branco).
- `cyclomatic_complexity_mean` (Complexidade ciclomática média de McCabe por bloco).
- `maintainability_index` (Índice de Manutenibilidade de 0 a 100).
- `duplication_pct` (Duplicação de blocos de código).

**Pareamento.** Cada participante contribui com **um par**: a mediana das métricas dos seus 2 trials com IA contra a mediana dos seus 2 trials manuais. O pareamento within-subject isola a variação de estilo individual de codificação. Resulta em **$n = 3$ pares**.

**Testes estatísticos.** Teste de Wilcoxon signed-rank pareado **bilateral** (pois a hipótese alternativa $H_1$ postula que a mediana difere entre os tratamentos: $IA \neq Manual$). Descritivas reportadas em mediana e Intervalo Interquartil (IQR).

---

## Hipóteses

* **$H_0$:** Não há diferença na mediana da complexidade ciclomática média, na verbosidade (LOC) nem na duplicação entre o tratamento manual e o tratamento de geração integral por IA.
* **$H_1$:** A mediana da complexidade ciclomática, do LOC e/ou da duplicação difere entre o tratamento manual e o tratamento de geração integral por IA.

---

## Resultados Descritivos

### Tabela Descritiva Consolidada (Mediana e IQR)

| Métrica | Tratamento | n | Mediana | Q1 | Q3 | IQR | Min | Max |
|---|---|---|---|---|---|---|---|---|
| **LOC (Total)** | IA | 6 | **16,00** | 16,00 | 19,00 | 3,00 | 15,00 | 40,00 |
| | Manual | 6 | **21,00** | 15,25 | 27,50 | 12,25 | 13,00 | 52,00 |
| **SLOC (Código puro)** | IA | 6 | **8,00** | 7,25 | 10,25 | 3,00 | 6,00 | 23,00 |
| | Manual | 6 | **9,50** | 6,75 | 11,50 | 4,75 | 2,00 | 30,00 |
| **Complexidade Ciclomática** | IA | 6 | **2,50** | 2,00 | 3,00 | 1,00 | 2,00 | 12,00 |
| | Manual | 6 | **2,50** | 2,00 | 3,75 | 1,75 | 1,00 | 12,00 |
| **Índice de Manutenibilidade**| IA | 6 | **98,74** | 95,98 | 100,00 | 4,02 | 85,84 | 100,00 |
| | Manual | 6 | **97,08** | 93,32 | 98,52 | 5,20 | 82,10 | 100,00 |
| **Duplicação (%)** | IA | 6 | **0,00%** | 0,00% | 0,00% | 0,00% | 0,00% | 0,00% |
| | Manual | 6 | **0,00%** | 0,00% | 0,00% | 0,00% | 0,00% | 0,00% |

---

## Pares por Participante ($n=3$)

Mediana dos 2 trials de cada participante em cada tratamento:

### 1. LOC (Linhas de Código)
| Participante | IA | Manual | Diferença ($IA - Manual$) |
|---|---|---|---|
| gabrielchagas13 | 18,00 | 13,50 | +4,50 |
| gguilhermelana | 15,50 | 40,50 | −25,00 |
| marcusvv12 | 28,00 | 21,00 | +7,00 |

### 2. Complexidade Ciclomática Média
| Participante | IA | Manual | Diferença ($IA - Manual$) |
|---|---|---|---|
| gabrielchagas13 | 2,50 | 1,50 | +1,00 |
| gguilhermelana | 2,50 | 7,50 | −5,00 |
| marcusvv12 | 7,00 | 3,00 | +4,00 |

### 3. Índice de Manutenibilidade (MI)
| Participante | IA | Manual | Diferença ($IA - Manual$) |
|---|---|---|---|
| gabrielchagas13 | 100,00 | 99,44 | +0,56 |
| gguilhermelana | 98,74 | 87,14 | +11,60 |
| marcusvv12 | 90,66 | 97,08 | −6,42 |

---

## Testes Inferenciais (Wilcoxon Pareado Bilateral)

| Métrica | $W$ | p-valor | Menor p possível ($n=3$) | Decisão ($\alpha = 0,05$) |
|---|---|---|---|---|
| **LOC** | 3,0 | 1,0000 | 0,2500 | **Não rejeita $H_0$** |
| **SLOC** | 3,0 | 1,0000 | 0,2500 | **Não rejeita $H_0$** |
| **Complexidade Ciclomática** | 3,0 | 1,0000 | 0,2500 | **Não rejeita $H_0$** |
| **Índice de Manutenibilidade** | 2,0 | 0,7500 | 0,2500 | **Não rejeita $H_0$** |
| **Duplicação (%)** | 0,0 | 1,0000 | 0,2500 | **Não rejeita $H_0$** (empate absoluto) |

---

## Discussão dos Resultados e Limitações

1. **Decisão Formal:** Para todas as métricas estruturais avaliadas, **não se rejeita $H_0$** ao nível de significância de $\alpha = 0{,}05$.
2. **Poder Estatístico e Tamanho Amostral:**
   - Em um teste de Wilcoxon pareado **bilateral** com apenas 3 pares ($n=3$), existem $2^3 = 8$ combinações possíveis de sinais. O evento mais extremo possível tem probabilidade bicaudal de $2 \times (1/2^3) = 0{,}2500$.
   - Consequentemente, **era matematicamente impossível atingir significância estatística ($\alpha < 0{,}05$)**, independentemente dos dados observados. Essa limitação estrutural decorre do número de participantes no grupo ($n=3$).
3. **Padrões Qualitativos Observados:**
   - **Verbosidade / LOC:** Ao contrário do temor de que a IA gerasse soluções excessivamente prolixas, a mediana de LOC do código gerado por IA (**16,0 LOC**) foi ligeiramente inferior à do código manual (**21,0 LOC**). A dispersão no código de IA também foi consideravelmente menor ($IQR = 3{,}0$ vs. $12{,}25$), indicando maior padronização no formato das soluções.
   - **Complexidade Ciclomática:** Ambas as abordagens atingiram exatamente a mesma mediana (**2,50**). Os katas 01, 02 e 04 exigiram complexidade baixa ($\approx 2-3$), enquanto o kata 03 (escalonador de intervalos com ordenação/lógica gulosa) concentrou os picos de complexidade ($CC = 12$) tanto na IA quanto no desenvolvimento manual.
   - **Duplicação de Código:** Como os katas consistem em funções puras focadas e autônomas (entre 13 e 52 linhas no total), a duplicação interna foi de **0,00%** em todos os 12 trials.
   - **Manutenibilidade:** O Índice de Manutenibilidade (MI) permaneceu consistentemente classificado na faixa mais alta ("Rank A", com medianas $\ge 97$), evidenciando que a geração integral por IA produziu código tão legível e manutenível quanto o código manual.

---

## Arquivos Gerados

| Arquivo | Descrição |
|---|---|
| `data/rq03_trials_metricas.csv` | Métricas brutas (LOC, SLOC, CC, MI, duplicação) para os 12 trials |
| `data/rq03_descritivas.csv` | Mediana, IQR, Q1, Q3, min e max por tratamento |
| `data/rq03_pares.csv` | Pares (IA vs. Manual) por participante |
| `data/rq03_testes.csv` | Estatística $W$, p-valor, piso do teste e decisão formal |
