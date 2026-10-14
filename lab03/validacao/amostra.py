"""Sorteio da amostra-ouro e geração das planilhas de rotulagem (enunciado, seção 6).

Sorteia 60 repositórios da amostra final e 5 releases de cada um, com semente
fixa e documentada, e gera uma planilha por avaliador com **links diretos** para
o repositório e para cada release no GitHub.

Os três integrantes rotulam de forma independente, sem consultar os demais e
sem ver a saída da heurística de release corretiva: é essa independência que dá
sentido ao kappa de Fleiss calculado em `concordancia.py` (issue #66). Por isso
as planilhas saem com as colunas de rótulo **vazias** e um arquivo por pessoa.

Uso:
    python -m validacao.amostra --config config.json
"""
import argparse
import csv
import html
import json
import os
import random

SEED = 42          # semente do sorteio; fixa para o sorteio ser reproduzível
N_REPOS = 60       # tamanho da amostra-ouro (enunciado, seção 6.1)
N_RELEASES = 5     # releases sorteadas por repositório (enunciado, seção 6.2.iii)
AVALIADORES = ("mv", "gc", "gl")   # Marcus Vinicius, Gabriel Chagas, Guilherme Lana

COLUNAS_REPOS = ["full_name", "url", "linguagem", "estrelas", "tipo_projeto",
                 "releases_sao_entregas"]
COLUNAS_RELEASES = ["full_name", "tag", "url", "release_nome", "notas",
                    "n_commits", "commits", "corretiva"]

MAX_NOTAS = 400        # trecho das release notes embutido na planilha
MAX_COMMITS = 12       # mensagens de commit mostradas por release

# IMPORTANTE: a planilha traz apenas EVIDÊNCIA BRUTA (notas da release e
# mensagens de commit), que é o que o enunciado manda o avaliador ler. Não
# embute sinais derivados — "mudou só o patch", "tem 'fix' nos commits" — porque
# esses são exatamente as entradas da heurística automática. Mostrá-los
# induziria o avaliador a concordar com a heurística, e a precisão/recall
# medidos depois seriam inflados por construção.

# Valores aceitos em cada coluna de rótulo, repetidos no cabeçalho de ajuda.
OPCOES = {
    "tipo_projeto": "biblioteca | aplicacao | cli | outro",
    "releases_sao_entregas": "sim | nao | incerto",
    "corretiva": "sim | nao",
}


def _arquivo(data_dir, pasta, full_name):
    return os.path.join(data_dir, pasta, full_name.replace("/", "__") + ".json")


def _arquivo_releases(data_dir, full_name):
    return _arquivo(data_dir, "releases", full_name)


def _uma_linha(texto, limite):
    """Achata o texto para caber numa célula de planilha, sem quebras de linha.

    Release notes vêm em Markdown com HTML no meio; as entidades `&nbsp;` e afins
    viram ruído ilegível na planilha e atrapalham a leitura do avaliador."""
    limpo = html.unescape(texto or "").replace("\xa0", " ")
    limpo = " ".join(limpo.split())
    return limpo[:limite] + ("..." if len(limpo) > limite else "")


def commits_por_tag(data_dir, full_name):
    """{tag: [mensagens]} a partir dos commits já coletados na mineração.

    Evita que o avaliador precise abrir a página de cada release no navegador:
    a evidência que ele tem que ler vem junto na planilha."""
    caminho = _arquivo(data_dir, "commits", full_name)
    if not os.path.isfile(caminho):
        return {}
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    return {item["tag"]: [c["message"] for c in item["commits"]]
            for item in dados.get("releases", [])}


def releases_da_janela(data_dir, full_name):
    """Releases elegíveis para rotulagem: na janela, publicadas, sem pré-release."""
    caminho = _arquivo_releases(data_dir, full_name)
    if not os.path.isfile(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    return [r for r in dados.get("releases", [])
            if r.get("in_window") and not r.get("prerelease")]


def sortear(data_dir, n_repos=N_REPOS, n_releases=N_RELEASES, seed=SEED):
    """Sorteia repositórios e releases. Retorna (linhas_repos, linhas_releases).

    O mesmo objeto `random.Random(seed)` é usado do começo ao fim: dada a mesma
    amostra final e a mesma semente, o sorteio é sempre idêntico.
    """
    with open(os.path.join(data_dir, "selecao", "repos.csv"), encoding="utf-8") as f:
        meta = {linha["full_name"]: linha for linha in csv.DictReader(f)}
    todos = list(meta)

    rng = random.Random(seed)
    escolhidos = sorted(rng.sample(todos, min(n_repos, len(todos))))

    linhas_repos, linhas_releases = [], []
    for full_name in escolhidos:
        info = meta.get(full_name, {})
        linhas_repos.append({"full_name": full_name,
                             "url": f"https://github.com/{full_name}",
                             "linguagem": info.get("language", ""),
                             "estrelas": info.get("stars", ""),
                             "tipo_projeto": "", "releases_sao_entregas": ""})
        disponiveis = releases_da_janela(data_dir, full_name)
        msgs_por_tag = commits_por_tag(data_dir, full_name)
        for rel in sorted(rng.sample(disponiveis, min(n_releases, len(disponiveis))),
                          key=lambda r: r.get("published_at") or ""):
            tag = rel["tag_name"]
            msgs = msgs_por_tag.get(tag, [])
            linhas_releases.append({
                "full_name": full_name, "tag": tag,
                "url": f"https://github.com/{full_name}/releases/tag/{tag}",
                "release_nome": _uma_linha(rel.get("name"), 120),
                "notas": _uma_linha(rel.get("body"), MAX_NOTAS),
                "n_commits": len(msgs),
                "commits": " | ".join(_uma_linha(m, 100) for m in msgs[:MAX_COMMITS]),
                "corretiva": ""})
    return linhas_repos, linhas_releases


def _gravar(caminho, colunas, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def gerar_planilhas(data_dir, avaliadores=AVALIADORES, **kwargs):
    """Grava uma planilha por avaliador em `data/validacao/`.

    Nunca sobrescreve um arquivo existente: depois que alguém começou a
    preencher, regerar apagaria o trabalho dessa pessoa. Para refazer de fato,
    apague o arquivo à mão.
    """
    destino = os.path.join(data_dir, "validacao")
    os.makedirs(destino, exist_ok=True)
    linhas_repos, linhas_releases = sortear(data_dir, **kwargs)

    criados, preservados = [], []
    for inic in avaliadores:
        for nivel, colunas, linhas in (("repos", COLUNAS_REPOS, linhas_repos),
                                       ("releases", COLUNAS_RELEASES, linhas_releases)):
            caminho = os.path.join(destino, f"rotulos_{nivel}_{inic}.csv")
            if os.path.exists(caminho):
                preservados.append(os.path.basename(caminho))
                continue
            _gravar(caminho, colunas, linhas)
            criados.append(os.path.basename(caminho))

    # Registro do sorteio: sem isto, ninguém consegue repetir a amostragem.
    with open(os.path.join(destino, "amostra.json"), "w", encoding="utf-8") as f:
        json.dump({"seed": kwargs.get("seed", SEED),
                   "n_repos": len({r["full_name"] for r in linhas_repos}),
                   "n_releases_total": len(linhas_releases),
                   "repos": [r["full_name"] for r in linhas_repos]}, f, indent=2)

    return {"criados": criados, "preservados": preservados,
            "n_repos": len(linhas_repos), "n_releases": len(linhas_releases)}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="validacao.amostra", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        data_dir = json.load(f)["data_dir"]

    res = gerar_planilhas(data_dir)
    print(f"amostra-ouro: {res['n_repos']} repositórios, {res['n_releases']} releases "
          f"(semente {SEED})")
    for nome in res["criados"]:
        print(f"  criado     {nome}")
    for nome in res["preservados"]:
        print(f"  preservado {nome} (já existe; apague à mão para refazer)")
    print("\nColunas a preencher:")
    for coluna, opcoes in OPCOES.items():
        print(f"  {coluna:<24} {opcoes}")
    print("\nRotule sem consultar os colegas e sem ver a saída da heurística.")


if __name__ == "__main__":
    main()
