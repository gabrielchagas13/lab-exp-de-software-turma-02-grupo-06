"""
Kata 03 - Ordem de execucao de tarefas com dependencias. Ver kata.md.

Implemente a funcao abaixo. Nao altere a assinatura.

NOTA (issue #45): o trial oficial da Sprint 2 (manual, gabrielchagas13)
foi encerrado CENSURADO em 2100s (35min) sem solucao -- ver o registro em
data/trials.csv (linha 03_escalonador_tarefas_gabrielchagas13_manual_
20260916T150941, time_to_green=None, censored=True, success_rate=0.0).
A implementacao abaixo foi concluida DEPOIS do encerramento do time-box,
fora do trial cronometrado -- mantida aqui como registro de que o kata
era soluvel, mas nao deve ser usada como entrada para as metricas
estaticas de RQ3 desse trial (nao existia nesse estado quando o trial
terminou).
"""

import heapq


def schedule_tasks(dependencies: dict[str, list[str]]) -> list[str]:
    pending = {task: set(required) for task, required in dependencies.items()}
    for required in dependencies.values():
        for task in required:
            pending.setdefault(task, set())

    dependents = {task: [] for task in pending}
    for task, required in pending.items():
        for prerequisite in required:
            dependents[prerequisite].append(task)

    available = [task for task, required in pending.items() if not required]
    heapq.heapify(available)
    order = []

    while available:
        task = heapq.heappop(available)
        order.append(task)
        for dependent in dependents[task]:
            pending[dependent].remove(task)
            if not pending[dependent]:
                heapq.heappush(available, dependent)

    if len(order) != len(pending):
        raise ValueError("cycle")
    return order
