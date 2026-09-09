# Desenho experimental — variáveis, tratamentos e crossover (issue #29)

Complementa [`hipoteses_ameacas.md`](hipoteses_ameacas.md) (hipóteses e ameaças, issue #27) e [`katas_escolhidos.md`](katas_escolhidos.md) (objetos experimentais, issue #26). Define os itens (B), (C), (D), (F) e (G) do desenho do experimento pedidos no enunciado.

## (C) Variável independente

**Uso de assistente de IA**, categórica com 2 níveis (os "tratamentos", ver seção D). O mesmo assistente de IA é usado em todos os trials do grupo (fixado na issue #30), para que o tratamento seja comparável dentro do experimento.

## (D) Tratamentos

| Tratamento | Descrição |
|---|---|
| **IA** | Participante resolve o kata com o assistente de IA habilitado (autocomplete/chat), dentro do time-box. |
| **Manual** | Participante resolve o kata sem nenhum assistente de IA (sem autocomplete de IA, sem chat), dentro do time-box. |

## (B) Variáveis dependentes

| RQ | Variável | Tipo | Observações |
|---|---|---|---|
| RQ1 | `time_to_green_seconds` | contínua (segundos) | Censurada em 2100s (35min) se o trial não terminar a tempo — não descartada. Coletada automaticamente por [`scripts/timer.py`](../scripts/timer.py) (issue #28). |
| RQ2 | `success_rate` | proporção [0,1] | % de testes de aceitação passando ao final do trial. Métrica primária — normaliza katas com números diferentes de testes. |
| RQ2 | `n_tests_failing` | inteira | Complementar ao success_rate, mais simples de reportar bruto. |
| RQ3 | `cyclomatic_complexity_mean` | contínua | Via Radon `cc` (issue #31), sobre o `solution.py` final do trial. |
| RQ3 | `duplication_pct` | contínua (%) | Via jscpd ou equivalente (issue #31). |
| RQ3 | `loc` | inteira | Controle **obrigatório** — necessário pra normalizar complexidade/duplicação, já que código gerado por IA pode ser mais verboso. |

## Variáveis de controle (fixadas para isolar o efeito da IV)

- Linguagem: Python em todos os katas/trials (consistente com Radon, issue #31).
- Assistente de IA: o mesmo para todo o grupo em todos os trials (issue #30).
- Time-box: 35 minutos (2100s) fixo para todo trial, de todo participante, nos dois tratamentos.
- Dificuldade dos katas: os 4 katas foram desenhados com a mesma "forma" (função pura, sem I/O, 15-30min de esforço estimado — ver `katas_escolhidos.md`).
- Ferramenta de execução dos testes: pytest, mesma versão para todos.

## Variáveis não controláveis registradas como limitação

- Familiaridade prévia de cada participante com o assistente de IA escolhido (ameaça já documentada em `hipoteses_ameacas.md`) — não é possível igualar entre os 3 integrantes, então será registrada explicitamente no Relatório Final em vez de ignorada.

## (F) Tipo de projeto experimental: crossover / within-subject, contrabalanceado

Cada um dos 3 integrantes do grupo resolve **todos os 4 katas**: 2 sob o tratamento IA e 2 sob o tratamento Manual. Isso faz de cada participante seu próprio controle (within-subject) — elimina a variação individual de habilidade como fator de confusão, já que a comparação IA vs. Manual acontece *dentro* da mesma pessoa, não entre pessoas diferentes.

**Contrabalanceamento:** a atribuição kata→tratamento varia entre os 3 integrantes, de forma que (i) cada participante fique com exatamente 2 katas em cada tratamento, e (ii) cada kata individual seja resolvido tanto com IA quanto sem IA por integrantes diferentes — isso evita que a dificuldade específica de um kata se confunda com o efeito do tratamento.

### Tabela de atribuição (kata × participante → tratamento)

| Participante | Kata 01 | Kata 02 | Kata 03 | Kata 04 |
|---|---|---|---|---|
| A — Marcus Vinicius | IA | Manual | IA | Manual |
| B — Gabriel Chagas | Manual | IA | Manual | IA |
| C — Guilherme Lana | IA | Manual | Manual | IA |

**Ordem de execução:** cada participante resolve os katas na ordem numérica (01→02→03→04). Como o tratamento associado a cada posição na sequência varia entre os participantes (A e C começam com IA, B começa com Manual; nenhum dos três repete o mesmo padrão IA/Manual/IA/Manual dos outros dois), o efeito de aprendizado/fadiga ao longo da sequência se distribui pelos dois tratamentos em vez de favorecer sistematicamente um deles — mitigação já registrada em `hipoteses_ameacas.md` para a ameaça "efeito de aprendizado entre katas".

### Verificação de balanceamento

- Por participante: 2 IA + 2 Manual (exigido pelo enunciado — "metade dos katas com IA, metade sem").
- Por kata, contagem de trials em cada tratamento no grupo todo:

| Kata | Trials com IA | Trials Manual |
|---|---|---|
| 01 | 2 (A, C) | 1 (B) |
| 02 | 1 (B) | 2 (A, C) |
| 03 | 1 (A) | 2 (B, C) |
| 04 | 2 (B, C) | 1 (A) |

- Total no experimento: **6 trials com IA** e **6 trials Manual** — perfeitamente balanceado na amostra agregada, apesar de nenhum kata individual ter distribuição 50/50 (impossível com apenas 3 participantes por kata, N ímpar). A soma agregada é o que importa para o teste de Wilcoxon pareado (compara, por participante, a mediana IA vs. Manual — não compara kata a kata).

## (G) Quantidade de medições

**3 participantes × 4 katas = 12 trials no total** (6 com IA, 6 Manual). Cada trial gera **uma linha de dados** cobrindo as 3 RQs simultaneamente: o mesmo código final do trial alimenta `time_to_green_seconds`/`success_rate` (via `scripts/timer.py`, RQ1/RQ2) e as métricas estáticas (via script da issue #31, RQ3) — não são coletas separadas.

Isso está dentro da faixa "4-6 trials/integrante" sugerida no enunciado para o teste de Wilcoxon pareado, no limite inferior (4), consistente com a escolha de 4 katas (não 6) feita na issue #26.

## Rastreabilidade no GitHub Projects

Cada uma das 12 combinações kata×participante×tratamento acima vira, na Sprint 2, uma Issue individual no board (campo Assignee = o participante), conforme exigido no enunciado ("todos os trials devem ser registrados no GitHub Projects... uma por kata/tratamento"). A tabela de atribuição desta seção é a fonte de verdade para criar essas 12 Issues.
