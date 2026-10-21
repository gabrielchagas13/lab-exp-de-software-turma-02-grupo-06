"""Commits entre releases via clone local, no lugar do endpoint `compare`.

Por que trocar a API por git
----------------------------
Na coleta de 100 repositórios, as chamadas ao `compare` foram ~75% de todo o
tráfego (≈22.000 de 29.276). Um único repositório, o `frappe/erpnext`, custou
~5.600 chamadas e 1h23 — porque ele mantém v14, v15 e v16 em paralelo, e o
`compare` entre releases de ramos diferentes varre a divergência inteira,
paginada de 100 em 100.

Um clone `--bare --filter=tree:0` baixa só os objetos de commit (sem conteúdo
de arquivo). O mesmo `erpnext` leva **17 segundos e 42 MB**, e daí em diante
`git log base..head` responde localmente, sem nenhuma chamada à API.

Além de mais rápido, é mais correto: o `compare` **trunca em 10.000 commits**.
Na validação contra os dados já coletados do `erpnext`, 134 dos 184 pares
bateram exatamente, e os 50 divergentes eram todos casos em que a API parou em
10.000 — com o conjunto dela contido no do git. Para esses, o "commit mais
antigo da release" (variante (a) do lead time, RQ 02) estava errado.

Semântica
---------
`GET /compare/base...head` devolve os commits alcançáveis a partir de `head` e
não de `base`, a partir do merge base — que é exatamente `git log base..head`.
A equivalência foi verificada em `tests/test_git_local.py`.

Os workflow runs (RQ 03a e RQ 04) e as releases continuam vindo da API: não
existem no clone, porque são recursos do GitHub e não do git.
"""
import os
import subprocess

# Só os objetos de commit: sem árvores nem blobs, que é o que pesa num clone.
CLONE_ARGS = ["--bare", "--filter=tree:0", "--quiet"]
SEP = "\x1f"  # separador improvável dentro de uma mensagem de commit
LOG_FORMAT = SEP.join(["%H", "%aI", "%cI", "%s"])


class GitError(Exception):
    """Falha ao executar git (clone indisponível, referência inexistente...)."""


def _git(*args, cwd=None, timeout=600):
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode:
        raise GitError((proc.stderr or proc.stdout).strip()[:300])
    return proc.stdout


def caminho_clone(clones_dir, repo):
    return os.path.join(clones_dir, repo.replace("/", "__") + ".git")


def clonar(repo, clones_dir, *, url=None):
    """Garante o clone local e devolve o caminho. Reaproveita se já existir.

    O clone existente não é atualizado: a janela de observação é fechada e os
    dados precisam ficar estáveis entre execuções. Para recoletar, apague a
    pasta."""
    destino = caminho_clone(clones_dir, repo)
    if os.path.isdir(destino):
        return destino
    os.makedirs(clones_dir, exist_ok=True)
    url = url or f"https://github.com/{repo}.git"
    try:
        _git("clone", *CLONE_ARGS, url, destino, timeout=1800)
    except GitError:
        # Servidor sem suporte a partial clone: cai para o clone bare completo.
        if os.path.isdir(destino):
            _rmtree(destino)
        _git("clone", "--bare", "--quiet", url, destino, timeout=1800)
    return destino


def _rmtree(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


def tag_existe(repo_dir, tag):
    """Tag presente no clone. Tags apagadas no GitHub somem daqui também."""
    try:
        _git("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}", cwd=repo_dir)
        return True
    except GitError:
        return False


def commits_entre(repo_dir, base, head):
    """Commits alcançáveis de `head` e não de `base`, do mais novo ao mais antigo.

    Mesmo formato dos commits vindos da API (`pipeline.commits._slim`), para que
    o restante do pipeline e as métricas não precisem saber de onde vieram.
    """
    saida = _git("log", f"--format={LOG_FORMAT}", f"{base}..{head}", cwd=repo_dir)
    commits = []
    for linha in saida.splitlines():
        if not linha.strip():
            continue
        partes = linha.split(SEP)
        if len(partes) < 4:
            continue
        sha, author_date, committer_date, message = partes[0], partes[1], partes[2], partes[3]
        commits.append({"sha": sha, "author_date": author_date,
                        "committer_date": committer_date, "message": message})
    return commits


def disponivel():
    """git instalado e utilizável."""
    try:
        _git("--version", timeout=30)
        return True
    except (GitError, OSError, subprocess.SubprocessError):
        return False
