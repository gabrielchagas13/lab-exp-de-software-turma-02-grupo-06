# Validação RQ01/RQ02 (1000 repositórios)

Issues: [#19](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/19) (medianas/contagens), [#20](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/20) (visualizações)
Responsável: Marcus Vinicius
Dataset: [`data/repos_rq1_rq2_1000.csv`](../data/repos_rq1_rq2_1000.csv) (1000/1000 — dataset completo para RQ01/RQ02; ver nota da issue #12 sobre o timeout de paginação profunda que limitou `data/repos_1000.csv` a 990/1000)
Script: [`scripts/analyze_rq1_rq2.py`](../scripts/analyze_rq1_rq2.py) — calcula estatísticas e gera os gráficos SVG abaixo

## RQ01: Idade do repositório (anos)

**Valores ausentes:** 0. `age_years` é sempre calculável a partir de `createdAt`.

**Duplicatas:** 0 repositórios duplicados na amostra.

**Distribuição:** aproximadamente simétrica, sem cauda extrema (idade é naturalmente limitada pela data de fundação do GitHub, 2008).

| Estatística | Valor |
|---|---|
| Mínimo | 0,02 anos |
| Máximo | 18,35 anos |
| Mediana | 7,75 anos |
| Média | 7,66 anos |
| P10 / P25 | 1,28 / 3,52 |
| P75 / P90 | 11,35 / 13,62 |
| P99 | 16,52 |

Faixas:

| Faixa (anos) | Repositórios | % |
|---|---|---|
| 0-1 | 81 | 8,1% |
| 1-3 | 109 | 10,9% |
| 3-5 | 133 | 13,3% |
| 5-10 | 331 | 33,1% |
| 10-15 | 297 | 29,7% |
| 15+ | 49 | 4,9% |

**Outliers (regra IQR 1,5x):** 0 — a distribuição de idade não tem outliers pela regra padrão, apesar da cauda de repositórios recentes (0-1 ano) ser proporcionalmente pequena (8,1%).

**Top 5 mais antigos:** `rails/rails` (18,35), `git/git` (18,07), `jekyll/jekyll` (17,83), `redis/redis` (17,41), `jquery/jquery` (17,37).

**Top 5 mais recentes:** todos com menos de 0,35 ano (~4 meses), a maioria projetos de IA/LLM que viralizaram rapidamente após o lançamento.

![RQ01 - Distribuição de idade dos repositórios](img/rq01_age_distribution.svg)

## RQ02: Total de pull requests aceitas (merged)

**Valores ausentes:** 0. A API sempre retorna `totalCount`, mesmo para repositórios sem nenhuma PR mergeada (valor 0).

**Duplicatas:** 0.

**Distribuição:** fortemente assimétrica à direita, com mediana bem abaixo da média.

| Estatística | Valor |
|---|---|
| Mínimo | 0 |
| Máximo | 103.346 |
| Mediana | 768 |
| Média | 4.236,5 |
| P10 / P25 | 32 / 175 |
| P75 / P90 | 3.415,8 / 9.800,1 |
| P99 | 60.707,8 |

Faixas:

| Faixa (PRs aceitas) | Repositórios | % |
|---|---|---|
| 0 | 20 | 2,0% |
| 1-50 | 106 | 10,6% |
| 51-200 | 147 | 14,7% |
| 201-1000 | 275 | 27,5% |
| 1001-5000 | 266 | 26,6% |
| 5001-20000 | 136 | 13,6% |
| 20000+ | 50 | 5,0% |

**Outliers (regra IQR 1,5x):** 124 repositórios (12,4%), todos na cauda superior — a assimetria é intrínseca à métrica (poucos projetos concentram um volume desproporcional de contribuições), não um problema de coleta.

**Top 5 com mais PRs aceitas:** `firstcontributions/first-contributions` (103.346 — projeto criado especificamente para receber PRs de iniciantes, caso atípico), `llvm/llvm-project` (97.086), `elastic/elasticsearch` (95.518), `getsentry/sentry` (91.168), `home-assistant/core` (90.113).

**Achado de qualidade de dados:** 20 repositórios (2,0%) têm 0 PRs mergeadas via GitHub, incluindo `torvalds/linux` — o kernel Linux não usa o fluxo de Pull Request do GitHub (patches por mailing list), então a métrica subestima a contribuição externa real nesse caso. Os demais zeros são majoritariamente listas/coleções (ex.: `awesome-selfhosted/awesome-selfhosted`) ou projetos muito recentes ainda sem PRs mergeadas.

![RQ02 - Distribuição de pull requests aceitas](img/rq02_prs_distribution.svg)

## Hipóteses informais

> **RQ01: Sistemas populares são maduros/antigos?**
> Esperava-se que repositórios populares tendessem a ser maduros/antigos, pois é necessário tempo para acumular estrelas e comunidade. Os dados **confirmam parcialmente**: mediana de 7,75 anos e média de 7,66 anos indicam maturidade típica, e 63,7% da amostra tem mais de 5 anos. Ainda assim, 8,1% dos repositórios têm menos de 1 ano — uma cauda relevante de projetos muito recentes que já viralizaram rápido, principalmente na onda atual de ferramentas de IA/LLM, mostrando que popularidade não exige necessariamente maturidade.

> **RQ02: Sistemas populares recebem muita contribuição externa?**
> Esperava-se alta contribuição externa, medida por PRs aceitas. Os dados **confirmam para a maioria** da amostra (mediana de 768 PRs aceitas), mas com distribuição muito assimétrica: a média (4.236,5) é quase 5,5x a mediana, puxada por outliers como `firstcontributions/first-contributions` e `llvm/llvm-project`. Um achado relevante limita a métrica: `torvalds/linux` aparece com 0 PRs mergeadas porque o kernel Linux não usa o fluxo de Pull Request do GitHub — a métrica subestima a contribuição externa nesse caso específico, reforçando que "PRs aceitas" mede adoção do fluxo do GitHub, não contribuição externa em si.

## Notas para o relatório (template oficial)

- **Seção 1 (Introdução):** usar os dois blocos de hipótese informal acima, um por RQ.
- **Seção 4.1 (Coleta de Dados):** citar dataset completo (1000/1000, `data/repos_rq1_rq2_1000.csv`), ausentes (0 em ambas as métricas) e a ressalva de `torvalds/linux` em RQ02.
- **Seção 4.3 (Discussão):** RQ01 = hipótese parcialmente confirmada (maioria madura, mas cauda relevante de projetos recentes/virais); RQ02 = hipótese confirmada para a maioria, com ressalva sobre a métrica subestimar projetos que não usam PRs do GitHub (ex.: Linux).
