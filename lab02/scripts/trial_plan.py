"""
Plano de execucao dos trials da Sprint 2 (issue #33+): ordem contrabalanceada
de katas x tratamento (manual/geração total por IA) por integrante.

Principios de contrabalanceamento usados (dado N=3 participantes, 4 katas):
  1. Cada integrante resolve os 4 katas: 2 com IA, 2 sem IA.
  2. Cada kata e feito por pelo menos 1 pessoa com IA e 1 sem IA (evita
     confundir "kata dificil" com "tratamento ruim").
  3. Tratamento alterna dentro da sequencia de cada pessoa (nunca 2 katas
     seguidos no mesmo tratamento), para reduzir efeito de fadiga/momentum
     dentro da sessao.
  4. Metade do trio comeca com IA, a outra com codificacao manual (ABAB vs
     BABA), para nao confundir "efeito de aquecimento" com "efeito da IA".
  5. A ordem das katas tambem varia entre pessoas (nao e sempre 1,2,3,4),
     para diluir o efeito de aprendizado entre katas.

Uso:
    from trial_plan import TRIALS
    for t in TRIALS:
        print(t.person, t.kata, t.treatment, t.sequence_position)
"""

from dataclasses import dataclass

KATAS = [
    "01_gastos_semanais",
    "02_normalizador_tags",
    "03_escalonador_tarefas",
    "04_clusters_anagramas",
]


@dataclass(frozen=True)
class Trial:
    person: str
    kata: str
    treatment: str  # "ia_total" (geracao integral) | "manual"
    sequence_position: int  # ordem de execucao dentro da sessao da pessoa (1-4)


TRIALS: list[Trial] = [
    # Marcus: comeca com IA, ordem natural das katas (IA, sem, IA, sem)
    Trial("marcusvv12", "01_gastos_semanais", "ia_total", 1),
    Trial("marcusvv12", "02_normalizador_tags", "manual", 2),
    Trial("marcusvv12", "03_escalonador_tarefas", "ia_total", 3),
    Trial("marcusvv12", "04_clusters_anagramas", "manual", 4),
    # Guilherme: comeca sem IA, mesma ordem de katas que o Marcus (sem, IA, sem, IA)
    Trial("gguilhermelana", "01_gastos_semanais", "manual", 1),
    Trial("gguilhermelana", "02_normalizador_tags", "ia_total", 2),
    Trial("gguilhermelana", "03_escalonador_tarefas", "manual", 3),
    Trial("gguilhermelana", "04_clusters_anagramas", "ia_total", 4),
    # Gabriel: comeca sem IA, ordem de katas diferente (2,1,3,4)
    Trial("gabrielchagas13", "02_normalizador_tags", "manual", 1),
    Trial("gabrielchagas13", "01_gastos_semanais", "ia_total", 2),
    Trial("gabrielchagas13", "03_escalonador_tarefas", "manual", 3),
    Trial("gabrielchagas13", "04_clusters_anagramas", "ia_total", 4),
]


def summary_by_kata() -> dict[str, dict[str, int]]:
    """Conta quantos trials manual/geração total por IA cada kata recebe, para conferir o balanceamento."""
    out = {k: {"ia_total": 0, "manual": 0} for k in KATAS}
    for t in TRIALS:
        out[t.kata][t.treatment] += 1
    return out


if __name__ == "__main__":
    for kata, counts in summary_by_kata().items():
        print(f"{kata}: {counts['ia_total']} geração total por IA / {counts['manual']} manual")
