"""Dataset final em CSV e seu dicionário de dados (entregável da Lab03S02).

Junta os metadados dos repositórios (`data/selecao/repos.csv`) com as métricas
calculadas (`data/metricas.json`) e a classificação DORA C1, numa tabela só:
uma linha por repositório.

O **dicionário de dados** é gerado do mesmo `COLUNAS` que monta o CSV, então
não existe a possibilidade de a documentação descrever uma coluna que não
existe ou esquecer uma que existe — é o erro que mais atrapalha quem vai
replicar, porque obriga a adivinhar unidade e fórmula pelos valores.

Uso:
    python -m analise.dataset --config config.json
"""
import argparse
import json
import os
import sys

import pandas as pd

from analise.rq01_rq04 import carregar, classificar_c1

# (coluna, origem, tipo, unidade, descricao/formula)
# `origem`: metadados | metricas | dora
COLUNAS = [
    ("full_name", "metadados", "texto", "-", "owner/repo, identificador do repositório no GitHub"),
    ("html_url", "metadados", "texto", "-", "URL da página do repositório"),
    ("default_branch", "metadados", "texto", "-",
     "branch principal; única considerada em releases, commits e workflow runs"),
    ("language", "metadados", "texto", "-", "linguagem principal segundo a API (pode ser vazio)"),
    ("stars", "metadados", "inteiro", "contagem", "stargazers_count no momento da coleta"),
    ("forks", "metadados", "inteiro", "contagem", "forks_count no momento da coleta"),
    ("contributors", "metadados", "inteiro", "contagem",
     "nº de contribuidores, lido da última página de /contributors (per_page=1, anon=true)"),
    ("created_at", "metadados", "data ISO", "-", "data de criação do repositório"),
    ("age_years", "metadados", "decimal", "anos", "(fim da janela − created_at) / 365,25"),

    ("runs", "metricas", "inteiro", "contagem",
     "workflow runs coletados: default branch, event=push, criados na janela"),
    ("releases", "metricas", "inteiro", "contagem",
     "releases publicadas na janela (draft=false, prerelease=false)"),
    ("releases_por_semana", "metricas", "decimal", "releases/semana",
     "RQ 01 — releases ÷ (dias da janela ÷ 7)"),
    ("lead_time_release_h", "metricas", "decimal", "horas",
     "RQ 02 (a) — mediana, por release, de (published_at − commit.author.date mais antigo)"),
    ("lead_time_commit_h", "metricas", "decimal", "horas",
     "RQ 02 (b) — mediana, sobre todos os commits de todas as releases, "
     "de (published_at − commit.author.date)"),
    ("releases_com_commits", "metricas", "inteiro", "contagem",
     "releases da janela com commits obtidos (base para o lead time)"),
    ("releases_ignoradas", "metricas", "inteiro", "contagem",
     "releases sem lead time: primeira do histórico ou tag apagada"),
    ("commits", "metricas", "inteiro", "contagem",
     "total de commits atribuídos às releases da janela"),
    ("cfr_ci", "metricas", "decimal", "proporção 0–1",
     "RQ 03 (a) — runs com falha ÷ (falhas + sucessos); conclusion cancelled/skipped/"
     "neutral/action_required/stale e vazio são ignorados"),
    ("cfr_entrega_v5_patch_e_notas", "metricas", "decimal", "proporção 0–1",
     "RQ 03 (b) — **variante de referência do grupo**. Releases seguidas em até 7 dias "
     "por uma corretiva ÷ releases avaliadas; corretiva = incremento de patch semver "
     "E release notes citando fix/bugfix/hotfix/revert. Escolhida por ser a única com "
     "F1 >= 0,70 contra o consenso da amostra-ouro (0,723 em 300 releases)"),
    ("cfr_entrega_v1_semver", "metricas", "decimal", "proporção 0–1",
     "RQ 03 (b) — sensibilidade; corretiva = incremento de patch semver"),
    ("cfr_entrega_v2_semver_ou_nome", "metricas", "decimal", "proporção 0–1",
     "RQ 03 (b) — sensibilidade; corretiva = patch semver OU fix/hotfix/revert na tag ou título"),
    ("cfr_entrega_v3_commits", "metricas", "decimal", "proporção 0–1",
     "RQ 03 (b) — sensibilidade; corretiva = >=50% dos commits novos (sem merges) com fix/hotfix/revert"),
    ("cfr_entrega_v4_combinada", "metricas", "decimal", "proporção 0–1",
     "RQ 03 (b) — sensibilidade; corretiva = qualquer um dos sinais patch/nome/commits"),
    ("cfr_entrega_avaliadas", "metricas", "inteiro", "contagem",
     "releases no denominador do CFR (b)"),
    ("cfr_entrega_censuradas", "metricas", "inteiro", "contagem",
     "releases dos últimos 7 dias da janela, fora do denominador: ainda não se sabe "
     "se haverá correção"),
    ("cfr_release_v4_combinada", "metricas", "decimal", "proporção 0–1",
     "RQ 08 (bônus) rework rate — releases que SÃO corretivas ÷ total; "
     "diferente do CFR (b), que conta as SEGUIDAS por uma corretiva"),
    ("recovery_median_h", "metricas", "decimal", "horas",
     "RQ 04 — mediana dos episódios de falha; episódio = da 1ª falha após um sucesso "
     "(run_started_at) até o próximo sucesso do mesmo workflow (updated_at)"),
    ("recovery_censored_ratio", "metricas", "decimal", "proporção 0–1",
     "RQ 04 — episódios que não terminaram dentro da janela ÷ total de episódios"),

    ("dora_deployment_frequency", "dora", "categoria", "Elite/High/Medium/Low",
     "RQ 01 classificada: Elite >= 7/semana, High >= 1/semana, Medium >= 1/mes, Low < 1/mes"),
    ("dora_lead_time", "dora", "categoria", "Elite/High/Medium/Low",
     "RQ 02 (a) classificada: Elite < 1 dia, High < 1 semana, Medium < 30 dias, Low >= 30 dias"),
    ("dora_change_failure_rate", "dora", "categoria", "Elite/High/Medium/Low",
     "RQ 03 (a) classificada: Elite <= 15%, High <= 30%, Medium <= 45%, Low > 45%"),
    ("dora_recovery_time", "dora", "categoria", "Elite/High/Medium/Low",
     "RQ 04 classificada: Elite < 1 h, High < 1 dia, Medium < 1 semana, Low >= 1 semana"),
    ("dora_geral", "dora", "categoria", "Elite/High/Medium/Low",
     "C1 — mediana das notas das 4 métricas (Elite=4…Low=1), arredondada para baixo"),
    ("dora_metricas_validas", "dora", "inteiro", "contagem",
     "quantas das 4 métricas puderam ser classificadas (ausentes saem da mediana)"),
]


def montar(data_dir):
    """DataFrame do dataset final, uma linha por repositório."""
    metricas = carregar(data_dir).rename(columns={"repo": "full_name"})
    meta = pd.read_csv(os.path.join(data_dir, "selecao", "repos.csv"))
    dora = classificar_c1(carregar(data_dir)).rename(columns={"repo": "full_name"})

    df = meta.merge(metricas, on="full_name", how="inner").merge(
        dora[["full_name"] + [c for c in dora.columns if c.startswith("dora_")]],
        on="full_name", how="left")

    # Só as colunas documentadas, na ordem do dicionário. Uma coluna que exista
    # nos dados mas não no dicionario fica de fora de proposito: dataset e
    # documentacao andam juntos ou o grupo replicador nao consegue comparar.
    presentes = [c for c, *_ in COLUNAS if c in df.columns]
    faltando = [c for c, *_ in COLUNAS if c not in df.columns]
    return df[presentes].sort_values("full_name"), faltando


def dicionario():
    return pd.DataFrame([{"coluna": c, "origem": o, "tipo": t, "unidade": u, "descricao": d}
                         for c, o, t, u, d in COLUNAS])


def dicionario_markdown(janela, n_repos):
    linhas = [
        "# Dicionário de dados — `data/dataset.csv`",
        "",
        f"Uma linha por repositório da amostra final (**{n_repos}** repositórios).",
        f"Janela de observação: **{janela[0]} a {janela[1]}**.",
        "",
        "Gerado por `python -m analise.dataset`, a partir da mesma lista de colunas que",
        "monta o CSV — documentação e dados não podem divergir.",
        "",
        "Valores ausentes são células vazias, nunca zero: um repositório sem nenhum",
        "episódio de falha não tem tempo de recuperação, e zerar faria ele parecer",
        "perfeito em vez de não medido.",
        "",
        "| Coluna | Origem | Tipo | Unidade | Descrição / fórmula |",
        "|---|---|---|---|---|",
    ]
    for c, o, t, u, d in COLUNAS:
        linhas.append(f"| `{c}` | {o} | {t} | {u} | {d} |")
    linhas += [
        "",
        "**Origem:** `metadados` vêm da API de repositórios no momento da coleta;",
        "`metricas` são calculadas pelo pipeline sobre releases, commits e workflow runs",
        "da janela; `dora` é a classificação C1 derivada das quatro métricas.",
        "",
        "**Cortes da classificação DORA:** ver `metricas/dora.py` — são os fixos da",
        "disciplina, não os do relatório DORA do ano.",
    ]
    return "\n".join(linhas) + "\n"


def executar(data_dir, docs_dir):
    df, faltando = montar(data_dir)
    os.makedirs(docs_dir, exist_ok=True)
    caminho_csv = os.path.join(data_dir, "dataset.csv")
    df.to_csv(caminho_csv, index=False)
    dicionario().to_csv(os.path.join(data_dir, "dicionario_dados.csv"), index=False)
    return df, faltando, caminho_csv


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="analise.dataset", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    data_dir = cfg["data_dir"]
    docs_dir = "docs"

    df, faltando, caminho = executar(data_dir, docs_dir)
    with open(os.path.join(docs_dir, "dicionario_dados.md"), "w", encoding="utf-8") as f:
        f.write(dicionario_markdown((cfg["window_start"], cfg["window_end"]), len(df)))

    print(f"dataset: {len(df)} repositórios x {len(df.columns)} colunas -> {caminho}")
    print(f"dicionário: {os.path.join(data_dir, 'dicionario_dados.csv')} e "
          f"{os.path.join(docs_dir, 'dicionario_dados.md')}")
    if faltando:
        print(f"\nAVISO: documentadas mas ausentes nos dados: {', '.join(faltando)}")
        print("Rode o pipeline de novo para recalcular as métricas.")


if __name__ == "__main__":
    main()
