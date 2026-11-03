"""Coleta o tempo até o merge de PRs com e sem review do bot (#76).

Uso: python -m coleta --config config.json
"""
import argparse
import csv
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import numpy as np

API = "https://api.github.com/search/issues"


def token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def get_com_retry(req, tentativas=6):
    """Repete com espera crescente quando a API devolve 403/429 (rate limit)."""
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429) or i == tentativas - 1:
                raise
            espera = int(e.headers.get("Retry-After") or 30 * (i + 1))
            print(f"rate limit, aguardando {espera}s")
            time.sleep(espera)


def buscar(q, paginas, tok):
    """Busca PRs pela Search API (até 100 por página)."""
    itens = []
    for page in range(1, paginas + 1):
        url = API + "?" + urllib.parse.urlencode({"q": q, "per_page": 100, "page": page, "sort": "created", "order": "desc"})
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
        lote = get_com_retry(req)["items"]
        itens += lote
        if len(lote) < 100:
            break
        time.sleep(3)  # evita o rate limit secundário da busca
    return itens


def horas_ate_merge(item):
    criado = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
    merge = datetime.fromisoformat(item["pull_request"]["merged_at"].replace("Z", "+00:00"))
    return (merge - criado).total_seconds() / 3600


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    cfg = json.loads(Path(ap.parse_args().config).read_text())["coleta"]
    tok = token()
    rng = np.random.default_rng(cfg["seed"])
    base = f"repo:{cfg['repo']} is:pr is:merged merged:{cfg['janela']} " + " ".join(f"-author:{a}" for a in cfg["excluir_autores"])
    consultas = {"com_bot": f"{base} reviewed-by:{cfg['bot']}", "sem_bot": f"{base} -reviewed-by:{cfg['bot']}"}

    linhas = []
    for grupo, q in consultas.items():
        candidatos = buscar(q, cfg["paginas"], tok)
        escolhidos = rng.choice(len(candidatos), size=cfg["n_por_grupo"], replace=False)
        for i in sorted(escolhidos):
            it = candidatos[i]
            linhas.append({
                "grupo": grupo,
                "numero": it["number"],
                "autor": it["user"]["login"],
                "criado_em": it["created_at"],
                "merge_em": it["pull_request"]["merged_at"],
                "horas_ate_merge": round(horas_ate_merge(it), 4),
                "url": it["html_url"],
            })
        print(f"{grupo}: {len(candidatos)} candidatos, {cfg['n_por_grupo']} sorteados")

    saida = Path(cfg["saida"])
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"salvo em {saida}")


if __name__ == "__main__":
    main()
