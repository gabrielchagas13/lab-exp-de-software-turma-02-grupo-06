**Definições operacionais e variantes das métricas**

| Métrica | RQ | Variante | Definição operacional | Unidade | Coluna | Repos com valor |
|---|---|---|---|---|---|---|
| Frequência de deploy | RQ01 | principal | Releases publicadas (sem draft e sem pré-release) na janela / semanas da janela | releases/semana | `releases_por_semana` | 300/300 |
| Lead time | RQ02 | (a) por release | Mediana, entre as releases, de publicação − `author_date` do commit mais antigo que ela entrega | horas | `lead_time_release_h` | 300/300 |
| Lead time | RQ02 | (b) por commit | Mediana, sobre todos os commits novos, de publicação da release − `author_date` | horas | `lead_time_commit_h` | 300/300 |
| Change failure rate | RQ03 | (a) proxy de CI | Falhas / (falhas + sucessos) dos runs de push no default branch; falha = `failure`, `timed_out`, `startup_failure` | proporção | `cfr_ci` | 300/300 |
| Change failure rate | RQ03 | (b) v1 semver | Releases corretivas / releases da janela; corretiva = tag semver X.Y.Z com Z > 0 | proporção | `cfr_release_v1_semver` | 300/300 |
| Change failure rate | RQ03 | (b) v2 semver ou nome | Como (b) v1, ou tag/título com fix, hotfix, bugfix ou revert | proporção | `cfr_release_v2_semver_ou_nome` | 300/300 |
| Change failure rate | RQ03 | (b) v3 commits | Corretiva = ao menos metade dos commits novos (sem merges) com fix, hotfix, bugfix ou revert | proporção | `cfr_release_v3_commits` | 300/300 |
| Change failure rate | RQ03 | (b) v4 combinada | Corretiva = qualquer um dos sinais de v1, v2 ou v3 | proporção | `cfr_release_v4_combinada` | 300/300 |
| Tempo de recuperação | RQ04 | principal | Mediana, por workflow, de sucesso seguinte − primeira falha após um sucesso (episódios sem sucesso posterior são censurados) | horas | `recovery_median_h` | 276/300 |
| Tempo de recuperação | RQ04 | censura | Proporção de episódios de falha censurados | proporção | `recovery_censored_ratio` | 280/300 |
