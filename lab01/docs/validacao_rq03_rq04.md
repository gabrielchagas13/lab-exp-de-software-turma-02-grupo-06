# Validação RQ03/RQ04 (amostra de 1000 repositórios)

Issue: [#14](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/14)
Responsável: Guilherme Lana
Dataset: [`data/repos_1000.csv`](../data/repos_1000.csv) (990/1000; ver nota da issue #12 sobre timeout do gateway do GitHub em paginação profunda)

## RQ03: Total de releases

**Valores ausentes:** 0. A API sempre retorna `totalCount`, mesmo para repositórios sem nenhuma release (valor 0).

**Duplicatas:** 0 repositórios duplicados na amostra.

**Distribuição:** fortemente assimétrica à direita.

| Estatística | Valor |
|---|---|
| Mínimo | 0 |
| Máximo | 1000 |
| Mediana | 38 |
| Média | 126,4 |
| P10 / P25 | 0 / 0 |
| P75 / P90 | 146,8 / 348,4 |
| P99 | 1000 |

Faixas:

| Faixa | Repositórios |
|---|---|
| 0 releases | 288 (29,1%) |
| 1-5 | 51 (5,2%) |
| 6-20 | 77 (7,8%) |
| 21-100 | 236 (23,8%) |
| 101-999 | 317 (32,0%) |
| 1000 (teto da API) | 21 (2,1%) |

**Outliers (regra IQR 1,5x):** 92 repositórios (9,3%), todos na cauda superior, já que o mínimo (0) é o menor valor possível e não há outliers inferiores.

**Achado de qualidade de dados:** 21 repositórios (2,1%) retornam exatamente `total_releases = 1000`, incluindo `pnpm/pnpm`, `home-assistant/core`, `TanStack/query`, `chakra-ui/chakra-ui`, `langchain-ai/langchain` e `electron/electron`, projetos conhecidos por terem histórico de releases muito superior a 1000. A ocorrência de exatamente o mesmo valor redondo em 21 repositórios independentes não é compatível com coincidência; é evidência de um **teto de contagem da API GraphQL do GitHub** na conexão `releases.totalCount` para volumes muito grandes. Para esses casos, o valor real da métrica deve ser lido como "maior ou igual a 1000", não como um total exato: é uma limitação a registrar na Metodologia do relatório.

## RQ04: Dias desde a última atualização (`pushed_at`)

**Valores ausentes:** 0.

**Inconsistências temporais:** nenhum valor negativo encontrado (nenhum repositório com `pushed_at` no "futuro" em relação à coleta, ou seja, sem indício de erro de fuso/relógio no script).

**Distribuição:** também assimétrica à direita, mas na direção oposta ao esperado por uma métrica de inatividade, com a moda concentrada em valores baixos.

| Estatística | Valor |
|---|---|
| Mínimo | 0 dias |
| Máximo | 2451 dias (~6,7 anos) |
| Mediana | 2 dias |
| Média | 112,2 dias |
| P10 / P25 | 0 / 0 |
| P75 / P90 | 48,8 / 462,2 |
| P99 | 1132,7 |

Faixas:

| Faixa | Repositórios |
|---|---|
| Hoje (0 dias) | 432 (43,6%) |
| 1-7 dias | 179 (18,1%) |
| 8-30 dias | 109 (11,0%) |
| 31-90 dias | 64 (6,5%) |
| 91-365 dias | 93 (9,4%) |
| Mais de 365 dias | 113 (11,4%) |

**Outliers (regra IQR 1,5x):** 192 repositórios (19,4%), todos no lado "parado" (cauda superior).

**Top 5 repositórios mais parados:**

| Repositório | Dias sem push | Releases |
|---|---|---|
| exacity/deeplearningbook-chinese | 2451 | 7 |
| GitSquared/edex-ui | 1764 | 0 |
| lib-pku/libpku | 1687 | 0 |
| floodsung/Deep-Learning-Papers-Reading-Roadmap | 1360 | 0 |
| atom/atom | 1324 | 538 |

## Hipóteses informais

> **RQ03: Sistemas populares lançam releases com frequência?**
> Esperava-se que sistemas populares, por serem mantidos ativamente (muitos por empresas ou fundações com pipelines de CI/CD), lançassem releases com frequência. Os dados confirmam essa hipótese **parcialmente**: entre os repositórios que de fato usam o mecanismo de Releases do GitHub, a frequência é alta, a ponto de 21 deles (2,1%) ultrapassarem o teto de contagem de 1000 da própria API. Porém, quase 30% da amostra (288 repositórios) nunca publicou nenhuma release, tipicamente porque não são "software" no sentido tradicional (listas curadas, livros, roadmaps, coleções de links); para esses, a métrica simplesmente não se aplica. A média (126,4) é distorcida por essa mistura de população; a **mediana (38)** é a medida mais representativa e indica frequência moderada-alta entre quem efetivamente versiona releases.

> **RQ04: Sistemas populares são atualizados com frequência?**
> Esperava-se atualização frequente, já que engajamento ativo tende a atrair e reter estrelas. Os dados **confirmam fortemente** essa hipótese para a maior parte da amostra: quase metade (43,6%) recebeu um push no próprio dia da coleta, e 75% nos últimos ~49 dias. Ainda assim, existe uma cauda relevante: cerca de 11,4% dos repositórios não são atualizados há mais de um ano, mantendo popularidade por valor histórico/educacional (livros, roadmaps, listas, ou projetos descontinuados como `atom/atom`) e não por manutenção ativa. Ou seja, **popularidade (estrelas) não implica necessariamente atividade recente**: a métrica precisa ser lida em conjunto com o tipo/natureza do repositório, não isoladamente.

## Notas para o relatório (template oficial)

- **Seção 1 (Introdução):** usar os dois blocos de hipótese informal acima, um por RQ.
- **Seção 4.1 (Coleta de Dados):** citar volume final (990/1000), ausentes (0 em ambas as métricas) e o achado do teto de 1000 releases como outlier/limitação tratada.
- **Seção 4.3 (Discussão):** RQ03 = hipótese parcialmente confirmada (bimodal: "não usa releases" vs. "usa intensamente"); RQ04 = hipótese majoritariamente confirmada, com ressalva da cauda de repositórios inativos.
