# Roteiro da apresentação — Lab 04

Par P1: **t de Welch × Mann-Whitney**. Cenário: tempo até o merge de PRs com e
sem review do CodeRabbit.

Duração alvo: **15 minutos** de fala + 5 de perguntas. A apresentação é feita
**navegando o dashboard**, não slides separados — cada bloco abaixo corresponde
a uma seção da página, e a barra de navegação do topo serve de índice.

> Os blocos marcados com ⏳ dependem de issues ainda não fechadas. Enquanto
> estiverem abertas, a seção correspondente aparece como "em construção" no
> dashboard e o número a dizer na fala ainda não existe.

| # | Bloco | Quem | Tempo | Seção do dashboard |
|---|---|---|---|---|
| 1 | Abertura e pergunta | — | 1 min | 1 |
| 2 | Dados e por que lognormal | — | 2 min | 1 (G1) |
| 3 | Hipóteses: os dois testes não testam a mesma coisa | — | 2 min | 1 |
| 4 | De onde vem o p-valor | — | 2 min | 2 (G2) |
| 5 | Q1: erro tipo I | — | 3 min | 3 (G3) |
| 6 | ⏳ Q2: poder | — | 2 min | 4 (G4) |
| 7 | ⏳ Q3: violações de pressupostos | — | 1 min | 5 |
| 8 | ⏳ Os testes nos dados reais | — | 1 min | 6 |
| 9 | Conclusão e recomendação | — | 1 min | 7 |

Preencher a coluna "Quem" na reunião de alinhamento. Sugestão: quem fez a issue
apresenta o bloco correspondente.

---

## 1. Abertura e pergunta (1 min)

> "A pergunta é simples: **PRs revisados por um bot demoram mais ou menos até o
> merge do que PRs sem review de bot?** A resposta interessante não é o sim ou
> não — é que dois testes estatísticos perfeitamente legítimos, aplicados aos
> **mesmos dados**, dão respostas opostas. O trabalho é entender por quê, e
> decidir em qual confiar."

Mostrar a pergunta no topo da seção 1.

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
> Q2 — e é exatamente o que aconteceu no exemplo da seção 2."

Se alguém perguntar se não é bug no código: temos um teste automatizado que
roda o mesmo experimento com σ baixo (quase normal) e confirma que aí o Welch
volta aos 5%. A conservadoria vem da assimetria, não da implementação.

## 6. ⏳ Q2: poder (2 min) — issue #80

Estrutura da fala, a completar quando a issue fechar:

> "Com efeito conhecido crescente, medimos quantas vezes cada teste acerta em
> detectá-lo. O poder do Mann-Whitney foi de ___% contra ___% do Welch no efeito
> que observamos na coleta."

Fechar com: "é a contrapartida direta da Q1 — o Welch economiza em falsos
positivos e paga em efeitos reais não detectados."

## 7. ⏳ Q3: violações de pressupostos (1 min) — issue #81

A completar. O código já suporta os três casos: σ desigual entre grupos,
contaminação por outliers e n pequeno/desbalanceado.

## 8. ⏳ Os testes nos dados reais (1 min) — issue #82

A completar com a tabela dos dois testes aplicados aos 60 PRs coletados.
Lembrar de repetir a limitação: **o bot não foi sorteado**, então nada disso é
causal.

## 9. Conclusão e recomendação (1 min)

Mostrar a tabela "previsto × encontrado" da seção 7.

> "A gente registrou as previsões **antes** de rodar qualquer simulação, e elas
> estão versionadas no código. Isso não é formalidade: com o resultado na mão é
> fácil contar uma história em que tudo era esperado."

- Previmos que o Welch ficaria longe dos 5% → **ficou** (1,68%), mas para o lado
  conservador, que não é o que normalmente se teme. Veredito honesto:
  **parcial**, porque a previsão não dizia a direção.
- Previmos que o Mann-Whitney ficaria perto dos 5% → **confirmada** (4,74%).
- ⏳ A previsão de poder depende da Q2.

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
- [ ] `python -m dashboard --config config.json` rodado com a versão mais
      recente do código, e `dashboard/index.html` commitado.
- [ ] `dashboard.pages_url` e `dashboard.projects_url` preenchidos em
      `config.json` (hoje aparecem como "(pendente)" no topo da página).
- [ ] Dashboard publicado no GitHub Pages e aberto no navegador antes de
      começar — não abrir o arquivo local na hora.
- [ ] Botão **Horas / Escala log** do G1 testado na máquina da apresentação.
- [ ] Coluna "Quem" da tabela de blocos preenchida.
- [ ] Blocos ⏳ atualizados ou removidos conforme as issues #80, #81 e #82.
