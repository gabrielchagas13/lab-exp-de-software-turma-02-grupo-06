"""RQ 01 a RQ 04 e classificação DORA de referência C1 (issue #71).

Lê `data/metricas.json` (uma linha por repositório, produzida pelo pipeline) e
produz a estatística descritiva das quatro métricas DORA e a classificação C1
de cada repositório.

**Mediana e IQR, não média e desvio-padrão.** Métricas de repositórios têm
distribuição muito assimétrica — alguns projetos publicam dezenas de releases
por semana enquanto a maioria publica uma por mês — e a média é dominada por
esses extremos. O enunciado exige mediana e IQR em todas as RQs.

**Combinação C1** (referência da RQ 07): unidade de deploy = release publicada,
lead time = variante (a) por release, CFR = variante (a) proxy de CI.

Saídas em `data/analise/`:
  rq01_rq04_descritivas.csv   mediana, IQR, min e max por métrica
  dora_c1.csv                 classificação de cada repositório
  dora_c1_distribuicao.csv    quantos repositórios em cada categoria

Uso:
    python -m analise.rq01_rq04 --config config.json
"""
import argparse
import json
import os
import sys

import pandas as pd

from metricas.dora import CATEGORIAS, classificar_repo

# Métrica -> (coluna em metricas.json, unidade, RQ que ela responde).
# A ordem é a das RQs, que é como as tabelas aparecem no artigo.
METRICAS_C1 = {
    "deployment_frequency": ("releases_por_semana", "releases/semana", "RQ 01"),
    "lead_time": ("lead_time_release_h", "horas", "RQ 02 (a)"),
    "change_failure_rate": ("cfr_ci", "proporção", "RQ 03 (a)"),
    "recovery_time": ("recovery_median_h", "horas", "RQ 04"),
}

# Métricas descritas além das quatro do C1, para a seção de resultados.
# CFR (b) de referência do grupo: v5 (patch semver E release notes citando
# fix/bugfix/hotfix/revert). É a única variante com F1 >= 0,70 contra o consenso
# da amostra-ouro; as outras ficam como sensibilidade na RQ 07 e na RQ 08.
CFR_B_REFERENCIA = "cfr_entrega_v5_patch_e_notas"

EXTRAS = {
    "lead_time_commit_h": ("horas", "RQ 02 (b) — lead time por commit"),
    CFR_B_REFERENCIA: ("proporção", "RQ 03 (b) — CFR proxy de entrega, variante v5"),
    "recovery_censored_ratio": ("proporção", "RQ 04 — episódios censurados"),
}


def carregar(data_dir):
    caminho = os.path.join(data_dir, "metricas.json")
    with open(caminho, encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f))
    if df.empty:
        raise SystemExit(f"{caminho} está vazio — rode o pipeline primeiro.")
    return df


def descritivas(df, colunas):
    """Mediana, IQR, min e max de cada coluna, ignorando valores ausentes.

    `n` é quantos repositórios têm a métrica; `ausentes` é o complemento — um
    repositório sem nenhum episódio de falha não tem tempo de recuperação, e
    tratá-lo como zero faria o repositório parecer perfeito em vez de não
    medido."""
    linhas = []
    for coluna, (unidade, descricao) in colunas.items():
        valores = pd.to_numeric(df[coluna], errors="coerce").dropna()
        q1, q3 = valores.quantile(0.25), valores.quantile(0.75)
        linhas.append({
            "metrica": coluna, "descricao": descricao, "unidade": unidade,
            "n": len(valores), "ausentes": len(df) - len(valores),
            "mediana": round(valores.median(), 4) if len(valores) else None,
            "q1": round(q1, 4) if len(valores) else None,
            "q3": round(q3, 4) if len(valores) else None,
            "iqr": round(q3 - q1, 4) if len(valores) else None,
            "min": round(valores.min(), 4) if len(valores) else None,
            "max": round(valores.max(), 4) if len(valores) else None,
        })
    return pd.DataFrame(linhas)


def classificar_c1(df):
    """Classificação DORA C1 de cada repositório, uma linha por repositório."""
    linhas = []
    for _, row in df.iterrows():
        valores = {nome: _numero(row.get(coluna))
                   for nome, (coluna, _, _) in METRICAS_C1.items()}
        linhas.append({"repo": row["repo"],
                       **{f"valor_{n}": v for n, v in valores.items()},
                       **classificar_repo(valores)})
    return pd.DataFrame(linhas)


def _numero(valor):
    """Converte para float, devolvendo None para ausente/não numérico."""
    if valor is None:
        return None
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(n) else n


def distribuicao(c1):
    """Quantos repositórios caem em cada categoria, por métrica e no geral."""
    colunas = [f"dora_{nome}" for nome in METRICAS_C1] + ["dora_geral"]
    linhas = []
    for coluna in colunas:
        contagem = c1[coluna].value_counts()
        total = int(contagem.sum())
        linhas.append({
            "dimensao": coluna.replace("dora_", ""),
            **{cat: int(contagem.get(cat, 0)) for cat in CATEGORIAS},
            "sem_classificacao": len(c1) - total,
            "pct_elite_ou_high": (round(100 * (contagem.get("Elite", 0)
                                               + contagem.get("High", 0)) / total, 1)
                                  if total else None),
        })
    return pd.DataFrame(linhas)


def executar(data_dir):
    df = carregar(data_dir)
    saida = os.path.join(data_dir, "analise")
    os.makedirs(saida, exist_ok=True)

    colunas = {coluna: (unidade, f"{rq} — {coluna}")
               for (coluna, unidade, rq) in METRICAS_C1.values()}
    colunas.update(EXTRAS)

    desc = descritivas(df, colunas)
    c1 = classificar_c1(df)
    dist = distribuicao(c1)

    desc.to_csv(os.path.join(saida, "rq01_rq04_descritivas.csv"), index=False)
    c1.to_csv(os.path.join(saida, "dora_c1.csv"), index=False)
    dist.to_csv(os.path.join(saida, "dora_c1_distribuicao.csv"), index=False)
    return df, desc, c1, dist


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="analise.rq01_rq04", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]

    df, desc, c1, dist = executar(data_dir)

    print("=" * 78)
    print(f"RQ 01 a RQ 04 e classificação DORA C1 — {len(df)} repositórios")
    print("=" * 78)
    print("\nDescritivas (mediana e IQR; média seria dominada pelos extremos):\n")
    print(desc.to_string(index=False))

    print("\n" + "-" * 78)
    print("Classificação DORA C1 (release | lead time (a) | CFR (a))")
    print("-" * 78 + "\n")
    print(dist.to_string(index=False))

    geral = c1["dora_geral"].value_counts()
    print("\nCategoria geral do repositório (mediana das 4 notas, para baixo):")
    for cat in CATEGORIAS:
        n = int(geral.get(cat, 0))
        print(f"  {cat:<7} {n:>4}  {'#' * round(60 * n / max(len(c1), 1))}")

    incompletos = int((c1["dora_metricas_validas"] < 4).sum())
    if incompletos:
        print(f"\n{incompletos} repositórios foram classificados com menos de 4 métricas "
              f"(métrica ausente é excluída da mediana, não zerada).")

    print(f"\nSaídas em {os.path.join(data_dir, 'analise')}/")
    print("=" * 78)


if __name__ == "__main__":
    main()
