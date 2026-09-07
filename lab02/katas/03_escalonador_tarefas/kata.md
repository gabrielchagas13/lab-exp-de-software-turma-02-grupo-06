# Kata 03 — Ordem de execução de tarefas com dependências

Um sistema de build recebe uma lista de tarefas, cada uma com uma lista de dependências (tarefas que precisam terminar antes dela).

Implemente `schedule_tasks(dependencies)` que:
1. Retorna uma lista com uma ordem válida de execução (toda tarefa aparece depois de todas as suas dependências).
2. Quando mais de uma tarefa está livre para ser escolhida num dado momento (sem dependências pendentes), escolha a **ordem alfabética**.
3. Se houver uma dependência circular, levante `ValueError("cycle")`.

**Assinatura:**
```python
def schedule_tasks(dependencies: dict[str, list[str]]) -> list[str]:
    ...
```

**Exemplo:** `{"build": ["compile"], "compile": [], "test": ["build"]}` → `["compile", "build", "test"]`.

Tarefas que aparecem apenas como dependência de outra (e não como chave do dicionário) também devem aparecer na ordem final, sem dependências próprias.
