"""RQ1 (M2, M3): resultado do teste manual com teclado e VoiceOver.

O teste é feito por uma pessoa, seguindo data/acessibilidade/checklist.csv
(4 telas do fluxo "perda de documento" × 14 critérios WCAG 2.1). Em cada linha,
preencha `resultado` com: passa | falha | nao_aplica.

    python -m analise.checklist_wcag

Junta com as violações automáticas do Lighthouse/axe e responde H1:
a tela falha se tiver >= 1 violação de nível A ou AA (manual ou automática).
M3 = a tarefa é concluível só com teclado se nenhuma tela falhar em 2.1.1/2.1.2.
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
VALIDOS = {"passa", "falha", "nao_aplica"}
CRITERIOS_TECLADO = {"2.1.1", "2.1.2"}


def carregar(caminho: Path = DATA / "acessibilidade" / "checklist.csv") -> pd.DataFrame:
    df = pd.read_csv(caminho, dtype=str).fillna("")
    df["resultado"] = df["resultado"].str.strip().str.lower()
    invalidos = df[(df["resultado"] != "") & ~df["resultado"].isin(VALIDOS)]
    if len(invalidos):
        raise ValueError(f"resultados inválidos: {sorted(set(invalidos['resultado']))}")
    return df


def resumir(df: pd.DataFrame) -> dict:
    preenchido = df[df["resultado"] != ""]
    falhas = preenchido[preenchido["resultado"] == "falha"]
    por_tela = (falhas.groupby("tela")["criterio_wcag"].apply(lambda s: "|".join(sorted(s)))
                .reindex(df["tela"].unique(), fill_value=""))
    teclado_ok = not falhas["criterio_wcag"].isin(CRITERIOS_TECLADO).any()
    return {
        "progresso": f"{len(preenchido)}/{len(df)}",
        "completo": len(preenchido) == len(df),
        "falhas_por_tela": por_tela.to_dict(),
        "tarefa_so_teclado": teclado_ok if len(preenchido) else None,
        "h1_todas_telas_falham": bool(len(preenchido)) and (por_tela != "").all(),
    }


def main() -> None:
    r = resumir(carregar())
    print(f"Checklist preenchido: {r['progresso']}")
    if not r["completo"]:
        print("⚠ teste manual incompleto: preencha a coluna `resultado` (passa | falha | nao_aplica)")
    for tela, f in r["falhas_por_tela"].items():
        print(f"  {tela:<26} falhas: {f or '—'}")
    print(f"M3 tarefa só com teclado: {r['tarefa_so_teclado']}")
    print(f"H1 (toda tela com ≥ 1 falha A/AA): {r['h1_todas_telas_falham']}")


if __name__ == "__main__":
    main()
