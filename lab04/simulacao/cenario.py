"""Cenário do experimento: pergunta, hipóteses e parâmetros da simulação (issue #77).

Os parâmetros **não são escritos à mão**: saem dos dados reais coletados na
issue #76 (`data/real.csv`), lidos em tempo de execução. Assim, se a coleta for
refeita, o cenário acompanha e não vira documentação desatualizada.

Escolha da distribuição
-----------------------
O tempo até o merge é fortemente assimétrico à direita nos dois grupos
(assimetria +2,7 e +2,2; média bem acima da mediana). Em escala logarítmica a
assimetria some (−0,07 e −0,14) e o Shapiro-Wilk não rejeita a normalidade
(p = 0,93 e p = 0,31). Isto é a definição de uma **lognormal**, então é ela que
gera os dados simulados.

A escolha não é cosmética: é exatamente o tipo de distribuição em que o t de
Welch (que compara médias) e o Mann-Whitney (que compara postos) podem
discordar, que é o objeto do laboratório.

Efeito
------
Numa lognormal, o efeito natural é **multiplicativo**: somar `delta` em escala
log multiplica a mediana por `exp(delta)`. Por isso o tamanho do efeito é
parametrizado em log, e não em horas — assim "efeito zero" é exatamente
H0 verdadeira, e os efeitos crescentes da Q2 (sprint 2) ficam numa escala
comparável.
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

GRUPO_CONTROLE = "sem_bot"
GRUPO_TRATAMENTO = "com_bot"
ALFA = 0.05

PERGUNTA = ("O tempo até o merge de um pull request difere entre PRs revisados "
            "pelo bot CodeRabbit e PRs sem revisão do bot?")

# As hipóteses são enunciadas por teste porque os dois NÃO testam a mesma coisa:
# o t de Welch compara médias; o Mann-Whitney compara a probabilidade de um valor
# de um grupo superar o do outro. Tratá-los como intercambiáveis é o erro que o
# laboratório pede para investigar.
HIPOTESES = {
    "welch": {
        "h0": "As médias do tempo até o merge são iguais nos dois grupos "
              "(mu_com_bot = mu_sem_bot).",
        "h1": "As médias diferem (mu_com_bot != mu_sem_bot).",
        "compara": "médias",
    },
    "mannwhitney": {
        "h0": "Um PR sorteado de um grupo tem a mesma chance de demorar mais que "
              "um PR do outro grupo (P(X > Y) = P(Y > X) = 0,5).",
        "h1": "Essa chance é diferente de 0,5; um grupo tende a demorar mais.",
        "compara": "postos (dominância estocástica)",
    },
}
BICAUDAL = ("Bicaudal. A pergunta é se o tempo *difere*, não se o bot acelera. "
            "Um review automático pode tanto adiantar o merge (ao achar problemas "
            "cedo) quanto atrasá-lo (ao gerar rodadas extras de correção), e o "
            "grupo não tem base para descartar uma das direções antes de olhar.")

# Previsão registrada ANTES de rodar as simulações da sprint 2. Fica aqui para
# que a comparação "esperado x obtido" na conclusão seja verificável.
PREVISAO = (
    "Esperamos que o **Mann-Whitney tenha mais poder** neste cenário. Com "
    "lognormal de sigma ~2,2 a média amostral é dominada por poucos valores "
    "extremos, o que infla o erro-padrão do t de Welch; o Mann-Whitney usa só a "
    "ordem e não sofre com isso. Esperamos também que o **erro tipo I do Welch "
    "fique longe de 5%** com n = 30: a assimetria é forte demais para o teorema "
    "central do limite resolver nesse tamanho de amostra. O Mann-Whitney não "
    "depende de normalidade, então deve ficar perto dos 5% nominais."
)


# A mesma previsão acima, quebrada em afirmações verificáveis uma a uma
# (issue #84). `PREVISAO` é o texto que vai na seção 1 do dashboard; esta lista
# é o que a conclusão confronta com os resultados, e cada item diz de qual
# experimento depende. Separar assim evita o truque de reler a previsão em prosa
# à luz do resultado e declarar que "era isso mesmo que a gente queria dizer".
PREVISOES = [
    {
        "id": "poder",
        "previsto": "O Mann-Whitney terá mais poder que o t de Welch: com sigma "
                    "(log) de ~2,2 a média amostral é dominada por poucos valores "
                    "extremos, o que infla o erro-padrão do t, enquanto o "
                    "Mann-Whitney usa só a ordem.",
        "decide": "Q2 (curvas de poder)",
        "issue": 80,
    },
    {
        "id": "erro_welch",
        "previsto": "O erro tipo I do t de Welch ficará longe dos 5% nominais com "
                    "n = 30: a assimetria é forte demais para o teorema central do "
                    "limite resolver nesse tamanho de amostra.",
        "decide": "Q1 (erro tipo I)",
        "issue": 79,
    },
    {
        "id": "erro_mannwhitney",
        "previsto": "O erro tipo I do Mann-Whitney ficará perto dos 5% nominais, "
                    "porque ele não depende de normalidade.",
        "decide": "Q1 (erro tipo I)",
        "issue": 79,
    },
]

# Recomendação prática, escrita depois dos resultados: é a resposta que o grupo
# daria a quem fosse rodar esta análise de novo. Fica aqui junto do cenário para
# que a conclusão do dashboard e o roteiro da apresentação digam a mesma coisa.
RECOMENDACAO = (
    "Para comparar tempo até o merge — ou qualquer medida de duração em "
    "engenharia de software, que é quase sempre assimétrica à direita — use o "
    "**Mann-Whitney** como teste principal, e relate o **delta de Cliff** junto "
    "com o p-valor. O t de Welch não é "
    "*errado*, mas neste cenário ele é conservador a ponto de não conseguir "
    "produzir p-valores pequenos, o que faz um efeito real passar despercebido. "
    "Se a média for mesmo a quantidade de interesse, o caminho é **transformar "
    "em log antes** (em escala log os dados são aproximadamente normais, e aí o "
    "t volta a ser adequado) e lembrar que o resultado passa a ser sobre a "
    "mediana, não sobre a média em horas."
)


def _parametros_log(amostra):
    """Média e desvio em escala log: são os parâmetros mu e sigma da lognormal."""
    log = np.log(amostra)
    return float(log.mean()), float(log.std(ddof=1))


def carregar_reais(caminho):
    """Lê o CSV da coleta (#76) e devolve {grupo: array de horas}."""
    if not os.path.isfile(caminho):
        raise SystemExit(f"{caminho} não encontrado — rode `python -m coleta` antes.")
    df = pd.read_csv(caminho)
    dados = {g: sub["horas_ate_merge"].to_numpy(dtype=float)
             for g, sub in df.groupby("grupo")}
    faltando = {GRUPO_CONTROLE, GRUPO_TRATAMENTO} - set(dados)
    if faltando:
        raise SystemExit(f"Grupos ausentes em {caminho}: {', '.join(sorted(faltando))}")
    if any((v <= 0).any() for v in dados.values()):
        raise SystemExit("Há tempos <= 0; a lognormal exige valores estritamente positivos.")
    return dados


def descrever(amostra):
    """Resumo de um grupo, com as estatísticas que justificam a lognormal."""
    log = np.log(amostra)
    return {
        "n": int(amostra.size),
        "mediana": float(np.median(amostra)),
        "media": float(amostra.mean()),
        "dp": float(amostra.std(ddof=1)),
        "min": float(amostra.min()),
        "max": float(amostra.max()),
        "assimetria": float(stats.skew(amostra)),
        "assimetria_log": float(stats.skew(log)),
        "shapiro_p": float(stats.shapiro(amostra).pvalue),
        "shapiro_log_p": float(stats.shapiro(log).pvalue),
        "mu_log": float(log.mean()),
        "sigma_log": float(log.std(ddof=1)),
    }


def montar(caminho_real):
    """Monta o cenário a partir dos dados reais.

    `sigma` é comum aos dois grupos no cenário-base: o teste de Levene sobre os
    logs não rejeita a igualdade de variâncias (p = 0,12), e manter um sigma só
    deixa "efeito zero" significando exatamente H0 verdadeira, sem que uma
    diferença de dispersão entre os grupos entre por acaso. A variância
    desigual observada fica reservada para a violação de pressuposto da Q3.
    """
    reais = carregar_reais(caminho_real)
    controle, tratamento = reais[GRUPO_CONTROLE], reais[GRUPO_TRATAMENTO]
    mu_c, sigma_c = _parametros_log(controle)
    mu_t, sigma_t = _parametros_log(tratamento)

    # Desvio combinado (pooled) dos dois grupos em escala log.
    n_c, n_t = controle.size, tratamento.size
    sigma_comum = float(np.sqrt(((n_c - 1) * sigma_c ** 2 + (n_t - 1) * sigma_t ** 2)
                                / (n_c + n_t - 2)))
    levene_p = float(stats.levene(np.log(controle), np.log(tratamento),
                                  center="median").pvalue)

    return {
        "pergunta": PERGUNTA,
        "hipoteses": HIPOTESES,
        "bicaudal": BICAUDAL,
        "previsao": PREVISAO,
        "previsoes": PREVISOES,
        "recomendacao": RECOMENDACAO,
        "alfa": ALFA,
        "n_por_grupo": int(min(n_c, n_t)),
        "mu_controle": mu_c,
        "sigma_controle": sigma_c,
        "mu_tratamento": mu_t,
        "sigma_tratamento": sigma_t,
        "sigma_comum": sigma_comum,
        "levene_log_p": levene_p,
        # Efeito observado nos dados reais, em log: é a referência de "efeito
        # realista" para as curvas de poder da Q2.
        "efeito_observado_log": mu_t - mu_c,
        "razao_medianas_observada": float(np.median(tratamento) / np.median(controle)),
        "descritivas": {GRUPO_CONTROLE: descrever(controle),
                        GRUPO_TRATAMENTO: descrever(tratamento)},
    }
