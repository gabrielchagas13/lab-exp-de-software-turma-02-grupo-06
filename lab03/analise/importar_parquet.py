"""Reconstrói os JSON da coleta a partir de `data/parquet/` (caminho inverso da exportação).

Os JSON em `data/{runs,releases,commits}` não são versionados (1,45 GB), mas são
o que o pipeline lê para **retomar a coleta** (`pipeline.store.load_or_build`).
Quem clona o repositório recebe só os Parquet, e rodar `python -m pipeline`
recoletaria tudo da API — horas.

Este módulo regrava os JSON a partir dos Parquet, e aí a retomada volta a
funcionar sem nenhuma chamada de rede. Serve para:

- um integrante que clonou e quer rodar o pipeline (ex.: aumentar a amostra);
- o grupo replicador, que pode rodar o pipeline sobre os dados originais em vez
  de recoletar e comparar maçãs com laranjas.

A ida e volta é verificada em `tests/test_importar_parquet.py`: exporta,
reimporta e compara com o JSON original campo a campo.

Uso:
    python -m analise.importar_parquet --config config.json
    python -m analise.importar_parquet --config config.json --force   # sobrescreve
"""
import argparse
import json
import os
import sys

import pandas as pd

CAMPOS_RUN = ["id", "workflow_id", "name", "conclusion",
              "created_at", "run_started_at", "updated_at"]
CAMPOS_RELEASE = ["id", "tag_name", "name", "body", "draft", "prerelease",
                  "target_commitish", "created_at", "published_at", "in_window"]
CAMPOS_COMMIT = ["sha", "author_date", "committer_date", "message"]


def _limpar(valor):
    """NaN do pandas vira None, que é o `null` do JSON original."""
    if valor is None:
        return None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    if hasattr(valor, "item"):          # numpy int64/bool_ -> tipo nativo
        return valor.item()
    return valor


def _registros(df, campos):
    """Lista de dicts só com `campos`, na ordem deles e sem NaN."""
    return [{c: _limpar(linha[c]) for c in campos}
            for linha in df[campos].to_dict("records")]


def _ler(parquet_dir, nome):
    caminho = os.path.join(parquet_dir, f"{nome}.parquet")
    if not os.path.isfile(caminho):
        raise SystemExit(f"{caminho} não encontrado — rode `python -m analise.exportar_parquet`.")
    return pd.read_parquet(caminho)


def _gravar(saida, repo, conteudo, force):
    """Grava `<saida>/<owner>__<repo>.json`. Retorna True se escreveu."""
    os.makedirs(saida, exist_ok=True)
    caminho = os.path.join(saida, repo.replace("/", "__") + ".json")
    if os.path.exists(caminho) and not force:
        return False
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(conteudo, f)
    os.replace(tmp, caminho)
    return True


def reconstruir_runs(parquet_dir, saida, force=False):
    runs = _ler(parquet_dir, "runs")
    coleta = _ler(parquet_dir, "runs_coleta").set_index("repo")
    escritos = 0
    for repo, grupo in runs.groupby("repo", sort=False):
        meta = coleta.loc[repo]
        escritos += _gravar(saida, repo, {
            "repo": repo,
            "branch": _limpar(meta["branch"]),
            "runs": _registros(grupo, CAMPOS_RUN),
            "splits": _limpar(meta["splits"]),
            "capped_days": list(meta["capped_days"]),
        }, force)
    # Repositórios sem nenhuma run válida não aparecem em runs.parquet.
    for repo, meta in coleta.iterrows():
        if repo in set(runs["repo"]):
            continue
        escritos += _gravar(saida, repo, {
            "repo": repo, "branch": _limpar(meta["branch"]), "runs": [],
            "splits": _limpar(meta["splits"]), "capped_days": list(meta["capped_days"]),
        }, force)
    return escritos


def reconstruir_releases(parquet_dir, saida, force=False):
    releases = _ler(parquet_dir, "releases")
    tags = _ler(parquet_dir, "tags")
    coleta = _ler(parquet_dir, "releases_coleta")
    por_repo = {r: g for r, g in releases.groupby("repo", sort=False)}
    por_repo_tags = {r: g for r, g in tags.groupby("repo", sort=False)}
    escritos = 0
    # Itera pela tabela de controle, nao pelas releases: repositorio sem
    # nenhuma release tambem precisa do JSON, senao o pipeline recoleta.
    for repo in coleta["repo"]:
        grupo, g_tags = por_repo.get(repo), por_repo_tags.get(repo)
        escritos += _gravar(saida, repo, {
            "repo": repo,
            "releases": _registros(grupo, CAMPOS_RELEASE) if grupo is not None else [],
            "tags": _registros(g_tags, ["name", "sha"]) if g_tags is not None else [],
        }, force)
    return escritos


def reconstruir_commits(parquet_dir, saida, force=False):
    vinculo = _ler(parquet_dir, "release_commits")
    conteudo = _ler(parquet_dir, "commits")
    comparacoes = _ler(parquet_dir, "comparacoes")
    coleta = _ler(parquet_dir, "commits_coleta").set_index("repo")
    puladas = _ler(parquet_dir, "releases_puladas")

    junto = vinculo.merge(conteudo, on=["repo", "sha"], how="left", sort=False)
    # Indexa os commits por (repo, tag, base_tag) para montar cada comparação.
    por_comparacao = {chave: g for chave, g in
                      junto.groupby(["repo", "tag", "base_tag"], sort=False)}
    por_repo_puladas = ({r: g for r, g in puladas.groupby("repo", sort=False)}
                        if len(puladas) else {})

    escritos = 0
    # Itera pelas COMPARAÇÕES, não pelos commits: uma release sem nenhum commit
    # novo não aparece em release_commits e sumiria da reconstrução.
    for repo, grupo in comparacoes.groupby("repo", sort=False):
        itens = []
        for linha in grupo.itertuples():
            g = por_comparacao.get((repo, linha.tag, linha.base_tag))
            itens.append({"tag": linha.tag,
                          "published_at": _limpar(linha.published_at),
                          "base_tag": linha.base_tag,
                          "commits": _registros(g, CAMPOS_COMMIT) if g is not None else []})
        g_pul = por_repo_puladas.get(repo)
        escritos += _gravar(saida, repo, {
            "repo": repo,
            "fonte": _limpar(coleta.loc[repo, "fonte"]) if repo in coleta.index else None,
            "releases": itens,
            "skipped": _registros(g_pul, ["tag", "reason"]) if g_pul is not None else [],
        }, force)

    # Repositório sem nenhuma comparação (todas as releases puladas) ainda
    # precisa do JSON, senão o pipeline recoleta.
    vistos = set(comparacoes["repo"])
    for repo, meta in coleta.iterrows():
        if repo in vistos:
            continue
        g_pul = por_repo_puladas.get(repo)
        escritos += _gravar(saida, repo, {
            "repo": repo, "fonte": _limpar(meta["fonte"]), "releases": [],
            "skipped": _registros(g_pul, ["tag", "reason"]) if g_pul is not None else [],
        }, force)
    return escritos


def importar(data_dir, parquet_dir=None, force=False):
    parquet_dir = parquet_dir or os.path.join(data_dir, "parquet")
    return {
        "runs": reconstruir_runs(parquet_dir, os.path.join(data_dir, "runs"), force),
        "releases": reconstruir_releases(parquet_dir, os.path.join(data_dir, "releases"), force),
        "commits": reconstruir_commits(parquet_dir, os.path.join(data_dir, "commits"), force),
    }


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="analise.importar_parquet", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--force", action="store_true",
                        help="sobrescreve JSON existentes (por padrão são preservados)")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]

    escritos = importar(data_dir, force=args.force)
    for pasta, n in escritos.items():
        print(f"  data/{pasta:<9} {n} arquivos escritos")
    if not any(escritos.values()):
        print("\nNenhum arquivo escrito: os JSON já existem. Use --force para sobrescrever.")
    else:
        print("\nO pipeline agora retoma do disco, sem recoletar da API.")


if __name__ == "__main__":
    main()
