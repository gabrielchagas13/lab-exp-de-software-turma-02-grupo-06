**Definições operacionais e variantes das métricas**

| Métrica | RQ | Variante | Definição operacional | Unidade | Coluna | Repos com valor |
|---|---|---|---|---|---|---|
| Frequência de deploy | RQ01 | principal | Releases publicadas (sem draft e sem pré-release) na janela / semanas da janela | releases/semana | `releases_por_semana` | 300/300 |
| Lead time | RQ02 | (a) por release | Mediana, entre as releases, de publicação − `author_date` do commit mais antigo que ela entrega | horas | `lead_time_release_h` | 300/300 |
| Lead time | RQ02 | (b) por commit | Mediana, sobre todos os commits novos, de publicação da release − `author_date` | horas | `lead_time_commit_h` | 300/300 |
| Change failure rate | RQ03 | (a) proxy de CI | Falhas / (falhas + sucessos) dos runs de push no default branch; falha = `failure`, `timed_out`, `startup_failure` | proporção | `cfr_ci` | 300/300 |
| Change failure rate | RQ03 | (b) v1 semver | Releases seguidas, em até 7 dias, por uma release corretiva / releases avaliadas (as dos últimos 7 dias da janela ficam fora, censuradas); corretiva = incremento de patch semver | proporção | `cfr_entrega_v1_semver` | 300/300 |
| Change failure rate | RQ03 | (b) v2 semver ou nome | Como (b) v1, com corretiva = patch semver ou fix, hotfix, bugfix ou revert na tag/título | proporção | `cfr_entrega_v2_semver_ou_nome` | 300/300 |
| Change failure rate | RQ03 | (b) v3 commits | Como (b) v1, com corretiva = ao menos metade dos commits novos (sem merges) com fix, hotfix, bugfix ou revert | proporção | `cfr_entrega_v3_commits` | 300/300 |
| Change failure rate | RQ03 | (b) v4 combinada | Como (b) v1, com corretiva = qualquer um dos sinais de v1, v2 ou v3 | proporção | `cfr_entrega_v4_combinada` | 300/300 |
| Change failure rate | RQ03 | (b) v5 patch e notas | Como (b) v1, com corretiva = incremento de patch e release notes que citam fix, bugfix, hotfix ou revert | proporção | `cfr_entrega_v5_patch_e_notas` | 300/300 |
| Rework rate (bônus) | RQ08 | proporção de corretivas | Releases que são corretivas (v4) / releases da janela; difere do CFR (b), que conta as releases seguidas por uma corretiva | proporção | `cfr_release_v4_combinada` | 300/300 |
| Tempo de recuperação | RQ04 | principal | Mediana, por workflow, de sucesso seguinte − primeira falha após um sucesso (episódios sem sucesso posterior são censurados) | horas | `recovery_median_h` | 276/300 |
| Tempo de recuperação | RQ04 | censura | Proporção de episódios de falha censurados | proporção | `recovery_censored_ratio` | 280/300 |
