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

## Q1: erro tipo I (#79)

Experimento repetido com **H0 verdadeira por construção**: 10.000 réplicas em que
os dois grupos saem da *mesma* lognormal, de modo que toda rejeição é um falso
positivo. A proporção de rejeições estima o erro tipo I real de cada teste.

```bash
python -m simulacao.experimentos --config config.json
```

Ou direto no dashboard, que inclui a Q1 e o G3 na seção 3:

```bash
python -m dashboard --config config.json
```

| Teste | Falsos positivos | Erro tipo I | IC 95% | Obs ÷ nominal | Menor p em 10.000 | Veredito |
|---|---|---|---|---|---|---|
| t de Welch | 168 / 10.000 | **1,68%** | 1,45% – 1,95% | 0,34× | 0,0045 | conservador |
| Mann-Whitney U | 474 / 10.000 | **4,74%** | 4,34% – 5,17% | 0,95× | 1,8×10⁻⁴ | calibrado |

**O t de Welch é fortemente conservador neste cenário**: rejeita 1,68% das vezes
quando deveria rejeitar 5%, cerca de 3× menos. Sob H0 seus p-valores não são
uniformes — amontoam-se entre 0,2 e 0,4 — e em 10.000 réplicas o menor que ele
produziu foi 0,0045, ou seja, com dados desta assimetria um resultado a 1% de
significância é inalcançável para ele. O **Mann-Whitney fica calibrado**: 4,74%,
com o α nominal dentro do intervalo de confiança, e a curva de calibração segue a
diagonal em toda a faixa de α testada.

Um teste conservador não gera falsos positivos a mais, mas paga em poder: quem
rejeita de menos sob H0 também rejeita de menos quando o efeito existe. É a
mesma razão pela qual o Welch não acusou a diferença do exemplo da seção 2.

**G3** tem dois painéis: a distribuição dos p-valores sob H0 (um teste calibrado
produz p-valores uniformes) e a taxa de rejeição observada contra o α nominal
(a diagonal é a calibração perfeita).

Onde ficam as peças:

| Arquivo | Conteúdo |
|---|---|
| `simulacao/experimentos.py` | réplicas vetorizadas, intervalo de Wilson e o veredito de calibração |
| `simulacao/gerador.py` | o parâmetro `repeticoes` devolve as amostras no formato (réplicas, n) |
| `dashboard/graficos.py` | `g3_erro_tipo1` |

> Para a Q2 (#80): `p_valores_replicas` já aceita qualquer `efeito_log`, e
> `erro_tipo1` aceita `sigma_tratamento`/`n_tratamento` para a Q3 (#81). As
> 10.000 réplicas rodam em menos de 0,1 s porque os dois testes são aplicados de
> forma vetorizada (`axis=1`), então não há motivo para guardar resultados em
> disco.

## Conclusão e roteiro da apresentação (#84)

A seção 7 do dashboard confronta, item a item, as **previsões registradas antes
de qualquer simulação** (`simulacao/cenario.PREVISOES`) com o que os
experimentos encontraram. Registrar a previsão em código versionado é o que
impede reinterpretá-la depois à luz do resultado.

| Previsto | Decidido por | Encontrado | Veredito |
|---|---|---|---|
| O Mann-Whitney terá mais poder que o t de Welch | Q2 (#80) | — | pendente |
| O erro tipo I do Welch ficará longe dos 5% | Q1 (#79) | 1,68% (IC 1,45%–1,95%) | **parcial** |
| O erro tipo I do Mann-Whitney ficará perto dos 5% | Q1 (#79) | 4,74% (IC 4,34%–5,17%) | **confirmada** |

A previsão sobre o Welch sai como *parcial*, e não como confirmada: ela acertou
que o erro tipo I ficaria longe dos 5%, mas não dizia a direção, e o desvio foi
para o lado **conservador** — o oposto do risco que normalmente se teme num
teste mal calibrado.

**Recomendação:** para comparar duração em engenharia de software (tempo até o
merge, tempo de build, tempo de resolução), use o **Mann-Whitney** como teste
principal e relate o **delta de Cliff** junto com o p-valor. Se a média for
mesmo a quantidade de interesse, transforme em log antes — aí o t volta a ser
adequado, mas o resultado passa a ser sobre a mediana.

O roteiro da apresentação está em
[docs/roteiro_apresentacao.md](docs/roteiro_apresentacao.md): divisão em blocos
com tempo, os números a dizer em cada um, as perguntas prováveis com resposta e
um checklist de antes de apresentar.

> Enquanto as issues #80, #81 e #82 estiverem abertas, as previsões que dependem
> delas aparecem como *pendente* na tabela, com link para a issue — a página não
> conclui a partir de dados que não tem. Quando a Q2 fechar, basta passar
> `poder={"welch": taxa, "mannwhitney": taxa}` para `simulacao.conclusao.avaliar`
> e a linha se preenche sozinha.

## Testes

```bash
python -m pytest tests -q
```

## Painel interativo (#81, #82)
```bash
python -m painel               # gera painel/index.html (10.000 réplicas, seed 42, ~3 s)
```
Página com laboratório de simulação ao vivo (JS no navegador), distribuição nula por permutação dos dados reais, G3/G4 com os cenários de Q3 (`sigma_alto`, `outliers`, `n_pequeno`), mapa de poder n × efeito e o veredito nos dados reais. Os cálculos estão em `sim/`; as saídas, em `data/simulacao.csv` e `data/poder_por_n.csv`.
