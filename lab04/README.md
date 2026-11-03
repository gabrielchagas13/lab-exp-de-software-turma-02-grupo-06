# Lab 04: Testes de hipótese por dentro

Par escolhido: **P1, t de Welch × Mann-Whitney**. Cenário: tempo até o merge de PRs com e sem review de bot.

## Requisitos
- Python 3.12+
- Token do GitHub em `GITHUB_TOKEN` (ou `gh auth login`; nunca commite o token). Só é necessário para recoletar os dados reais.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Coleta dos dados reais (#76)
```bash
python -m coleta --config config.json
```
O CSV já está versionado em `data/real.csv`, então não é preciso recoletar para rodar a simulação.

### Origem dos dados
- **Repositório:** [MCPJam/inspector](https://github.com/MCPJam/inspector), que usa o CodeRabbit (`coderabbitai[bot]`) para revisar parte dos PRs.
- **Janela:** PRs mergeados entre 2026-07-01 e 2026-09-30.
- **Grupos:** `com_bot` = PR com pelo menos um review do `coderabbitai[bot]` (`reviewed-by:`); `sem_bot` = PR sem review dele.
- **Exclusões:** PRs abertos por dependabot, renovate e github-actions.
- **Sorteio:** os 300 PRs mais recentes de cada grupo (Search API), dos quais 30 são sorteados com `numpy.random.default_rng(42)`.
- **Variável:** `horas_ate_merge = merged_at − created_at`, em horas.

| Grupo | n | Mediana (h) | Média (h) | Máx. (h) |
|---|---|---|---|---|
| com_bot | 30 | 4,26 | 22,82 | 203,5 |
| sem_bot | 30 | 0,83 | 4,36 | 30,1 |

Nos dois grupos a distribuição é muito assimétrica à direita (média bem acima da mediana, com outliers), o que sugere uma lognormal para a simulação.

**Limitação:** o bot não é atribuído aleatoriamente. PRs que ele revisa podem ser maiores ou de outros autores, então a diferença observada não é necessariamente efeito causal do bot.

`data/real.csv`:
| Coluna | Descrição |
|---|---|
| `grupo` | `com_bot` ou `sem_bot` |
| `numero` | Número do PR |
| `autor` | Login do autor |
| `criado_em` / `merge_em` | Timestamps ISO 8601 (UTC) |
| `horas_ate_merge` | Horas entre abertura e merge |
| `url` | Link do PR |

## Simulação e aplicação dos dois testes (#77)

Um único comando roda tudo de ponta a ponta, com semente fixa
(`numpy.random.default_rng(42)`, lida de `config.json`):

```bash
python -m simulacao --config config.json
```

Ele monta o cenário a partir de `data/real.csv`, imprime hipóteses, parâmetros
e a previsão registrada antes de simular, gera um conjunto simulado e aplica o
**t de Welch** e o **Mann-Whitney U** sobre ele, cada um com seu tamanho de
efeito (d de Cohen e delta de Cliff).

Variações úteis:

```bash
python -m simulacao --config config.json --efeito 0     # gera sob H0 verdadeira
python -m simulacao --config config.json --semente 7    # outra amostra
```

Saídas gravadas em `data/`:

| Arquivo | Conteúdo |
|---|---|
| `simulado_exemplo.csv` | o conjunto simulado, no mesmo formato longo de `real.csv` |
| `testes_exemplo.csv` | estatística, p-valor, tamanho de efeito e decisão de cada teste |

O cenário completo — pergunta, hipóteses por teste, justificativa da lognormal,
parâmetros e previsão — está em [docs/cenario.md](docs/cenario.md).

### Resultado da execução

Com o efeito observado na coleta (razão de medianas de 5,14×), **os dois testes
discordam**: o Mann-Whitney rejeita H0 (p = 0,00002, delta de Cliff +0,636,
grande) e o t de Welch não rejeita (p = 0,102, d de Cohen +0,436, pequeno). A
média do grupo tratado é puxada por poucos valores extremos, o que infla o
erro-padrão do t; o Mann-Whitney usa só a ordenação. Sob `--efeito 0` nenhum
dos dois rejeita.

## Dashboard (#78)

Um comando gera o dashboard inteiro em um único HTML, publicável no GitHub Pages:

```bash
python -m dashboard --config config.json
```

A saída vai para `dashboard/index.html` (configurável em `config.json`, chave
`dashboard.saida`, ou com `--saida`). O dashboard reaproveita `simulacao.executar`,
então o conjunto simulado e os testes são os mesmos de `python -m simulacao` com
a mesma semente, e rodar duas vezes gera um HTML idêntico.

A página segue as sete seções do enunciado. Por enquanto estão prontas:

| Seção | Gráfico | Conteúdo |
|---|---|---|
| 1. Cenário e dados | **G1** | histogramas reais × simulados por grupo, com a curva da lognormal do gerador; botão para alternar entre escala log e horas |
| 2. Estatística sob H0 | **G2** | distribuição da estatística sob H0 de cada teste, região de rejeição (α = 5%, bicaudal) sombreada e p-valor do exemplo como área hachurada |

As seções 3 a 7 aparecem como "em construção", com link para a issue que vai
preenchê-las (#79 a #84).

**Cores:** cada teste tem uma cor fixa em todos os gráficos (t de Welch
`#0072B2`, Mann-Whitney `#D55E00`). Os gráficos novos devem importar
`CORES_TESTE` de `dashboard/graficos.py` em vez de escolher cores próprias.

**Links do topo:** vêm de `config.json` (`dashboard.repo_url`, `projects_url`,
`pages_url`). Enquanto um deles for `null`, aparece como "(pendente)".

| Arquivo | Conteúdo |
|---|---|
| `dashboard/distribuicoes.py` | curvas sob H0 com a mesma aproximação do scipy, para que a área desenhada seja o p-valor da tabela |
| `dashboard/graficos.py` | G1, G2 e a paleta fixa por teste |
| `dashboard/pagina.py` | HTML e as sete seções |

## Testes

```bash
python -m pytest tests -q
```
