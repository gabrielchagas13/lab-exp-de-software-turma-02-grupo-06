# Laboratório de Experimentação de Software — LAB01

**Curso:** Engenharia de Software | **Turno:** Noite | **Professor:** Danilo Maia

## Equipe

- Gabriel Chagas ([@gabrielchagas13](https://github.com/gabrielchagas13))
- Guilherme Lana ([@gguilhermelana](https://github.com/gguilhermelana))
- Marcus Vinicius ([@marcusvv12](https://github.com/marcusvv12))

## Sobre o laboratório

Estudo das principais características de sistemas populares open-source, com mineração de dados dos 1.000 repositórios com maior número de estrelas no GitHub (via GraphQL, script próprio) e setup do GitHub Projects (Kanban) que acompanhará o grupo durante o semestre.

### Questões de Pesquisa (RQs)

| RQ | Pergunta | Métrica |
|---|---|---|
| RQ01 | Sistemas populares são maduros/antigos? | Idade do repositório |
| RQ02 | Sistemas populares recebem muita contribuição externa? | Total de pull requests aceitas |
| RQ03 | Sistemas populares lançam releases com frequência? | Total de releases |
| RQ04 | Sistemas populares são atualizados com frequência? | Tempo até a última atualização |
| RQ05 | Sistemas populares são escritos nas linguagens mais populares? | Linguagem primária (fonte: [GitHub Octoverse](https://octoverse.github.com)) |
| RQ06 | Sistemas populares possuem alto percentual de issues fechadas? | Razão issues fechadas / total |
| RQ07 | Sistemas em linguagens mais populares recebem mais contribuição, lançam mais releases e são atualizados com mais frequência? | RQ02, RQ03 e RQ04 agrupadas por linguagem |

### Processo de desenvolvimento

| Sprint | Pontos | Entrega |
|---|---|---|
| Lab01S01 | 4 | Consulta GraphQL p/ 100 repositórios + GitHub Projects criado (colunas + WIP) |
| Lab01S02 | 4 | Paginação p/ 1000 repositórios + CSV + relatório preliminar + snapshot do board |
| Lab01S03 | 4 | Análise e visualização de dados para as 7 RQs |
| Relatório Final | 3 | Documento final + print do board |

**Observação:** não é permitido usar bibliotecas de terceiros que consultem a API do GitHub — as queries GraphQL são escritas e consumidas por scripts próprios do grupo. Commits devem referenciar o número da Issue correspondente (ex.: `#7 adiciona campos de RQ06`); a correção é feita a partir do board.

## Tarefas

Board: GitHub Projects (v2) do grupo (link a preencher).

### Sprint 1 — Lab01S01 (4 pontos)

| Issue | Tarefa | Responsável | Status |
|---|---|---|---|
| [#1](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/1) | Setup do GitHub Projects (v2) — colunas Status + limite de WIP | Gabriel Chagas | ⬜ Não iniciado |
| [#2](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/2) | Setup do script base de consulta GraphQL (auth, sessão, rate limit) | Marcus Vinicius | ✅ Pronto |
| [#3](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/3) | RQ01 — Idade do repositório | Marcus Vinicius | ✅ Pronto |
| [#4](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/4) | RQ02 — Total de pull requests aceitas | Marcus Vinicius | ✅ Pronto |
| [#5](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/5) | RQ03 — Total de releases | Guilherme Lana | ⬜ Não iniciado |
| [#6](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/6) | RQ04 — Tempo até a última atualização | Guilherme Lana | ⬜ Não iniciado |
| [#7](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/7) | RQ05 — Linguagem primária (+ fonte de "linguagens mais populares") | Gabriel Chagas | ✅ Pronto |
| [#8](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/8) | RQ06 — Percentual de issues fechadas | Gabriel Chagas | ✅ Pronto |
| [#9](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/9) | RQ07 — Cruzamento por linguagem (depende de #4, #5, #6) | Gabriel Chagas | ⬜ Bloqueada (aguardando #5 e #6) |
| [#10](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/10) | Integrar scripts individuais em query única do grupo | Gabriel Chagas | ⬜ Aguardando #5 e #6 |
| [#11](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/11) | Rodar consulta para 100 repositórios e validar saída | Gabriel Chagas | 🟡 Parcial (rodado por RQ separadas: RQ01/RQ02 e RQ05/RQ06) |

**Pendências para fechar a sprint:**
- Criar o Project (v2) e mover as issues acima pelas colunas conforme o progresso real
- Referenciar o número da issue em cada commit (ex.: `#3 extrai idade dos repositorios`) — commits sem isso não contam na correção
- Concluir RQ03–RQ04 (Guilherme), integrar tudo num script único e rodar a versão final para 100 repositórios

### Sprint 2 — Lab01S02 (4 pontos)

- [ ] Ajustar script para paginar até 1000 repositórios
- [ ] Cada integrante valida individualmente, na sua parte de RQs, a consistência dos dados nos 1000 repositórios (distribuição, outliers, valores ausentes)
- [ ] Cada integrante escreve, em Issue própria, a hipótese informal da sua parte
- [ ] Gerar CSV final com 1000 repositórios
- [ ] Primeira versão do relatório (introdução + hipóteses)
- [ ] Rodar script de snapshot do board (GraphQL) e exportar CSV do status das issues

### Sprint 3 — Lab01S03 (4 pontos)

- [ ] Calcular valores medianos / contagens por categoria para cada RQ
- [ ] Gerar visualizações (gráficos) por RQ
- [ ] Análise RQ07 (cruzamento por linguagem)

### Relatório Final (3 pontos)

- [ ] Introdução com hipóteses informais
- [ ] Metodologia de coleta
- [ ] Resultados por RQ (medianas, contagens por categoria)
- [ ] Discussão hipótese vs. resultado
- [ ] Seção "Configuração do processo" (colunas do board, política de WIP)
- [ ] Print do board mostrando o fluxo completo do Lab01
- [ ] Link do repositório/GitHub Projects preenchido

## Estrutura do projeto

```
scripts/
  fetch_repos_rq1_rq2.py   # RQ01 (idade) + RQ02 (PRs aceitas)
  fetch_repos_rq5_rq6.py   # RQ05 (linguagem) + RQ06 (% issues fechadas)
data/
  repos.csv                # saída RQ01/RQ02 (100 repositórios)
  repos_rq5_rq6.csv        # saída RQ05/RQ06 (100 repositórios)
```

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Crie um `.env` na raiz com um [Personal Access Token](https://github.com/settings/tokens) (escopo `public_repo`):

```
GITHUB_TOKEN=ghp_seu_token_aqui
```
