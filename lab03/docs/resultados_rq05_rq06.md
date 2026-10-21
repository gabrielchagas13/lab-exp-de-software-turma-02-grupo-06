# Resultados — RQ 05 e RQ 06

Issue [#72](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/72) · Lab03S03
Reprodução: `python -m analise.rq05_rq06 --config config.json` (300 repositórios, `data/dataset.csv`).
Versão HTML com os gráficos: [`resultados_rq05_rq06.html`](resultados_rq05_rq06.html).

## RQ 05 — Frequência de deploy x CFR (Spearman)

Frequência = `releases_por_semana`. Dispersões em `data/analise/rq05_dispersao_<cfr>.png` (x em escala log, y symlog).

| CFR | rho | p-valor |
|---|---|---|
| (a) proxy de CI (`cfr_ci`) | 0,18 | 0,002 |
| (b) v1 semver | 0,71 | < 0,001 |
| (b) v2 semver ou nome | 0,71 | < 0,001 |
| (b) v3 commits | 0,63 | < 0,001 |
| (b) v4 combinada | 0,77 | < 0,001 |

**Leitura.** Os dados não confirmam que velocidade e estabilidade andam juntas, como afirma o DORA. Com o CFR (a) a correlação é positiva e fraca. Com o CFR (b) é positiva e forte: quem publica mais releases tem mais releases seguidas por uma corretiva.

**Cuidado com o CFR (b).** Ele conta uma release como falha quando outra release corretiva a segue em até 7 dias. Quem publica com frequência tem, mecanicamente, mais chance de ter a próxima release dentro de 7 dias, e boa parte delas é *patch*, que a heurística conta como corretivo. Parte do ρ de 0,63 a 0,77 pode, portanto, ser efeito da definição, e não de instabilidade real. Só dá para avaliar isso depois da validação contra o consenso (#67), e a seção de ameaças à validade (construto) deve registrar o risco.

## RQ 06 — Fatores associados às métricas DORA

Fatores: linguagem (as com menos de 10 repositórios viram "outros"), estrelas, contribuidores e idade (esses três divididos em quartis, Q1 a Q4). Métricas: frequência de deploy, lead time (a) e (b), CFR (a) e as quatro variantes do (b), e tempo de recuperação. Kruskal-Wallis com ε² = H / (n − 1). Os 36 testes (4 fatores x 9 métricas) formam uma família, corrigida por Holm. Tabela completa em `data/analise/rq06_fatores.csv`.

**11 dos 36 testes são significativos depois de Holm:**

| Fator | Métrica | p (Holm) | ε² |
|---|---|---|---|
| Idade | Frequência de deploy | < 0,001 | 0,09 |
| Idade | Lead time (a) | < 0,001 | 0,26 |
| Idade | Lead time (b) | < 0,001 | 0,19 |
| Idade | CFR (b) v1, v2, v3 e v4 | < 0,001 | 0,10 a 0,18 |
| Contribuidores | Lead time (a) | < 0,001 | 0,18 |
| Contribuidores | Lead time (b) | < 0,001 | 0,16 |
| Linguagem | Lead time (a) | < 0,001 | 0,12 |
| Linguagem | Lead time (b) | 0,005 | 0,10 |

**Leitura.**
- **Idade:** repositórios mais velhos publicam menos (mediana de 0,81 releases por semana no Q1 contra 0,31 no Q4), têm lead time muito maior (62 h no Q1 contra 713 h no Q4) e CFR (b) menor (0,65 no Q1 contra 0,25 no Q4 na v4). Projetos novos entregam rápido e muito, com mais correções; projetos antigos entregam devagar e com menos releases corretivas.
- **Contribuidores:** quanto mais contribuidores, maior o lead time (mediana de 105 h no Q1 contra 818 h no Q4). Pode refletir revisão e coordenação mais pesadas.
- **Linguagem:** Java (mediana de 1.951 h), C# (840 h) e C++ (787 h) têm lead time bem maior que TypeScript (136 h) e JavaScript (112 h). Java, C# e C++ têm poucos repositórios na amostra (12, 5 e 14).
- **Sem efeito:** estrelas, e nenhum fator para o tempo de recuperação nem para o CFR (a). Linguagem tem p = 0,006 bruto no CFR (a), mas não sobrevive ao Holm (0,15).

**Ressalva.** Idade é um fator de confusão natural: repositórios mais velhos acumulam releases e commits antigos, o que alonga o lead time (a), que usa o commit mais antigo da release.

## Pendências
- **Tipo de projeto** (biblioteca, aplicação, CLI, outro) é um quinto fator previsto, mas só existe depois do consenso da amostra-ouro. Quando sair, entra em `CATEGORICOS` em `analise/rq05_rq06.py` e a análise é reexecutada.
- **Qual variante do CFR (b)** é a de referência depende do F1 (#67). Hoje as quatro estão reportadas.
