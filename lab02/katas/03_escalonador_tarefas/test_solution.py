import pytest

from solution import schedule_tasks


def test_simple_chain():
    deps = {"build": ["compile"], "compile": [], "test": ["build"]}
    assert schedule_tasks(deps) == ["compile", "build", "test"]


def test_dependency_only_task_included():
    deps = {"build": ["compile"], "test": ["build"]}
    # "compile" so aparece como dependencia, nunca como chave
    assert schedule_tasks(deps) == ["compile", "build", "test"]


def test_alphabetical_tiebreak_among_free_tasks():
    deps = {"c": [], "a": [], "b": []}
    assert schedule_tasks(deps) == ["a", "b", "c"]


def test_diamond_dependency():
    deps = {"d": ["b", "c"], "b": ["a"], "c": ["a"], "a": []}
    assert schedule_tasks(deps) == ["a", "b", "c", "d"]


def test_cycle_raises_value_error():
    deps = {"a": ["b"], "b": ["a"]}
    with pytest.raises(ValueError):
        schedule_tasks(deps)
