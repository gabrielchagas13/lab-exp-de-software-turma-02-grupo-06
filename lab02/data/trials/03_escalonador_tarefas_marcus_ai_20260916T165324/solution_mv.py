"""
Kata 03 - Ordem de execucao de tarefas com dependencias. Ver kata.md.

Trial: marcus (MV) | tratamento: IA (Claude) | issue #37
"""

import heapq


def schedule_tasks(dependencies: dict[str, list[str]]) -> list[str]:
    # Tarefas que so aparecem como dependencia de outra tambem entram na ordem.
    tasks = set(dependencies)
    for deps in dependencies.values():
        tasks.update(deps)

    pending = {task: set(dependencies.get(task, [])) for task in tasks}
    dependents: dict[str, list[str]] = {task: [] for task in tasks}
    for task, deps in pending.items():
        for dep in deps:
            dependents[dep].append(task)

    # Heap em vez de lista: entre as tarefas livres, sai sempre a menor
    # alfabeticamente, que e o criterio de desempate do enunciado.
    ready = [task for task, deps in pending.items() if not deps]
    heapq.heapify(ready)

    order: list[str] = []
    while ready:
        task = heapq.heappop(ready)
        order.append(task)
        for dependent in dependents[task]:
            pending[dependent].discard(task)
            if not pending[dependent]:
                heapq.heappush(ready, dependent)

    # Sobrou tarefa sem nunca ficar livre => ha ciclo de dependencia.
    if len(order) != len(tasks):
        raise ValueError("cycle")

    return order
