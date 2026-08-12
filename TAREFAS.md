# Tarefas — LAB01 (15 pontos)

Divisão de tarefas por sprint, com status atual e responsável. Board: GitHub Projects (v2) do grupo (link a preencher).

## Sprint 1 — Lab01S01 (4 pontos)
**Objetivo:** Consulta GraphQL para 100 repositórios (todas as métricas) + requisição automática + GitHub Projects criado (colunas + WIP + primeiras Issues em uso).

| Issue | Tarefa | Responsável | Status |
|---|---|---|---|
| [#1](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/1) | Setup do GitHub Projects (v2) — colunas Status + limite de WIP | gabrielchagas13 | ⬜ Não iniciado |
| [#2](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/2) | Setup do script base de consulta GraphQL (auth, sessão, rate limit) | marcusvv12 | ✅ Pronto |
| [#3](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/3) | RQ01 — Idade do repositório | marcusvv12 | ✅ Pronto |
| [#4](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/4) | RQ02 — Total de pull requests aceitas | marcusvv12 | ✅ Pronto |
| [#5](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/5) | RQ03 — Total de releases | gguilhermelana | ⬜ Não iniciado |
| [#6](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/6) | RQ04 — Tempo até a última atualização | gguilhermelana | ⬜ Não iniciado |
| [#7](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/7) | RQ05 — Linguagem primária (+ fonte de "linguagens mais populares") | gabrielchagas13 | 🟡 Parcial (campo já vem no CSV, falta documentar fonte) |
| [#8](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/8) | RQ06 — Percentual de issues fechadas | gabrielchagas13 | ⬜ Não iniciado |
| [#9](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/9) | RQ07 — Cruzamento por linguagem (depende de #4, #5, #6) | gabrielchagas13 | ⬜ Não iniciado |
| [#10](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/10) | Integrar scripts individuais em query única do grupo | gabrielchagas13 | ⬜ Não iniciado |
| [#11](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/11) | Rodar consulta para 100 repositórios e validar saída | gabrielchagas13 | 🟡 Parcial (rodado só p/ RQ01/RQ02) |

**Pendências para fechar a sprint:**
- Criar o Project (v2) e mover as issues acima pelas colunas conforme o progresso real
- Referenciar o número da issue em cada commit (ex.: `#3 extrai idade dos repositorios`) — commits sem isso não contam na correção
- Concluir RQ03–RQ07 e integrar tudo num script único antes de considerar a sprint fechada

---

## Sprint 2 — Lab01S02 (4 pontos)
**Objetivo:** Paginação para 1000 repositórios + dados em .csv + primeira versão do relatório com hipóteses informais + board atualizado + primeiro snapshot exportado.

- [ ] Ajustar script para paginar até 1000 repositórios
- [ ] Cada integrante valida individualmente, na sua parte de RQs, a consistência dos dados nos 1000 repositórios (distribuição, outliers, valores ausentes)
- [ ] Cada integrante escreve, em Issue própria, a hipótese informal da sua parte
- [ ] Gerar CSV final com 1000 repositórios
- [ ] Primeira versão do relatório (introdução + hipóteses)
- [ ] Rodar script de snapshot do board (GraphQL) e exportar CSV do status das issues

## Sprint 3 — Lab01S03 (4 pontos)
**Objetivo:** Análise e visualização de dados para as 7 RQs.

- [ ] Calcular valores medianos / contagens por categoria para cada RQ
- [ ] Gerar visualizações (gráficos) por RQ
- [ ] Análise RQ07 (cruzamento por linguagem)

## Relatório Final (3 pontos)
**Objetivo:** Documento final consolidado.

- [ ] Introdução com hipóteses informais
- [ ] Metodologia de coleta
- [ ] Resultados por RQ (medianas, contagens por categoria)
- [ ] Discussão hipótese vs. resultado
- [ ] Seção "Configuração do processo" (colunas do board, política de WIP)
- [ ] Print do board mostrando o fluxo completo do Lab01
- [ ] Link do repositório/GitHub Projects preenchido
