"""Roda o Lighthouse (versão fixada no config) nas páginas públicas, em mobile e desktop.

Só carrega as páginas, como um cidadão faria; não preenche nem envia nada.
Uma execução por vez, com pausa entre elas. Salva o JSON bruto em
data/lighthouse/raw/ e uma linha resumida por (página, dispositivo) em
data/lighthouse/resultados.csv.

    python -m coleta.lighthouse --config config.json [--repeticoes 5] [--paginas dv_inicio ...]

Requer Node.js e Google Chrome instalados (usa `npx lighthouse@<versao>`).
"""
import argparse
import csv
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

CAMPOS = [
    "timestamp_utc", "pagina", "dispositivo", "rede", "repeticao",
    "nota_performance", "nota_acessibilidade", "nota_boas_praticas", "nota_seo",
    "lcp_ms", "fcp_ms", "tbt_ms", "cls", "speed_index_ms", "peso_total_kb",
    "violacoes_acessibilidade", "erro",
]


def resumir(rel: dict) -> dict:
    cat = rel.get("categories", {})
    aud = rel.get("audits", {})

    def nota(k):
        s = cat.get(k, {}).get("score")
        return "" if s is None else round(s * 100)

    def num(k):
        v = aud.get(k, {}).get("numericValue")
        return "" if v is None else round(v, 3)

    # auditorias de acessibilidade que falharam (score 0) = violações detectadas pelo axe-core
    refs = cat.get("accessibility", {}).get("auditRefs", [])
    violacoes = [r["id"] for r in refs if r.get("weight", 0) > 0 and aud.get(r["id"], {}).get("score") == 0]
    peso = aud.get("total-byte-weight", {}).get("numericValue")
    return {
        "nota_performance": nota("performance"),
        "nota_acessibilidade": nota("accessibility"),
        "nota_boas_praticas": nota("best-practices"),
        "nota_seo": nota("seo"),
        "lcp_ms": num("largest-contentful-paint"),
        "fcp_ms": num("first-contentful-paint"),
        "tbt_ms": num("total-blocking-time"),
        "cls": num("cumulative-layout-shift"),
        "speed_index_ms": num("speed-index"),
        "peso_total_kb": "" if peso is None else round(peso / 1024, 1),
        "violacoes_acessibilidade": "|".join(violacoes),
    }


def flags_perfil(perfil: dict) -> list:
    """Converte um perfil do config (preset + rede simulada) em flags do Lighthouse."""
    if perfil.get("preset") == "desktop":
        return ["--preset=desktop"]
    flags = ["--form-factor=mobile", "--throttling-method=simulate"]
    if "rtt_ms" in perfil:
        flags += [f"--throttling.rttMs={perfil['rtt_ms']}",
                  f"--throttling.throughputKbps={perfil['kbps']}",
                  f"--throttling.cpuSlowdownMultiplier={perfil.get('cpu', 4)}"]
    return flags


def rodar(url: str, perfil: dict, versao: str, categorias: list, saida_json: Path) -> dict:
    cmd = [
        "npx", "--yes", f"lighthouse@{versao}", url,
        "--output=json", f"--output-path={saida_json}",
        f"--only-categories={','.join(categorias)}",
        "--chrome-flags=--headless=new", "--quiet", *flags_perfil(perfil),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not saida_json.exists():
        return {"erro": (proc.stderr.strip().splitlines() or ["falha"])[-1][:200]}
    rel = json.loads(saida_json.read_text(encoding="utf-8"))
    if rel.get("runtimeError"):
        return {"erro": rel["runtimeError"].get("code", "runtimeError")}
    return {**resumir(rel), "erro": ""}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--repeticoes", type=int, default=None)
    ap.add_argument("--paginas", nargs="*", help="subconjunto das páginas do config")
    ap.add_argument("--saida", default="data/lighthouse/resultados.csv")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    lh = cfg["lighthouse"]
    reps = args.repeticoes or lh.get("repeticoes", 1)
    paginas = {k: v for k, v in cfg["paginas"].items() if not args.paginas or k in args.paginas}
    saida = Path(args.saida)
    raw = saida.parent / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    novo = not saida.exists()

    with saida.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        if novo:
            w.writeheader()
        for rep in range(1, reps + 1):
            for nome, url in paginas.items():
                for nome_perfil, perfil in lh["perfis"].items():
                    disp = "desktop" if perfil.get("preset") == "desktop" else "mobile"
                    rede = "cabo" if disp == "desktop" else nome_perfil.split("_")[-1]
                    ts = datetime.now(timezone.utc)
                    arq = raw / f"{ts:%Y%m%dT%H%M%S}_{nome}_{nome_perfil}.json"
                    res = rodar(url, perfil, lh["versao"], lh["categorias"], arq)
                    linha = {"timestamp_utc": ts.isoformat(timespec="seconds"), "pagina": nome,
                             "dispositivo": disp, "rede": rede, "repeticao": rep, **res}
                    w.writerow(linha)
                    f.flush()
                    print(f"{nome:<22} {nome_perfil:<10} perf={linha.get('nota_performance','')!s:>3} "
                          f"a11y={linha.get('nota_acessibilidade','')!s:>3} lcp={linha.get('lcp_ms','')} {linha['erro']}")
                    time.sleep(2)


if __name__ == "__main__":
    main()
