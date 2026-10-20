"""Avaliação da heurística de release corretiva contra o consenso (issue #67).

Compara cada variante de `metricas.corretiva.VARIANTES` com o rótulo
`corretiva` de consenso da amostra-ouro (saída de `validacao.concordancia`) e
calcula precisão, recall e F1, com "corretiva = sim" como classe positiva. A
meta do enunciado é F1 >= 0,70; abaixo disso a heurística é refinada, e cada
variante (inclusive as descartadas) fica registrada em `avaliacao_heuristica.csv`.

A evidência de cada release (tag, título e mensagens de commit) vem da própria
planilha de rotulagem, que é igual para os três avaliadores. A planilha mostra
no máximo 12 commits por release; no pipeline a heurística vê todos, então o
sinal `commits` pode diferir nas releases com muitos commits.

Rode só DEPOIS que os três avaliadores terminarem: o arquivo de itens mostra a
saída da heurística na amostra, e ver isso antes de rotular contamina o rótulo.

Uso:
    python -m validacao.avaliar_heuristica --config config.json
"""
import argparse
import glob
import json
import os

import pandas as pd

from metricas.corretiva import VARIANTES, sinais
from validacao.concordancia import SEM_CONSENSO

META_F1 = 0.70
SEPARADOR_COMMITS = " | "   # como `validacao.amostra` junta as mensagens


def metricas_binarias(esperado, previsto):
    """Matriz de confusão, precisão, recall e F1 (positivo = True).

    Divisão por zero vira None em vez de 0: "a variante nunca disse sim" é
    diferente de "disse sim e errou todas", e a tabela precisa mostrar isso.
    """
    pares = list(zip(esperado, previsto))
    vp = sum(e and p for e, p in pares)
    fp = sum(not e and p for e, p in pares)
    fn = sum(e and not p for e, p in pares)
    vn = sum(not e and not p for e, p in pares)
    precisao = vp / (vp + fp) if vp + fp else None
    recall = vp / (vp + fn) if vp + fn else None
    if precisao is None or recall is None:
        f1 = None
    elif precisao + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precisao * recall / (precisao + recall)
    return {"n": len(pares), "vp": vp, "fp": fp, "fn": fn, "vn": vn,
            "precisao": precisao, "recall": recall, "f1": f1}


def classificar(evidencia):
    """Acrescenta ao DataFrame de evidência uma coluna booleana por variante."""
    out = evidencia.copy()
    for i, row in out.iterrows():
        msgs = [m for m in str(row.get("commits") or "").split(SEPARADOR_COMMITS) if m]
        s = sinais(row["tag"], row.get("release_nome"), msgs)
        for nome, regra in VARIANTES.items():
            out.loc[i, nome] = bool(regra(s))
    return out


def avaliar(consenso, evidencia):
    """Resumo por variante e tabela por item. Itens `sem_consenso` ficam de fora."""
    base = consenso[consenso["corretiva"].isin(["sim", "nao"])][["full_name", "tag", "corretiva"]]
    itens = classificar(base.merge(evidencia, on=["full_name", "tag"], how="left"))
    esperado = (itens["corretiva"] == "sim").tolist()
    resumo = []
    for nome in VARIANTES:
        m = metricas_binarias(esperado, itens[nome].astype(bool).tolist())
        resumo.append({"variante": nome, **m,
                       "atinge_meta": m["f1"] is not None and m["f1"] >= META_F1})
    colunas = ["full_name", "tag", "corretiva", *VARIANTES]
    return pd.DataFrame(resumo), itens[colunas]


def executar(dir_val):
    caminho = os.path.join(dir_val, "consenso_corretiva.csv")
    if not os.path.isfile(caminho):
        raise SystemExit(f"{caminho} não existe: rode `python -m validacao.concordancia` "
                         "depois que os três avaliadores terminarem.")
    consenso = pd.read_csv(caminho, dtype=str).fillna("")
    planilhas = sorted(glob.glob(os.path.join(dir_val, "rotulos_releases_*.csv")))
    if not planilhas:
        raise SystemExit(f"Nenhuma planilha rotulos_releases_*.csv em {dir_val}.")
    evidencia = pd.read_csv(planilhas[0], dtype=str).fillna("")
    evidencia = evidencia[["full_name", "tag", "release_nome", "commits"]]

    resumo, itens = avaliar(consenso, evidencia)
    resumo.to_csv(os.path.join(dir_val, "avaliacao_heuristica.csv"), index=False)
    itens.to_csv(os.path.join(dir_val, "avaliacao_heuristica_itens.csv"), index=False)
    n_sem = int((consenso["corretiva"] == SEM_CONSENSO).sum())
    return resumo, n_sem


def main(argv=None):
    parser = argparse.ArgumentParser(prog="validacao.avaliar_heuristica", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        dir_val = os.path.join(json.load(f)["data_dir"], "validacao")

    resumo, n_sem = executar(dir_val)
    print(resumo.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    if n_sem:
        print(f"\n{n_sem} release(s) sem consenso ficaram de fora (resolver em reunião).")
    melhor = resumo.sort_values("f1", ascending=False, na_position="last").iloc[0]
    status = "atinge" if melhor["atinge_meta"] else "NÃO atinge"
    print(f"\nMelhor variante: {melhor['variante']} (F1 = {melhor['f1']}), "
          f"{status} a meta de {META_F1}.")


if __name__ == "__main__":
    main()
