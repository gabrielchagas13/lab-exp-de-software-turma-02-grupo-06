"""Classificação DORA de um repositório (Elite / High / Medium / Low).

Os cortes são os **fixos da disciplina** (enunciado, RQ 07), não os do relatório
DORA do ano: os relatórios definem as faixas por clusterização das respostas de
cada edição e elas mudam ano a ano, então a turma inteira usa a mesma tabela
para que os resultados sejam comparáveis entre grupos.

| Métrica              | Elite      | High            | Medium               | Low        |
|----------------------|------------|-----------------|----------------------|------------|
| Deployment frequency | >= 7/sem   | >= 1 e < 7/sem  | >= 1/mês e < 1/sem   | < 1/mês    |
| Lead time (mediana)  | < 1 dia    | 1 dia a < 1 sem | 1 sem a < 30 dias    | >= 30 dias |
| Change failure rate  | <= 15%     | > 15% e <= 30%  | > 30% e <= 45%       | > 45%      |
| Tempo de recuperação | < 1 h      | 1 h a < 1 dia   | 1 dia a < 1 sem      | >= 1 sem   |

Unidades esperadas: frequência em **releases por semana**, lead time e
recuperação em **horas**, CFR em **proporção** (0 a 1, não percentual).
"""
import math

ELITE, HIGH, MEDIUM, LOW = "Elite", "High", "Medium", "Low"
PONTOS = {ELITE: 4, HIGH: 3, MEDIUM: 2, LOW: 1}
CATEGORIAS = (ELITE, HIGH, MEDIUM, LOW)

HORAS_DIA = 24
HORAS_SEMANA = 7 * HORAS_DIA          # 168
HORAS_30_DIAS = 30 * HORAS_DIA        # 720
SEMANAS_NO_ANO = 52.1                 # mesma constante usada na frequência (RQ 01)
POR_SEMANA_MENSAL = 12 / SEMANAS_NO_ANO   # "1 por mês" convertido para por-semana

# Cada métrica declara se valores MAIORES são melhores e os cortes em ordem
# Elite -> High -> Medium. O que sobra é Low.
METRICAS = ("deployment_frequency", "lead_time", "change_failure_rate", "recovery_time")


def classificar_frequencia(releases_por_semana):
    """Maior é melhor."""
    if releases_por_semana is None:
        return None
    if releases_por_semana >= 7:
        return ELITE
    if releases_por_semana >= 1:
        return HIGH
    if releases_por_semana >= POR_SEMANA_MENSAL:
        return MEDIUM
    return LOW


def classificar_lead_time(horas):
    """Menor é melhor. Fronteiras fechadas à esquerda: 24 h exatas já é High."""
    if horas is None:
        return None
    if horas < HORAS_DIA:
        return ELITE
    if horas < HORAS_SEMANA:
        return HIGH
    if horas < HORAS_30_DIAS:
        return MEDIUM
    return LOW


def classificar_cfr(proporcao):
    """Menor é melhor. Cortes inclusivos: 15% exatos ainda é Elite."""
    if proporcao is None:
        return None
    if proporcao <= 0.15:
        return ELITE
    if proporcao <= 0.30:
        return HIGH
    if proporcao <= 0.45:
        return MEDIUM
    return LOW


def classificar_recuperacao(horas):
    """Menor é melhor. 1 h exata já é High; 1 semana exata já é Low."""
    if horas is None:
        return None
    if horas < 1:
        return ELITE
    if horas < HORAS_DIA:
        return HIGH
    if horas < HORAS_SEMANA:
        return MEDIUM
    return LOW


CLASSIFICADORES = {
    "deployment_frequency": classificar_frequencia,
    "lead_time": classificar_lead_time,
    "change_failure_rate": classificar_cfr,
    "recovery_time": classificar_recuperacao,
}


def classificar_metricas(valores):
    """{metrica: valor} -> {metrica: categoria}. Valor ausente vira None."""
    return {nome: CLASSIFICADORES[nome](valores.get(nome)) for nome in METRICAS}


def categoria_geral(categorias):
    """Categoria do repositório: mediana dos pontos das 4 métricas, para baixo.

    Enunciado: 4 pontos para Elite, 3 High, 2 Medium, 1 Low; a categoria geral
    é a mediana desses valores arredondada para baixo. Exemplo: (4, 3, 3, 1)
    tem mediana 3, logo High.

    Com número par de métricas a mediana cai entre dois valores, e é aí que o
    "para baixo" importa: (4, 4, 3, 3) tem mediana 3,5 e vira High, não Elite.

    Métricas sem valor (ex.: repositório sem nenhum episódio de falha, que não
    tem tempo de recuperação) são excluídas em vez de receberem nota arbitrária
    — uma nota inventada empurraria a mediana numa direção qualquer. Devolve
    None se nenhuma métrica pôde ser classificada.
    """
    pontos = sorted(PONTOS[c] for c in categorias.values() if c is not None)
    if not pontos:
        return None
    meio = len(pontos) // 2
    mediana = pontos[meio] if len(pontos) % 2 else (pontos[meio - 1] + pontos[meio]) / 2
    nota = math.floor(mediana)
    return {v: k for k, v in PONTOS.items()}[nota]


def classificar_repo(valores):
    """Classificação completa: por métrica e geral.

    `valores` usa as chaves de `METRICAS`. Retorna
    {"dora_<metrica>": categoria, ..., "dora_geral": categoria,
     "dora_metricas_validas": quantas entraram na mediana}.
    """
    categorias = classificar_metricas(valores)
    return {**{f"dora_{nome}": cat for nome, cat in categorias.items()},
            "dora_geral": categoria_geral(categorias),
            "dora_metricas_validas": sum(1 for c in categorias.values() if c is not None)}
