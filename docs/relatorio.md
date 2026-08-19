# Relatório — LAB01: Características de repositórios populares

Issue: [#17](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/17)
Status: primeira versão (Sprint 2 / Lab01S02) — introdução, hipóteses informais e metodologia de coleta. Resultados por RQ, discussão completa e configuração do processo serão completados nas Sprints 3 e no Relatório Final.

Equipe: Gabriel Chagas, Guilherme Lana, Marcus Vinicius.

## 1. Introdução

Este trabalho estuda características de repositórios populares open-source no GitHub, a partir de uma amostra dos 1.000 repositórios com maior número de estrelas. Analisamos maturidade, contribuição externa, frequência de releases, frequência de atualização, alinhamento com as linguagens mais populares do mercado e percentual de resolução de issues — sete questões de pesquisa (RQ01-RQ07), cada uma com uma hipótese informal levantada antes da análise dos dados.

### RQ01 — Sistemas populares são maduros/antigos?

> Repositórios populares tendem a ser maduros/antigos, pois é necessário tempo para acumular estrelas e comunidade.
> **Resultado preliminar (990 repositórios):** parcialmente confirmada. Mediana de 7,75 anos e média de 7,66 anos sugerem maturidade típica, mas há uma cauda relevante de repositórios muito recentes que já viralizaram rápido, principalmente na onda atual de ferramentas de IA.

### RQ02 — Sistemas populares recebem muita contribuição externa?

> Repositórios populares recebem muita contribuição externa, medida por pull requests aceitas.
> **Resultado preliminar:** confirmada para a maioria (mediana de 768 PRs aceitas), mas com distribuição muito assimétrica — poucos projetos concentram dezenas de milhares de PRs (média de 4.236, puxada por outliers). Achado relevante: `torvalds/linux` aparece com 0 PRs mergeadas, pois o kernel Linux não usa o fluxo de Pull Request do GitHub (patches via mailing list) — a métrica subestima a contribuição externa nesse caso específico.

### RQ03 — Sistemas populares lançam releases com frequência?

> Sistemas populares, por serem mantidos ativamente (muitos por empresas ou fundações com pipelines de CI/CD), lançam releases com frequência.
> **Resultado preliminar:** confirmada parcialmente. Entre os repositórios que de fato usam o mecanismo de Releases do GitHub, a frequência é alta — a ponto de 21 (2,1%) atingirem o teto de contagem de 1000 da própria API. Porém, quase 30% da amostra nunca publicou nenhuma release, tipicamente por não serem "software" no sentido tradicional (listas curadas, livros, roadmaps). A mediana (38) é a medida mais representativa dessa população mista.

### RQ04 — Sistemas populares são atualizados com frequência?

> Engajamento ativo tende a atrair e reter estrelas, logo espera-se atualização frequente.
> **Resultado preliminar:** confirmada fortemente para a maior parte da amostra — quase metade (43,6%) recebeu um push no próprio dia da coleta, 75% nos últimos ~49 dias. Existe, porém, uma cauda de ~11,4% inativa há mais de um ano, mantendo popularidade por valor histórico/educacional, não por manutenção ativa. Popularidade não implica necessariamente atividade recente.

### RQ05 — Sistemas populares são escritos nas linguagens mais populares?

> Espera-se alinhamento entre a linguagem dos repositórios mais populares e o ranking geral de linguagens mais usadas no mercado (fonte de referência: [GitHub Octoverse](https://octoverse.github.com)).
> **Resultado preliminar:** confirmada parcialmente. Python, TypeScript e JavaScript (top 3 do Octoverse) somam 51,4% da amostra, mas linguagens fora do top 10 aparecem com peso relevante (Go 7,7%, Rust 5,7%), e 8,6% dos repositórios não têm linguagem primária detectável (listas, documentação).

### RQ06 — Sistemas populares possuem um alto percentual de issues fechadas?

> Projetos populares tendem a ter mais mantenedores/contribuidores ativos, logo espera-se alto percentual de resolução de issues.
> **Resultado preliminar:** confirmada. Mediana de 87,6% de issues fechadas, com 45% da amostra acima de 90%. A cauda inferior (11,2% abaixo de 50%) é dominada por projetos muito recentes/em crescimento explosivo (vários ligados a IA/LLM), sugerindo volume de issues crescendo mais rápido que a capacidade de triagem, não necessariamente abandono.

### RQ07 — Sistemas em linguagens populares recebem mais contribuição, releases e atualizações?

> Repositórios em linguagens populares (Octoverse) devem superar os demais nas métricas de RQ02, RQ03 e RQ04.
> **Resultado preliminar:** confirmada na tendência geral — mediana de PRs aceitas 63% maior, mediana de releases 2,5x maior, atualização ligeiramente mais rápida em linguagens populares. O efeito não é uniforme: Rust e Go, fora do top 10 do Octoverse, superam várias linguagens populares (Java, C, Shell) em PRs aceitas — sugerindo que o tipo de ecossistema (ex.: linguagens de sistemas) pode pesar mais que o ranking geral de popularidade.

## 2. Metodologia de coleta

**Fonte de dados:** API GraphQL do GitHub (`https://api.github.com/graphql`), consultada por script próprio do grupo (sem bibliotecas de terceiros de acesso à API), conforme exigido pelo enunciado.

**Amostragem:** busca por `search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, ...)`, paginada via cursor (`pageInfo.hasNextPage` / `endCursor`), replicando a ordenação por estrelas usada na busca web do GitHub.

**Evolução do volume coletado:**
- Sprint 1 (Lab01S01): 100 repositórios (`data/repos_completo.csv`)
- Sprint 2 (Lab01S02): 990 de 1000 repositórios-alvo (`data/repos_1000.csv`)

**Campos coletados por repositório:** `nameWithOwner`, `url`, `stargazerCount`, `createdAt`, `pushedAt`, `primaryLanguage`, `pullRequests(states: MERGED)`, `releases`, `issues(states: OPEN)`, `issues(states: CLOSED)`.

**Scripts do grupo** (`scripts/`):
- `fetch_repos.py` — script único, coleta RQ01-RQ06 numa única consulta GraphQL
- `fetch_repos_rq1_rq2.py`, `fetch_repos_rq3_rq4.py`, `fetch_repos_rq5_rq6.py` — scripts individuais usados para validação em amostra por integrante, antes da integração
- `fetch_repos_rq7.py` — análise derivada (não consulta a API): agrupa RQ02/RQ03/RQ04 por linguagem primária a partir do CSV já coletado
- `fetch_project_snapshot.py` — exporta snapshot do status do GitHub Projects em CSV, ao final de cada sprint

**Limitações conhecidas da coleta (documentadas em `docs/validacao_*.md`):**
- **Teto de contagem da API:** o campo `releases.totalCount` (e, com menor incidência, `pullRequests.totalCount`) satura em 1000 para projetos com histórico muito extenso (ex.: `pnpm/pnpm`, `home-assistant/core`, `langchain-ai/langchain`). Nesses casos, o valor deve ser lido como "≥ 1000", não como total exato.
- **Timeout de gateway em paginação profunda:** a consulta que inclui `releases.totalCount` é computacionalmente cara para a API; em `--count 1000`, o gateway do GitHub retornou 502/504 de forma persistente após a página ~990, mesmo com retry/backoff exponencial (`scripts/fetch_repos.py`). O dataset final da Sprint 2 tem **990/1000** repositórios por esse motivo. Um dataset auxiliar (`data/repos_rq1_rq2_1000.csv`), sem o campo de releases, completou os 1000/1000 — usado como checagem cruzada para RQ01/RQ02.
- **Linguagem/releases ausentes são dados válidos, não erros:** repositórios sem `primaryLanguage` (listas, documentação) e sem nenhuma release são estados legítimos da API, tratados como categoria própria (`(sem linguagem)`) ou zero, não descartados.

## 3. Resultados por RQ

*Pendente — Sprint 3 (Lab01S03): valores medianos, contagens por categoria e visualizações completas para as 7 RQs. Ver issues #19-#24.*

## 4. Discussão: hipótese vs. resultado

*Discussão consolidada pendente — Sprint 3 / Relatório Final, após a análise estatística completa. Discussões preliminares por RQ já estão registradas na Introdução (Seção 1) e em `docs/validacao_rq01_rq02.md` (pendente), `docs/validacao_rq03_rq04.md` e `docs/validacao_rq05_rq06_rq07.md`.*

## 5. Configuração do processo

*Pendente — Relatório Final: descrição da estrutura do GitHub Projects (colunas, política de WIP) e print do board ao final do laboratório.*

- Board: GitHub Projects (v2) "KANBAN - Lab Grupo 06", vinculado ao repositório do grupo
- Colunas de Status: `Backlog → To Do → Doing → Review → Done` (mínimo exigido)
- Limite de WIP: **a justificar** — ainda não documentado formalmente (issue #1); preencher antes do Relatório Final
- Snapshot de sprint: `scripts/fetch_project_snapshot.py` (issue #15), exportado em `data/snapshot_lab01s02.csv`
