"""Simulação de poder para definir o nº de rodadas do Lighthouse (issue #104).

Mesma ideia do Lab04 (`lab04/simulacao`): repetir o experimento milhares de
vezes com a verdade conhecida e contar quantas vezes o teste rejeita H0.
Aqui a pergunta é: **quantas rodadas por tela e dispositivo precisamos para o
Wilcoxon pareado (H2: LCP celular > computador) ter poder ≥ 80%?**

Modelo (tudo em escala log, porque o LCP é positivo e assimétrico)
-----------------------------------------------------------------
Para cada tela `i` e rodada `j`, a diferença pareada celular − computador é

    d_ij = delta + u_i + e_ij,    u_i ~ N(0, sigma_tela²),  e_ij ~ N(0, 2·sigma_rodada²)

- `delta`: efeito verdadeiro (log da razão de medianas celular/computador).
- `u_i`: o efeito varia de uma tela para outra (a tela pesada sofre mais).
- `e_ij`: ruído de rodada. A diferença de duas medidas independentes tem
  variância 2·sigma_rodada².

Do piloto de 17/11 (`data/lighthouse/resultados.csv`) só dá para estimar
`delta` e `sigma_tela`: cada tela e dispositivo foi medido **uma vez**, então
a variância entre rodadas (`sigma_rodada`) **não é observável**. Por isso ela
entra como grade de sensibilidade, e não como um número único. A primeira
rodada da S02 deve repor o valor medido (ver `estimar_piloto`).

Dois testes são avaliados:

- `por_rodada`: Wilcoxon sobre as `k·r` diferenças (cada rodada de cada tela é
  um par). Tem poder, mas trata rodadas da mesma tela como independentes
  (pseudo-replicação) — ameaça de validade declarada na proposta.
- `por_tela`: Wilcoxon sobre as `k` medianas por tela. É o teste correto na
  unidade de análise, mas com `k` telas o menor p-valor unilateral possível
  é 1/2^k: com k = 3 é 0,125, então **nunca rejeita a 5% por mais rodadas que
  se faça**; com k = 5 é 0,031, e só rejeita se as 5 telas forem no mesmo
  sentido.

Uso:
    python -m analise.poder
"""
import argparse
import os
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

ALFA = 0.05
PODER_ALVO = 0.80
REPETICOES = 1_000
SEMENTE = 20261117
RODADAS = (1, 2, 3, 5, 8, 10, 15, 20)
MAX_RODADAS = 30

# Efeitos (log da razão celular/computador). 0,223 ≈ razão 1,25.
EFEITOS = {"1,25x": float(np.log(1.25)), "1,5x": float(np.log(1.5)),
           "2x": float(np.log(2.0)), "5,5x (piloto)": None}
SIGMAS_RODADA = (0.05, 0.10, 0.20, 0.30)
TELAS = (3, 5)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(RAIZ, "data", "lighthouse", "resultados.csv")
SAIDA = os.path.join(RAIZ, "data", "poder", "poder_rodadas.csv")


@dataclass(frozen=True)
class Piloto:
    delta: float          # média do log(celular/computador) entre as telas
    sigma_tela: float     # desvio entre telas desse log
    n_telas: int
    n_rodadas_min: int    # menor nº de rodadas por célula (1 → sigma_rodada indisponível)
    sigma_rodada: float   # desvio do log do LCP entre rodadas; nan se n_rodadas_min < 2


def estimar_piloto(caminho=ENTRADA):
    """Estima delta, sigma_tela e (se houver ≥ 2 rodadas) sigma_rodada."""
    df = pd.read_csv(caminho)
    df = df[df["lcp_ms"].notna() & (df["lcp_ms"] > 0)].copy()
    df["log_lcp"] = np.log(df["lcp_ms"])
    celulas = df.groupby(["pagina", "dispositivo"])["log_lcp"]
    medias = celulas.mean().unstack("dispositivo").dropna()
    dif = medias["mobile"] - medias["desktop"]
    contagem = celulas.size()
    if contagem.min() >= 2:
        sigma_rodada = float(np.sqrt(celulas.var(ddof=1).mean()))
    else:
        sigma_rodada = float("nan")
    return Piloto(delta=float(dif.mean()),
                  sigma_tela=float(dif.std(ddof=1)) if len(dif) > 1 else float("nan"),
                  n_telas=int(len(dif)), n_rodadas_min=int(contagem.min()),
                  sigma_rodada=sigma_rodada)


def _diferencas(rng, repeticoes, k, r, delta, sigma_tela, sigma_rodada):
    """Diferenças pareadas, formato (repeticoes, k, r)."""
    u = rng.normal(0.0, sigma_tela, size=(repeticoes, k, 1))
    e = rng.normal(0.0, np.sqrt(2) * sigma_rodada, size=(repeticoes, k, r))
    return delta + u + e


def _wilcoxon_unilateral(d):
    """p-valor do Wilcoxon de postos sinalizados (H1: mediana > 0), por linha.

    Linhas com todas as diferenças zero (impossível aqui, o ruído é contínuo)
    ficariam sem p-valor; o scipy devolve nan e contam como "não rejeitou".
    """
    return np.asarray(stats.wilcoxon(d, axis=1, alternative="greater",
                                     method="auto").pvalue, dtype=float)


def poder(rng, k, r, delta, sigma_tela, sigma_rodada, repeticoes=REPETICOES,
          alfa=ALFA):
    """Poder dos dois testes: `{"por_rodada": float, "por_tela": float}`."""
    if r < 1 or k < 2:
        raise ValueError("precisa de r >= 1 e k >= 2")
    d = _diferencas(rng, repeticoes, k, r, delta, sigma_tela, sigma_rodada)
    p_rodada = _wilcoxon_unilateral(d.reshape(repeticoes, k * r))
    p_tela = _wilcoxon_unilateral(np.median(d, axis=2))
    return {"por_rodada": float(np.mean(p_rodada < alfa)),
            "por_tela": float(np.mean(p_tela < alfa))}


def menor_p_possivel(k):
    """Menor p-valor unilateral do Wilcoxon com `k` pares sem empates: 1/2^k."""
    return 0.5 ** k


def rodadas_necessarias(rng, k, delta, sigma_tela, sigma_rodada,
                        alvo=PODER_ALVO, maximo=MAX_RODADAS,
                        repeticoes=REPETICOES):
    """Menor `r` com poder `por_rodada` ≥ alvo, ou None se passar de `maximo`."""
    for r in range(1, maximo + 1):
        if poder(rng, k, r, delta, sigma_tela, sigma_rodada,
                 repeticoes)["por_rodada"] >= alvo:
            return r
    return None


def tabela(piloto, repeticoes=REPETICOES, semente=SEMENTE):
    """Poder por (telas, efeito, sigma_rodada, rodadas), formato longo."""
    rng = np.random.default_rng(semente)
    sigma_tela = piloto.sigma_tela if np.isfinite(piloto.sigma_tela) else 0.1
    linhas = []
    for k in TELAS:
        for rotulo, delta in EFEITOS.items():
            delta = piloto.delta if delta is None else delta
            for sr in SIGMAS_RODADA:
                for r in RODADAS:
                    p = poder(rng, k, r, delta, sigma_tela, sr, repeticoes)
                    linhas.append({"telas": k, "efeito": rotulo,
                                   "delta_log": round(delta, 4),
                                   "sigma_rodada": sr, "rodadas": r,
                                   "poder_por_rodada": p["por_rodada"],
                                   "poder_por_tela": p["por_tela"]})
    return pd.DataFrame(linhas)


def minimo_de_rodadas(df, alvo=PODER_ALVO):
    """Menor nº de rodadas da grade com poder_por_rodada ≥ alvo, por cenário."""
    ok = df[df["poder_por_rodada"] >= alvo]
    achado = ok.groupby(["telas", "efeito", "sigma_rodada"])["rodadas"].min()
    cenarios = df.groupby(["telas", "efeito", "sigma_rodada"]).size().index
    return achado.reindex(cenarios).rename("rodadas_minimas")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="analise.poder",
                                 description="Poder para definir as rodadas (#104)")
    ap.add_argument("--repeticoes", type=int, default=REPETICOES)
    ap.add_argument("--saida", default=SAIDA)
    args = ap.parse_args(argv)

    piloto = estimar_piloto()
    print(f"Piloto: {piloto.n_telas} telas, delta = {piloto.delta:.3f} "
          f"(razão {np.exp(piloto.delta):.2f}x), sigma_tela = {piloto.sigma_tela:.3f}")
    if np.isnan(piloto.sigma_rodada):
        print("sigma_rodada: indisponível (1 rodada por célula); usando grade "
              f"{SIGMAS_RODADA}")
    for k in TELAS:
        print(f"k = {k} telas: menor p possível (unilateral) = "
              f"{menor_p_possivel(k):.4f} "
              f"-> teste por tela {'pode' if menor_p_possivel(k) < ALFA else 'NÃO pode'}"
              f" rejeitar a {ALFA:.0%}")

    df = tabela(piloto, repeticoes=args.repeticoes)
    os.makedirs(os.path.dirname(args.saida), exist_ok=True)
    df.to_csv(args.saida, index=False)

    print(f"\nRodadas mínimas (da grade {RODADAS}) para poder ≥ {PODER_ALVO:.0%}, "
          "teste por rodada:")
    m = minimo_de_rodadas(df).reset_index()
    pivo = m.pivot_table(index=["telas", "efeito"], columns="sigma_rodada",
                         values="rodadas_minimas", aggfunc="first")
    print(pivo.fillna(f">{RODADAS[-1]}").to_string())
    print(f"\nTabela completa em {os.path.relpath(args.saida, RAIZ)}")


if __name__ == "__main__":
    main()
