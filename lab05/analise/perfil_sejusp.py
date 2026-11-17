"""Perfil rápido do CSV de ocorrências da SEJUSP-MG (baixado manualmente).

O portal dados.mg.gov.br bloqueia acesso automatizado (HTTP 403), então o
arquivo é baixado pelo navegador e salvo em data/sejusp/. Este script mostra
colunas, tipos, período coberto e valores mais frequentes, para decidir quais
perguntas do GQM os dados conseguem responder.

    python -m analise.perfil_sejusp --config config.json [--arquivo data/sejusp/x.csv]
"""
import argparse
import json
from pathlib import Path

import pandas as pd


def carregar(caminho: Path, sep: str, encoding: str) -> pd.DataFrame:
    for enc in (encoding, "utf-8", "latin-1"):
        try:
            return pd.read_csv(caminho, sep=sep, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não consegui ler {caminho}")


def perfil(df: pd.DataFrame) -> None:
    print(f"Linhas: {len(df):,} | Colunas: {df.shape[1]}\n")
    for c in df.columns:
        s = df[c]
        top = s.value_counts(dropna=True).head(5)
        print(f"- {c} [{s.dtype}] nulos={s.isna().mean():.1%} distintos={s.nunique():,}")
        print("    top:", "; ".join(f"{k} ({v:,})" for k, v in top.items()))
    for c in df.columns:
        if any(t in c.lower() for t in ("data", "ano", "mes", "mês")):
            print(f"\nFaixa de {c}: {df[c].min()} → {df[c].max()}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--arquivo")
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))["sejusp"]
    caminho = Path(args.arquivo or cfg["arquivo"])
    if not caminho.exists():
        raise SystemExit(f"Arquivo não encontrado: {caminho}. Baixe pelo navegador (ver README).")
    perfil(carregar(caminho, cfg["separador"], cfg["encoding"]))


if __name__ == "__main__":
    main()
