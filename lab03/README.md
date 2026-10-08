# Lab 03: Mineração de métricas DORA

Pipeline reprodutível que coleta dados do GitHub (REST, sem bibliotecas de terceiros para a API) e calcula métricas DORA.

## Requisitos
- Python 3.12+
- Um token do GitHub na variável de ambiente `GITHUB_TOKEN` (nunca commite o token)

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
O cliente (`pipeline/http.py`) lê `X-RateLimit-Remaining`/`X-RateLimit-Reset` e espera a renovação sozinho (também respeita `Retry-After`). Erros 5xx e de rede são repetidos com backoff exponencial (1 s, 2 s, 4 s, 8 s, 16 s).

## Workflow runs
`pipeline/runs.py` coleta runs do default branch com `event=push`, uma consulta por mês. Se um intervalo atinge o teto de 1.000 resultados da API, ele é dividido ao meio recursivamente. Os casos que ainda estouram (um único dia) ficam em `capped_days` no JSON do repositório.

## Releases e commits
- `pipeline/releases.py`: releases não-rascunho (pré-releases marcadas em `prerelease`) e tags, com paginação via header `Link`. As releases anteriores à janela ficam no JSON com `in_window=false`, porque servem de base para a primeira release da janela.
- `pipeline/commits.py`: `compare/{base}...{head}` entre releases consecutivas da definição principal (pré-releases são puladas e não servem de base), paginado com `per_page`/`page` (funciona com mais de 250 commits). Se uma tag foi apagada (404), a release vai para `skipped`, é ignorada, e a próxima usa a última release válida como base.

## Métricas (`metricas/`)
- `cfr.py`: classificação de `conclusion` e CFR (a), proxy de CI.
- `recuperacao.py`: episódios de falha por workflow, tempo de recuperação (mediana) e proporção de episódios censurados.
- `lead_time.py`: lead time (RQ2). (a) por release = publicação da release − commit mais antigo que ela entrega; (b) por commit = publicação da release − data de cada commit novo. Usa `author_date`, sem commits novos o resultado é `None`, e commits com data posterior à release contam como 0 h. O resumo por repositório usa a mediana de (a) e a mediana de (b) sobre todos os commits.

## Testes
```bash
pytest --cov=metricas --cov=pipeline --cov-report=term-missing
```
O CI (`.github/workflows/testes.yml`) roda os testes a cada push, exigindo ≥ 80% de cobertura do módulo `metricas`.
