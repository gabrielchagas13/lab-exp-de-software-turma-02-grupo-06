"""Concordância entre avaliadores e consolidação do consenso (issue #66).

Os três integrantes rotulam a mesma amostra-ouro de forma independente, sem ver
a saída da heurística nem os rótulos uns dos outros. Este módulo faz duas
coisas com esses rótulos:

1. **Mede a concordância** com o kappa de Fleiss, em cada dimensão rotulada.
2. **Consolida o consenso**, que vira a referência (*gold standard*) contra a
   qual a heurística de release corretiva é avaliada (precisão/recall/F1) e de
   onde sai o `tipo_projeto` usado como fator na RQ 06.

Por que kappa e não "% de vezes que concordamos": se 90% das releases não são
corretivas, três pessoas respondendo "não" no automático concordariam em ~90%
dos casos sem olhar nada. O kappa desconta essa concordância esperada por
acaso. Um kappa baixo não significa que os avaliadores foram desleixados —
significa que o próprio critério é ambíguo, e isso é um achado a discutir no
artigo (enunciado, seção 6).

Interpretação (Landis & Koch, 1977):
    < 0      pobre          0,41–0,60  moderada
    0–0,20   leve           0,61–0,80  substancial
    0,21–0,40 razoável      0,81–1,00  quase perfeita
"""
import os

import pandas as pd
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

SEM_CONSENSO = "sem_consenso"

# Dimensões rotuladas: (arquivo, chave que identifica o item, coluna do rótulo).
DIMENSOES = (
    ("repos", ["full_name"], "tipo_projeto"),
    ("repos", ["full_name"], "releases_sao_entregas"),
    ("releases", ["full_name", "tag"], "corretiva"),
)


def faixa_landis_koch(k):
    """Rótulo qualitativo do kappa, para a tabela do artigo."""
    if k < 0:
        return "pobre"
    for limite, nome in ((0.20, "leve"), (0.40, "razoável"), (0.60, "moderada"),
                         (0.80, "substancial")):
        if k <= limite:
            return nome
    return "quase perfeita"


def kappa_fleiss(rotulos_por_avaliador, chave, coluna):
    """Kappa de Fleiss de uma dimensão.

    `rotulos_por_avaliador` é {iniciais: DataFrame}. Os DataFrames são alinhados
    pela `chave` para garantir que a linha i seja o MESMO item para os três —
    sem isso o kappa compararia itens diferentes e o número sairia sem sentido.
    Itens que algum avaliador deixou em branco são descartados e contados em
    `itens_descartados`.
    """
    alinhado = None
    for inic, df in sorted(rotulos_por_avaliador.items()):
        col = df[chave + [coluna]].rename(columns={coluna: inic})
        alinhado = col if alinhado is None else alinhado.merge(col, on=chave, how="inner")

    avaliadores = sorted(rotulos_por_avaliador)
    total = len(alinhado)
    alinhado = alinhado.dropna(subset=avaliadores)
    alinhado = alinhado[~(alinhado[avaliadores] == "").any(axis=1)]

    if len(alinhado) == 0:
        return {"dimensao": coluna, "n_itens": 0, "kappa": None,
                "interpretacao": "sem itens rotulados", "itens_descartados": total}

    # aggregate_raters transforma (itens x avaliadores) em (itens x categorias),
    # que é o formato de contagem que o fleiss_kappa espera.
    tabela, _ = aggregate_raters(alinhado[avaliadores].to_numpy())
    k = float(fleiss_kappa(tabela))
    return {"dimensao": coluna, "n_itens": len(alinhado), "kappa": round(k, 4),
            "interpretacao": faixa_landis_koch(k),
            "itens_descartados": total - len(alinhado)}


def consenso(rotulos_por_avaliador, chave, coluna):
    """Rótulo de consenso por item, por maioria simples.

    Com 3 avaliadores e maioria simples: 3-0 e 2-1 resolvem sozinhos; o caso
    1-1-1 (os três discordam) não tem maioria e fica marcado como
    `sem_consenso`, para ser decidido em reunião — o protocolo de desempate
    precisa estar registrado no repositório (enunciado, seção 6.4).
    """
    alinhado = None
    for inic, df in sorted(rotulos_por_avaliador.items()):
        col = df[chave + [coluna]].rename(columns={coluna: inic})
        alinhado = col if alinhado is None else alinhado.merge(col, on=chave, how="inner")

    avaliadores = sorted(rotulos_por_avaliador)
    linhas = []
    for _, row in alinhado.iterrows():
        votos = [row[a] for a in avaliadores if pd.notna(row[a]) and row[a] != ""]
        contagem = pd.Series(votos).value_counts() if votos else pd.Series(dtype=int)
        if len(contagem) and contagem.iloc[0] * 2 > len(votos):
            vencedor, unanime = contagem.index[0], contagem.iloc[0] == len(votos)
        else:
            vencedor, unanime = SEM_CONSENSO, False
        linhas.append({**{c: row[c] for c in chave},
                       **{a: row[a] for a in avaliadores},
                       coluna: vencedor, "unanime": unanime})
    return pd.DataFrame(linhas)


def carregar_rotulos(dir_rotulos, nivel):
    """Lê `rotulos_<nivel>_<iniciais>.csv` de cada avaliador. {iniciais: DataFrame}."""
    out = {}
    prefixo = f"rotulos_{nivel}_"
    for nome in sorted(os.listdir(dir_rotulos)):
        if not (nome.startswith(prefixo) and nome.endswith(".csv")):
            continue
        inic = nome[len(prefixo):-4]
        out[inic] = pd.read_csv(os.path.join(dir_rotulos, nome), dtype=str).fillna("")
    return out


def executar(dir_rotulos, dir_saida):
    """Roda as três dimensões: grava concordância e consenso, devolve o resumo."""
    os.makedirs(dir_saida, exist_ok=True)
    cache, resumo = {}, []
    for nivel, chave, coluna in DIMENSOES:
        if nivel not in cache:
            cache[nivel] = carregar_rotulos(dir_rotulos, nivel)
        rot = cache[nivel]
        if len(rot) < 2:
            raise SystemExit(
                f"Encontrei {len(rot)} arquivo(s) de rótulos '{nivel}' em {dir_rotulos}. "
                f"O kappa de Fleiss compara avaliadores: são necessários os 3.")
        resumo.append({**kappa_fleiss(rot, chave, coluna), "n_avaliadores": len(rot)})
        consenso(rot, chave, coluna).to_csv(
            os.path.join(dir_saida, f"consenso_{coluna}.csv"), index=False)

    df = pd.DataFrame(resumo)
    df.to_csv(os.path.join(dir_saida, "concordancia.csv"), index=False)
    return df


def main(argv=None):
    import argparse
    import json

    parser = argparse.ArgumentParser(prog="validacao.concordancia", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]

    dir_val = os.path.join(data_dir, "validacao")
    df = executar(dir_val, dir_val)
    print("Kappa de Fleiss por dimensão:\n")
    print(df.to_string(index=False))

    sem = []
    for _, _, coluna in DIMENSOES:
        caminho = os.path.join(dir_val, f"consenso_{coluna}.csv")
        n = int((pd.read_csv(caminho)[coluna] == SEM_CONSENSO).sum())
        if n:
            sem.append(f"{coluna}: {n}")
    print("\nItens sem maioria (decidir em reunião): " + (", ".join(sem) if sem else "nenhum"))
    print(f"Saídas em {dir_val}/: concordancia.csv e consenso_*.csv")


if __name__ == "__main__":
    main()
