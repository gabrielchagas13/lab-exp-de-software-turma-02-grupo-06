"""Exporta os dados brutos da coleta para Parquet, versionáveis no repositório.

Os JSON por repositório somam ~1,45 GB e não cabem no git (limite de 100 MB por
arquivo). Em Parquet o mesmo conteúdo, **sem perder nenhum campo**, cai para
~157 MB em arquivos bem abaixo do limite — o bastante para o dado bruto entrar
no repositório e ficar disponível para o resto do grupo e para quem for
replicar o estudo.

Por que encolhe tanto: Parquet é colunar e usa dicionário para valores
repetidos. `conclusion` tem três valores possíveis em 2,1 milhões de linhas de
workflow runs, e o nome do workflow se repete milhares de vezes por
repositório — esse tipo de coluna praticamente desaparece.

**Normalização dos commits.** O mesmo commit aparece em várias comparações
release-a-release (são 2,9 milhões de linhas para 911 mil commits distintos,
efeito dos `compare` que cruzam linhas de versão). Guardar o conteúdo do commit
uma vez só, com uma tabela de vínculo separada, corta pela metade sem perder
informação: `commits` responde "o que é este commit" e `release_commits`
responde "em quais releases ele entra".

**Isto é exportação, não substituição.** Os JSON em `data/{runs,releases,
commits}` continuam sendo o que o pipeline lê para retomar a coleta. Apagá-los
achando que o Parquet os substitui faz a próxima execução recoletar tudo do
zero, que são horas de API.

Uso:
    python -m analise.exportar_parquet --config config.json

Leitura de volta:
    import pandas as pd
    runs = pd.read_parquet("data/parquet/runs.parquet")
    # ou só as colunas necessárias, sem carregar o resto:
    pd.read_parquet("data/parquet/commits.parquet", columns=["repo", "author_date"])
"""
import argparse
import json
import os
import sys

import pandas as pd

COMPRESSAO = "zstd"   # melhor razão que snappy e lido por qualquer pyarrow recente


def _ler_json(pasta):
    """Itera (nome_do_arquivo, conteúdo) de uma pasta de JSON por repositório."""
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".json"):
            continue
        with open(os.path.join(pasta, nome), encoding="utf-8") as f:
            yield json.load(f)


def tabelas_runs(data_dir):
    """workflow runs + os campos de controle da coleta.

    `splits` e `capped_days` registram onde a janela precisou ser subdividida
    por causa do teto de 1.000 resultados da API; sem eles não dá para saber
    se algum dia ficou truncado."""
    runs, coleta = [], []
    for d in _ler_json(os.path.join(data_dir, "runs")):
        repo = d["repo"]
        runs.extend({"repo": repo, **r} for r in d.get("runs", []))
        coleta.append({"repo": repo, "branch": d.get("branch"),
                       "splits": d.get("splits"), "capped_days": d.get("capped_days") or []})
    return {"runs": pd.DataFrame(runs), "runs_coleta": pd.DataFrame(coleta)}


def tabelas_releases(data_dir):
    """releases (com o `body` completo) e as tags, usadas na variante C3 da RQ 07."""
    releases, tags = [], []
    for d in _ler_json(os.path.join(data_dir, "releases")):
        repo = d["repo"]
        releases.extend({"repo": repo, **r} for r in d.get("releases", []))
        tags.extend({"repo": repo, **t} for t in d.get("tags", []))
    return {"releases": pd.DataFrame(releases), "tags": pd.DataFrame(tags)}


def tabelas_commits(data_dir):
    """Commits normalizados em três tabelas.

    - `commits`: um commit por (repo, sha), com data e mensagem.
    - `release_commits`: quais commits entram em cada release (só as chaves).
    - `commits_coleta`: procedência (`git` ou `api`) e releases puladas, com o
      motivo — primeira release do histórico ou tag apagada.
    """
    vinculo, conteudo, coleta = [], {}, []
    for d in _ler_json(os.path.join(data_dir, "commits")):
        repo = d["repo"]
        coleta.append({"repo": repo, "fonte": d.get("fonte"),
                       "releases_puladas": len(d.get("skipped") or [])})
        for pulada in d.get("skipped") or []:
            coleta[-1].setdefault("_puladas", []).append(pulada)
        for rel in d.get("releases", []):
            for c in rel["commits"]:
                vinculo.append({"repo": repo, "tag": rel["tag"],
                                "base_tag": rel["base_tag"], "sha": c["sha"]})
                conteudo.setdefault((repo, c["sha"]), {
                    "repo": repo, "sha": c["sha"], "author_date": c["author_date"],
                    "committer_date": c.get("committer_date"), "message": c.get("message")})

    puladas = [{"repo": c["repo"], **p}
               for c in coleta for p in c.pop("_puladas", [])]
    return {"commits": pd.DataFrame(list(conteudo.values())),
            "release_commits": pd.DataFrame(vinculo),
            "commits_coleta": pd.DataFrame(coleta),
            "releases_puladas": pd.DataFrame(puladas)}


def exportar(data_dir, saida=None):
    """Grava todas as tabelas. Retorna [{tabela, linhas, bytes}]."""
    saida = saida or os.path.join(data_dir, "parquet")
    os.makedirs(saida, exist_ok=True)

    tabelas = {}
    tabelas.update(tabelas_runs(data_dir))
    tabelas.update(tabelas_releases(data_dir))
    tabelas.update(tabelas_commits(data_dir))

    resumo = []
    for nome, df in tabelas.items():
        caminho = os.path.join(saida, f"{nome}.parquet")
        df.to_parquet(caminho, compression=COMPRESSAO, index=False)
        resumo.append({"tabela": nome, "linhas": len(df),
                       "bytes": os.path.getsize(caminho)})
    return resumo


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="analise.exportar_parquet", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]

    resumo = exportar(data_dir)
    print(f"{'tabela':<20} {'linhas':>10} {'tamanho':>10}")
    print("-" * 42)
    for r in sorted(resumo, key=lambda x: -x["bytes"]):
        print(f"{r['tabela']:<20} {r['linhas']:>10} {r['bytes'] / 1e6:>8.1f} MB")
    total = sum(r["bytes"] for r in resumo)
    print("-" * 42)
    print(f"{'TOTAL':<20} {'':>10} {total / 1e6:>8.1f} MB")

    acima = [r for r in resumo if r["bytes"] >= 100e6]
    if acima:
        print("\nATENÇÃO: o GitHub recusa arquivos de 100 MB ou mais:")
        for r in acima:
            print(f"  {r['tabela']}.parquet = {r['bytes'] / 1e6:.1f} MB")
    print(f"\nGravado em {os.path.join(data_dir, 'parquet')}/")
    print("Os JSON em data/{runs,releases,commits} continuam necessários para "
          "a retomada do pipeline — não apague.")


if __name__ == "__main__":
    main()
