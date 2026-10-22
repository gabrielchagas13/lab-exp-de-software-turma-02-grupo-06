# Resultados — RQ 07: sensibilidade da classificação DORA

Issue [#73](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/73) · Lab03S03
Reprodução: `python -m analise.rq07 --config config.json` (lê `data/dataset.csv` e `data/parquet/releases.parquet`; saídas em `data/analise/rq07_*.csv`)

Amostra final: **300 repositórios**. Janela: 2025-10-01 a 2026-09-30.

## Combinações comparadas

| Combinação | Unidade de deploy | Lead time | CFR | Papel |
|---|---|---|---|---|
| C1 | release | (a) | (a) proxy de CI | referência |
| C2 | release + pré-release | (b) | (b) `v2` | troca os três eixos |
| C3 | release | (b) | (a) | só o lead time muda |
| C4 | release | (a) | (b) `v2` | só o CFR muda |
| C5 | release + pré-release | (a) | (a) | só a unidade de deploy muda |

C3, C4 e C5 diferem de C1 em **um** eixo cada, então a diferença entre C1 e cada uma delas é atribuível àquele eixo. C2 mostra o efeito acumulado. O tempo de recuperação não tem variante (vem dos workflow runs) e é idêntico em todas as combinações.

**Tag como unidade de deploy ficou de fora.** A API de tags não traz data (o enunciado manda usar a do commit apontado) e a coleta só buscou commits entre releases publicadas. Datar as tags exigiria uma nova coleta; vai como limitação na seção de ameaças à validade.

## Distribuição da categoria geral

| | Elite | High | Medium | Low |
|---|---|---|---|---|
| C1 | 21 | 126 | 137 | 16 |
| C2 | 8 | 93 | 163 | 36 |
| C3 | 27 | 134 | 120 | 19 |
| C4 | 6 | 83 | 179 | 32 |
| C5 | 21 | 129 | 134 | 16 |

## Concordância entre combinações (categoria geral)

Kappa de Cohen com ponderação linear; IC 95% por bootstrap dos repositórios (1.000 réplicas, semente 42).

| Par | % que mudou | subiu / desceu | Kappa linear | IC 95% |
|---|---|---|---|---|
| C1 × C2 | **34,3** | 9,7 / 24,7 | **0,496** | 0,414 – 0,574 |
| C1 × C3 | 19,3 | 12,3 / 7,0 | 0,732 | 0,669 – 0,800 |
| C2 × C3 | 26,0 | 23,7 / 2,3 | 0,647 | 0,574 – 0,710 |
| C1 × C4 | 23,3 | 1,3 / 22,0 | 0,660 | 0,591 – 0,726 |
| C1 × C5 | 1,0 | 1,0 / 0,0 | 0,986 | 0,971 – 1,000 |

(Os 10 pares estão em `rq07_pares.csv`; "subiu" significa que o segundo membro do par classifica o repositório melhor que o primeiro.)

Pela escala usual de Landis & Koch (1977), 0,41–0,60 é concordância moderada e 0,61–0,80 substancial. Entre a referência e a troca completa (C1 × C2) a concordância é **moderada**: **cerca de 1 em cada 3 repositórios muda de categoria**. A mudança é quase toda para pior (24,7% descem, 9,7% sobem).

## De onde vem a mudança: eixo por eixo

| Eixo | Troca | % que mudou de categoria na métrica | Kappa linear |
|---|---|---|---|
| Unidade de deploy | release → release + pré-release | 8,3 | 0,887 |
| Lead time | (a) → (b) | 43,3 | 0,558 |
| CFR | (a) → (b) v5 | **62,0** | **0,008** |
| Recuperação | sem variante | 0,0 | 1,000 |

- **Unidade de deploy tem efeito pequeno.** Só 25 repositórios sobem de categoria de frequência ao contar pré-releases, e no geral só 1% muda (C1 × C5).
- **Lead time tem efeito médio.** (a) e (b) concordam só moderadamente por métrica. As trocas vão nos dois sentidos (24,7% sobem e 18,7% descem), então não há viés sistemático para um lado.
- **O CFR domina.** Entre (a) e (b) o kappa é 0,008, ou seja, **não há concordância além do acaso**: 54,3% dos repositórios descem na métrica e 7,7% sobem. O proxy de CI põe 83% dos repositórios em Elite nessa dimensão. O proxy de entrega espalha-os por todas as categorias. Medem fenômenos diferentes (falha de pipeline no default branch contra release que precisou de correção), como já discutido na RQ 03.

### Dentro do CFR (b): a versão da heurística também importa

| Heurística corretiva | Mediana do CFR | % que mudou (geral, C1 × C1 + versão) | Kappa linear |
|---|---|---|---|
| **v5 patch e notas (referência)** | **23,5%** | **23,3** | **0,660** |
| v1 semver | 37,5% | 31,7 | 0,558 |
| v2 semver ou nome | 37,5% | 31,7 | 0,558 |
| v3 commits | 10,8% | **15,3** | 0,775 |
| v4 combinada | 40,5% | 34,0 | 0,522 |

A escolha entre (a) e (b) importa mais que a escolha da versão, mas a versão não é neutra: a v3 muda menos da metade dos repositórios que a v4 muda. Foi por isso que o grupo deixou a escolha da versão depender do F1 contra a amostra-ouro, e não da preferência: a **v5** foi adotada como referência por ser a única com F1 >= 0,70 (0,723).

## As conclusões das RQ 01 a 06 são robustas?

| RQ | Conclusão | Robustez à definição |
|---|---|---|
| RQ 01 | Poucos repositórios publicam diariamente | **Robusta.** Contar pré-releases move 8% das categorias de frequência. |
| RQ 02 | Lead time mediano de dias, não de horas | **Parcial.** A categoria muda para 43% dos repositórios conforme (a) ou (b), nos dois sentidos. |
| RQ 03 | Taxa de falha baixa pelo CI, alta pela entrega | **Depende totalmente da definição.** Kappa 0,013. |
| RQ 04 | Tempo de recuperação | Sem variante nesta análise; só vale a definição por workflow. |
| RQ 05 | Frequência × CFR | **Sinal robusto, magnitude não** (tabela abaixo). |

Spearman entre frequência de deploy e CFR (n = 300) em cada combinação (`rq07_robustez_rq05.csv`):

| Combinação | CFR | ρ | p |
|---|---|---|---|
| C1 (release) | (a) | 0,178 | 0,002 |
| C5 (release + pré) | (a) | 0,176 | 0,002 |
| C4 (release) | (b) v2 | 0,715 | < 0,001 |
| C2 (release + pré) | (b) v2 | 0,691 | < 0,001 |

O sinal é positivo em todas as combinações: nesta amostra, quem faz mais releases tem **mais**, não menos, falha por qualquer proxy. A força passa de fraca (ρ ≈ 0,18) a forte (ρ ≈ 0,7) conforme o CFR, e o que determina o resultado é o CFR, não a unidade de deploy.
**Cautela com o CFR (b):** parte dessa correlação pode ser mecânica, já que repositórios que publicam mais releases têm mais releases de patch, e a heurística semver trata incremento de patch como correção. Isto é uma hipótese, não foi testada aqui, e deve ser discutida com a RQ 05 (#72) e a validação da heurística.

## Conclusão

A classificação DORA **não é robusta à definição operacional**. A fragilidade vem quase toda do CFR e, em menor grau, do lead time. A unidade de deploy (release contra release + pré-release) quase não importa. Resultados em categorias (Elite/High/...) devem ser reportados **sempre com a combinação usada**, e as conclusões sobre estabilidade (RQ 03 e RQ 05) devem apresentar as duas variantes de CFR lado a lado, nunca só uma.

## Limitações

- Tags não foram usadas como unidade de deploy (acima).
- O lead time de C2 usa commits entre releases publicadas; a coleta não buscou commits entre pré-releases, então a unidade "release + pré-release" só altera a **frequência**, não o lead time nem o CFR.
- Há 276 repositórios com tempo de recuperação (24 sem episódios de falha); esses ficam fora dessa métrica, e a categoria geral deles é a mediana das três métricas restantes.
- O kappa depende de as faixas serem as fixas da disciplina; com outros cortes os percentuais mudariam.
