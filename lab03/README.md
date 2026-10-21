# Lab 03: Mineração de métricas DORA

Pipeline reprodutível que coleta dados do GitHub (REST, sem bibliotecas de terceiros para a API) e calcula métricas DORA.

## Requisitos
- Python 3.12+
- Um token do GitHub, de duas formas (a variável de ambiente tem precedência):
  - variável de ambiente `GITHUB_TOKEN`; ou
  - arquivo `lab03/.env` com `GITHUB_TOKEN=<token>` — ignorado pelo git, **nunca commite o token**

O token só precisa de acesso de leitura a repositórios públicos: um *fine-grained token* com "Public Repositories (read-only)", ou um *classic token* **sem nenhum escopo marcado**, já dá os 5.000 req/h. Sem token são 60 req/h e a coleta trava em minutos. Para conferir o token antes de uma coleta longa (não consome cota):

```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
```

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Executar (um único comando)
```bash
export GITHUB_TOKEN=<seu token>
python -m pipeline --config config.json
```

`config.json`:
| Campo | Descrição |
|---|---|
| `window_start` / `window_end` | Janela de observação (AAAA-MM-DD), fixada pelo professor |
| `data_dir` | Pasta de saída (`data/`) |
| `selection` | Parâmetros da seleção de repositórios (ver abaixo) |
| `repos` | Alternativa a `selection`: lista fixa de `{full_name, default_branch}` (útil para testar poucos repositórios) |

`selection`:
| Campo | Padrão | Descrição |
|---|---|---|
| `sample_size` | 100 | Tamanho da amostra final |
| `min_releases` | 5 | Mínimo de releases (sem draft e sem pré-release) na janela |
| `min_runs` | 50 | Mínimo de workflow runs válidos (`push`, default branch, `success`/falha) na janela |
| `seed` | 42 | Semente do embaralhamento dos candidatos (sorteio reprodutível) |
| `query` | `""` | Qualificadores extras da busca (ex.: `language:python`) |
| `star_ranges` | `1000..2000` … `>=50000` | Faixas de estrelas; uma busca por faixa (teto de 1.000 resultados por busca) |

Saídas em `data/`: `selecao/` (funil e metadados, ver abaixo), `runs/<owner>__<repo>.json` (workflow runs coletados), `metricas.json` (por repositório: releases/semana, lead time (a) e (b), CFR (a), tempo de recuperação e % de censurados), `releases/` e `commits/` (releases não-rascunho, tags e commits entre releases) e `cache/` (respostas brutas da API, ignorado pelo git).

## Seleção de repositórios e funil
`pipeline/selection.py` busca candidatos em `/search/repositories`, uma consulta por faixa de estrelas, e junta os resultados sem duplicatas. Os candidatos são ordenados por nome e embaralhados com `seed`, depois avaliados nessa ordem até completar `sample_size`. Os filtros vão do mais barato ao mais caro em chamadas à API, e o descarte acontece no primeiro que falhar:

1. `fork_ou_arquivado`: fork ou arquivado (dado da própria busca, sem chamada).
2. `sem_push_na_janela`: `pushed_at` anterior ao início da janela (sem chamada).
3. `inacessivel`: a API respondeu 404/451 etc. durante a avaliação.
4. `sem_actions`: `GET /actions/workflows` com `total_count = 0`.
5. `poucas_releases`: menos de `min_releases` releases publicadas (draft=false, prerelease=false) na janela.
6. `poucos_runs`: menos de `min_runs` runs válidos. Primeiro uma chamada com `per_page=1` lê o `total_count` (limite superior); só se ele passar os runs são coletados de fato (e ficam em `runs/` para as métricas).

Saídas em `data/selecao/`:
| Arquivo | Conteúdo |
|---|---|
| `funil.csv` | `etapa`, `restantes` (após a etapa), `descartados` (na etapa), `motivo`. A última linha (`amostra_final`) separa os candidatos que nem foram avaliados porque a amostra já estava completa |
| `candidatos.csv` | Um candidato por linha: `full_name`, `stars`, `status` (`incluido`, motivo de descarte ou `nao_avaliado`), `releases` e `valid_runs` contados até o ponto de parada |
| `buscas.csv` | Cada consulta de busca: `query`, `total_count` (quantos existem) e `fetched` (quantos vieram; menor que `total_count` quando a faixa passa do teto de 1.000) |
| `repos.csv` | Metadados da amostra final (abaixo) |

## Metadados (`repos.csv`)
`pipeline/metadata.py`. Os campos vêm do item da busca, exceto `contributors`.
| Coluna | Tipo | Unidade | Origem |
|---|---|---|---|
| `full_name` | texto | | `full_name` |
| `html_url` | texto | | `html_url` |
| `default_branch` | texto | | `default_branch` |
| `stars` | inteiro | estrelas | `stargazers_count` (no momento da busca) |
| `forks` | inteiro | forks | `forks_count` |
| `language` | texto | | `language` (linguagem principal; vazio se o GitHub não detecta) |
| `contributors` | inteiro | pessoas | Última página de `GET /contributors?per_page=1&anon=true` (header `Link`, `rel="last"`), incluindo anônimos; vazio se a API recusa listar (403, histórico grande demais) |
| `created_at` | data ISO 8601 | | `created_at` |
| `age_years` | decimal | anos | `(window_end − created_at) / 365,25` dias |

## Cache e retomada
Toda resposta da API é salva em `data/cache/`, e cada repositório concluído em `data/runs/`. Se a execução for interrompida (rate limit, rede, `Ctrl+C`), rode o mesmo comando de novo: ele continua de onde parou, sem repetir chamadas. Para recoletar do zero, apague `data/`.

## Rate limit e erros
O GitHub impõe **dois** limites diferentes, e o cliente (`pipeline/http.py`) trata os dois:

**Limite primário** — cota por hora: 5.000 req/h no `core` com token (60/h sem token, por isso `GITHUB_TOKEN` é obrigatório). A busca (`/search/*`) tem cota **própria e bem menor, 30 req/min**. O cliente lê `X-RateLimit-Remaining`/`X-RateLimit-Reset` e guarda a cota **por recurso** (`X-RateLimit-Resource`), para que esgotar a busca não faça o pipeline esperar à toa nos endpoints normais. Quando a cota zera, ele dorme até a renovação.

**Limite secundário** — proteção contra rajadas. Dispara **mesmo com cota primária sobrando**, quando as requisições vêm rápido demais, e responde 403/429 com a mensagem `secondary rate limit`. Foi o que derrubava a coleta antes: o cliente só olhava a cota primária, via que ainda havia quota e levantava exceção. Agora:

- **Prevenção:** intervalo mínimo entre requisições — `min_interval` 0,75 s nos endpoints normais e `search_interval` 2,1 s na busca (cota de 30/min). É isso que evita o bloqueio acontecer.
- **Remediação:** se ainda assim disparar, o cliente espera 60 s, **dobra o intervalo** (repetir no mesmo ritmo dispara de novo) e repete, até `max_retries` esperas.

Os intervalos são configuráveis em `config.json`; aumente-os se a coleta continuar esbarrando no limite:

```json
"http": { "min_interval": 0.75, "search_interval": 2.1 }
```

Um 403 **sem** mensagem de rate limit (token sem permissão, repositório bloqueado) continua propagando como erro — não vira espera. Erros 5xx e de rede são repetidos com backoff exponencial (1 s, 2 s, 4 s, 8 s, 16 s).

### Paralelismo (`workers`)
Medindo a coleta com uma única thread, o pipeline usava só **20% da cota** (16 de 83 req/min disponíveis): as páginas de workflow runs são grandes e a coleta ficava ~80% do tempo parada esperando resposta. O gargalo era latência, não cota.

Os 12 intervalos mensais de runs de um repositório são independentes, então são buscados em paralelo (`"workers": 4` no `config.json`). Isso **não aumenta as requisições por minuto**: o `GitHubClient` reserva os slots de ritmo **globalmente**, sob lock, então o teto continua sendo `60 / min_interval` ≈ 80 req/min independentemente do número de threads — o que muda é que o tempo ocioso de uma thread passa a ser usado por outra.

O resultado é idêntico ao serial: a ordem dos meses é preservada na junção, a deduplicação por `id` é determinística, e `splits`/`capped_days` são acumulados por thread e mesclados no fim (um dicionário compartilhado perderia incrementos). Há teste comparando as duas saídas.

Se mesmo assim o limite secundário disparar, baixe `workers` para 2 ou aumente `min_interval`.

**Quanto tempo leva.** Com 4 workers e o ritmo padrão, a seleção roda a ~50-60 repositórios/hora; a amostra de 300 leva da ordem de **4 a 6 h** no total, contra ~27 h do caminho serial com `compare` via API. Como tudo é cacheado, dá para interromper com `Ctrl+C` e retomar depois. **Rode só uma instância por vez** — dois processos somam requisições na mesma conta sem compartilhar o limitador de ritmo, e aí sim o limite secundário dispara.

## Workflow runs
`pipeline/runs.py` coleta runs do default branch com `event=push`, uma consulta por mês. Se um intervalo atinge o teto de 1.000 resultados da API, ele é dividido ao meio recursivamente. Os casos que ainda estouram (um único dia) ficam em `capped_days` no JSON do repositório.

## Releases e commits
- `pipeline/releases.py`: releases não-rascunho (pré-releases marcadas em `prerelease`) e tags, com paginação via header `Link`. As releases anteriores à janela ficam no JSON com `in_window=false`, porque servem de base para a primeira release da janela.
- `pipeline/commits.py`: commits entre releases consecutivas da definição principal (pré-releases são puladas e não servem de base). Se uma tag foi apagada, a release vai para `skipped`, é ignorada, e a próxima usa a última release válida como base.

### Commits via clone local (padrão)
Por padrão os commits vêm de um **clone local** (`pipeline/git_local.py`), não do endpoint `compare`. Desligue com `"use_git_clones": false` no `config.json` para voltar ao caminho da API; o JSON de cada repositório registra a origem no campo `fonte` (`git` ou `api`).

**Por que:** na coleta de 100 repositórios, o `compare` foi ~75% de todo o tráfego (≈22.000 de 29.276 chamadas). O `frappe/erpnext` sozinho custou ~5.600 chamadas e 1h23, porque mantém v14/v15/v16 em paralelo e o `compare` entre releases de ramos diferentes varre a divergência inteira, paginada de 100 em 100. Um clone `--bare --filter=tree:0` baixa só objetos de commit: o mesmo `erpnext` leva **17 s e 42 MB**, e daí em diante `git log base..head` responde localmente.

**Também é mais correto.** O `compare` **trunca em 10.000 commits**. Na validação contra os dados já coletados do `erpnext`, 134 dos 184 pares bateram exatamente e os 50 divergentes eram todos casos em que a API parou em 10.000, com o conjunto dela contido no do git. Para essas releases, o "commit mais antigo" da variante (a) do lead time (RQ 02) estava errado.

**Equivalência.** `GET /compare/base...head` devolve os commits alcançáveis de `head` e não de `base`, a partir do merge base — exatamente `git log base..head`. Verificado em `tests/test_git_local.py` e contra os dados reais: em 5 repositórios (120 releases, 2.567 commits) os conjuntos de SHA bateram 120/120.

**Custos.** ~4 MB por repositório na mediana (o maior da amostra, `erpnext`, 42 MB), ou seja **1 a 4,5 GB** para 300 repositórios em `data/clones/` — ignorado pelo git. Requer `git` no PATH; sem ele o pipeline avisa e usa a API.

Os **workflow runs** e as **releases** continuam vindo da API: não existem no clone, porque são recursos do GitHub e não do git. São eles que fixam o piso de tempo da coleta.

## Métricas (`metricas/`)
- `cfr.py`: classificação de `conclusion` e CFR (a), proxy de CI.
- `corretiva.py`: heurística de release corretiva e CFR (b) = releases corretivas / releases da janela. Três sinais (versão semver de *patch*; tag/título com `fix`/`hotfix`/`bugfix`/`revert`; ao menos metade dos commits, sem merges, com essas palavras) combinados em quatro variantes (`v1_semver`, `v2_semver_ou_nome`, `v3_commits`, `v4_combinada`). O pipeline grava todas em `metricas.json` (`cfr_release_<variante>`); a escolha sai da avaliação contra o consenso (abaixo).
- `recuperacao.py`: episódios de falha por workflow, tempo de recuperação (mediana) e proporção de episódios censurados.
- `lead_time.py`: lead time (RQ2). (a) por release = publicação da release − commit mais antigo que ela entrega; (b) por commit = publicação da release − data de cada commit novo. Usa `author_date`, sem commits novos o resultado é `None`, e commits com data posterior à release contam como 0 h. O resumo por repositório usa a mediana de (a) e a mediana de (b) sobre todos os commits.

## Validação manual (amostra-ouro)
Uma heurística automática pode errar bastante; a forma de saber o quanto ela erra é comparar com o julgamento humano. `validacao/` cobre as duas etapas (enunciado, seção 6).

**1. Sortear a amostra e gerar as planilhas** (issues de rotulagem):

```bash
python -m validacao.amostra --config config.json
```

Sorteia 60 repositórios e 5 releases de cada com semente fixa (`SEED = 42`, registrada em `data/validacao/amostra.json` junto com a lista sorteada) e gera **uma planilha por avaliador** em `data/validacao/`, com colunas de rótulo vazias e links diretos para o GitHub:

| Arquivo | Colunas a preencher | Valores |
|---|---|---|
| `rotulos_repos_<iniciais>.csv` | `tipo_projeto` | `biblioteca` \| `aplicacao` \| `cli` \| `outro` |
| | `releases_sao_entregas` | `sim` \| `nao` \| `incerto` |
| `rotulos_releases_<iniciais>.csv` | `corretiva` | `sim` \| `nao` |

As demais colunas vêm preenchidas e são **contexto para o avaliador**, não rótulos: `linguagem` e `estrelas` no nível do repositório; `release_nome`, `notas` (trecho das release notes) e `commits` (mensagens dos commits daquela release) no nível da release. Isso evita abrir 300 páginas no navegador — a evidência que o enunciado manda ler vem na própria linha.

A planilha traz apenas **evidência bruta**. Não embute sinais derivados do tipo "mudou só o número de patch" ou "contém `fix` nos commits", porque esses são exatamente as entradas da heurística automática: mostrá-los induziria o avaliador a concordar com ela, e a precisão/recall medidas depois contra esse mesmo gabarito sairiam infladas por construção. Há um teste que falha se alguém adicionar uma coluna dessas.

Os três avaliadores recebem exatamente a mesma amostra, e **rotulam de forma independente, sem consultar os colegas e sem ver a saída da heurística** — é essa independência que dá sentido ao kappa. Rodar o comando de novo **não sobrescreve** planilha já preenchida; para refazer, apague o arquivo à mão.

**2. Calcular concordância e consenso** (issue [#66](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/66)):

```bash
python -m validacao.concordancia --config config.json
```

| Saída | Conteúdo |
|---|---|
| `concordancia.csv` | kappa de Fleiss por dimensão, nº de itens, interpretação (Landis & Koch) e itens descartados por rótulo em branco |
| `consenso_<dimensao>.csv` | rótulo de consenso por item, o voto de cada avaliador e se foi unânime |

O consenso sai por **maioria simples**: 3-0 e 2-1 resolvem sozinhos; um 1-1-1 fica como `sem_consenso` e vai para reunião — o protocolo de desempate deve ficar registrado no repositório. Os rótulos alinham pela chave do item (`full_name`, ou `full_name`+`tag`), não pela ordem das linhas, então um avaliador pode reordenar a planilha sem corromper o cálculo.

**Antes de entregar os rótulos**, valide a planilha (colunas intactas, itens da amostra, valores aceitos; rótulo em branco aparece como pendência):

```bash
python -m validacao.validar_rotulos --avaliador gl              # durante a rotulagem
python -m validacao.validar_rotulos --avaliador gl --completo   # falha se faltar rótulo
```

O consenso alimenta duas coisas: o `tipo_projeto` é fator da RQ 06, e o rótulo `corretiva` é a referência contra a qual se mede precisão/recall/F1 da heurística de release corretiva (RQ 03 b).

**3. Avaliar a heurística de release corretiva** (issue [#67](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/67)), só depois que os três terminarem de rotular:

```bash
python -m validacao.avaliar_heuristica --config config.json
```

Grava `avaliacao_heuristica.csv` (VP/FP/FN/VN, precisão, recall e F1 de cada variante, e se atinge a meta F1 ≥ 0,70) e `avaliacao_heuristica_itens.csv` (previsão de cada variante por release, para analisar os erros ao refinar). Releases sem consenso ficam de fora.

## Tabelas do relatório
```bash
python -m scripts.tabelas_metodologia --config config.json
```
Gera, a partir dos dados, as tabelas da Metodologia em `docs/tabelas/` (`.md` e `.tex`): funil de seleção, definições operacionais e variantes (com quantos repositórios têm valor em cada coluna) e protocolo da amostra-ouro. As versões Markdown são escritas em `docs/relatorio.md` entre os marcadores `<!-- tabela:... -->`; rode de novo depois de cada coleta.

## Dados brutos em Parquet (`data/parquet/`)
Os JSON por repositório em `data/{runs,releases,commits}` somam ~1,45 GB e não cabem no git (limite de 100 MB **por arquivo**). O mesmo conteúdo, **sem perder nenhum campo**, é exportado para Parquet e versionado:

```bash
python -m analise.exportar_parquet --config config.json
```

| Tabela | Linhas | Tamanho | Conteúdo |
|---|---|---|---|
| `release_commits` | 2.896.721 | 51,5 MB | quais commits entram em cada release (`repo`, `tag`, `base_tag`, `sha`) |
| `commits` | 911.421 | 48,7 MB | um commit por `(repo, sha)`: data do autor, do committer e mensagem |
| `releases` | 80.070 | 39,8 MB | releases com `body` (release notes) completo |
| `runs` | 2.115.418 | 21,2 MB | workflow runs com `conclusion`, `run_started_at`, `updated_at` |
| `tags` | 165.970 | 3,1 MB | tags e seus commits — unidade de deploy da variante C3 (RQ 07) |
| `runs_coleta` | 302 | — | `branch`, `splits` e `capped_days` por repositório |
| `commits_coleta` | 300 | — | procedência dos commits (`git` ou `api`) |
| `releases_puladas` | 54 | — | releases sem lead time e o motivo |
| **Total** | | **164,3 MB** | maior arquivo: 51,5 MB |

**Por que encolhe ~9x.** Parquet é colunar e usa dicionário para valores repetidos: `conclusion` tem três valores possíveis em 2,1 milhões de linhas. Além disso os commits são **normalizados** — o mesmo commit aparece em várias comparações release-a-release (2,9 milhões de linhas para 911 mil commits distintos, efeito dos `compare` que cruzam linhas de versão), então o conteúdo é guardado uma vez e o vínculo fica à parte. Nada se perde: `release_commits ⋈ commits` reconstrói o formato original, e há teste garantindo isso.

**Nada foi truncado.** O `sha` é o completo de 40 caracteres e o `body` das releases vai inteiro — ele é o que o avaliador da amostra-ouro precisa ler (seção 6) e o sinal mais óbvio para refinar a heurística de release corretiva se o F1 não atingir 0,70.

Leitura de volta, inclusive só das colunas necessárias:

```python
import pandas as pd
runs = pd.read_parquet("data/parquet/runs.parquet")
datas = pd.read_parquet("data/parquet/commits.parquet", columns=["repo", "author_date"])
```

> **Isto é exportação, não substituição.** Os JSON em `data/{runs,releases,commits}` continuam sendo o que o pipeline lê para retomar a coleta (`load_or_build`), e estão no `.gitignore`. Apagá-los achando que o Parquet os substitui faz a próxima execução recoletar tudo da API — horas de coleta. Rode `exportar_parquet` de novo sempre que a coleta mudar.

## Testes
```bash
pytest --cov=metricas --cov=pipeline --cov-report=term-missing
```
O CI (`.github/workflows/testes.yml`) roda os testes a cada push, exigindo ≥ 80% de cobertura do módulo `metricas`.

## Análise de sensibilidade (RQ 07)
```bash
python -m analise.rq07 --config config.json
```
Compara cinco combinações de definições (unidade de deploy, lead time e CFR) por % de repositórios que mudam de categoria DORA e kappa linear ponderado. Saídas em `data/analise/rq07_*.csv`; resultados e discussão em `docs/resultados_rq07.md`.

## Rework rate (RQ 08, bônus)
```bash
python -m analise.rq08 --config config.json
```
Proporção de releases corretivas sobre o total, nas quatro versões da heurística, comparada ao CFR (b). Saídas em `data/analise/rq08_*.csv`; resultados em `docs/resultados_rq08.md`.

## Relatório em HTML
```bash
python -m scripts.gerar_relatorio_html --config config.json   # gera docs/index.html
```
