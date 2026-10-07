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
| `repos` | Lista de `{full_name, default_branch}` |

Saídas em `data/`: `runs/<owner>__<repo>.json` (workflow runs coletados), `metricas_ci.json` (CFR (a) e tempo de recuperação por repositório) e `cache/` (respostas brutas da API, ignorado pelo git).

## Cache e retomada
Toda resposta da API é salva em `data/cache/`, e cada repositório concluído em `data/runs/`. Se a execução for interrompida (rate limit, rede, `Ctrl+C`), rode o mesmo comando de novo: ele continua de onde parou, sem repetir chamadas. Para recoletar do zero, apague `data/`.

## Rate limit e erros
O cliente (`pipeline/http.py`) lê `X-RateLimit-Remaining`/`X-RateLimit-Reset` e espera a renovação sozinho (também respeita `Retry-After`). Erros 5xx e de rede são repetidos com backoff exponencial (1 s, 2 s, 4 s, 8 s, 16 s).

## Workflow runs
`pipeline/runs.py` coleta runs do default branch com `event=push`, uma consulta por mês. Se um intervalo atinge o teto de 1.000 resultados da API, ele é dividido ao meio recursivamente. Os casos que ainda estouram (um único dia) ficam em `capped_days` no JSON do repositório.

## Releases e commits
- `pipeline/releases.py`: releases não-rascunho (pré-releases marcadas em `prerelease`) e tags, com paginação via header `Link`. As releases anteriores à janela ficam no JSON com `in_window=false`, porque servem de base para a primeira release da janela.
- `pipeline/commits.py`: `compare/{base}...{head}` entre releases consecutivas, paginado com `per_page`/`page` (funciona com mais de 250 commits). Se uma tag foi apagada (404), a release vai para `skipped`, é ignorada, e a próxima usa a última release válida como base.

## Métricas (`metricas/`)
- `cfr.py`: classificação de `conclusion` e CFR (a), proxy de CI.
- `recuperacao.py`: episódios de falha por workflow, tempo de recuperação (mediana) e proporção de episódios censurados.
- `lead_time.py`: lead time (RQ2). (a) por release = publicação da release − commit mais antigo que ela entrega; (b) por commit = publicação da release − data de cada commit novo. Usa `author_date`, sem commits novos o resultado é `None`, e commits com data posterior à release contam como 0 h. O resumo por repositório usa a mediana de (a) e a mediana de (b) sobre todos os commits.

## Testes
```bash
pytest --cov=metricas --cov=pipeline --cov-report=term-missing
```
O CI (`.github/workflows/testes.yml`) roda os testes a cada push, exigindo ≥ 80% de cobertura do módulo `metricas`.
