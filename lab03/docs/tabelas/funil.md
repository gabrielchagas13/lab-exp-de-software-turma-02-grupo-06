**Funil de seleção dos repositórios**

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
