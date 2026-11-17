"""Série mensal de ocorrências da SEJUSP-MG (contexto de demanda, RQ4).

Os CSVs (baixados manualmente de dados.mg.gov.br) estão em data/:
furto_consumado.csv (2012–2026) e crimes_violentos_<ano>.csv (2019–2026).
Os arquivos têm nomes de coluna diferentes entre si (ano × ano_fato,
cod_ibge × cod_municipio); aqui tudo é padronizado.

    python -m analise.sejusp            # imprime o resumo e salva data/sejusp/serie_mensal.csv

Limite: são crimes registrados por qualquer canal, não boletins da Delegacia
Virtual. Servem como demanda potencial, não como uso do sistema.
"""
import glob
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
ANOS_PANDEMIA = (2020, 2021)


def _ler(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig")
    df = df.rename(columns={"ano_fato": "ano", "cod_ibge": "cod_municipio"})
    return df[["registros", "natureza", "municipio", "cod_municipio", "mes", "ano", "risp", "rmbh"]]


def carregar_furtos() -> pd.DataFrame:
    return _ler(str(DATA / "furto_consumado.csv"))


def carregar_violentos() -> pd.DataFrame:
    arquivos = sorted(glob.glob(str(DATA / "crimes_violentos_*.csv")))
    return pd.concat([_ler(a) for a in arquivos], ignore_index=True)


def serie_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Total por mês, só com meses que têm dados (o último ano é parcial)."""
    s = df.groupby(["ano", "mes"], as_index=False).registros.sum()
    s = s[s.registros > 0]
    s["data"] = pd.to_datetime(dict(year=s.ano, month=s.mes, day=1))
    return s.sort_values("data").reset_index(drop=True)


def anos_completos(serie: pd.DataFrame) -> list:
    meses = serie.groupby("ano").mes.nunique()
    return sorted(meses[meses == 12].index)


def sazonalidade(serie: pd.DataFrame) -> pd.Series:
    """Desvio % de cada mês em relação à média do próprio ano (anos completos, sem pandemia)."""
    anos = [a for a in anos_completos(serie) if a not in ANOS_PANDEMIA]
    m = serie[serie.ano.isin(anos)].pivot(index="ano", columns="mes", values="registros")
    return (m.div(m.mean(axis=1), axis=0).mean() * 100 - 100).round(1)


def efeito_pandemia(serie: pd.DataFrame) -> dict:
    """Média mensal no isolamento (abr–jul/2020) contra jan–fev/2020 e contra abr–jul/2019."""
    def media(ano, meses):
        return serie[(serie.ano == ano) & serie.mes.isin(meses)].registros.mean()
    antes = media(2020, [1, 2])
    isol = media(2020, [4, 5, 6, 7])
    mesmo_periodo_2019 = media(2019, [4, 5, 6, 7])
    return {
        "media_jan_fev_2020": antes,
        "media_abr_jul_2020": isol,
        "media_abr_jul_2019": mesmo_periodo_2019,
        "queda_vs_jan_fev_pct": (isol / antes - 1) * 100,
        "queda_vs_2019_pct": (isol / mesmo_periodo_2019 - 1) * 100,
    }


def por_rmbh(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["ano", "rmbh"]).registros.sum().unstack()


def main() -> None:
    furtos = carregar_furtos()
    serie = serie_mensal(furtos)
    (DATA / "sejusp").mkdir(exist_ok=True)
    serie.to_csv(DATA / "sejusp" / "serie_mensal_furtos.csv", index=False)

    anual = serie.groupby("ano").registros.sum()
    print("Furtos consumados por ano (MG):")
    print(anual.to_string())
    print("\nEfeito da pandemia:")
    for k, v in efeito_pandemia(serie).items():
        print(f"  {k}: {v:,.1f}")
    print("\nSazonalidade (% em relação à média do ano):")
    print(sazonalidade(serie).to_string())


if __name__ == "__main__":
    main()
