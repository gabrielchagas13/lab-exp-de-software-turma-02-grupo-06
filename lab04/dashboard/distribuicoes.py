"""Distribuição de cada estatística sob H0, para o G2 (issue #78).

O G2 mostra *de onde vem* o p-valor: a curva da estatística quando H0 é
verdadeira, a região de rejeição a alfa = 5% e a área além do valor observado.
Para que a área desenhada seja de fato o p-valor que o scipy devolve, cada
curva aqui é a mesma aproximação que o scipy usa no cálculo:

- **t de Welch:** t de Student com os graus de liberdade de
  Welch-Satterthwaite.
- **Mann-Whitney U:** com n = 30 por grupo e sem empates o scipy usa a
  aproximação normal, com média n1·n2/2, desvio sqrt(n1·n2·(n1+n2+1)/12) e
  correção de continuidade de 0,5. A correção entra nos limiares das áreas,
  não na curva.

Os dois testes são bicaudais (ver `docs/cenario.md`), então tanto a região de
rejeição quanto o p-valor ocupam as duas caudas.
"""
from dataclasses import dataclass

import numpy as np
from scipy import stats

# Número de pontos de cada curva: suficiente para a área parecer contínua.
PONTOS = 801


@dataclass(frozen=True)
class Nula:
    """Curva da estatística sob H0 e os limiares que o gráfico sombreia.

    As áreas são simétricas em torno de `centro`: a região de rejeição é
    |x − centro| >= `dist_critica` e o p-valor é |x − centro| >= `dist_p`.
    """
    nome: str
    x: np.ndarray
    densidade: np.ndarray
    centro: float
    dist_critica: float
    dist_p: float
    observado: float
    p_valor: float
    descricao: str

    def cauda(self, distancia):
        """Máscara dos pontos nas duas caudas a `distancia` ou mais do centro."""
        return np.abs(self.x - self.centro) >= distancia


def gl_welch(tratamento, controle):
    """Graus de liberdade de Welch-Satterthwaite."""
    v1 = tratamento.var(ddof=1) / tratamento.size
    v2 = controle.var(ddof=1) / controle.size
    return float((v1 + v2) ** 2 / (v1 ** 2 / (tratamento.size - 1)
                                   + v2 ** 2 / (controle.size - 1)))


def _grade(centro, escala, observado, minimo=4.5):
    """Eixo x que cobre a curva e o valor observado, com folga."""
    meia = max(minimo * escala, abs(observado - centro) + escala)
    return np.linspace(centro - meia, centro + meia, PONTOS)


def nula_welch(tratamento, controle, alfa=0.05):
    gl = gl_welch(tratamento, controle)
    t_obs = float(stats.ttest_ind(tratamento, controle, equal_var=False).statistic)
    dist = stats.t(gl)
    x = _grade(0.0, 1.0, t_obs)
    return Nula(
        nome="welch", x=x, densidade=dist.pdf(x), centro=0.0,
        dist_critica=float(dist.ppf(1 - alfa / 2)),
        dist_p=abs(t_obs), observado=t_obs,
        p_valor=float(2 * dist.sf(abs(t_obs))),
        descricao=f"t de Student com {gl:.1f} graus de liberdade (Welch)".replace(".", ","),
    )


def nula_mann_whitney(tratamento, controle, alfa=0.05):
    n1, n2 = tratamento.size, controle.size
    u_obs = float(stats.mannwhitneyu(tratamento, controle,
                                     alternative="two-sided").statistic)
    media = n1 * n2 / 2
    dp = float(np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12))
    dist = stats.norm(media, dp)
    x = _grade(media, dp, u_obs)
    # Correção de continuidade: o scipy calcula z = (|U − média| − 0,5) / dp.
    # Somar/subtrair 0,5 nos limiares faz a área sob a normal sem correção
    # coincidir com o p-valor corrigido.
    dist_p = max(abs(u_obs - media) - 0.5, 0.0)
    return Nula(
        nome="mannwhitney", x=x, densidade=dist.pdf(x), centro=media,
        dist_critica=float(stats.norm.ppf(1 - alfa / 2) * dp + 0.5),
        dist_p=dist_p, observado=u_obs,
        p_valor=float(2 * stats.norm.sf(dist_p / dp)),
        descricao=f"Normal com média {media:.0f} e desvio {dp:.1f} "
                  f"(aproximação usada pelo scipy)".replace(".", ","),
    )


def nulas(tratamento, controle, alfa=0.05):
    """As duas curvas, na mesma ordem e com as mesmas chaves de `aplicar_ambos`."""
    return {"welch": nula_welch(tratamento, controle, alfa),
            "mannwhitney": nula_mann_whitney(tratamento, controle, alfa)}
