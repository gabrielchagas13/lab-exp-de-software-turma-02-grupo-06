"""Confronto entre o previsto e o encontrado (issue #84).

A previsão do grupo foi registrada em `cenario.PREVISOES` **antes** de qualquer
simulação repetida. Este módulo a confronta com os resultados, item a item, e
devolve um veredito por previsão.

O ponto de registrar a previsão antes é evitar o `HARKing` (*hypothesizing
after the results are known*): com os resultados na mão é fácil contar uma
história em que tudo era esperado. Guardar a previsão em código, versionada,
tira essa saída — inclusive a nossa.

Cada previsão sabe de que experimento depende. Enquanto esse experimento não
existir, o veredito é `pendente` e aponta a issue que falta, em vez de o
dashboard inventar uma conclusão a partir de dados que não tem.
"""
from dataclasses import dataclass

from simulacao.cenario import PREVISOES

# Resultado de cada previsão e como ele deve ser lido.
VEREDITOS = {
    "confirmada": "o que encontramos bate com o que prevíamos",
    "parcial": "a direção geral se confirmou, mas com uma ressalva importante",
    "refutada": "o resultado contradiz a previsão",
    "pendente": "o experimento que decide esta previsão ainda não foi rodado",
}


@dataclass(frozen=True)
class Avaliacao:
    """Uma previsão confrontada com o resultado correspondente."""
    id: str
    previsto: str
    encontrado: str
    veredito: str
    issue: int | None = None

    @property
    def resolvida(self):
        return self.veredito != "pendente"


def _pct(valor):
    return f"{valor * 100:.2f}%".replace(".", ",")


def _num(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


def _avaliar_erro_welch(cenario, erros):
    """P2: o erro tipo I do t de Welch fica longe do α nominal."""
    if erros is None:
        return "—", "pendente"
    r = erros["welch"]
    longe = not (r.taxa.ic_baixo <= r.alfa <= r.taxa.ic_alto)
    encontrado = (
        f"{_pct(r.taxa.taxa)} contra {_pct(r.alfa)} nominais "
        f"(IC 95%: {_pct(r.taxa.ic_baixo)} a {_pct(r.taxa.ic_alto)}), "
        f"{_num(r.razao)}× o nominal — {r.veredito}."
    )
    if not longe:
        return encontrado, "refutada"
    # A previsão acertou que ficaria longe, mas não dizia para que lado. O
    # desvio foi para o lado conservador, que é o oposto do risco que
    # normalmente se teme num teste mal calibrado — daí "parcial".
    if r.veredito == "conservador":
        encontrado += (" A previsão não dizia a direção; o desvio foi para o lado"
                       " conservador, não para o de falsos positivos a mais.")
        return encontrado, "parcial"
    return encontrado, "confirmada"


def _avaliar_erro_mw(cenario, erros):
    """P3: o erro tipo I do Mann-Whitney fica perto do α nominal."""
    if erros is None:
        return "—", "pendente"
    r = erros["mannwhitney"]
    encontrado = (f"{_pct(r.taxa.taxa)} contra {_pct(r.alfa)} nominais "
                  f"(IC 95%: {_pct(r.taxa.ic_baixo)} a {_pct(r.taxa.ic_alto)}) — "
                  f"{r.veredito}.")
    return encontrado, ("confirmada" if r.veredito == "calibrado" else "refutada")


def _avaliar_poder(cenario, poder):
    """P1: o Mann-Whitney tem mais poder que o t de Welch neste cenário."""
    if not poder:
        return "—", "pendente"
    welch, mw = poder["welch"], poder["mannwhitney"]
    encontrado = (f"poder de {_pct(mw)} contra {_pct(welch)} do t de Welch, "
                  f"no efeito observado na coleta.")
    if mw > welch:
        return encontrado, "confirmada"
    if mw == welch:
        return encontrado, "parcial"
    return encontrado, "refutada"


# Cada previsão e a função que a decide. Manter o mapa aqui, e não dentro de
# `PREVISOES`, deixa `cenario.py` livre de lógica de avaliação: lá fica só o
# que foi prometido, sem nada que dependa de resultado.
AVALIADORES = {
    "poder": ("poder", _avaliar_poder),
    "erro_welch": ("erros_tipo1", _avaliar_erro_welch),
    "erro_mannwhitney": ("erros_tipo1", _avaliar_erro_mw),
}


def avaliar(cenario, erros_tipo1=None, poder=None):
    """Confronta cada previsão com o resultado disponível.

    `poder` é opcional e vem da Q2 (#80), no formato
    `{"welch": taxa, "mannwhitney": taxa}` — a proporção de rejeições de cada
    teste no efeito observado na coleta. Enquanto não existir, a previsão de
    poder fica pendente e o resto da conclusão é entregue normalmente.
    """
    disponiveis = {"erros_tipo1": erros_tipo1, "poder": poder}
    avaliacoes = []
    for previsao in PREVISOES:
        fonte, avaliador = AVALIADORES[previsao["id"]]
        encontrado, veredito = avaliador(cenario, disponiveis[fonte])
        avaliacoes.append(Avaliacao(
            id=previsao["id"], previsto=previsao["previsto"],
            encontrado=encontrado, veredito=veredito,
            issue=previsao["issue"] if veredito == "pendente" else None))
    return avaliacoes


def resumo(avaliacoes):
    """Contagem por veredito, para a frase de abertura da conclusão."""
    contagem = {v: 0 for v in VEREDITOS}
    for a in avaliacoes:
        contagem[a.veredito] += 1
    return contagem
