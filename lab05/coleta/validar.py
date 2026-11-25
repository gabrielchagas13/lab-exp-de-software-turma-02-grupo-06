"""Validação dos dados coletados (Lighthouse, disponibilidade, segurança).

    python -m coleta.validar          # imprime os problemas; sai com código 1 se houver erro grave

Regras:
- Lighthouse: notas em 0–100, métricas >= 0, CLS em [0, 5], sem erro de execução,
  5 repetições por (página, perfil) e nenhuma linha duplicada.
- Disponibilidade: status HTTP numérico quando ok=1.
- Segurança: os três CSVs existem e não estão vazios.
"""
import sys
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
NOTAS = ["nota_performance", "nota_acessibilidade", "nota_boas_praticas", "nota_seo"]
METRICAS = ["lcp_ms", "fcp_ms", "tbt_ms", "speed_index_ms", "peso_total_kb"]


def validar_lighthouse(df: pd.DataFrame, repeticoes: int = 5) -> list:
    erros = []
    falhas = df[df["erro"].astype("string").fillna("") != ""]
    if len(falhas):
        erros.append(f"lighthouse: {len(falhas)} execução(ões) com erro: {sorted(set(falhas['erro']))}")
    ok = df[df["erro"].astype("string").fillna("") == ""]
    for c in NOTAS:
        fora = ok[(ok[c] < 0) | (ok[c] > 100)]
        if len(fora):
            erros.append(f"lighthouse: {len(fora)} valor(es) de {c} fora de 0–100")
    for c in METRICAS:
        if (ok[c] < 0).any():
            erros.append(f"lighthouse: {c} negativo")
    if ((ok["cls"] < 0) | (ok["cls"] > 5)).any():
        erros.append("lighthouse: CLS fora de [0, 5]")
    chave = ["pagina", "dispositivo", "rede", "repeticao"]
    dup = ok[ok.duplicated(chave, keep=False)]
    if len(dup):
        erros.append(f"lighthouse: {len(dup)} linha(s) duplicada(s) em {chave}")
    principal = ok[ok["repeticao"] > 0]  # repetição 0 = piloto
    cont = principal.groupby(["pagina", "dispositivo", "rede"]).size()
    faltando = cont[cont < repeticoes]
    for idx, n in faltando.items():
        erros.append(f"lighthouse: {idx} tem {n}/{repeticoes} repetições")
    return erros


def validar_disponibilidade(df: pd.DataFrame) -> list:
    ruins = df[(df["ok"] == 1) & df["status_http"].isna()]
    return [f"disponibilidade: {len(ruins)} linha(s) ok=1 sem status HTTP"] if len(ruins) else []


def validar_seguranca(pasta: Path) -> list:
    erros = []
    for arq in ["cabecalhos.csv", "tls.csv", "bibliotecas.csv"]:
        p = pasta / arq
        if not p.exists() or len(pd.read_csv(p)) == 0:
            erros.append(f"segurança: {arq} ausente ou vazio (rode python -m coleta.seguranca)")
    return erros


def main() -> int:
    erros = []
    lh = DATA / "lighthouse" / "resultados.csv"
    if lh.exists():
        erros += validar_lighthouse(pd.read_csv(lh))
    else:
        erros.append("lighthouse: resultados.csv ausente")
    disp = DATA / "disponibilidade" / "checagens.csv"
    if disp.exists():
        erros += validar_disponibilidade(pd.read_csv(disp))
    erros += validar_seguranca(DATA / "seguranca")
    for e in erros:
        print("✗", e)
    if not erros:
        print("✓ dados válidos")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
