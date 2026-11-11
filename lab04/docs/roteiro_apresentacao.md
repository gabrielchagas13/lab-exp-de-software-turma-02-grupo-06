# Roteiro da apresentação — Lab 04

Par P1: **t de Welch × Mann-Whitney**. Cenário: tempo até o merge de PRs com e
sem review do CodeRabbit.

Duração alvo: **15 minutos** de fala + 5 de perguntas. A apresentação é feita
**navegando o painel interativo**, não slides separados — cada bloco abaixo
corresponde a uma seção dele, com navegação por ← →.

> **Página da apresentação:** [painel interativo](https://gabrielchagas13.github.io/lab-exp-de-software-turma-02-grupo-06/lab04/painel/)
> (navegar com ← → como slides). O [dashboard estático](https://gabrielchagas13.github.io/lab-exp-de-software-turma-02-grupo-06/lab04/dashboard/)
> fica como material de apoio/entrega.

Regra de divisão: **quem fechou a issue apresenta o bloco correspondente**.

| # | Bloco | Quem | Tempo | Seção do painel | Issue |
|---|---|---|---|---|---|
| 1 | Abertura e pergunta | Gabriel Chagas | 1 min | topo + 01 (os 60 PRs) | #76 |
| 2 | Dados e por que lognormal | Gabriel Chagas | 2 min | 02 (G1, botão “sortear”) | #76 |
| 3 | Hipóteses: os dois testes não testam a mesma coisa | Marcus Vinicius | 2 min | 01 (hipóteses e previsões) | #77 |
| 4 | De onde vem o p-valor | Guilherme Lana | 2 min | 03 (G2, permutações ao vivo) | #78 |
| 5 | Q1: erro tipo I | Marcus Vinicius | 3 min | 04 (laboratório, preset “H0 base”) + 05 (G3) | #79 |
| 6 | Q2: poder | Guilherme Lana\* | 2 min | 04 (preset “efeito real”) + 06 (G4) + 07 | #80 |
| 7 | Q3: violações de pressupostos | Gabriel Chagas | 1 min | 04 (presets “outliers”, “n = 10”) + abas do G4 | #81 |
| 8 | Os testes nos dados reais | Gabriel Chagas | 1 min | 08 (veredito) | #82 |
| 9 | Conclusão e recomendação | Marcus Vinicius | 1 min | 09 (esperado × encontrado) | #84 |

Tempo por pessoa: Marcus 6 min, Gabriel 5 min, Guilherme 4 min.

\* A #80 é a única sem dono registrado em commit; o bloco 6 está com o Guilherme
só para equilibrar o tempo. Quem fechar a issue assume o bloco.


---

## 1. Abertura e pergunta (1 min)

> "A pergunta é simples: **PRs revisados por um bot demoram mais ou menos até o
> merge do que PRs sem review de bot?** Nos 60 PRs que coletamos, os dois testes
> que aplicamos concordam: ambos rejeitam H0. Só que um deles passa raspando —
> **p = 0,037 contra p = 0,0019** — e essa diferença de margem não é detalhe.
> Mostramos ao longo da apresentação que, nesse tipo de dado, basta pouca coisa
> para o teste de margem apertada deixar de enxergar um efeito que está lá: em
> dados simulados **com efeito colocado por nós**, ele não enxerga. O trabalho é
> entender por que isso acontece e decidir em qual dos dois confiar."

Mostrar a pergunta no topo da seção 1.

Cuidado com a formulação: **nos dados reais os dois testes concordam.** A
discordância aparece no exemplo simulado da seção 2, onde a verdade é conhecida.
Dizer que "os testes dão respostas opostas" sem essa distinção contradiz a
seção 6 do dashboard.

## 2. Dados e por que lognormal (2 min)

Números a dizer:

- 60 PRs do repositório **MCPJam/inspector**, 30 por grupo, mergeados entre
  julho e setembro de 2026.
- `com_bot`: mediana **4,26 h**, média **22,82 h**. `sem_bot`: mediana
  **0,83 h**, média **4,36 h**.

> "Repare na distância entre média e mediana: a média é cinco vezes a mediana.
> Isso é a assinatura de uma distribuição assimétrica à direita — a maioria dos
> PRs fecha rápido e alguns ficam esquecidos por dias. O Shapiro-Wilk rejeita
> normalidade com p da ordem de 10⁻⁸ nos dois grupos. **Mas em escala log a
> assimetria some** e o Shapiro não rejeita (p = 0,93 e p = 0,31). Isso é a
> definição de uma lognormal, e é ela que o gerador usa."

No **G1**, clicar no botão **Horas** para mostrar a cauda longa e voltar para
**Escala log** para mostrar o ajuste. É o momento mais visual da apresentação —
vale a pena fazer a troca devagar.

> "E essa escolha não é detalhe de implementação: é justamente o tipo de
> distribuição em que um teste de médias e um teste de postos discordam. Se a
> gente tivesse simulado com normal, os dois concordariam sempre e não haveria
> trabalho nenhum."

## 3. Hipóteses (2 min)

Este é o ponto conceitual da apresentação. Mostrar a tabela de hipóteses.

> "Quase todo mundo escreve 'H0: os grupos são iguais' e aplica os dois testes.
> Isso está errado. O **t de Welch** testa se as **médias** são iguais. O
> **Mann-Whitney** testa se um PR sorteado de um grupo tem a mesma chance de
> demorar mais que um PR do outro — ele compara **postos**, não médias. São
> hipóteses diferentes, então os dois podem discordar sem que nenhum esteja
> com defeito."

Mencionar também que o teste é **bicaudal**: um review automático pode tanto
adiantar o merge quanto atrasá-lo, e não havia base para descartar uma direção
antes de olhar os dados.

## 4. De onde vem o p-valor (2 min)

Mostrar o **G2** e apontar os três elementos: a curva sob H0, a região de
rejeição sólida nas duas caudas e a área hachurada do p-valor.

> "Num conjunto simulado com o efeito que observamos na coleta — mediana oito
> vezes maior no grupo tratado — o **Mann-Whitney rejeita com p = 0,00002** e o
> **Welch não rejeita, p = 0,10**. O efeito existe, foi colocado por nós, e um
> dos dois não viu."

Mostrar os tamanhos de efeito na tabela: delta de Cliff **+0,636** (grande)
contra d de Cohen **+0,436** (pequeno).

> "Olhando só esta amostra não dá para saber qual dos dois acertou, porque num
> estudo real ninguém conhece a verdade. É exatamente por isso que a gente
> simula: na simulação a verdade é conhecida por construção."

## 5. Q1: erro tipo I (3 min)

O bloco mais importante. Mostrar a seção 3 e o **G3**.

> "Rodamos **10.000 réplicas** em que os dois grupos saem da mesma distribuição.
> H0 é verdadeira por construção, então **toda rejeição é um falso positivo**.
> Um teste honesto a 5% deveria rejeitar em 5% das réplicas."

Números a dizer:

| | Erro tipo I observado | IC 95% | Veredito |
|---|---|---|---|
| t de Welch | **1,68%** | 1,45% – 1,95% | conservador |
| Mann-Whitney | **4,74%** | 4,34% – 5,17% | calibrado |

> "O Welch rejeita **três vezes menos** do que promete. E o histograma da
> esquerda mostra por quê: os p-valores dele deveriam ser uniformes sob H0, mas
> se amontoam entre 0,2 e 0,4. **Em 10.000 réplicas, o menor p-valor que o
> Welch conseguiu produzir foi 0,0045.** Ou seja, com dados desta assimetria,
> um resultado a 1% de significância é literalmente inalcançável para ele."

Apontar no painel da direita que a curva azul fica abaixo da diagonal em toda a
faixa de α, enquanto a laranja a acompanha.

**Antecipar a pergunta óbvia:** "conservador não é bom? não dá falso positivo."

> "Dá para pensar assim, mas conservador tem preço: quem rejeita de menos
> quando não há efeito também rejeita de menos quando há. É o que vamos ver na
> Q2 — e é exatamente o que aconteceu no exemplo da seção 2, onde ele não viu um
> efeito que nós mesmos colocamos. Nos dados reais ele até rejeita, mas com
> p = 0,037, raspando no limite, enquanto o Mann-Whitney vai a 0,0019."

Se alguém perguntar se não é bug no código: temos um teste automatizado que
roda o mesmo experimento com σ baixo (quase normal) e confirma que aí o Welch
volta aos 5%. A conservadoria vem da assimetria, não da implementação.

## 6. Q2: poder (2 min) — issue #80

Mesma máquina da Q1, agora com efeito **presente e conhecido**: a mediana do
grupo tratado é multiplicada por um fator, e contamos quantas vezes cada teste
consegue detectá-lo. Isso é o poder.

| Efeito (razão de medianas) | Poder do t de Welch | Poder do Mann-Whitney |
|---|---|---|
| 1,0× (H0 verdadeira — é a Q1) | 1,7% | 4,7% |
| 2,0× | 4,8% | 20,4% |
| **5,14× (o observado na coleta)** | **20,9%** | **76,4%** |

> "No efeito que a gente realmente observou na coleta, o **Mann-Whitney detecta
> em 3 de cada 4 experimentos e o Welch em 1 de cada 5**. É a contrapartida
> direta da Q1: o Welch economiza em falsos positivos e paga em efeitos reais
> não detectados."

O número mais forte para fechar o bloco:

> "Com a mediana **dobrada** — um efeito enorme para qualquer padrão de
> engenharia de software — o Welch acerta em 4,8% das vezes. Isso é *menos* do
> que um teste calibrado rejeitaria por puro acaso quando não há efeito nenhum.
> Na prática, nesse cenário o t de Welch não enxerga."

Mostrar o G4 e apontar que a curva do Mann-Whitney sobe muito antes da do Welch.

Para conferir o número do efeito observado (IC 95%: 20,1%–21,7% e 75,6%–77,3%;
trocar a semente move cerca de meio ponto percentual):

```bash
python -c "import numpy as np, sim; m,s=sim.parametros_base(); print(sim.taxa_rejeicao(5.14,'base',10000,np.random.default_rng(42),mediana=m,sigma=s))"
```

## 7. Q3: violações de pressupostos (1 min) — issue #81

Mostrar o laboratório ao vivo do painel interativo (`painel/index.html`, botões
**outliers** e **n = 10**) ou a tabela abaixo (10.000 réplicas, seed 42).

| Cenário | Tipo I Welch | Tipo I MW | Poder Welch (razão 2×) | Poder MW (razão 2×) |
|---|---|---|---|---|
| Base (σ log ≈ 2,24, n=30) | 1,7% | 4,7% | 4,8% | 20,4% |
| Assimetria forte (σ ×1,5) | 0,7% | 4,7% | 1,2% | 11,2% |
| Outliers (10% ×20) | 1,2% | 4,7% | 3,2% | 19,0% |
| Amostra pequena (n=10) | 0,9% | 4,3% | 1,3% | 8,4% |

> "Quanto mais a gente viola o que o t assume, mais o Welch fica conservador e
> perde poder: com assimetria forte ele rejeita 0,7% sob H0 e só 1,2% com a
> mediana dobrada. O Mann-Whitney fica em ~5% sob H0 em todos os cenários,
> porque só usa a ordem dos dados: assimetria e tamanho de outlier não mudam
> os postos."

## 8. Os testes nos dados reais (1 min) — issue #82

| Teste | Estatística | p-valor | Tamanho de efeito | Conclusão (α=5%) |
|---|---|---|---|---|
| t de Welch | t = 2,18 (gl = 30,8) | 0,037 | Cohen d = 0,56 | Rejeita H0 |
| Mann-Whitney | U = 661 | 0,002 | Cliff δ = 0,47; razão de medianas = 5,14 | Rejeita H0 |

> "Nos 60 PRs os dois testes rejeitam H0: PRs revisados pelo CodeRabbit levam
> mais tempo até o merge, com mediana cerca de 5× maior. Mas a evidência do
> Mann-Whitney é ~20× mais forte (p = 0,002 contra 0,037). É exatamente o que a
> simulação previa: com essa assimetria o Welch quase não tem poder, e aqui ele
> passou raspando. O Cliff δ de 0,47 está no limite de um efeito grande; o
> Cohen d não é confiável porque a média é puxada por um PR de 203 h."

Repetir a limitação: **o bot não foi sorteado**, então nada disso é causal.
PRs que o bot revisa podem ser maiores ou de outros autores.

## 9. Conclusão e recomendação (1 min)

Mostrar a tabela "previsto × encontrado" da seção 7.

> "A gente registrou as previsões **antes** de rodar qualquer simulação, e elas
> estão versionadas no código. Isso não é formalidade: com o resultado na mão é
> fácil contar uma história em que tudo era esperado."

- Previmos que o Welch ficaria longe dos 5% → **ficou** (1,68%), mas para o lado
  conservador, que não é o que normalmente se teme. Veredito honesto:
  **parcial**, porque a previsão não dizia a direção.
- Previmos que o Mann-Whitney ficaria perto dos 5% → **confirmada** (4,74%).
- Previmos que o Mann-Whitney teria mais poder → **confirmada**, e com folga:
  76,4% contra 20,9% no efeito observado na coleta.

Fechar com a recomendação:

> "Para comparar duração em engenharia de software — tempo de merge, tempo de
> build, tempo de resolução de issue, que são quase sempre assimétricos — use o
> **Mann-Whitney** e relate o **delta de Cliff** junto com o p-valor. Se a média
> for mesmo o que interessa, transforme em log antes; aí o t volta a ser
> adequado, mas o resultado passa a ser sobre a mediana, não sobre a média em
> horas."

---

## Perguntas prováveis

**"Por que não usaram o teste t comum em vez do de Welch?"**
Porque o t comum assume variâncias iguais, uma suposição a mais sem ganho. O
Welch é estritamente mais seguro, e mesmo assim falhou aqui — o que torna o
achado mais forte, não mais fraco.

**"10.000 réplicas é suficiente?"**
O intervalo de confiança responde: com 10.000 réplicas a estimativa de 1,68%
tem IC de 1,45% a 1,95%. Mudar a semente move o resultado em menos de um ponto
percentual — existe um teste automatizado que verifica isso.

**"Vocês não estão só mostrando que o Mann-Whitney é melhor?"**
Não em geral. É melhor **neste cenário**, com esta assimetria e n = 30. Com
dados aproximadamente normais o t de Welch é melhor, porque usa mais informação
que a ordem. A conclusão é condicional, e a seção 7 diz isso explicitamente.

**"Se nos dados reais os dois testes concordam, qual é o problema?"**
A concordância é de decisão, não de margem: Welch p = 0,037, Mann-Whitney
p = 0,0019. Um está raspando no limite e o outro não. A Q1 explica a diferença —
o Welch é conservador neste tipo de dado — e a simulação mostra o caso em que
isso custa caro: com efeito presente e conhecido, ele deixa de rejeitar.

**"A diferença nos dados reais é causada pelo bot?"**
Não sabemos. O bot não foi atribuído aleatoriamente — PRs que ele revisa podem
ser maiores ou de autores diferentes. Os dados reais serviram para calibrar a
simulação, não para afirmar causalidade.

**"Por que bicaudal, se vocês esperavam que o bot atrasasse?"**
Porque a pergunta é se o tempo *difere*. Escolher a direção depois de olhar os
dados dobraria artificialmente a significância.

---

## Checklist antes de apresentar

- [ ] `python -m pytest tests -q` passando.
- [ ] `python -m dashboard --config config.json` e o gerador do painel rodados
      com a versão mais recente do código, e os HTML commitados.
- [ ] `dashboard.projects_url` preenchido em `config.json` (ainda aparece como
      "(pendente)" no topo da página).
- [ ] Painel e dashboard abertos **pelo GitHub Pages** antes de começar — não
      abrir o arquivo local na hora.
- [ ] Navegação por ← → do painel testada na máquina da apresentação, e o botão
      **Horas / Escala log** do G1.
- [ ] Bloco 6 confirmado com quem fechar a #80.
