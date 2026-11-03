"""Os dois testes do par P1 e seus tamanhos de efeito (issue #77).

**t de Welch** compara *médias* e não assume variâncias iguais. Assume que as
médias amostrais são aproximadamente normais — o que, com dados lognormais de
sigma alto e n = 30, é justamente o que está em xeque.

**Mann-Whitney U** compara *postos*: testa se um valor sorteado de um grupo
tende a superar um valor do outro. Não assume normalidade, mas também não testa
médias — e sob H0 geral (distribuições diferentes com a mesma mediana) ele pode
rejeitar por diferença de forma, não de posição.

Cada teste vem com o tamanho de efeito que lhe corresponde, porque o p-valor
sozinho não diz se a diferença importa:

- Welch -> **d de Cohen**, na mesma unidade das médias (desvios-padrão).
- Mann-Whitney -> **delta de Cliff**, que é a diferença entre a probabilidade
  de um grupo superar o outro e a probabilidade inversa. Vai de −1 a +1 e se
  obtém direto da estatística U, sem supor distribuição nenhuma.

Convenção de sinal: positivo significa que o **tratamento** (com bot) demora
mais que o controle.
"""
from dataclasses import asdict, dataclass

import numpy as np
from scipy import stats

# Romano et al. (2006), a mesma escala usada no Lab03.
FAIXAS_CLIFF = ((0.147, "desprezível"), (0.33, "pequeno"), (0.474, "médio"))
FAIXAS_COHEN = ((0.2, "desprezível"), (0.5, "pequeno"), (0.8, "médio"))


def _rotular(valor, faixas):
    for limite, nome in faixas:
        if abs(valor) < limite:
            return nome
    return "grande"


@dataclass(frozen=True)
class Resultado:
    teste: str
    estatistica: float
    p_valor: float
    efeito_nome: str
    efeito: float
    efeito_interpretacao: str
    rejeita_h0: bool

    def como_dict(self):
        return asdict(self)


def cohen_d(tratamento, controle):
    """d de Cohen com desvio combinado. Positivo = tratamento maior."""
    n1, n2 = tratamento.size, controle.size
    s1, s2 = tratamento.std(ddof=1), controle.std(ddof=1)
    combinado = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    if combinado == 0:
        return 0.0
    return float((tratamento.mean() - controle.mean()) / combinado)


def cliff_delta(u_tratamento, n_tratamento, n_controle):
    """delta de Cliff a partir do U do grupo tratado: 2U/(n1·n2) − 1."""
    return float(2.0 * u_tratamento / (n_tratamento * n_controle) - 1.0)


def welch(tratamento, controle, alfa=0.05):
    r = stats.ttest_ind(tratamento, controle, equal_var=False)
    d = cohen_d(tratamento, controle)
    return Resultado("t de Welch", float(r.statistic), float(r.pvalue),
                     "d de Cohen", d, _rotular(d, FAIXAS_COHEN),
                     bool(r.pvalue < alfa))


def mann_whitney(tratamento, controle, alfa=0.05):
    r = stats.mannwhitneyu(tratamento, controle, alternative="two-sided")
    delta = cliff_delta(r.statistic, tratamento.size, controle.size)
    return Resultado("Mann-Whitney U", float(r.statistic), float(r.pvalue),
                     "delta de Cliff", delta, _rotular(delta, FAIXAS_CLIFF),
                     bool(r.pvalue < alfa))


def aplicar_ambos(tratamento, controle, alfa=0.05):
    """Roda os dois testes na mesma amostra. Devolve {chave: Resultado}."""
    return {"welch": welch(tratamento, controle, alfa),
            "mannwhitney": mann_whitney(tratamento, controle, alfa)}


def p_valores(tratamento, controle):
    """Só os p-valores — atalho usado pelas 10.000 repetições da sprint 2.

    Evita construir dataclasses num laço de dezenas de milhares de iterações.
    """
    return (float(stats.ttest_ind(tratamento, controle, equal_var=False).pvalue),
            float(stats.mannwhitneyu(tratamento, controle,
                                     alternative="two-sided").pvalue))
