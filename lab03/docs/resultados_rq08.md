# Resultados — RQ 08 (bônus): rework rate

Issue [#74](https://github.com/gabrielchagas13/lab-exp-de-software-turma-02-grupo-06/issues/74) · Lab03S03
Reprodução: `python -m analise.rq08 --config config.json` (lê `data/metricas.json`; saídas em `data/analise/rq08_*.csv`)

Amostra final: **300 repositórios**. Janela: 2025-10-01 a 2026-09-30.

**Rework rate** é a proporção de releases **corretivas** sobre o total de releases do repositório (métrica que o DORA acrescentou em 2024). A classificação "corretiva" é a mesma heurística do CFR (b), nas quatro versões.

> **Ressalva.** A heurística corretiva foi validada contra a amostra-ouro e **só a v5 atinge F1 ≥ 0,70**, e de forma otimista (F1 = 0,723, em 300 releases; as versões v1 a v4, que este resultado usa, ficam entre 0,54 e 0,68). Os números abaixo são o que cada versão produz, não a taxa real de retrabalho.

## Resultado

| Heurística | Rework (mediana) | IQR | CFR (b) (mediana) | IQR | % repositórios com rework > CFR (b) |
|---|---|---|---|---|---|
| v1 semver | **66,7%** | 42,9 – 88,6% | 37,5% | 12,5 – 64,0% | 70,7 |
| v2 semver ou nome | **66,7%** | 43,7 – 88,9% | 37,5% | 12,5 – 64,2% | 71,0 |
| v3 commits | **14,6%** | 2,9 – 32,4% | 10,8% | 0,0 – 31,6% | 35,7 |
| v4 combinada | **71,2%** | 46,9 – 90,3% | 40,5% | 14,3 – 66,2% | 75,0 |

Com as versões que usam semver (v1, v2, v4), a **mediana de repositórios tem dois terços das releases classificadas como corretivas**. Com a v3 (baseada nos commits) são 15%. A diferença entre as versões é de quase cinco vezes, maior que a diferença entre rework e CFR (b) dentro de uma mesma versão.

## Em que o rework difere do CFR (b)

As duas métricas usam o mesmo rótulo "release corretiva", mas contam coisas diferentes:

| | CFR (b) | Rework rate |
|---|---|---|
| Quem é contado | a release que **falhou**: foi **seguida** de uma corretiva | a release que **é** corretiva |
| Janela | só vale se a correção veio em até 7 dias | qualquer prazo |
| Censura | os últimos 7 dias da janela saem do denominador | nada é censurado |
| Depende do ritmo de releases | **sim** | quase não |

- **O rework é maior que o CFR (b) na maioria dos repositórios** (71% com a v2; mediana da diferença de +19,8 pontos percentuais). Um projeto que publica uma release por mês pode ter metade das releases como correções e ainda assim um CFR (b) próximo de zero, porque nenhuma correção cai a 7 dias da release anterior.
- **A diferença some quando a heurística usa commits** (v3: mediana da diferença 0 e 36% maior contra 34% menor): ela marca menos releases como corretivas, e as que marca estão mais perto das mudanças reais.

### O CFR (b) acompanha a frequência de releases; o rework não

| Spearman com a frequência de releases | v1 | v2 | v3 | v4 |
|---|---|---|---|---|
| CFR (b) | 0,713 | 0,715 | 0,635 | 0,768 |
| Rework | 0,147 | 0,150 | 0,261 | 0,203 |

O CFR (b) tem correlação forte com a frequência de releases (ρ ≈ 0,7), e o rework tem correlação fraca (ρ ≈ 0,15 a 0,26). Isto é coerente com a hipótese levantada na RQ 07: a correlação positiva entre frequência e CFR (b) é, em boa parte, **mecânica**, pois quem publica mais releases tem mais chance de uma correção cair dentro da janela de 7 dias. Não é prova, já que o rework também mede outra coisa (a fração, não a taxa), mas aponta que o sinal "mais releases, mais falhas" da RQ 05 pelo CFR (b) deve ser interpretado com cautela.

Spearman entre rework e CFR (b) dentro de cada repositório: ρ = 0,47 (v2), 0,68 (v3) e 0,41 (v4), isto é, as duas métricas ordenam os repositórios de forma só moderadamente parecida.

## Limitações

- O rework herda todos os erros da heurística corretiva. Em especial, a versão semver trata todo incremento de *patch* como correção, inclusive patches planejados em ramos de manutenção; isso pode inflar o rework dos projetos que fazem releases de várias linhas em paralelo.
- Releases são o único sinal de "deploy": correções que não geraram release não aparecem.
- Não há faixas DORA para o rework; por isso não há classificação Elite/High/Medium/Low.
