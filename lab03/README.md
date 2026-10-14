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

**Quanto tempo leva.** Com o ritmo padrão, ~100 repositórios levam da ordem de **2 a 3 horas**, e a amostra de 300+ da S02 passa de 6 h. É lento de propósito: o ritmo é a troca que evita o bloqueio. Como tudo é cacheado, dá para interromper com `Ctrl+C` e retomar depois. **Rode só uma instância por vez** — duas em paralelo somam requisições na mesma conta e disparam o limite secundário mesmo com o intervalo configurado.

## Workflow runs
`pipeline/runs.py` coleta runs do default branch com `event=push`, uma consulta por mês. Se um intervalo atinge o teto de 1.000 resultados da API, ele é dividido ao meio recursivamente. Os casos que ainda estouram (um único dia) ficam em `capped_days` no JSON do repositório.

## Releases e commits
- `pipeline/releases.py`: releases não-rascunho (pré-releases marcadas em `prerelease`) e tags, com paginação via header `Link`. As releases anteriores à janela ficam no JSON com `in_window=false`, porque servem de base para a primeira release da janela.
- `pipeline/commits.py`: `compare/{base}...{head}` entre releases consecutivas da definição principal (pré-releases são puladas e não servem de base), paginado com `per_page`/`page` (funciona com mais de 250 commits). Se uma tag foi apagada (404), a release vai para `skipped`, é ignorada, e a próxima usa a última release válida como base.

## Métricas (`metricas/`)
- `cfr.py`: classificação de `conclusion` e CFR (a), proxy de CI.
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

O consenso alimenta duas coisas: o `tipo_projeto` é fator da RQ 06, e o rótulo `corretiva` é a referência contra a qual se mede precisão/recall/F1 da heurística de release corretiva (RQ 03 b).

## Testes
```bash
pytest --cov=metricas --cov=pipeline --cov-report=term-missing
```
O CI (`.github/workflows/testes.yml`) roda os testes a cada push, exigindo ≥ 80% de cobertura do módulo `metricas`.
