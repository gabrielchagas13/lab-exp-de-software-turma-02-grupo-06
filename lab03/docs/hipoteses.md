# Hipóteses informais por RQ

O que o grupo espera encontrar em cada questão de pesquisa, e por quê. São
expectativas qualitativas derivadas do referencial DORA (Forsgren, Humble &
Kim, 2018) e das definições operacionais do laboratório — não previsões
numéricas.

## RQ 01 — Frequência de deploys

**Esperamos uma mediana bem abaixo do corte Elite (7 releases por semana),
provavelmente entre uma release por mês e uma por semana.**

O corte Elite do DORA foi calibrado em equipes de produto que fazem deploy
contínuo do próprio serviço. Projetos open-source publicam *releases*, que é
outro ritmo: a release é um evento de empacotamento e comunicação, com notas,
versionamento e compatibilidade a considerar. Mesmo projetos muito ativos
tendem a acumular mudanças antes de publicar. Esperamos, portanto, a maioria da
amostra em Medium e Low nessa dimensão, com uma cauda pequena de projetos que
automatizaram a publicação a cada merge.

## RQ 02 — Lead time

**Esperamos que a variante (a) resulte sistematicamente maior que a (b), e que
a diferença seja grande em parte dos repositórios.**

A variante (a) usa o commit **mais antigo** de cada release, que é um máximo: um
único commit vindo de um branch de longa duração arrasta o valor da release
inteira. A variante (b) dá um valor a cada commit, e esse mesmo commit antigo
vira um ponto entre muitos, quase sem efeito sobre a mediana. A diferença entre
as duas não deve ser uniforme — deve se concentrar em projetos que mantêm
branches paralelos ou que integram contribuições externas antigas.

Em nível absoluto, esperamos lead times na casa de dias a semanas, não de horas:
o intervalo medido vai do commit até a **release**, não até o merge.

## RQ 03 — Taxa de falha

**Esperamos que o proxy de CI (a) produza valores baixos, e que o proxy de
entrega (b) produza valores bastante maiores. As duas variantes devem
discordar.**

O CFR (a) mede falha de *pipeline* no default branch. Em projetos maduros o
pipeline quebrado é corrigido antes do merge, então o default branch fica verde
na maior parte do tempo — esperamos a maioria da amostra no corte Elite
(≤ 15 %). O CFR (b) mede falha que **chegou ao usuário** e exigiu uma release
corretiva, que é o que a definição DORA realmente descreve.

Essa divergência é esperada por construção e não é defeito da medição: é a
evidência de que "CI vermelho" é um proxy ruim de "falha em produção".

**Sobre a heurística de release corretiva:** esperamos que o sinal de versão
(incremento de patch) sozinho tenha recall alto e precisão baixa — muitos
projetos publicam correção *e* funcionalidade em patch. Esperamos precisar
combinar sinais para atingir a meta de F1 ≥ 0,70.

## RQ 04 — Tempo de recuperação

**Esperamos medianas na casa de horas, e uma proporção pequena de episódios
censurados.**

Uma falha de CI no branch principal bloqueia o trabalho de todo mundo, então
tende a ser resolvida no mesmo dia. Esperamos a maioria da amostra em Elite ou
High. A censura (falha que nunca se resolve dentro da janela) deve ser rara e
concentrada em repositórios com workflows abandonados — um job de lint ou de
publicação de documentação que quebrou e ninguém mais olha.

## RQ 05 — Frequência × taxa de falha

**Esperamos não encontrar o *trade-off* clássico, mas também não tomamos uma
correlação positiva como evidência a favor do DORA.**

O DORA afirma que velocidade e estabilidade andam juntas. Mas aqui há risco de
artefato: o CFR (b) depende de uma release ser **seguida** por outra em até 7
dias, e quem publica com mais frequência tem mais chance de ter uma release
seguinte dentro da janela. Isso produziria correlação positiva por mecânica da
definição, não por comportamento de engenharia.

Esperamos, por isso, correlações diferentes entre as duas variantes do CFR: mais
forte na (b) que na (a). Se isso se confirmar, é indício do artefato, e não
confirmação nem refutação da tese do DORA.

## RQ 06 — Características associadas ao desempenho

**Esperamos efeitos pequenos e poucos resultados sobrevivendo à correção de
comparações múltiplas.**

Dos fatores disponíveis, apostamos que **tipo de projeto** e **número de
contribuidores** expliquem mais que popularidade (estrelas). Estrelas medem
visibilidade, não prática de engenharia, e tendem a ser ruído. Bibliotecas
devem publicar com menos frequência que aplicações e ferramentas CLI, porque a
release de uma biblioteca impõe custo de atualização aos consumidores.

Com pelo menos 12 testes e correção de Holm, esperamos que boa parte do que
pareceria significativo a 5 % não sobreviva.

## RQ 07 — Sensibilidade à definição operacional

**Esperamos que uma parcela substancial dos repositórios mude de categoria DORA
quando a definição muda — o bastante para que a classificação não seja tratada
como propriedade do repositório.**

As variantes não são refinamentos uma da outra: o CFR (a) e o (b) medem coisas
diferentes, e o lead time (a) e (b) resumem distribuições diferentes. Esperamos
que a troca do CFR mova mais repositórios que a troca do lead time, e que o
kappa ponderado entre combinações fique em concordância moderada, não quase
perfeita.

Se a mudança for grande, a conclusão prática do trabalho deixa de ser "a amostra
é Elite/High/Medium/Low" e passa a ser "a categoria depende de uma escolha
arbitrária que nenhum relatório DORA explicita".

## RQ 08 (bônus) — Rework rate

**Esperamos que a rework rate seja maior que o CFR (b) e que as duas não se
substituam.**

A rework rate conta toda release corretiva, sem exigir proximidade temporal da
release anterior; o CFR (b) só conta a correção que vem em até 7 dias. Logo, a
primeira deve ser um limite superior da segunda. Esperamos também que a rework
rate se correlacione menos com a frequência de releases, justamente por não
depender da janela de 7 dias — o que a tornaria menos sujeita ao artefato
descrito na RQ 05.
