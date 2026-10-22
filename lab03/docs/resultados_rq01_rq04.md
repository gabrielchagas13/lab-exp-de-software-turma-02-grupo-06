# Resultados — RQ 01 a RQ 04 e classificação DORA C1

Issue [#71](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/71) · Lab03S03
Reprodução: `python -m analise.rq01_rq04 --config config.json`

Amostra final: **300 repositórios**. Janela: 2025-10-01 a 2026-09-30.
Todas as métricas reportadas em **mediana e IQR** — as distribuições são fortemente assimétricas e a média é dominada por poucos extremos (o maior lead time da amostra é de 70.293 h contra uma mediana de 226 h).

## RQ 01 — Frequência de deploys

| | Mediana | IQR | Min | Max |
|---|---|---|---|---|
| Releases por semana | **0,44** | 0,23 – 1,04 | 0,10 | 51,26 |

A mediana equivale a cerca de **uma release a cada 2,3 semanas**. Mesmo entre projetos populares com CI/CD, publicar release é evento quinzenal, não diário: só **6 repositórios (2%)** atingem o corte Elite de 7 por semana, e 83 (28%) ficam em Low (menos de uma por mês).

## RQ 02 — Lead time

| Variante | Mediana | IQR |
|---|---|---|
| (a) por release | **226,3 h** (9,4 dias) | 68,1 – 818,0 h |
| (b) por commit | **179,8 h** (7,5 dias) | 52,4 – 900,9 h |

**Por que as duas divergem.** A variante (a) usa, de cada release, o *commit mais antigo* incluído nela — é um máximo, e basta um commit esquecido num branch de longa duração para a release inteira parecer lenta. A variante (b) dá um valor a cada commit, então esse mesmo commit antigo vira um ponto entre centenas e quase não move a mediana. Em **98 dos 300 repositórios (33%)** a variante (a) ficou mais que o dobro da (b), o que mostra que o efeito não é raro.

A consequência prática é que a escolha da variante muda a categoria DORA de muitos repositórios, e é por isso que ela entra como eixo da análise de sensibilidade da RQ 07.

## RQ 03 — Taxa de falha

| Variante | Mediana | IQR |
|---|---|---|
| (a) proxy de CI | **4,9 %** | 2,1 – 10,9 % |
| (b) proxy de entrega — `v5_patch_e_notas` **(referência)** | **23,5 %** | 0,0 – 49,4 % |
| (b) — `v1_semver` | 37,5 % | 12,5 – 64,0 % |
| (b) — `v2_semver_ou_nome` | 37,5 % | 12,5 – 64,1 % |
| (b) — `v3_commits` | 10,8 % | 0,0 – 31,6 % |
| (b) — `v4_combinada` | 40,5 % | 14,3 – 66,2 % |

**Esse é o resultado mais importante da análise.** As duas variantes medem o mesmo conceito — "que proporção das entregas dá errado" — e discordam por um fator de cinco. Pelo proxy de CI a mediana é 4,9 %, bem dentro do Elite (≤ 15 %); pelo proxy de entrega é 23,5 % na variante de referência (v5), que cai em **High**, uma categoria abaixo. Com as variantes baseadas só em *patch* a distância é maior ainda: 37,5 % a 40,5 %, já em **Medium**.

A explicação é que os dois medem coisas diferentes apesar do nome comum. O CFR (a) mede **falha de pipeline no default branch**, e um pipeline que quebra é corrigido antes do merge na maioria dos projetos maduros — por isso 248 dos 300 repositórios (83 %) aparecem como Elite nessa dimensão. O CFR (b) mede **falha que chegou ao usuário e exigiu uma release corretiva**, que é o que a definição DORA realmente descreve.

Isso é material direto para a seção de ameaças à validade (construto): *"release publicada" é proxy de deploy e "CI vermelho" é proxy de falha*, e o segundo proxy subestima a instabilidade de forma sistemática.

Censura: **869 releases** publicadas nos últimos 7 dias da janela ficaram fora do denominador, contra 18.095 avaliadas (4,6 %). Descartá-las silenciosamente teria inflado artificialmente a taxa de sucesso.

> **Variante de referência.** O grupo adotou a **v5** (`patch` semver **e** release notes citando *fix/bugfix/hotfix/revert*) como CFR (b) principal: é a única com F1 ≥ 0,70 contra o consenso da amostra-ouro (0,723 em 300 releases). O valor é otimista, porque a v5 foi escolhida olhando parte da própria amostra — nas 33 releases fora da escolha o F1 foi 0,65, e o IC de 95 % vai de 0,63 a 0,80. As versões v1 a v4 continuam calculadas e entram como análise de sensibilidade na RQ 07 e na RQ 08.

## RQ 04 — Tempo de recuperação

| | Mediana | IQR | n |
|---|---|---|---|
| Tempo de recuperação | **2,70 h** | 0,95 – 9,69 h | 276 |
| Proporção de episódios censurados | 0,00 | 0,00 – 0,0018 | 280 |

**24 repositórios (8 %) não têm tempo de recuperação** porque não tiveram nenhum episódio de falha na janela. Eles entram na classificação com três métricas em vez de quatro: atribuir-lhes um valor arbitrário empurraria a mediana numa direção qualquer sem respaldo no dado.

A censura é praticamente nula na mediana — quase todo episódio de falha se resolve dentro da janela —, mas há repositórios com proporção 1,0, isto é, falhas que nunca foram corrigidas até o fim da observação.

## Classificação DORA C1

Combinação de referência: **unidade de deploy = release publicada, lead time = variante (a), CFR = variante (a)**.

| Dimensão | Elite | High | Medium | Low | Sem class. | % Elite+High |
|---|---|---|---|---|---|---|
| Deployment frequency | 6 | 70 | 141 | 83 | 0 | 25,3 % |
| Lead time | 46 | 83 | 91 | 80 | 0 | 43,0 % |
| Change failure rate | 248 | 36 | 10 | 6 | 0 | **94,7 %** |
| Tempo de recuperação | 75 | 162 | 27 | 12 | 24 | 85,9 % |
| **Geral (C1)** | **21** | **126** | **137** | **16** | 0 | **49,0 %** |

A categoria geral é a mediana das quatro notas (Elite = 4 … Low = 1) arredondada **para baixo**. Com quatro métricas a mediana cai entre dois valores com frequência, e o arredondamento para baixo é o que impede que um repositório (4, 4, 3, 3) seja promovido a Elite.

**Leitura.** O perfil da amostra é de projetos **estáveis e lentos**: muito bem nas duas dimensões de estabilidade (CFR 94,7 % e recuperação 85,9 % em Elite+High) e mal nas duas de velocidade (frequência 25,3 %, lead time 43,0 %). Metade da amostra fica em Elite ou High no geral, mas quase sempre carregada pelas notas de estabilidade.

Vale reportar esse desequilíbrio com cuidado: a nota alta em estabilidade vem do CFR (a), que é justamente o proxy que a RQ 03 mostrou ser otimista. Trocando para o CFR (b) na v5, a mediana de 23,5 % rebaixa essa dimensão de Elite para High, e 62,0 % dos repositórios mudam de categoria nela — é exatamente isso que a RQ 07 quantifica.

## Arquivos gerados

| Arquivo | Conteúdo |
|---|---|
| `data/analise/rq01_rq04_descritivas.csv` | mediana, IQR, min, max e ausentes por métrica |
| `data/analise/dora_c1.csv` | valor e categoria de cada métrica, por repositório |
| `data/analise/dora_c1_distribuicao.csv` | contagem por categoria, por dimensão |
| `data/dataset.csv` | dataset final (300 × 33), documentado em `docs/dicionario_dados.md` |
