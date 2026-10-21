"""RQ 08 (bônus): rework rate (issue #74).

Rework rate = proporção de releases **corretivas** sobre o total de releases do
repositório (DORA, 2024: deploys não planejados, feitos para corrigir problemas).
Usa a mesma heurística corretiva do CFR (b) (RQ 03), uma coluna por versão
(`cfr_release_<versão>` em `metricas.json`).

**Em que difere do CFR (b).** As duas partem do mesmo rótulo "release corretiva", mas
contam coisas diferentes:

- CFR (b) = releases **seguidas**, em até 7 dias, por uma corretiva ÷ releases avaliadas.
  O sujeito é a release que *falhou*; só conta se a correção veio rápido; as releases dos
  últimos 7 dias da janela saem do denominador (censura).
- Rework = releases que **são** corretivas ÷ todas as releases. O sujeito é a release
  *de correção*, venha ela quando vier, e nenhuma release é censurada.

Logo, o rework não depende do intervalo entre releases e o CFR (b) depende: um projeto que
publica uma release por mês tem correções que nunca caem na janela de 7 dias, e seu
CFR (b) tende a zero mesmo que metade das releases sejam correções.

Saídas em `data/analise/`:
  rq08_versoes.csv   por versão da heurística: mediana/IQR do rework, do CFR (b) e comparação
  rq08_por_repo.csv  rework e CFR (b) de cada repositório (versão padrão), para os gráficos

Uso:
    python -m analise.rq08 --config config.json
"""
import argparse
import json
import os
import sys

import pandas as pd
from scipy.stats import spearmanr

VERSOES = ("v1_semver", "v2_semver_ou_nome", "v3_commits", "v4_combinada")
PADRAO = "v2_semver_ou_nome"      # a que o pipeline usa por padrão (README)


def _spearman(x, y):
    ok = x.notna() & y.notna()
    if ok.sum() < 3 or x[ok].nunique() < 2 or y[ok].nunique() < 2:
        return None, None
    r = spearmanr(x[ok], y[ok])
    return round(float(r.statistic), 3), float(r.pvalue)


def comparar_versao(df, versao):
    """Rework × CFR (b) de uma versão da heurística, uma linha de resumo."""
    rework = pd.to_numeric(df[f"cfr_release_{versao}"], errors="coerce")
    cfr_b = pd.to_numeric(df[f"cfr_entrega_{versao}"], errors="coerce")
    freq = pd.to_numeric(df["releases_por_semana"], errors="coerce")
    ok = rework.notna() & cfr_b.notna()
    rho, p = _spearman(rework, cfr_b)
    rho_f_rw, _ = _spearman(freq, rework)
    rho_f_cfr, _ = _spearman(freq, cfr_b)
    q = lambda s, k: round(float(s.quantile(k)), 4)
    return {
        "versao": versao, "n": int(ok.sum()),
        "rework_mediana": q(rework, .5), "rework_q1": q(rework, .25), "rework_q3": q(rework, .75),
        "cfr_b_mediana": q(cfr_b, .5), "cfr_b_q1": q(cfr_b, .25), "cfr_b_q3": q(cfr_b, .75),
        "mediana_da_diferenca": round(float((rework[ok] - cfr_b[ok]).median()), 4),
        "pct_rework_maior": round(100 * float((rework[ok] > cfr_b[ok]).mean()), 1),
        "pct_rework_menor": round(100 * float((rework[ok] < cfr_b[ok]).mean()), 1),
        "spearman_rework_cfr_b": rho, "p_valor": p,
        "spearman_freq_rework": rho_f_rw, "spearman_freq_cfr_b": rho_f_cfr,
    }


def tabela_versoes(df, versoes=VERSOES):
    return pd.DataFrame([comparar_versao(df, v) for v in versoes])


def por_repo(df, versao=PADRAO):
    return pd.DataFrame({
        "repo": df["repo"], "releases": df["releases"],
        "releases_por_semana": df["releases_por_semana"],
        "rework": df[f"cfr_release_{versao}"], "cfr_b": df[f"cfr_entrega_{versao}"]})


def executar(data_dir):
    with open(os.path.join(data_dir, "metricas.json"), encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f))
    saida = os.path.join(data_dir, "analise")
    os.makedirs(saida, exist_ok=True)
    versoes, repos = tabela_versoes(df), por_repo(df)
    versoes.to_csv(os.path.join(saida, "rq08_versoes.csv"), index=False)
    repos.to_csv(os.path.join(saida, "rq08_por_repo.csv"), index=False)
    return df, versoes, repos


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="analise.rq08", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]
    df, versoes, _ = executar(data_dir)
    print(f"RQ 08: rework rate × CFR (b) — {len(df)} repositórios\n")
    print(versoes.to_string(index=False))
    print(f"\nSaídas em {os.path.join(data_dir, 'analise')}/rq08_*.csv")


if __name__ == "__main__":
    main()
