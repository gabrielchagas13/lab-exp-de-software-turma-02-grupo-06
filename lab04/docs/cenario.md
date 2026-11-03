# Cenário do experimento — Lab 04 (par P1: t de Welch × Mann-Whitney)

Documento da sprint 1 (issue #77). Registra a pergunta, as hipóteses, a
distribuição escolhida e a previsão feita **antes** de rodar as simulações
repetidas, para que a conclusão da sprint 2 possa ser confrontada com ela.

## 1. Pergunta

> O tempo até o merge de um pull request difere entre PRs revisados pelo bot
> CodeRabbit e PRs sem revisão do bot?

- **Unidade observada:** um pull request mergeado.
- **Variável de resposta:** `horas_ate_merge = merged_at − created_at`, contínua e positiva.
- **Fator:** presença de review do `coderabbitai[bot]`.
  - Controle (`sem_bot`): PR sem review do bot.
  - Tratamento (`com_bot`): PR com pelo menos um review do bot.
- **Dados reais:** `data/real.csv`, 30 PRs por grupo do repositório
  [MCPJam/inspector](https://github.com/MCPJam/inspector) (coleta da issue #76).

## 2. Hipóteses

Os dois testes **não testam a mesma coisa**, então cada um recebe seu próprio
par de hipóteses. Enunciar um H0 único para os dois é precisamente o erro
conceitual que este laboratório investiga.

| Teste | Compara | H0 | H1 |
|---|---|---|---|
| t de Welch | médias | `mu_com_bot = mu_sem_bot` | `mu_com_bot ≠ mu_sem_bot` |
| Mann-Whitney U | postos (dominância estocástica) | `P(X > Y) = P(Y > X) = 0,5` | essa probabilidade é diferente de 0,5 |

**Direção: bicaudal.** A pergunta é se o tempo *difere*, não se o bot acelera.
Um review automático pode tanto adiantar o merge (achando problemas cedo)
quanto atrasá-lo (gerando rodadas extras de correção), e não há base para
descartar uma das direções antes de olhar os dados.

**Nível de significância:** α = 0,05.

## 3. Distribuição escolhida: lognormal

Os dados reais são fortemente assimétricos à direita nos dois grupos, e a
assimetria desaparece em escala logarítmica:

| Grupo | n | Mediana (h) | Média (h) | Máx. (h) | Assimetria | Assimetria do log | Shapiro p | Shapiro p (log) |
|---|---|---|---|---|---|---|---|---|
| `sem_bot` | 30 | 0,83 | 4,36 | 30,1 | +2,15 | −0,14 | 7,9×10⁻⁸ | 0,310 |
| `com_bot` | 30 | 4,26 | 22,82 | 203,5 | +2,73 | −0,07 | 1,6×10⁻⁸ | 0,933 |

No bruto o Shapiro-Wilk rejeita a normalidade com folga; em log não rejeita em
nenhum dos dois grupos. Essa é a definição operacional de uma **lognormal**, e
é ela que o gerador usa.

A escolha não é cosmética: é exatamente o tipo de distribuição em que um teste
de médias e um teste de postos podem divergir. Se a simulação usasse uma
normal, os dois testes concordariam quase sempre e não haveria o que comparar.

## 4. Parâmetros, derivados dos dados reais

Todos saem de `data/real.csv` em tempo de execução (`simulacao/cenario.py`), não
são escritos à mão — se a coleta for refeita, o cenário acompanha.

| Parâmetro | Valor | Origem |
|---|---|---|
| `mu` (log) do controle | −0,576 | média de `log(horas)` no grupo `sem_bot` |
| `sigma` (log) comum | 2,245 | desvio combinado dos dois grupos (controle 2,481, tratamento 1,981) |
| Levene sobre os logs | p = 0,116 | não rejeita variâncias iguais |
| Efeito observado (log) | 2,105 | `mu_com_bot − mu_sem_bot`; razão de medianas de 5,14× |
| n por grupo | 30 | tamanho da coleta |
| α | 0,05 | — |

**Por que um `sigma` comum.** O teste de Levene sobre os logs não rejeita a
igualdade de variâncias, e manter um sigma só faz com que "efeito = 0"
signifique exatamente H0 verdadeira, sem que uma diferença de dispersão entre
os grupos entre por acaso no cálculo de erro tipo I. A variância desigual
observada fica reservada para a violação de pressupostos da Q3 (sprint 2), que
o gerador já suporta via `sigma_tratamento` e `n_tratamento`.

**Por que o efeito é aditivo em log.** Numa lognormal, somar `δ` em escala log
multiplica a mediana por `exp(δ)`. Logo o efeito é parametrizado em log e não
em horas: "efeito zero" é exatamente H0, e os efeitos crescentes das curvas de
poder ficam numa escala comparável.

## 5. Previsão registrada antes de simular

> Esperamos que o **Mann-Whitney tenha mais poder** neste cenário. Com
> lognormal de sigma ≈ 2,2 a média amostral é dominada por poucos valores
> extremos, o que infla o erro-padrão do t de Welch; o Mann-Whitney usa só a
> ordem e não sofre com isso. Esperamos também que o **erro tipo I do Welch
> fique longe de 5%** com n = 30: a assimetria é forte demais para o teorema
> central do limite resolver nesse tamanho de amostra. O Mann-Whitney não
> depende de normalidade, então deve ficar perto dos 5% nominais.

Essa previsão vive em `simulacao/cenario.PREVISAO` e é impressa pela execução,
de modo que a comparação "esperado × obtido" da conclusão seja verificável.

## 6. Resultado dos dois testes em um conjunto simulado

Saída de `python -m simulacao --config config.json` (semente 42), com os dados
gerados sob o efeito observado na coleta:

```
  Gerado com efeito_log = 2.105 (mediana do tratamento x8.20)
  Controle  : n=30  mediana=    0.70 h  média=    1.64 h
  Tratamento: n=30  mediana=    6.77 h  média=   33.62 h

         teste  estatística p-valor       tamanho de efeito magnitude rejeita H0 (a=0.05)
    t de Welch       1.6895 0.10185     +0.436 (d de Cohen)   pequeno                 não
Mann-Whitney U     736.0000 0.00002 +0.636 (delta de Cliff)    grande                 sim
```

**Os dois testes discordam, em dados com efeito conhecido e grande.** O
Mann-Whitney rejeita H0 com p = 0,00002 e delta de Cliff +0,636 (grande); o t
de Welch não rejeita (p = 0,102) e enxerga o efeito como pequeno (d = +0,436).

A razão é visível nas descritivas: a mediana do tratamento é quase 10× a do
controle, mas a média do tratamento (33,6 h) carrega poucos valores extremos
que inflam o desvio-padrão e, com ele, o erro-padrão do t. O Mann-Whitney usa
apenas a ordenação e não é afetado pela magnitude desses extremos.

Numa única amostra não há como dizer qual dos dois acertou — é por isso que as
repetições da sprint 2, com a verdade conhecida por construção, são
necessárias. Essa amostra isolada é consistente com a previsão da seção 5, mas
não a confirma.

Rodando sob H0 verdadeira (`--efeito 0`), nenhum dos dois rejeita (Welch
p = 0,302; Mann-Whitney p = 0,842), como esperado.

**Nota sobre tamanho de efeito.** Cada teste vem com a medida que lhe
corresponde — d de Cohen para o Welch (em desvios-padrão) e delta de Cliff para
o Mann-Whitney (obtido direto de U, sem supor distribuição) — porque um
p-valor isolado não diz se a diferença tem importância prática.

## 7. Limitação do cenário

O bot não é atribuído aleatoriamente aos PRs. PRs que ele revisa podem ser
maiores, de autores diferentes ou de áreas mais sensíveis do código, então a
diferença observada nos dados reais **não é necessariamente efeito causal do
bot**. Isso não compromete o laboratório: os dados reais servem só para
calibrar parâmetros realistas da simulação, e é na simulação — onde a verdade é
conhecida por construção — que os testes são comparados.

## 8. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `simulacao/cenario.py` | pergunta, hipóteses por teste, previsão e derivação dos parâmetros a partir de `data/real.csv` |
| `simulacao/gerador.py` | geração lognormal, efeito aditivo em log, variantes para violação de pressupostos |
| `simulacao/testes.py` | t de Welch e Mann-Whitney com d de Cohen e delta de Cliff |
| `simulacao/__main__.py` | execução de ponta a ponta com semente fixa |
| `tests/test_simulacao.py` | 26 testes dos três módulos |
| `data/simulado_exemplo.csv` | conjunto simulado gerado pela execução |
| `data/testes_exemplo.csv` | resultado dos dois testes sobre esse conjunto |
