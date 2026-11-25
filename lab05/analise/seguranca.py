"""RQ3: o sistema é seguro? (H3: faltam CSP/HSTS e há bibliotecas JS com CVE)

Resume os CSVs de coleta/seguranca.py por host.

    python -m analise.seguranca      # imprime e salva data/seguranca/resumo.csv
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "seguranca"


def resumo_hosts() -> pd.DataFrame:
    cab = pd.read_csv(DATA / "cabecalhos.csv")
    tls = pd.read_csv(DATA / "tls.csv")
    lib = pd.read_csv(DATA / "bibliotecas.csv")
    pags = pd.read_csv(DATA / "cabecalhos.csv")[["pagina", "host"]].drop_duplicates()
    lib = lib.merge(pags, on="pagina")
    linhas = []
    for host, g in cab.groupby("host", sort=False):
        por_cab = g.groupby("cabecalho")["presente"].max()
        l = lib[lib.host == host].drop_duplicates(["biblioteca", "versao"])
        t = tls[tls.host == host].iloc[0]
        cves = sorted({c for s in l.cves.dropna() for c in s.split("|")})
        linhas.append({
            "host": host,
            "cabecalhos_ausentes": "|".join(por_cab[por_cab == 0].index),
            "n_cabecalhos_ausentes": int((por_cab == 0).sum()),
            "tem_csp": bool(por_cab.get("content-security-policy", 0)),
            "tem_hsts": bool(por_cab.get("strict-transport-security", 0)),
            "aceita_tls_obsoleto": bool(t.tls1_0 == 1 or t.tls1_1 == 1),
            "aceita_tls1_3": bool(t.tls1_3 == 1),
            "bibliotecas": "|".join(f"{a} {b}" for a, b in zip(l.biblioteca, l.versao)),
            "bibliotecas_vulneraveis": int((l.n_cves > 0).sum()),
            "cves": "|".join(cves), "n_cves": len(cves),
            "cert_dias_para_expirar": t.dias_para_expirar,
        })
    return pd.DataFrame(linhas)


def bibliotecas() -> pd.DataFrame:
    lib = pd.read_csv(DATA / "bibliotecas.csv")
    pags = pd.read_csv(DATA / "cabecalhos.csv")[["pagina", "host"]].drop_duplicates()
    return (lib.merge(pags, on="pagina").drop_duplicates(["host", "biblioteca", "versao"])
            [["host", "biblioteca", "versao", "cves", "n_cves"]].fillna({"cves": ""}))


def main() -> None:
    r = resumo_hosts()
    print(r.T.to_string())
    h3 = (~r.tem_csp).any() and (r.bibliotecas_vulneraveis > 0).any()
    print(f"\nH3 (falta CSP/HSTS e há biblioteca com CVE): {'confirmada' if h3 else 'não confirmada'}")
    r.to_csv(DATA / "resumo.csv", index=False)


if __name__ == "__main__":
    main()
