# Katas escolhidos (issue #26)

4 katas autorais (não copiados de LeetCode/HackerRank/Codewars), todos em Python, com testes de aceitação em `pytest`. Código em `lab02/katas/<nome>/` (`kata.md` = enunciado, `solution.py` = stub a implementar, `test_solution.py` = testes de aceitação).

| # | Kata | Conceito | Assinatura |
|---|---|---|---|
| 01 | Semana de maior gasto | Agregação/agrupamento simples | `weekly_spending(purchases) -> (int, float)` |
| 02 | Ranking de tags normalizadas | Normalização de string + contagem | `normalize_tags(tags) -> list[tuple[str,int]]` |
| 03 | Ordem de execução com dependências | Grafo / ordenação topológica | `schedule_tasks(dependencies) -> list[str]` |
| 04 | Agrupamento de anagramas | Hashing / agrupamento | `anagram_clusters(words) -> list[list[str]]` |

## Por que 4 (número par)

Cada integrante resolve os 4 katas: 2 com IA, 2 sem, em ordem contrabalanceada (ex.: integrante A faz 01 e 03 com IA / 02 e 04 sem; integrante B faz 02 e 04 com IA / 01 e 03 sem; etc. — definir contrabalanceamento exato na issue #29).

## Por que dificuldade equivalente

Os 4 katas foram desenhados com a mesma "forma": uma função pura, sem I/O, sem dependência de bibliotecas externas, resolvível em poucas dezenas de linhas, cada um exercitando um conceito de estrutura de dados/algoritmo diferente (agregação, string, grafo, hashing) para não favorecer quem já treinou um conceito específico. Estimativa de esforço: 15-30 min de implementação dentro do time-box de 35 min, com folga para quem for mais devagar.

Foram validados rodando uma implementação de referência (não incluída no repositório, pra não vazar solução) contra os testes de cada kata — todos os testes passam com uma solução correta e falham com `NotImplementedError` no stub (conferido em `lab02/katas/*/test_solution.py`).

## Como rodar um kata

```bash
cd lab02
python3 -m venv venv && ./venv/bin/pip install pytest
cd katas/01_gastos_semanais
../../venv/bin/python3 -m pytest -q
```

## Pendência

Confirmar na issue #30 se a linguagem/ferramenta de métricas estáticas do grupo será Python + Radon (o que estes katas já assumem) ou se o grupo prefere Java + CK — nesse caso os katas precisam ser reescritos em Java antes da Sprint 2.
