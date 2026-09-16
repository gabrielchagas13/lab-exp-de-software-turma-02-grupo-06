"""
Kata 03 - Ordem de execucao de tarefas com dependencias. Ver kata.md.

Trial: guilherme (GL) | tratamento: manual | issue #41
"""


def schedule_tasks(dependencies: dict[str, list[str]]) -> list[str]:
    # 1. Coletar todas as tarefas (chaves e dependencias)
    todas_tarefas = set(dependencies.keys())
    for deps in dependencies.values():
        for dep in deps:
            todas_tarefas.add(dep)

    # 2. Mapear dependencias pendentes de cada tarefa e quem depende de quem
    grau_dependencias: dict[str, set[str]] = {}
    quem_espera: dict[str, list[str]] = {}

    for tarefa in todas_tarefas:
        deps = set(dependencies.get(tarefa, []))
        grau_dependencias[tarefa] = deps
        quem_espera[tarefa] = []

    for tarefa, deps in grau_dependencias.items():
        for dep in deps:
            quem_espera[dep].append(tarefa)

    # 3. Fila de tarefas prontas (sem dependencias pendentes)
    prontas: list[str] = []
    for tarefa in todas_tarefas:
        if len(grau_dependencias[tarefa]) == 0:
            prontas.append(tarefa)

    ordem_execucao: list[str] = []

    # 4. Processar tarefas prontas
    while prontas:
        # Desempate alfabetico entre tarefas livres no mesmo momento
        prontas.sort()
        tarefa_atual = prontas.pop(0)
        ordem_execucao.append(tarefa_atual)

        for dependente in quem_espera[tarefa_atual]:
            grau_dependencias[dependente].remove(tarefa_atual)
            if len(grau_dependencias[dependente]) == 0:
                prontas.append(dependente)

    # 5. Se nem todas as tarefas puderam ser executadas, ha ciclo
    if len(ordem_execucao) < len(todas_tarefas):
        raise ValueError("cycle")

    return ordem_execucao
