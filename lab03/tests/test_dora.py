"""Testes da classificação DORA (issue #71).

Os casos são os cortes da tabela do enunciado, testados **nas fronteiras**: é
onde um erro de `<` para `<=` muda a categoria de um repositório sem que
nenhum outro teste perceba.
"""
import pytest

from metricas.dora import (ELITE, HIGH, LOW, MEDIUM, categoria_geral,
                           classificar_cfr, classificar_frequencia,
                           classificar_lead_time, classificar_recuperacao,
                           classificar_repo)


# ---- RQ 01: frequência de deploy (releases por semana, maior é melhor) ----

@pytest.mark.parametrize("valor,esperado", [
    (10, ELITE), (7, ELITE),           # >= 7 por semana
    (6.99, HIGH), (1, HIGH),           # >= 1 e < 7
    (0.99, MEDIUM), (12 / 52.1, MEDIUM),   # >= 1 por mês e < 1 por semana
    (0.2, LOW), (0, LOW),              # < 1 por mês
])
def test_frequencia(valor, esperado):
    assert classificar_frequencia(valor) == esperado


# ---- RQ 02: lead time (horas, menor é melhor) ----

@pytest.mark.parametrize("valor,esperado", [
    (0, ELITE), (23.9, ELITE),         # < 1 dia
    (24, HIGH), (167.9, HIGH),         # 1 dia a < 1 semana
    (168, MEDIUM), (719.9, MEDIUM),    # 1 semana a < 30 dias
    (720, LOW), (5000, LOW),           # >= 30 dias
])
def test_lead_time(valor, esperado):
    assert classificar_lead_time(valor) == esperado


# ---- RQ 03: change failure rate (proporção, menor é melhor) ----

@pytest.mark.parametrize("valor,esperado", [
    (0, ELITE), (0.15, ELITE),         # <= 15%
    (0.1501, HIGH), (0.30, HIGH),      # > 15% e <= 30%
    (0.3001, MEDIUM), (0.45, MEDIUM),  # > 30% e <= 45%
    (0.4501, LOW), (1.0, LOW),         # > 45%
])
def test_cfr(valor, esperado):
    assert classificar_cfr(valor) == esperado


# ---- RQ 04: tempo de recuperação (horas, menor é melhor) ----

@pytest.mark.parametrize("valor,esperado", [
    (0.5, ELITE), (0.99, ELITE),       # < 1 hora
    (1, HIGH), (23.9, HIGH),           # 1 hora a < 1 dia
    (24, MEDIUM), (167.9, MEDIUM),     # 1 dia a < 1 semana
    (168, LOW), (1000, LOW),           # >= 1 semana
])
def test_recuperacao(valor, esperado):
    assert classificar_recuperacao(valor) == esperado


def test_valor_ausente_nao_classifica():
    assert classificar_frequencia(None) is None
    assert classificar_lead_time(None) is None
    assert classificar_cfr(None) is None
    assert classificar_recuperacao(None) is None


# ---- categoria geral: mediana dos pontos, arredondada para baixo ----

def test_exemplo_do_enunciado():
    """(4, 3, 3, 1) tem mediana 3 => High."""
    cat = {"deployment_frequency": ELITE, "lead_time": HIGH,
           "change_failure_rate": HIGH, "recovery_time": LOW}
    assert categoria_geral(cat) == HIGH


def test_mediana_fracionaria_arredonda_para_baixo():
    """(4, 4, 3, 3) tem mediana 3,5: arredondando para baixo vira High, não Elite.

    É a diferença entre `floor` e `round`, e com 4 métricas a mediana cai entre
    dois valores com frequência."""
    cat = {"deployment_frequency": ELITE, "lead_time": ELITE,
           "change_failure_rate": HIGH, "recovery_time": HIGH}
    assert categoria_geral(cat) == HIGH


def test_tudo_elite_e_tudo_low():
    assert categoria_geral(dict.fromkeys(
        ["deployment_frequency", "lead_time", "change_failure_rate", "recovery_time"],
        ELITE)) == ELITE
    assert categoria_geral(dict.fromkeys(
        ["deployment_frequency", "lead_time", "change_failure_rate", "recovery_time"],
        LOW)) == LOW


def test_metrica_ausente_sai_da_mediana():
    """Repositório sem episódio de falha não tem tempo de recuperação.

    Dar uma nota arbitrária a ele empurraria a mediana numa direção qualquer;
    o correto é calcular com as três métricas que existem."""
    cat = {"deployment_frequency": ELITE, "lead_time": ELITE,
           "change_failure_rate": ELITE, "recovery_time": None}
    assert categoria_geral(cat) == ELITE  # mediana de (4, 4, 4)


def test_sem_nenhuma_metrica_devolve_none():
    assert categoria_geral(dict.fromkeys(
        ["deployment_frequency", "lead_time", "change_failure_rate", "recovery_time"],
        None)) is None


# ---- classificação completa ----

def test_classificar_repo_devolve_tudo():
    r = classificar_repo({"deployment_frequency": 8, "lead_time": 10,
                          "change_failure_rate": 0.5, "recovery_time": 200})
    assert r["dora_deployment_frequency"] == ELITE
    assert r["dora_lead_time"] == ELITE
    assert r["dora_change_failure_rate"] == LOW
    assert r["dora_recovery_time"] == LOW
    assert r["dora_geral"] == MEDIUM        # (4, 4, 1, 1) -> mediana 2,5 -> 2
    assert r["dora_metricas_validas"] == 4


def test_classificar_repo_conta_metricas_validas():
    r = classificar_repo({"deployment_frequency": 8, "lead_time": None,
                          "change_failure_rate": None, "recovery_time": None})
    assert r["dora_metricas_validas"] == 1 and r["dora_geral"] == ELITE
