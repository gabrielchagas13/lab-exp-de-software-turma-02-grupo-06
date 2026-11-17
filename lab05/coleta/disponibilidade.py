"""Checagem de disponibilidade das páginas públicas da Delegacia Virtual (MG).

Cada execução faz UMA requisição GET por página, com no mínimo 1 s entre
requisições (regra de ética do enunciado), e acrescenta uma linha por página em
data/disponibilidade/checagens.csv. Para o estudo longitudinal, agende com cron
(ex.: a cada 15 min). Nunca envia formulários nem dados.

    python -m coleta.disponibilidade --config config.json
"""
import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

CAMPOS = ["timestamp_utc", "pagina", "url", "status_http", "ok", "tempo_s", "bytes", "erro"]


def checar(url: str, user_agent: str, timeout: float = 30.0) -> dict:
    inicio = time.perf_counter()
    try:
        r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
        return {
            "status_http": r.status_code,
            "ok": int(200 <= r.status_code < 400),
            "tempo_s": round(time.perf_counter() - inicio, 3),
            "bytes": len(r.content),
            "erro": "",
        }
    except requests.RequestException as e:
        return {
            "status_http": "",
            "ok": 0,
            "tempo_s": round(time.perf_counter() - inicio, 3),
            "bytes": 0,
            "erro": type(e).__name__,
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--saida", default="data/disponibilidade/checagens.csv")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    intervalo = max(1.0, float(cfg["intervalo_min_requisicoes_s"]))
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    novo = not saida.exists()

    with saida.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        for i, (nome, url) in enumerate(cfg["paginas"].items()):
            if i:
                time.sleep(intervalo)
            linha = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "pagina": nome,
                "url": url,
                **checar(url, cfg["user_agent"]),
            }
            w.writerow(linha)
            print(f"{linha['pagina']:<22} {linha['status_http']!s:>4} {linha['tempo_s']:>6}s {linha['erro']}")


if __name__ == "__main__":
    main()
