"""
Plano de execucao dos trials da Sprint 2 (issues #35-#46): representacao em
codigo da tabela de contrabalanceamento oficial definida em
lab02/docs/desenho_experimental.md (issue #29, fonte de verdade).

Desenho (dado N=3 participantes, 4 katas, ordem sempre 01->02->03->04):
  - Marcus:    K1=IA, K2=Manual, K3=IA,     K4=Manual
  - Guilherme: K1=IA, K2=Manual, K3=Manual, K4=IA
  - Gabriel:   K1=Manual, K2=IA, K3=Manual, K4=IA

Cada participante fica com 2 katas em cada tratamento; cada kata individual
e resolvido tanto com IA quanto sem IA por integrantes diferentes (2/1 ou
1/2 por kata); total agregado: 6 trials com IA e 6 manual.

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
    # Marcus: ordem 01->02->03->04, tratamento IA,Manual,IA,Manual
    Trial("marcusvv12", "01_gastos_semanais", "ia_total", 1),
    Trial("marcusvv12", "02_normalizador_tags", "manual", 2),
    Trial("marcusvv12", "03_escalonador_tarefas", "ia_total", 3),
    Trial("marcusvv12", "04_clusters_anagramas", "manual", 4),
    # Guilherme: ordem 01->02->03->04, tratamento IA,Manual,Manual,IA
    Trial("gguilhermelana", "01_gastos_semanais", "ia_total", 1),
    Trial("gguilhermelana", "02_normalizador_tags", "manual", 2),
    Trial("gguilhermelana", "03_escalonador_tarefas", "manual", 3),
    Trial("gguilhermelana", "04_clusters_anagramas", "ia_total", 4),
    # Gabriel: ordem 01->02->03->04, tratamento Manual,IA,Manual,IA
    Trial("gabrielchagas13", "01_gastos_semanais", "manual", 1),
    Trial("gabrielchagas13", "02_normalizador_tags", "ia_total", 2),
    Trial("gabrielchagas13", "03_escalonador_tarefas", "manual", 3),
    Trial("gabrielchagas13", "04_clusters_anagramas", "ia_total", 4),
]


def summary_by_kata() -> dict[str, dict[str, int]]:
    """Conta quantos trials manual/geracao-IA cada kata recebe, para conferir o balanceamento."""
    out = {k: {"ia_total": 0, "manual": 0} for k in KATAS}
    for t in TRIALS:
        out[t.kata][t.treatment] += 1
    return out


if __name__ == "__main__":
    for kata, counts in summary_by_kata().items():
        print(f"{kata}: {counts['ia_total']} geração total por IA / {counts['manual']} manual")
