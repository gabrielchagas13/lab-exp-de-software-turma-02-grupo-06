# Validação RQ05/RQ06/RQ07 (amostra de 1000 repositórios)

Issue: [#16](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/16)
Responsável: Gabriel Chagas
Dataset: [`data/repos_1000.csv`](../data/repos_1000.csv) (990/1000; ver nota da issue #12 sobre timeout do gateway do GitHub em paginação profunda)

## RQ05: Linguagem primária

**Valores ausentes:** 85 repositórios (8,6%) sem `primaryLanguage` — típico de listas curadas/documentação (ex.: `sindresorhus/awesome`), onde o GitHub não detecta uma linguagem dominante.

**Duplicatas:** 0 repositórios duplicados na amostra.

**Distribuição:** concentrada em poucas linguagens — 43 linguagens distintas no total, mas as 3 primeiras (Python, TypeScript, JavaScript) somam 51,4% da amostra.

| Linguagem | Repositórios | % |
|---|---|---|
| Python | 227 | 22,9% |
| TypeScript | 173 | 17,5% |
| JavaScript | 109 | 11,0% |
| (sem linguagem) | 85 | 8,6% |
| Go | 76 | 7,7% |
| Rust | 56 | 5,7% |
| C++ | 40 | 4,0% |
| Java | 40 | 4,0% |
| Jupyter Notebook | 23 | 2,3% |
| C | 21 | 2,1% |
| Shell | 20 | 2,0% |
| (demais 32 linguagens) | 120 | 12,1% |

Fonte de referência para "linguagens mais populares": [GitHub Octoverse](https://octoverse.github.com) — top 10: JavaScript, Python, Java, TypeScript, C#, C++, PHP, Shell, C, Ruby.

**Achado de qualidade de dados:** repositórios sem `primaryLanguage` não são "dados ausentes" no sentido de erro de coleta — é um valor semanticamente válido (o GitHub genuinamente não conseguiu classificar), então foram tratados como categoria própria (`(sem linguagem)`) em vez de descartados.

## RQ06: Percentual de issues fechadas

**Valores nulos (0 issues no total):** 43 repositórios (4,3%) têm `open_issues + closed_issues = 0`, o que torna a razão matematicamente indefinida (divisão por zero) — tratados como `null`, não como 0%.

**Duplicatas:** 0.

**Distribuição:** fortemente concentrada em valores altos, assimétrica à esquerda.

| Estatística | Valor |
|---|---|
| Mínimo | 0,0769 |
| Máximo | 1,0 |
| Mediana | 0,8757 |
| Média | 0,8027 |
| P10 / P25 | 0,4604 / 0,7042 |
| P75 / P90 | 0,9688 / 0,9928 |
| P99 | 1,0 |

Faixas:

| Faixa | Repositórios |
|---|---|
| 0-50% | 106 (11,2%) |
| 50-70% | 126 (13,3%) |
| 70-90% | 287 (30,3%) |
| 90-99% | 309 (32,6%) |
| 99-100% | 119 (12,6%) |

**Outliers (regra IQR 1,5x):** 38 repositórios (4,0%), todos na cauda inferior (poucas issues fechadas em relação ao total).

**Top 5 repositórios com menor percentual de issues fechadas:**

| Repositório | % fechadas | Abertas | Fechadas |
|---|---|---|---|
| ComposioHQ/awesome-claude-skills | 7,7% | 132 | 11 |
| floodsung/Deep-Learning-Papers-Reading-Roadmap | 8,6% | 53 | 5 |
| anthropics/prompt-eng-interactive-tutorial | 9,5% | 38 | 4 |
| elder-plinius/CL4R1T4S | 10,1% | 71 | 8 |
| anthropics/financial-services | 10,2% | 79 | 9 |

Nota-se que os 5 repositórios com pior razão são projetos **recentes/em alta** (temas de IA/LLM, vários deles das próprias Anthropic), o que sugere que percentual baixo de issues fechadas pode indicar popularidade repentina/crescimento rápido, não necessariamente descaso — hipótese a explorar na discussão.

## RQ07: Cruzamento de RQ02/RQ03/RQ04 por linguagem

Refeito com `scripts/fetch_repos_rq7.py --input data/repos_1000.csv`, salvo em [`data/rq07_by_language_1000.csv`](../data/rq07_by_language_1000.csv) (44 linguagens).

**Comparação agregada — linguagens populares (Octoverse) vs. demais:**

| Grupo | n | Mediana PRs aceitas | Mediana releases | Mediana dias desde atualização |
|---|---|---|---|---|
| Populares (Octoverse) | 655 | 928 | 50 | 1 |
| Outras | 335 | 571 | 20 | 6 |

Repositórios em linguagens populares têm mediana de PRs aceitas ~63% maior, mediana de releases 2,5x maior, e são atualizados um pouco mais rápido (mediana de 1 dia vs. 6 dias) que repositórios em outras linguagens.

**Maiores medianas de PRs aceitas por linguagem (n ≥ 10):**

| Linguagem | n | Mediana PRs aceitas |
|---|---|---|
| Ruby | 13 | 6.263,0 |
| Rust | 56 | 2.353,5 |
| TypeScript | 173 | 2.025,0 |
| Go | 76 | 1.702,5 |

## Hipóteses informais

> **RQ05: Sistemas populares são escritos nas linguagens mais populares?**
> Esperava-se alinhamento entre a linguagem dos repositórios mais populares e o ranking geral de linguagens do GitHub Octoverse. Os dados **confirmam parcialmente**: Python, TypeScript e JavaScript (top 3 do Octoverse) somam mais da metade (51,4%) da amostra, mas linguagens fora do top 10 do Octoverse aparecem com peso relevante — Go (7,7%) e Rust (5,7%) — e 8,6% dos repositórios sequer têm uma linguagem primária detectável (listas, documentação). Ou seja, popularidade de repositório e popularidade de linguagem estão correlacionadas, mas não são a mesma coisa: nichos como sistemas/infra (Rust, Go) parecem sobrerrepresentados entre os repositórios mais estrelados em comparação ao seu uso geral no mercado.

> **RQ06: Sistemas populares possuem um alto percentual de issues fechadas?**
> Esperava-se alto percentual de resolução, dado que projetos populares tendem a ter mais mantenedores/contribuidores ativos. Os dados **confirmam a hipótese**: mediana de 87,6% de issues fechadas, com 45% da amostra acima de 90%. A cauda inferior (11,2% abaixo de 50%) é dominada por projetos muito recentes ou em crescimento explosivo (vários ligados a IA/LLM), sugerindo que baixo percentual de fechamento nesses casos reflete volume de issues crescendo mais rápido que a capacidade de triagem, não necessariamente abandono.

> **RQ07: Sistemas em linguagens mais populares recebem mais contribuição, lançam mais releases e são atualizados com mais frequência?**
> Os dados **confirmam a hipótese** na direção esperada: repositórios em linguagens populares (Octoverse) têm mediana de PRs aceitas 63% maior, mediana de releases 2,5x maior e são atualizados ligeiramente mais rápido que repositórios em outras linguagens. Porém, o efeito não é uniforme dentro do grupo "não popular": Rust e Go, apesar de fora do top 10 do Octoverse, têm medianas de PRs aceitas maiores que várias linguagens populares (ex.: Java, C, Shell) — o que indica que o fator determinante pode ser menos "a linguagem em si" e mais "o tipo de ecossistema" (ex.: linguagens de sistemas atraem contribuição intensa de comunidades técnicas independentemente do ranking geral de popularidade).

## Notas para o relatório (template oficial)

- **Seção 1 (Introdução):** usar os três blocos de hipótese informal acima, um por RQ.
- **Seção 4.1 (Coleta de Dados):** citar volume final (990/1000), ausentes (85 em RQ05, 43 nulos em RQ06 por divisão por zero) e a fonte Octoverse usada para classificar linguagens populares.
- **Seção 4.3 (Discussão):** RQ05 = hipótese parcialmente confirmada (linguagens populares dominam, mas com nichos sobrerrepresentados); RQ06 = hipótese confirmada, com ressalva sobre projetos em crescimento rápido; RQ07 = hipótese confirmada na tendência geral, com ressalva sobre Rust/Go como exceções relevantes.
