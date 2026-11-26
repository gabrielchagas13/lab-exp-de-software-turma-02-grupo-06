# Roteiro da apresentação — Lab 04

Par P1: **t de Welch × Mann-Whitney**. Cenário: tempo até o merge de PRs com e
sem review do CodeRabbit.

**Duração total: 6 minutos** (limite duro), apresentados no **dashboard estilo
Power BI**, trocando entre as 4 abas: **Os PRs → Qual teste confiar →
Simulador → Veredito**. Cada um fala do que implementou.

> **Dashboard:** https://gabrielchagas13.github.io/lab-exp-de-software-turma-02-grupo-06/lab04/powerbi/

| # | Bloco | Quem | Tempo | Aba e elemento | Issue |
|---|---|---|---|---|---|
| 1 | Pergunta, palpite e dados | Gabriel | 0:45 | Os PRs (palpite, medianas, gráficos) | #76 |
| 2 | Hipóteses e por que simular | Marcus | 0:30 | Os PRs (“Como ler”) | #77 |
| 3 | Q1: alarmes falsos | Marcus | 0:50 | Qual teste confiar (cartões de alarmes falsos) | #79 |
| 4 | Q2: poder e tamanho de amostra | Guilherme | 1:00 | Qual teste confiar (curva, 100 experimentos, “Quantos PRs”) | #80 #83 |
| 5 | Q3: dados mais bagunçados | Gabriel | 0:30 | Qual teste confiar (filtro “Simulação: cenário”) | #81 |
| 6 | Simulação ao vivo | Guilherme | 0:45 | Simulador | #78 |
| 7 | Testes nos dados reais | Gabriel | 0:40 | Veredito (cartões de p-valor) | #82 |
| 8 | Conclusão e recomendação | Marcus | 0:30 | Veredito (previsto × encontrado, resumo) | #84 |

Total: **5:30** (30 s de folga para as trocas). Gabriel 1:55, Marcus 1:50,
Guilherme 1:45.

**Regra de ouro:** se estourar o tempo, corte o número secundário, nunca a
conclusão. Cada fala termina passando a vez ao próximo.

---

## 1. Pergunta, palpite e dados (Gabriel, 0:45) — aba Os PRs

Começar pelo **palpite**: pedir à plateia que chute quantas vezes o PR com bot
demora mais, e só depois clicar em **Revelar**.

> "O CodeRabbit atrasa o merge? Coletei 60 PRs de um projeto real, 30 com
> review do bot e 30 sem. Antes de ver: quantas vezes mais demora o PR com bot?
> [Revelar] Cerca de 5 vezes no tempo típico: 4,3 horas contra 0,8. Repare no
> gráfico de cada PR: quase todos fecham rápido, mas alguns demoram dias, e
> esses poucos puxam a média para cima. Por isso olhamos o tempo típico, a
> mediana. Esse formato vai ser a chave da conversa. Marcus."

## 2. Hipóteses e por que simular (Marcus, 0:30) — aba Os PRs

> "Vamos comparar dois testes que respondem perguntas diferentes: o t de Welch
> compara a média dos grupos, o Mann-Whitney compara quem costuma demorar mais.
> Nos dados reais ninguém sabe a resposta certa, então não dá para dizer qual
> teste acertou. Por isso criamos dados simulados com esse mesmo formato: nós
> decidimos se existe diferença e conferimos qual teste acerta."

## 3. Q1: alarmes falsos (Marcus, 0:50) — aba Qual teste confiar

Apontar os dois cartões de **alarmes falsos**.

> "Primeira pergunta: se não existe diferença nenhuma, quantas vezes o teste
> acusa uma por engano? Esse é o alarme falso, e o certo seria 5 em 100. Em 10
> mil simulações, o Mann-Whitney errou 4,7%, certinho. O Welch errou só 1,7%.
> Parece bom, mas significa que o Welch é tímido demais: ele quase nunca acusa
> diferença, nem quando ela existe. Guilherme mostra isso."

## 4. Q2: poder e tamanho de amostra (Guilherme, 1:00) — aba Qual teste confiar

Apontar a curva "Quantas vezes cada teste encontra a diferença" e a linha de 80%.
Depois, arrastar o controle dos **100 experimentos** até a diferença de 2×.

> "Segunda pergunta: quando a diferença existe de verdade, o teste percebe?
> Quanto mais alta a curva, melhor. A do Mann-Whitney sobe muito antes. Aqui
> cada bolinha é um experimento: com o tempo dobrado, o Mann-Whitney percebe
> em 20 de 100 e o Welch em menos de 5. No efeito que observamos, de 5 vezes,
> o Mann-Whitney percebe em cerca de 3 de cada 4 e o Welch em 1 de cada 5. E
> quantos PRs precisaríamos? Olhem a tabela: o Welch pede bem mais PRs que o
> Mann-Whitney para achar o mesmo efeito. Gabriel."

## 5. Q3: dados mais bagunçados (Gabriel, 0:30) — aba Qual teste confiar

No filtro **Simulação: cenário**, trocar para **Com outliers** e depois
**Só 10 PRs por grupo**, mostrando "Alarmes falsos e acertos por cenário".

> "Terceira pergunta: e se os dados ficarem ainda mais bagunçados, com casos
> extremos ou poucos PRs? Olhem as barras mudando: o Welch fica ainda mais
> tímido e acerta menos. O Mann-Whitney continua perto de 5% de alarme falso,
> porque só olha a ordem dos PRs, não o tamanho dos números. Guilherme."

## 6. Simulação ao vivo (Guilherme, 0:45) — aba Simulador

Clicar em **Igual aos dados reais (5×)** e depois em **Rodar 1.000
experimentos**. Se der tempo, repetir com **Sem diferença**.

> "Aqui vocês mesmos montam o cenário. Eu escolho 'igual aos dados reais', onde
> o bot deixa o PR 5 vezes mais lento, e rodo mil experimentos aqui no
> navegador. O Mann-Whitney encontra a diferença na maior parte das vezes; o
> Welch, na minoria. Com 'sem diferença', os dois ficam perto dos 5% de alarme
> falso, ou menos, no caso do Welch. Gabriel."

## 7. Testes nos dados reais (Gabriel, 0:40) — aba Veredito

> "Nos dados reais, os dois testes concordam: PRs com bot demoram mais. Mas
> olhem a força da evidência: o Mann-Whitney vai a p = 0,0019, bem forte, e o
> Welch passa raspando, p = 0,037, no limite de 0,05. É o que a simulação
> avisava. Cuidado: o bot não foi sorteado, então isso mostra que as duas coisas
> andam juntas, não que o bot causa a demora. Marcus."

## 8. Conclusão e recomendação (Marcus, 0:30) — aba Veredito

Apontar a tabela **O que previmos × o que encontramos** e o **Em resumo**.

> "Resumindo: nossas previsões, feitas antes de simular, se confirmaram quase
> todas, e uma foi parcial: o Welch errou para o lado tímido. Para medir tempo
> em engenharia de software, use o Mann-Whitney e mostre também o tamanho da
> diferença. Isso vale para dados assimétricos como esses, com cerca de 30 PRs
> por grupo. Obrigado."

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

- [ ] Dashboard aberto **pelo GitHub Pages** antes de começar, não o arquivo local.
- [ ] Testado na máquina da apresentação: as 4 abas, o botão **Revelar** do
      palpite, o filtro **Simulação: cenário**, o controle deslizante dos
      100 experimentos e os botões do **Simulador**.
- [ ] Filtro de grupo e de cenário na posição inicial (**Base**) antes de começar.
- [ ] Combinar quem segura o mouse em cada troca de aba.
- [ ] Cada um ensaiou seu bloco com cronômetro (total máximo: 6 min).
