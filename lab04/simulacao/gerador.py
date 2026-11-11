"""Gerador dos dados simulados (issue #77).

Gera duas amostras lognormais de tempo até o merge, parametrizadas em escala
log. O efeito é **aditivo em log**, o que equivale a multiplicar a mediana do
grupo tratado por `exp(efeito_log)` — a forma natural de deslocar uma lognormal
e a única que mantém "efeito = 0" exatamente igual a H0 verdadeira.

Por que importa para o laboratório: a comparação entre o t de Welch e o
Mann-Whitney depende de o gerador produzir dados assimétricos de verdade. Se a
simulação usasse normal, os dois testes concordariam quase sempre e não haveria
o que comparar.

Toda aleatoriedade passa por um `numpy.random.Generator` recebido de fora, para
que a semente fique sob controle de quem chama e os resultados sejam
reproduzíveis (exigência da seção 7 do enunciado).
"""
import numpy as np

import pandas as pd

from simulacao.cenario import GRUPO_CONTROLE, GRUPO_TRATAMENTO


def gerar_grupo(rng, n, mu_log, sigma_log, repeticoes=None):
    """Uma amostra lognormal de tamanho `n`, em horas (sempre > 0).

    Com `repeticoes`, devolve `repeticoes` amostras de uma vez, no formato
    (repeticoes, n). É o que permite às 10.000 réplicas da Q1 e da Q2 rodarem
    de forma vetorizada, sem mudar a distribuição gerada.
    """
    if n <= 0:
        raise ValueError("n deve ser positivo")
    if sigma_log <= 0:
        raise ValueError("sigma_log deve ser positivo")
    if repeticoes is not None and repeticoes <= 0:
        raise ValueError("repeticoes deve ser positivo")
    tamanho = n if repeticoes is None else (repeticoes, n)
    return rng.lognormal(mean=mu_log, sigma=sigma_log, size=tamanho)


def gerar_par(rng, n, mu_controle, sigma_log, efeito_log,
              sigma_tratamento=None, n_tratamento=None, repeticoes=None):
    """Par de amostras (controle, tratamento) para um cenário.

    - `efeito_log = 0` deixa os dois grupos com a mesma distribuição: é a
      configuração usada para medir erro tipo I (Q1).
    - `efeito_log > 0` multiplica a mediana do tratamento por `exp(efeito_log)`:
      é a configuração das curvas de poder (Q2).
    - `sigma_tratamento` e `n_tratamento` permitem quebrar a homogeneidade de
      variância e o balanceamento, que é o material da violação de pressupostos
      (Q3). Por padrão os dois grupos compartilham sigma e n.
    - `repeticoes` devolve as duas amostras no formato (repeticoes, n), uma
      réplica por linha, para os experimentos repetidos das Q1 e Q2.
    """
    sigma_t = sigma_log if sigma_tratamento is None else sigma_tratamento
    n_t = n if n_tratamento is None else n_tratamento
    controle = gerar_grupo(rng, n, mu_controle, sigma_log, repeticoes)
    tratamento = gerar_grupo(rng, n_t, mu_controle + efeito_log, sigma_t, repeticoes)
    return controle, tratamento


def gerar_contaminado(rng, n, mu_log, sigma_log, prop_outliers=0.05, fator=50.0):
    """Amostra lognormal com uma fração de outliers multiplicados por `fator`.

    Serve à Q3 como uma violação diferente da assimetria: alguns PRs ficam
    esquecidos por semanas e viram pontos extremos. É o caso em que a média
    (e portanto o t) deve sofrer mais que os postos.
    """
    if not 0 <= prop_outliers < 1:
        raise ValueError("prop_outliers deve estar em [0, 1)")
    amostra = gerar_grupo(rng, n, mu_log, sigma_log)
    quantos = int(round(n * prop_outliers))
    if quantos:
        indices = rng.choice(n, size=quantos, replace=False)
        amostra[indices] *= fator
    return amostra


def como_dataframe(controle, tratamento):
    """Formato longo, igual ao de `data/real.csv`, para reaproveitar os gráficos."""
    return pd.DataFrame({
        "grupo": [GRUPO_CONTROLE] * controle.size + [GRUPO_TRATAMENTO] * tratamento.size,
        "horas_ate_merge": np.concatenate([controle, tratamento]),
        "origem": "simulado",
    })
