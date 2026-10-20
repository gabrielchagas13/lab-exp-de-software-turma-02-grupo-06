# Lab 03: Métricas DORA em repositórios populares do GitHub

<!-- As tabelas entre os marcadores "tabela:" são geradas a partir dos dados.
     Não edite à mão: rode `python -m scripts.tabelas_metodologia --config config.json`
     na pasta lab03/ depois de cada coleta. -->

## Metodologia

### Fonte de dados

Os dados vêm exclusivamente da API REST do GitHub, acessada por um cliente próprio (`pipeline/http.py`), sem bibliotecas de terceiros. Toda resposta é guardada em cache em disco, de modo que a coleta pode ser interrompida e retomada sem repetir chamadas, e uma nova execução com o mesmo cache reproduz os mesmos resultados. O cliente respeita os dois limites de requisição do GitHub: a cota por hora (primário) e a proteção contra rajadas (secundário). Para isso, ele mantém um intervalo mínimo entre as requisições e, ao esbarrar no limite, espera e diminui o ritmo.

Por repositório, são coletados: (i) os metadados da busca (estrelas, forks, linguagem principal, data de criação) e o número de contribuidores; (ii) os *workflow runs* do GitHub Actions disparados por `push` no *default branch*; (iii) as releases não-rascunho e as tags; e (iv) os commits entre releases consecutivas, obtidos pelo endpoint `compare`.

### Seleção dos repositórios e funil

Os candidatos são obtidos por buscas em `/search/repositories`, uma por faixa de estrelas (1.000–2.000, 2.000–5.000, 5.000–10.000, 10.000–50.000 e ≥ 50.000), porque a API devolve no máximo 1.000 resultados por busca. Os resultados das faixas são unidos sem duplicatas, ordenados por nome e embaralhados com semente fixa. Os candidatos são então avaliados nessa ordem até completar o tamanho da amostra. Os filtros são aplicados do mais barato ao mais caro em chamadas à API, e um candidato é descartado no primeiro filtro em que falha. A Tabela 1 mostra quantos repositórios restaram e quantos foram descartados em cada etapa.

<!-- tabela:funil -->
| Etapa | Critério | Restantes | Descartados |
|---|---|---|---|
| candidatos (busca) | Resultado da busca por faixas de estrelas, sem duplicatas | 4511 | 0 |
| fork_ou_arquivado | Descarta forks e repositórios arquivados | 4475 | 36 |
| sem_push_na_janela | Descarta quem não teve push durante a janela | 4346 | 129 |
| inacessivel | Descarta erros da API (404, 451...) | 4346 | 0 |
| sem_actions | Descarta quem não tem workflows do GitHub Actions | 4304 | 42 |
| poucas_releases | Exige >= 5 releases publicadas (sem draft e sem pré-release) na janela | 4162 | 142 |
| poucos_runs | Exige >= 50 runs válidos (push, default branch, sucesso/falha) na janela | 4141 | 21 |
| amostra_final | Sorteio (semente 42) até completar 100; o resto não é avaliado | 100 | 4041 (não avaliados) |

5 buscas por faixa de estrelas retornaram 4511 de 65606 repositórios existentes (a API limita cada busca a 1.000 resultados). Janela de observação: 2025-10-01 a 2026-09-30 (365 dias).
<!-- /tabela:funil -->

### Janela de observação

Todas as métricas são calculadas sobre uma janela fixa de 12 meses, definida pelo professor e configurada em `config.json` (`window_start`, `window_end`). Uma release entra na janela pela data de publicação (`published_at`, ou `created_at` quando a primeira está ausente). As releases anteriores à janela são coletadas apenas para servir de base de comparação à primeira release da janela. Os workflow runs entram na janela pela data de criação.

### Definições operacionais e variantes

A Tabela 2 define cada métrica e suas variantes, e indica a coluna correspondente no conjunto de dados. A definição principal de *deploy* é uma release publicada que não é rascunho nem pré-release. As pré-releases ficam fora do denominador e não servem de base para o `compare` de commits, porque deslocariam os commits atribuídos a cada release. Em todos os casos, a métrica por repositório é a mediana dos valores individuais, e não a média, porque as distribuições de tempo têm cauda longa.

<!-- tabela:definicoes -->
| Métrica | RQ | Variante | Definição operacional | Unidade | Coluna | Repos com valor |
|---|---|---|---|---|---|---|
| Frequência de deploy | RQ01 | principal | Releases publicadas (sem draft e sem pré-release) na janela / semanas da janela | releases/semana | `releases_por_semana` | 100/100 |
| Lead time | RQ02 | (a) por release | Mediana, entre as releases, de publicação − `author_date` do commit mais antigo que ela entrega | horas | `lead_time_release_h` | 100/100 |
| Lead time | RQ02 | (b) por commit | Mediana, sobre todos os commits novos, de publicação da release − `author_date` | horas | `lead_time_commit_h` | 100/100 |
| Change failure rate | RQ03 | (a) proxy de CI | Falhas / (falhas + sucessos) dos runs de push no default branch; falha = `failure`, `timed_out`, `startup_failure` | proporção | `cfr_ci` | 100/100 |
| Change failure rate | RQ03 | (b) v1 semver | Releases corretivas / releases da janela; corretiva = tag semver X.Y.Z com Z > 0 | proporção | `cfr_release_v1_semver` | 0/100 |
| Change failure rate | RQ03 | (b) v2 semver ou nome | Como (b) v1, ou tag/título com fix, hotfix, bugfix ou revert | proporção | `cfr_release_v2_semver_ou_nome` | 0/100 |
| Change failure rate | RQ03 | (b) v3 commits | Corretiva = ao menos metade dos commits novos (sem merges) com fix, hotfix, bugfix ou revert | proporção | `cfr_release_v3_commits` | 0/100 |
| Change failure rate | RQ03 | (b) v4 combinada | Corretiva = qualquer um dos sinais de v1, v2 ou v3 | proporção | `cfr_release_v4_combinada` | 0/100 |
| Tempo de recuperação | RQ04 | principal | Mediana, por workflow, de sucesso seguinte − primeira falha após um sucesso (episódios sem sucesso posterior são censurados) | horas | `recovery_median_h` | 94/100 |
| Tempo de recuperação | RQ04 | censura | Proporção de episódios de falha censurados | proporção | `recovery_censored_ratio` | 95/100 |
<!-- /tabela:definicoes -->

Algumas decisões operacionais valem para todas as métricas:

- **Lead time.** Usa a data de autoria (`author_date`) do commit. Commits com data posterior à release (por exemplo, por *rebase*) contam como 0 h. Uma release sem commits novos não tem lead time e não entra na mediana.
- **CFR (a).** Os runs `cancelled`, `skipped`, `neutral`, `action_required` e `stale` não contam como sucesso nem como falha.
- **CFR (b).** Não há campo na API que marque uma release como corretiva, então ela é classificada por uma heurística (`metricas/corretiva.py`) com três sinais. O primeiro é a versão semver ser um incremento de *patch*. O segundo é a tag ou o título conter *fix*, *hotfix*, *bugfix* ou *revert*. O terceiro é ao menos metade dos commits novos, sem contar merges, conter essas palavras. As quatro combinações desses sinais são avaliadas contra o consenso da amostra-ouro (`validacao/avaliar_heuristica.py`), com meta de F1 ≥ 0,70. Se nenhuma atingir a meta, a heurística é refinada. Todas as variantes ficam registradas, inclusive as descartadas. As release notes não são usadas como sinal, porque quase toda release tem uma seção de correções, inclusive as de funcionalidade.
- **Tempo de recuperação.** Os episódios de falha são calculados dentro de cada workflow. Assim, a falha de um workflow não é "recuperada" pelo sucesso de outro. Um episódio sem sucesso posterior dentro da janela é censurado, e não descartado. A proporção de censurados é registrada junto, porque um repositório com muitos episódios censurados tem a mediana subestimada.

### Protocolo de validação manual

Uma heurística automática pode errar bastante, e a forma de medir esse erro é compará-la com o julgamento humano. Foi sorteada, com semente fixa, uma amostra-ouro de repositórios da amostra final e de até cinco releases da janela de cada um (Tabela 3). Os três integrantes do grupo rotularam essa amostra de forma independente, sem consultar os colegas e sem ver a saída da heurística. Cada um rotulou três dimensões: o tipo do projeto (biblioteca, aplicação, CLI ou outro), se as releases do repositório são entregas reais e se cada release sorteada é corretiva.

A planilha de rotulagem traz apenas evidência bruta: o link direto para a release, o trecho das release notes e as mensagens dos commits. Ela não traz sinais derivados, como "mudou só o *patch*", porque esses sinais são as próprias entradas da heurística. Mostrá-los induziria o avaliador a concordar com ela e inflaria a precisão e o recall medidos depois. Antes do cálculo da concordância, as planilhas passam por uma validação automática (`validacao/validar_rotulos.py`), que confere as colunas, os itens da amostra e os valores aceitos.

A concordância entre avaliadores é medida pelo kappa de Fleiss em cada dimensão e interpretada pela escala de Landis e Koch. O kappa desconta a concordância esperada por acaso, que é alta quando uma classe predomina, como "não corretiva". O rótulo de consenso sai por maioria simples. Os casos 3-0 e 2-1 se resolvem sozinhos, e os casos 1-1-1 são decididos em reunião. O consenso serve a dois fins: é a referência para medir precisão, recall e F1 da heurística de release corretiva, e fornece o tipo do projeto usado como fator na RQ06.

<!-- tabela:amostra_ouro -->
| Parâmetro | Valor |
|---|---|
| Semente do sorteio | 42 |
| Repositórios sorteados | 60 |
| Releases sorteadas (até 5 por repositório) | 300 |
| Avaliadores independentes | 3 |
| Dimensões rotuladas | tipo do projeto; releases são entregas reais; release corretiva |
| Concordância | kappa de Fleiss por dimensão (Landis & Koch) |
| Consenso | maioria simples; 1-1-1 decidido em reunião |
<!-- /tabela:amostra_ouro -->

### Reprodutibilidade

A coleta inteira roda com um único comando (`python -m pipeline --config config.json`), e as sementes de sorteio estão fixadas no código e registradas nos dados. As tabelas desta seção são geradas a partir dos dados por `python -m scripts.tabelas_metodologia`. Os testes automatizados (`pytest`) rodam no CI a cada push.
