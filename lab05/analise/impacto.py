"""RQ5: quanto a espera custa ao cidadão? (M13, M14)

M13 = registros/ano × Σ LCP das telas do fluxo, ponderado pela fração de
acessos no celular. As telas do fluxo e os LCPs são as medianas medidas
(analise/desempenho.py). Análise de sensibilidade em 3 eixos: fração no
celular, rede (4G × 3G) e telas não medidas após a identificação.

M14 = pessoas com deficiência visual em MG (estimativa: taxa nacional do
Censo 2022 aplicada à população mineira; conferir no SIDRA quando a tabela
por UF e tipo estiver disponível).

    python -m analise.impacto     # imprime e salva data/impacto/cenarios.csv
"""
import json
from pathlib import Path

import pandas as pd

from analise.desempenho import carregar

RAIZ = Path(__file__).resolve().parent.parent
# Tribuna de Minas (30/04/2021): 205,8 mil registros online de jan. a nov./2020 -> 12 meses.
REGISTROS_ANO = round(205_800 / 11 * 12)
# IBGE, Censo 2022: 7,9 mi com dificuldade de enxergar / 203,1 mi habitantes; MG: 20.539.989 hab.
TAXA_DEF_VISUAL_BR = 7.9e6 / 203.1e6
POP_MG = 20_539_989
PCD_MG = 1_472_199  # Censo 2022, total de pessoas com deficiência em MG (qualquer tipo)


def lcp_fluxo() -> dict:
    """Σ das medianas de LCP (s) das telas do fluxo, por perfil; e LCP mediano da última tela medida."""
    telas = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))["fluxo_perda_documento"]["telas"]
    med = carregar().groupby(["perfil", "pagina"])["lcp_ms"].median().unstack() / 1000
    return {p: {"soma_s": float(med.loc[p, telas].sum()), "ultima_s": float(med.loc[p, telas[-1]]),
                "n_telas": len(telas)} for p in med.index}


def cenarios(registros: int = REGISTROS_ANO) -> pd.DataFrame:
    fl = lcp_fluxo()
    linhas = []
    for frac in (0.5, 0.7, 0.9):
        for rede in ("4g", "3g"):
            for extras in (0, 2, 4):  # telas após a identificação, supostas iguais à última medida
                mob = fl[f"mobile_{rede}"]
                desk = fl["desktop"]
                t_mob = mob["soma_s"] + extras * mob["ultima_s"]
                t_desk = desk["soma_s"] + extras * desk["ultima_s"]
                seg = registros * (frac * t_mob + (1 - frac) * t_desk)
                seg_desk = registros * t_desk
                linhas.append({"fracao_celular": frac, "rede_celular": rede, "telas": mob["n_telas"] + extras,
                               "espera_por_registro_s": round(frac * t_mob + (1 - frac) * t_desk, 1),
                               "horas_ano": round(seg / 3600), "horas_se_tudo_no_computador": round(seg_desk / 3600),
                               "horas_extras_pelo_celular": round((seg - seg_desk) / 3600)})
    return pd.DataFrame(linhas)


def populacao_def_visual_mg() -> int:
    return round(TAXA_DEF_VISUAL_BR * POP_MG)


def main() -> None:
    c = cenarios()
    print(f"Registros/ano (2020): {REGISTROS_ANO:,}".replace(",", "."))
    for p, v in lcp_fluxo().items():
        print(f"  {p:<10} Σ LCP do fluxo = {v['soma_s']:.1f} s")
    print(c.to_string(index=False))
    base = c[(c.fracao_celular == .7) & (c.rede_celular == "4g") & (c.telas == 4)].iloc[0]
    br = lambda n: f"{int(n):,}".replace(",", ".")
    print(f"\nCenário base (70% celular, 4G, 4 telas): {br(base.horas_ano)} h/ano "
          f"(faixa {br(c.horas_ano.min())}–{br(c.horas_ano.max())} h)")
    print(f"M14 pessoas com deficiência visual em MG (estimativa): {populacao_def_visual_mg():,}".replace(",", "."))
    out = RAIZ / "data" / "impacto"
    out.mkdir(exist_ok=True)
    c.to_csv(out / "cenarios.csv", index=False)


if __name__ == "__main__":
    main()
