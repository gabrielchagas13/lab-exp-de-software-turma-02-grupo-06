"""
Hipoteses (H0/H1) e ameacas a validade do experimento (issue #27).

Titulo do laboratorio: "Geracao integral por IA vs. Codificacao manual".
A variavel independente e o METODO DE DESENVOLVIMENTO:
  - Tratamento A (manual): o integrante escreve o codigo do zero, sem IA.
  - Tratamento B (geracao integral por IA): o integrante NAO escreve o
    codigo base. Ele formula um prompt descrevendo o kata, cola o codigo
    gerado pela IA no ambiente, e corrige eventuais falhas gerando novos
    prompts (nao editando o codigo manualmente linha a linha).

Modulo estruturado para ser importado pelos scripts de analise estatistica
e de geracao do relatorio final (Sprint 3), evitando reescrever o texto das
hipoteses em varios lugares.

Uso:
    from hypotheses import HYPOTHESES, THREATS_TO_VALIDITY, TREATMENT_B_RULE
    for h in HYPOTHESES:
        print(h.rq, h.h0, h.h1)
"""

from dataclasses import dataclass

TREATMENT_B_RULE = (
    "Tratamento B (geracao integral por IA): o integrante nao escreve o "
    "codigo base manualmente. Ele descreve o kata em um prompt, a IA gera "
    "a solucao inteira, e o codigo gerado e colado no ambiente. Falhas "
    "identificadas pelos testes sao corrigidas por novos prompts (pedindo "
    "correcao) ou ajustes pontuais, nunca reescrevendo a solucao do zero "
    "manualmente. Tempo do trial inclui geracao + toda a depuracao."
)


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
        question="Delegar a geração total do código para a IA reduz o tempo total (geração + correção) necessário para resolver uma tarefa de programação em comparação à codificação manual?",
        h0="Não há diferença na mediana do tempo total até passar em todos os testes de aceitação (time-to-green, incluindo geração e depuração) entre o tratamento manual e o tratamento de geração integral por IA.",
        h1="A mediana do time-to-green é menor no tratamento de geração integral por IA do que no tratamento manual.",
        metric="time_to_green_seconds (geração + depuração; censurado em 2100s = 35min para trials que não terminam a tempo)",
        statistical_test="Wilcoxon signed-rank (pareado, within-subject)",
    ),
    Hypothesis(
        rq="RQ2",
        question="O código gerado integralmente por IA apresenta mais ou menos defeitos (testes que falham) do que o código feito à mão ao final do tempo limite?",
        h0="Não há diferença na mediana da taxa de sucesso (% de testes de aceitação passando ao final do time-box) entre o tratamento manual e o tratamento de geração integral por IA.",
        h1="A mediana da taxa de sucesso difere entre o tratamento manual e o tratamento de geração integral por IA.",
        metric="success_rate (testes_passando / testes_totais); complementar: n_testes_falhando",
        statistical_test="Wilcoxon signed-rank (pareado, within-subject)",
    ),
    Hypothesis(
        rq="RQ3",
        question="O código gerado por IA apresenta maior complexidade ciclomática, verbosidade ou duplicação em comparação ao código desenvolvido manualmente?",
        h0="Não há diferença na mediana da complexidade ciclomática média, na verbosidade (LOC) nem na duplicação entre o tratamento manual e o tratamento de geração integral por IA.",
        h1="A mediana da complexidade ciclomática, do LOC e/ou da duplicação difere entre o tratamento manual e o tratamento de geração integral por IA.",
        metric="cyclomatic_complexity_mean, duplication_pct, loc (obrigatória como métrica de controle, dado que código gerado por IA tende a ser mais verboso)",
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
        description="Resolver katas em sequência pode deixar o participante mais rápido nos últimos, independentemente do tratamento (manual vs. geração por IA).",
        mitigation="Ordem dos katas e do tratamento contrabalanceada entre os integrantes (issue #29, ver trial_plan.py), para que o efeito de aprendizado se distribua igualmente entre os dois tratamentos na amostra agregada.",
    ),
    Threat(
        name="Familiaridade prévia com a ferramenta de IA",
        description="Integrantes com mais prática em formular prompts para o assistente de IA escolhido podem ter vantagem de tempo não relacionada ao tratamento em si.",
        mitigation="Mesma ferramenta de IA para todos os trials do grupo (issue #30); registrar no relatório final o nível de familiaridade prévia de cada integrante como limitação.",
    ),
    Threat(
        name="Vazamento de solução já vista / memorização",
        description="Se o kata for muito conhecido (ex.: clássico de LeetCode), a IA pode reproduzir uma solução memorizada do treinamento em vez de efetivamente gerar a partir do enunciado.",
        mitigation="Katas autorais do grupo, não publicados (ver lab02/docs/katas_escolhidos.md), reduzindo a chance de estarem no conjunto de treinamento do modelo.",
    ),
    Threat(
        name="Alucinações da IA e tempo iterando prompts para correção",
        description="No tratamento de geração integral, a IA pode produzir código que não compila, usa APIs inexistentes, ou passa longe do enunciado — o tempo gasto reformulando prompts para corrigir esses erros é parte do tratamento, mas pode variar muito entre trials e mascarar o tempo real de 'geração' isolado.",
        mitigation="O tempo registrado é sempre o tempo total do trial (geração + toda a depuração via prompt), não só o tempo até a primeira resposta da IA — consistente com a definição do Tratamento B. Discutir no relatório final, quando ocorrer, quantos prompts de correção foram necessários por trial (métrica opcional/exploratória).",
    ),
    Threat(
        name="Variação individual de habilidade",
        description="Integrantes com níveis de habilidade diferentes (tanto em programação quanto em formular prompts) tornam a comparação entre pessoas pouco confiável.",
        mitigation="Desenho crossover/within-subject (issue #29): cada integrante é seu próprio controle, comparando os dois tratamentos dentro da mesma pessoa, não entre pessoas diferentes.",
    ),
    Threat(
        name="Trial não concluído no time-box",
        description="Descartar trials que não terminam a tempo enviesaria a amostra a favor do tratamento com mais falhas (sobrevivência seletiva dos casos rápidos).",
        mitigation="Trial não concluído em 35 min é registrado como censurado em 35 min (time_to_green_seconds = 2100), não descartado, conforme o enunciado.",
    ),
]


if __name__ == "__main__":
    print(TREATMENT_B_RULE, "\n")
    for h in HYPOTHESES:
        print(f"{h.rq}: {h.question}")
        print(f"  H0: {h.h0}")
        print(f"  H1: {h.h1}")
        print(f"  Métrica: {h.metric}")
        print(f"  Teste: {h.statistical_test}\n")
