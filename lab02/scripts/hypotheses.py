"""
Hipoteses (H0/H1) e ameacas a validade do experimento (issue #27).

Modulo estruturado para ser importado pelos scripts de analise estatistica
e de geracao do relatorio final (Sprint 3), evitando reescrever o texto das
hipoteses em varios lugares.

Uso:
    from hypotheses import HYPOTHESES, THREATS_TO_VALIDITY
    for h in HYPOTHESES:
        print(h.rq, h.h0, h.h1)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Hypothesis:
    rq: str
    question: str
    h0: str
    h1: str
    metric: str
    statistical_test: str


HYPOTHESES: list[Hypothesis] = [
    Hypothesis(
        rq="RQ1",
        question="O uso de assistente de IA reduz o tempo necessario para resolver uma tarefa de programacao?",
        h0="Nao ha diferenca na mediana do tempo até passar em todos os testes de aceitação (time-to-green) entre trials com e sem assistente de IA.",
        h1="A mediana do time-to-green é menor nos trials com assistente de IA do que nos trials sem.",
        metric="time_to_green_seconds (censurado em 2100s = 35min para trials que nao terminam a tempo)",
        statistical_test="Wilcoxon signed-rank (pareado, within-subject)",
    ),
    Hypothesis(
        rq="RQ2",
        question="O uso de assistente de IA reduz a quantidade de defeitos (testes que falham) no código produzido?",
        h0="Nao ha diferenca na mediana da taxa de sucesso (% de testes de aceitação passando ao final do time-box) entre trials com e sem assistente de IA.",
        h1="A mediana da taxa de sucesso é maior nos trials com assistente de IA do que nos trials sem.",
        metric="success_rate (testes_passando / testes_totais); complementar: n_testes_falhando",
        statistical_test="Wilcoxon signed-rank (pareado, within-subject)",
    ),
    Hypothesis(
        rq="RQ3",
        question="O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido?",
        h0="Nao ha diferenca na mediana da complexidade ciclomática média (nem na duplicação, normalizadas por LOC) entre trials com e sem assistente de IA.",
        h1="A mediana da complexidade ciclomática média e/ou da duplicação difere entre trials com e sem assistente de IA.",
        metric="cyclomatic_complexity_mean, duplication_pct, loc (controle obrigatorio)",
        statistical_test="Wilcoxon signed-rank (pareado, within-subject)",
    ),
]


@dataclass(frozen=True)
class Threat:
    name: str
    description: str
    mitigation: str


THREATS_TO_VALIDITY: list[Threat] = [
    Threat(
        name="Efeito de aprendizado entre katas",
        description="Resolver katas em sequência pode deixar o participante mais rápido nos últimos, independentemente do tratamento (com/sem IA).",
        mitigation="Ordem dos katas e do tratamento contrabalanceada entre os integrantes (issue #29), para que o efeito de aprendizado se distribua igualmente entre os dois tratamentos na amostra agregada.",
    ),
    Threat(
        name="Familiaridade prévia com a ferramenta de IA",
        description="Integrantes com mais prática no assistente de IA escolhido podem ter vantagem de tempo não relacionada ao tratamento em si.",
        mitigation="Mesmo assistente de IA para todos os trials do grupo (issue #30); registrar no relatório final o nível de familiaridade prévia de cada integrante como limitação.",
    ),
    Threat(
        name="Vazamento de solução já vista / memorização",
        description="Se o kata for muito conhecido (ex.: clássico de LeetCode), o assistente de IA pode reproduzir uma solução memorizada do treinamento em vez de efetivamente ajudar a raciocinar.",
        mitigation="Katas autorais do grupo, não publicados (ver lab02/docs/katas_escolhidos.md), reduzindo a chance de estarem no conjunto de treinamento do modelo.",
    ),
    Threat(
        name="Variação individual de habilidade",
        description="Integrantes com níveis de habilidade diferentes tornam a comparação entre pessoas pouco confiável.",
        mitigation="Desenho crossover/within-subject (issue #29): cada integrante é seu próprio controle, comparando tratamentos dentro da mesma pessoa, não entre pessoas diferentes.",
    ),
    Threat(
        name="Trial não concluído no time-box",
        description="Descartar trials que não terminam a tempo enviesaria a amostra a favor do tratamento com mais falhas (sobrevivência seletiva dos casos rápidos).",
        mitigation="Trial não concluído em 35 min é registrado como censurado em 35 min (time_to_green_seconds = 2100), não descartado, conforme o enunciado.",
    ),
]


if __name__ == "__main__":
    for h in HYPOTHESES:
        print(f"{h.rq}: {h.question}")
        print(f"  H0: {h.h0}")
        print(f"  H1: {h.h1}")
        print(f"  Métrica: {h.metric}")
        print(f"  Teste: {h.statistical_test}\n")
