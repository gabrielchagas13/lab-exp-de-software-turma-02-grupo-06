**Funil de seleção dos repositórios**

| Etapa | Critério | Restantes | Descartados |
|---|---|---|---|
| candidatos (busca) | Resultado da busca por faixas de estrelas, sem duplicatas | 4511 | 0 |
| fork_ou_arquivado | Descarta forks e repositórios arquivados | 4407 | 104 |
| sem_push_na_janela | Descarta quem não teve push durante a janela | 4092 | 315 |
| inacessivel | Descarta erros da API (404, 451...) | 4092 | 0 |
| sem_actions | Descarta quem não tem workflows do GitHub Actions | 3985 | 107 |
| poucas_releases | Exige >= 5 releases publicadas (sem draft e sem pré-release) na janela | 3559 | 426 |
| poucos_runs | Exige >= 50 runs válidos (push, default branch, sucesso/falha) na janela | 3492 | 67 |
| amostra_final | Sorteio (semente 42) até completar 300; o resto não é avaliado | 300 | 3192 (não avaliados) |

5 buscas por faixa de estrelas retornaram 4511 de 65606 repositórios existentes (a API limita cada busca a 1.000 resultados). Janela de observação: 2025-10-01 a 2026-09-30 (365 dias).
