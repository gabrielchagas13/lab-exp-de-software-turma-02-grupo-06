"""Experimentos repetidos: erro tipo I (Q1) — issue #79.

O p-valor de uma amostra só não diz se um teste é confiável. O que diz é
repetir o experimento milhares de vezes **com a verdade conhecida** e contar
quantas vezes cada teste erra.

Q1 (erro tipo I)
----------------
Geramos `REPETICOES` réplicas com `efeito_log = 0`, ou seja, com os dois grupos
saindo exatamente da mesma lognormal: **H0 é verdadeira por construção**. Toda
rejeição é um falso positivo. A proporção de rejeições estima o erro tipo I
real do teste, que deveria ficar no α nominal de 5%.

Um teste que rejeita mais que α é **anticonservador**: ele anuncia diferenças
que não existem, e o α declarado no artigo não é o α de verdade. Um que rejeita
menos é **conservador**: não mente, mas desperdiça poder.

Calibração em vários α
----------------------
Olhar só α = 5% pode esconder o comportamento do teste. Como a mesma réplica dá
um p-valor, dá para calcular a taxa de rejeição em qualquer α sem gerar nada
novo: basta contar `p < α`. A curva resultante (taxa observada × α nominal)
deve seguir a diagonal se o teste for calibrado — é um teste muito mais severo
do que conferir um ponto só.

No limite, isso equivale a dizer que **sob H0 os p-valores de um teste bem
calibrado são uniformes em [0, 1]**, o que o Kolmogorov-Smirnov verifica
diretamente.

Custo
-----
Os dois testes são aplicados de forma vetorizada (`axis=1`), uma chamada para
todas as réplicas. As 10.000 réplicas levam décimos de segundo, então o
dashboard recalcula tudo a cada execução em vez de guardar resultados em disco.
"""
from dataclasses import dataclass

import numpy as np
from scipy import stats

from simulacao.gerador import gerar_par

REPETICOES = 10_000

# Grade de α da curva de calibração. Vai só até 0,20 porque é a faixa em que
# alguém de fato declararia significância.
ALFAS = np.array([0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20])

# Até quanto a taxa observada pode se afastar do α nominal antes de o veredito
# deixar de ser "calibrado", quando o intervalo de confiança não decide sozinho.
TOLERANCIA_RELATIVA = 0.20


@dataclass(frozen=True)
class TaxaRejeicao:
    """Proporção de rejeições de um teste e a precisão dessa estimativa."""
    teste: str
    repeticoes: int
    rejeicoes: int
    taxa: float
    ic_baixo: float
    ic_alto: float

    @property
    def erro_padrao(self):
        return float(np.sqrt(self.taxa * (1 - self.taxa) / self.repeticoes))


@dataclass(frozen=True)
class ResultadoErroTipo1:
    """Q1 para um teste: taxa em α, curva de calibração e veredito."""
    teste: str
    alfa: float
    taxa: TaxaRejeicao
    alfas: np.ndarray
    calibracao: np.ndarray
    ks_p: float
    veredito: str
    p_valores: np.ndarray

    @property
    def razao(self):
        """Taxa observada dividida pelo α nominal. 1,0 seria perfeito."""
        return self.taxa.taxa / self.alfa

    @property
    def p_minimo(self):
        """Menor p-valor que o teste produziu em todas as réplicas.

        Diz até onde o teste consegue chegar neste cenário: se nem em 10.000
        tentativas ele alcança p pequeno, nenhum nível de significância
        exigente é atingível com dados assim.
        """
        return float(self.p_valores.min())


def ic_wilson(sucessos, total, confianca=0.95):
    """Intervalo de confiança de Wilson para uma proporção.

    Preferido ao intervalo normal simples porque aqui a proporção é pequena
    (~0,05) e o intervalo normal pode descer abaixo de zero ou ficar
    assimetricamente errado justamente nessa faixa.
    """
    if total <= 0:
        raise ValueError("total deve ser positivo")
    z = float(stats.norm.ppf(1 - (1 - confianca) / 2))
    p = sucessos / total
    denominador = 1 + z ** 2 / total
    centro = (p + z ** 2 / (2 * total)) / denominador
    meia = z * np.sqrt(p * (1 - p) / total + z ** 2 / (4 * total ** 2)) / denominador
    return float(max(0.0, centro - meia)), float(min(1.0, centro + meia))


def _taxa(nome, p_valores, alfa):
    rejeicoes = int((p_valores < alfa).sum())
    baixo, alto = ic_wilson(rejeicoes, p_valores.size)
    return TaxaRejeicao(nome, int(p_valores.size), rejeicoes,
                        rejeicoes / p_valores.size, baixo, alto)


def _veredito(taxa, alfa):
    """Classifica o teste comparando o intervalo de confiança com o α nominal.

    Se o intervalo contém α, a diferença observada é compatível com ruído de
    simulação e o teste passa como calibrado. Se o intervalo inteiro está de um
    lado, a distorção é real — mas só vira veredito se também for grande o
    bastante para importar na prática (`TOLERANCIA_RELATIVA`): com 10.000
    réplicas o intervalo fica estreito, e sem esse piso qualquer desvio
    minúsculo viraria "anticonservador".
    """
    if taxa.ic_baixo <= alfa <= taxa.ic_alto:
        return "calibrado"
    if abs(taxa.taxa - alfa) <= TOLERANCIA_RELATIVA * alfa:
        return "calibrado"
    return "anticonservador" if taxa.taxa > alfa else "conservador"


def p_valores_replicas(rng, repeticoes, n, mu_controle, sigma_log, efeito_log,
                       sigma_tratamento=None, n_tratamento=None):
    """p-valores dos dois testes em `repeticoes` réplicas independentes.

    Devolve `{"welch": array, "mannwhitney": array}`, cada um com um p-valor
    por réplica. Os dois testes veem exatamente as mesmas amostras — é o que
    torna a comparação pareada e elimina a sorte do sorteio como explicação
    para a diferença entre eles.
    """
    controle, tratamento = gerar_par(
        rng, n=n, mu_controle=mu_controle, sigma_log=sigma_log,
        efeito_log=efeito_log, sigma_tratamento=sigma_tratamento,
        n_tratamento=n_tratamento, repeticoes=repeticoes)
    return {
        "welch": np.asarray(stats.ttest_ind(tratamento, controle, axis=1,
                                            equal_var=False).pvalue, dtype=float),
        "mannwhitney": np.asarray(stats.mannwhitneyu(tratamento, controle, axis=1,
                                                     alternative="two-sided").pvalue,
                                  dtype=float),
    }


def erro_tipo1(cenario, repeticoes=REPETICOES, semente=42, n=None, **violacoes):
    """Q1: erro tipo I dos dois testes, com H0 verdadeira por construção.

    `violacoes` (`sigma_tratamento`, `n_tratamento`) vai direto ao gerador e
    fica disponível para a Q3 repetir este mesmo experimento com os pressupostos
    quebrados. No cenário-base não é usado.

    Devolve `{chave: ResultadoErroTipo1}`.
    """
    rng = np.random.default_rng(semente)
    alfa = cenario["alfa"]
    ps = p_valores_replicas(
        rng, repeticoes=repeticoes, n=n or cenario["n_por_grupo"],
        mu_controle=cenario["mu_controle"], sigma_log=cenario["sigma_comum"],
        efeito_log=0.0, **violacoes)

    resultados = {}
    for chave, p in ps.items():
        taxa = _taxa(chave, p, alfa)
        # Taxa de rejeição em cada α da grade: as mesmas réplicas, outro corte.
        calibracao = np.array([(p < a).mean() for a in ALFAS], dtype=float)
        resultados[chave] = ResultadoErroTipo1(
            teste=chave, alfa=alfa, taxa=taxa, alfas=ALFAS, calibracao=calibracao,
            ks_p=float(stats.kstest(p, "uniform").pvalue),
            veredito=_veredito(taxa, alfa), p_valores=p)
    return resultados


def poder(cenario, efeito_log=None, repeticoes=REPETICOES, semente=42, n=None,
          **violacoes):
    """Proporção de rejeições com efeito **presente**: o poder de cada teste.

    É o mesmo experimento da Q1 com `efeito_log != 0`, então a comparação entre
    as duas é direta: mesma máquina, mesmas amostras, só muda a verdade.

    Por padrão usa o efeito correspondente à razão de medianas observada na
    coleta, que é a referência que o resto do grupo usa no G4 e na seção 6.
    Devolve `{chave: TaxaRejeicao}`.

    O artefato oficial da Q2 (G4 e as curvas) é o do módulo `sim`; esta função
    existe para a conclusão poder citar um número de poder calculado na mesma
    máquina da Q1 — os dois caminhos concordam dentro do ruído de simulação.
    """
    if efeito_log is None:
        efeito_log = float(np.log(cenario["razao_medianas_observada"]))
    if efeito_log == 0:
        raise ValueError("efeito_log = 0 é H0 verdadeira; use erro_tipo1()")
    rng = np.random.default_rng(semente)
    ps = p_valores_replicas(
        rng, repeticoes=repeticoes, n=n or cenario["n_por_grupo"],
        mu_controle=cenario["mu_controle"], sigma_log=cenario["sigma_comum"],
        efeito_log=efeito_log, **violacoes)
    return {chave: _taxa(chave, valores, cenario["alfa"])
            for chave, valores in ps.items()}


def main(argv=None):
    """Imprime a Q1 no terminal, sem precisar gerar o dashboard inteiro.

    Uso:
        python -m simulacao.experimentos --config config.json
    """
    import argparse
    import json
    import os
    import sys

    import pandas as pd

    from simulacao import cenario as cen

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="simulacao.experimentos",
                                     description="Q1: erro tipo I (issue #79)")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--repeticoes", type=int, default=REPETICOES)
    parser.add_argument("--semente", type=int, default=None)
    args = parser.parse_args(argv)

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    raiz = os.path.dirname(os.path.abspath(args.config))
    c = cen.montar(os.path.join(raiz, cfg["coleta"]["saida"]))
    resultados = erro_tipo1(c, repeticoes=args.repeticoes,
                            semente=args.semente if args.semente is not None
                            else cfg["seed"])

    print(f"\nQ1: erro tipo I em {args.repeticoes:,} réplicas com H0 verdadeira"
          .replace(",", "."))
    print(f"n = {c['n_por_grupo']} por grupo, lognormal com sigma(log) = "
          f"{c['sigma_comum']:.3f}, alfa nominal = {c['alfa']}\n")
    print(pd.DataFrame([{
        "teste": r.teste,
        "falsos positivos": f"{r.taxa.rejeicoes}/{r.taxa.repeticoes}",
        "erro tipo I": f"{r.taxa.taxa:.4f}",
        "IC 95%": f"[{r.taxa.ic_baixo:.4f}, {r.taxa.ic_alto:.4f}]",
        "obs/nominal": f"{r.razao:.2f}x",
        "menor p": f"{r.p_minimo:.2e}",
        "veredito": r.veredito,
    } for r in resultados.values()]).to_string(index=False))
    print()


if __name__ == "__main__":
    main()
