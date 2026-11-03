"""Aplica os dois testes a um conjunto de dados simulado (issue #77).

Monta o cenário a partir dos dados reais, gera **um** conjunto simulado com o
efeito observado na coleta e roda o t de Welch e o Mann-Whitney sobre ele,
imprimindo a interpretação. É a entrega da sprint 1; as 10.000 repetições de
erro tipo I e poder são a sprint 2.

Uso:
    python -m simulacao --config config.json
    python -m simulacao --config config.json --efeito 0      # H0 verdadeira
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

from simulacao import cenario as cen
from simulacao.gerador import como_dataframe, gerar_par
from simulacao.testes import aplicar_ambos


def _cabecalho(titulo):
    print("\n" + "=" * 76)
    print(titulo)
    print("=" * 76)


def imprimir_cenario(c):
    _cabecalho("CENÁRIO")
    print(f"\nPergunta: {c['pergunta']}\n")
    for chave, h in c["hipoteses"].items():
        print(f"  [{chave}] compara {h['compara']}")
        print(f"      H0: {h['h0']}")
        print(f"      H1: {h['h1']}")
    print(f"\n  Direção: {c['bicaudal']}")

    _cabecalho("DADOS REAIS (base dos parâmetros)")
    linhas = []
    for grupo, d in c["descritivas"].items():
        linhas.append({
            "grupo": grupo, "n": d["n"],
            "mediana_h": round(d["mediana"], 2), "media_h": round(d["media"], 2),
            "max_h": round(d["max"], 1),
            "assim.": round(d["assimetria"], 2),
            "assim.log": round(d["assimetria_log"], 2),
            "shapiro_p": f"{d['shapiro_p']:.1e}",
            "shapiro_log_p": round(d["shapiro_log_p"], 3),
        })
    print("\n" + pd.DataFrame(linhas).to_string(index=False))
    print("\n  No bruto os dois grupos são muito assimétricos e o Shapiro-Wilk rejeita")
    print("  a normalidade; em log a assimetria some e o Shapiro não rejeita.")
    print("  Por isso a simulação usa uma LOGNORMAL.")

    _cabecalho("PARÂMETROS DA SIMULAÇÃO")
    print(f"\n  mu (log) do controle     : {c['mu_controle']:.3f}")
    print(f"  sigma (log) comum        : {c['sigma_comum']:.3f}"
          f"   [controle {c['sigma_controle']:.3f} | tratamento {c['sigma_tratamento']:.3f}]")
    print(f"  Levene sobre os logs     : p = {c['levene_log_p']:.3f}"
          f" -> {'não rejeita' if c['levene_log_p'] >= .05 else 'rejeita'} variâncias iguais")
    print(f"  efeito observado (log)   : {c['efeito_observado_log']:.3f}"
          f"   (razão de medianas = {c['razao_medianas_observada']:.2f}x)")
    print(f"  n por grupo              : {c['n_por_grupo']}")
    print(f"  alfa                     : {c['alfa']}")

    _cabecalho("PREVISÃO, ANTES DE SIMULAR")
    print("\n  " + c["previsao"].replace("**", ""))


def imprimir_resultados(resultados, alfa, efeito_log, controle, tratamento):
    _cabecalho("OS DOIS TESTES NO CONJUNTO SIMULADO")
    print(f"\n  Gerado com efeito_log = {efeito_log:.3f} "
          f"(mediana do tratamento x{np.exp(efeito_log):.2f})")
    print(f"  Controle  : n={controle.size}  mediana={np.median(controle):8.2f} h  "
          f"média={controle.mean():8.2f} h")
    print(f"  Tratamento: n={tratamento.size}  mediana={np.median(tratamento):8.2f} h  "
          f"média={tratamento.mean():8.2f} h\n")

    # Uma coluna só para o efeito, com o nome ao lado: os dois testes usam
    # medidas diferentes (d de Cohen e delta de Cliff) e colunas separadas
    # deixariam metade da tabela vazia.
    tabela = pd.DataFrame([{
        "teste": r.teste, "estatística": round(r.estatistica, 4),
        "p-valor": f"{r.p_valor:.5f}",
        "tamanho de efeito": f"{r.efeito:+.3f} ({r.efeito_nome})",
        "magnitude": r.efeito_interpretacao,
        f"rejeita H0 (a={alfa})": "sim" if r.rejeita_h0 else "não",
    } for r in resultados.values()])
    print(tabela.to_string(index=False))

    _cabecalho("INTERPRETAÇÃO")
    w, mw = resultados["welch"], resultados["mannwhitney"]
    concordam = w.rejeita_h0 == mw.rejeita_h0
    print()
    for r in (w, mw):
        veredito = ("rejeita H0" if r.rejeita_h0 else "não rejeita H0")
        print(f"  {r.teste}: p = {r.p_valor:.5f} -> {veredito} a {alfa:.0%}.")
        print(f"      {r.efeito_nome} = {r.efeito:+.3f} ({r.efeito_interpretacao}).")
    print()
    if concordam and w.rejeita_h0:
        print("  Os dois concordam em rejeitar: há evidência de diferença no tempo até")
        print("  o merge. Note que eles rejeitam por motivos diferentes — Welch porque")
        print("  as médias diferem, Mann-Whitney porque um grupo tende a ficar à frente")
        print("  do outro na ordenação.")
    elif concordam:
        print("  Nenhum dos dois rejeita. Com n = 30 e dados desta assimetria, isso não")
        print("  prova ausência de efeito: pode ser falta de poder, que é exatamente o")
        print("  que as curvas da sprint 2 vão medir.")
    else:
        mais_sensivel = w if w.rejeita_h0 else mw
        outro = mw if w.rejeita_h0 else w
        print(f"  Os testes DISCORDAM: o {mais_sensivel.teste} rejeita e o {outro.teste}")
        print("  não. É o caso mais informativo do laboratório: numa única amostra não")
        print("  dá para saber qual acertou, porque não se conhece a verdade. Só a")
        print("  simulação com efeito conhecido (sprint 2) resolve isso.")
    print("\n  Em qualquer caso, um p-valor isolado não diz se a diferença tem")
    print("  importância prática — por isso o tamanho de efeito vai ao lado.")


def executar(config_path, efeito=None, semente=None):
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    raiz = os.path.dirname(os.path.abspath(config_path))
    caminho_real = os.path.join(raiz, cfg["coleta"]["saida"])

    c = cen.montar(caminho_real)
    efeito_log = c["efeito_observado_log"] if efeito is None else efeito
    rng = np.random.default_rng(cfg["seed"] if semente is None else semente)

    controle, tratamento = gerar_par(
        rng, n=c["n_por_grupo"], mu_controle=c["mu_controle"],
        sigma_log=c["sigma_comum"], efeito_log=efeito_log)
    resultados = aplicar_ambos(tratamento, controle, c["alfa"])
    return c, controle, tratamento, resultados, efeito_log, raiz


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="simulacao", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--efeito", type=float, default=None,
                        help="efeito em escala log (padrão: o observado nos dados reais; "
                             "use 0 para gerar sob H0 verdadeira)")
    parser.add_argument("--semente", type=int, default=None)
    args = parser.parse_args(argv)

    c, controle, tratamento, resultados, efeito_log, raiz = executar(
        args.config, args.efeito, args.semente)

    imprimir_cenario(c)
    imprimir_resultados(resultados, c["alfa"], efeito_log, controle, tratamento)

    saida = os.path.join(raiz, "data")
    os.makedirs(saida, exist_ok=True)
    como_dataframe(controle, tratamento).to_csv(
        os.path.join(saida, "simulado_exemplo.csv"), index=False)
    pd.DataFrame([r.como_dict() for r in resultados.values()]).to_csv(
        os.path.join(saida, "testes_exemplo.csv"), index=False)
    print(f"\n  Saídas: {os.path.join('data', 'simulado_exemplo.csv')} e "
          f"{os.path.join('data', 'testes_exemplo.csv')}\n")


if __name__ == "__main__":
    main()
