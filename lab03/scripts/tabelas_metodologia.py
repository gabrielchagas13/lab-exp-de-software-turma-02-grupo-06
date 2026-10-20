"""Tabelas da seção de Metodologia, geradas a partir dos dados (issue #70).

Gera três tabelas, cada uma em Markdown e em LaTeX, em `docs/tabelas/`:

- `funil`: etapas da seleção de repositórios, de `data/selecao/funil.csv`, com
  os critérios preenchidos a partir do `config.json` (mínimos de releases/runs);
- `definicoes`: definição operacional de cada métrica e variante, a coluna
  correspondente em `metricas.json` e quantos repositórios têm valor nela;
- `amostra_ouro`: parâmetros da validação manual, de `data/validacao/amostra.json`.

As versões Markdown também são escritas no relatório (`docs/relatorio.md`),
entre os marcadores `<!-- tabela:<nome> -->` e `<!-- /tabela:<nome> -->`. Assim
os números do texto nunca ficam desatualizados em relação aos dados: depois de
uma nova coleta (S02, >= 300 repositórios), basta rodar o script de novo.

Uso:
    python -m scripts.tabelas_metodologia --config config.json
"""
import argparse
import csv
import json
import os
import re
from datetime import date

from metricas.corretiva import VARIANTES

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Critério de cada etapa do funil; {min_releases}/{min_runs} vêm do config.
CRITERIOS = {
    "candidatos (busca)": "Resultado da busca por faixas de estrelas, sem duplicatas",
    "fork_ou_arquivado": "Descarta forks e repositórios arquivados",
    "sem_push_na_janela": "Descarta quem não teve push durante a janela",
    "inacessivel": "Descarta erros da API (404, 451...)",
    "sem_actions": "Descarta quem não tem workflows do GitHub Actions",
    "poucas_releases": "Exige >= {min_releases} releases publicadas (sem draft e sem pré-release) na janela",
    "poucos_runs": "Exige >= {min_runs} runs válidos (push, default branch, sucesso/falha) na janela",
    "amostra_final": "Sorteio (semente {seed}) até completar {sample_size}; o resto não é avaliado",
}

# (métrica, RQ, variante, definição operacional, unidade, coluna em metricas.json)
DEFINICOES = [
    ("Frequência de deploy", "RQ01", "principal",
     "Releases publicadas (sem draft e sem pré-release) na janela / semanas da janela",
     "releases/semana", "releases_por_semana"),
    ("Lead time", "RQ02", "(a) por release",
     "Mediana, entre as releases, de publicação − `author_date` do commit mais antigo que ela entrega",
     "horas", "lead_time_release_h"),
    ("Lead time", "RQ02", "(b) por commit",
     "Mediana, sobre todos os commits novos, de publicação da release − `author_date`",
     "horas", "lead_time_commit_h"),
    ("Change failure rate", "RQ03", "(a) proxy de CI",
     "Falhas / (falhas + sucessos) dos runs de push no default branch; falha = "
     "`failure`, `timed_out`, `startup_failure`", "proporção", "cfr_ci"),
    ("Change failure rate", "RQ03", "(b) v1 semver",
     "Releases corretivas / releases da janela; corretiva = tag semver X.Y.Z com Z > 0",
     "proporção", "cfr_release_v1_semver"),
    ("Change failure rate", "RQ03", "(b) v2 semver ou nome",
     "Como (b) v1, ou tag/título com fix, hotfix, bugfix ou revert",
     "proporção", "cfr_release_v2_semver_ou_nome"),
    ("Change failure rate", "RQ03", "(b) v3 commits",
     "Corretiva = ao menos metade dos commits novos (sem merges) com fix, hotfix, bugfix ou revert",
     "proporção", "cfr_release_v3_commits"),
    ("Change failure rate", "RQ03", "(b) v4 combinada",
     "Corretiva = qualquer um dos sinais de v1, v2 ou v3",
     "proporção", "cfr_release_v4_combinada"),
    ("Tempo de recuperação", "RQ04", "principal",
     "Mediana, por workflow, de sucesso seguinte − primeira falha após um sucesso "
     "(episódios sem sucesso posterior são censurados)", "horas", "recovery_median_h"),
    ("Tempo de recuperação", "RQ04", "censura",
     "Proporção de episódios de falha censurados", "proporção", "recovery_censored_ratio"),
]

# Uma linha de DEFINICOES por variante de CFR (b): se alguém criar uma variante
# nova na heurística, a tabela do artigo precisa acompanhar.
assert {f"cfr_release_{v}" for v in VARIANTES} <= {d[5] for d in DEFINICOES}


# ---- renderização -----------------------------------------------------------

def markdown(cabecalho, linhas):
    def celula(v):
        return str(v).replace("|", "\\|")
    out = ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    out += ["| " + " | ".join(celula(v) for v in linha) + " |" for linha in linhas]
    return "\n".join(out)


_LATEX = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
          "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
          "^": r"\textasciicircum{}", ">=": r"$\geq$", ">": r"$>$", "<": r"$<$",
          "−": "--"}


def latex_escape(texto):
    texto = re.sub(r"`([^`]*)`", r"\1", str(texto))   # crase de código só faz sentido no md
    padrao = re.compile("|".join(re.escape(k) for k in sorted(_LATEX, key=len, reverse=True)))
    return padrao.sub(lambda m: _LATEX[m.group(0)], texto)


def latex(cabecalho, linhas, legenda, rotulo, colunas=None):
    colunas = colunas or "l" * len(cabecalho)
    corpo = [" & ".join(latex_escape(v) for v in linha) + r" \\" for linha in linhas]
    return "\n".join([
        r"\begin{table}[htbp]", r"\centering", f"\\caption{{{latex_escape(legenda)}}}",
        f"\\label{{tab:{rotulo}}}", f"\\begin{{tabular}}{{{colunas}}}", r"\hline",
        " & ".join(latex_escape(c) for c in cabecalho) + r" \\", r"\hline",
        *corpo, r"\hline", r"\end{tabular}", r"\end{table}"])


# ---- tabelas ----------------------------------------------------------------

def _ler_csv(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def tabela_funil(data_dir, selecao):
    """Linhas do funil com critério, restantes e descartados."""
    parametros = {"min_releases": 5, "min_runs": 50, "seed": 42, "sample_size": 100, **selecao}
    linhas = []
    for etapa in _ler_csv(os.path.join(data_dir, "selecao", "funil.csv")):
        criterio = CRITERIOS.get(etapa["etapa"], etapa["motivo"]).format(**parametros)
        descartados = etapa["descartados"]
        if etapa["etapa"] == "amostra_final":
            descartados = f"{descartados} (não avaliados)"
        linhas.append([etapa["etapa"], criterio, etapa["restantes"], descartados])
    return ["Etapa", "Critério", "Restantes", "Descartados"], linhas


def resumo_buscas(data_dir):
    """Frase sobre a cobertura da busca (teto de 1.000 resultados por consulta)."""
    buscas = _ler_csv(os.path.join(data_dir, "selecao", "buscas.csv"))
    existentes = sum(int(b["total_count"]) for b in buscas)
    obtidos = sum(int(b["fetched"]) for b in buscas)
    return (f"{len(buscas)} buscas por faixa de estrelas retornaram {obtidos} de "
            f"{existentes} repositórios existentes (a API limita cada busca a 1.000 resultados).")


def tabela_definicoes(data_dir):
    """Definições operacionais com a cobertura de cada coluna em metricas.json."""
    caminho = os.path.join(data_dir, "metricas.json")
    metricas = []
    if os.path.isfile(caminho):
        with open(caminho, encoding="utf-8") as f:
            metricas = json.load(f)
    total = len(metricas)
    linhas = []
    for metrica, rq, variante, definicao, unidade, coluna in DEFINICOES:
        n = sum(1 for m in metricas if m.get(coluna) is not None)
        linhas.append([metrica, rq, variante, definicao, unidade, f"`{coluna}`", f"{n}/{total}"])
    return ["Métrica", "RQ", "Variante", "Definição operacional", "Unidade", "Coluna",
            "Repos com valor"], linhas


def tabela_amostra_ouro(data_dir):
    with open(os.path.join(data_dir, "validacao", "amostra.json"), encoding="utf-8") as f:
        amostra = json.load(f)
    return ["Parâmetro", "Valor"], [
        ["Semente do sorteio", amostra["seed"]],
        ["Repositórios sorteados", amostra["n_repos"]],
        ["Releases sorteadas (até 5 por repositório)", amostra["n_releases_total"]],
        ["Avaliadores independentes", 3],
        ["Dimensões rotuladas", "tipo do projeto; releases são entregas reais; release corretiva"],
        ["Concordância", "kappa de Fleiss por dimensão (Landis & Koch)"],
        ["Consenso", "maioria simples; 1-1-1 decidido em reunião"],
    ]


# ---- saída ------------------------------------------------------------------

def gerar(cfg, dir_saida, relatorio=None):
    """Grava as tabelas em `dir_saida` e, se dado, atualiza o relatório. Devolve {nome: md}."""
    data_dir = cfg["data_dir"]
    inicio, fim = date.fromisoformat(cfg["window_start"]), date.fromisoformat(cfg["window_end"])
    janela = f"Janela de observação: {inicio} a {fim} ({(fim - inicio).days + 1} dias)."

    cab_f, lin_f = tabela_funil(data_dir, cfg.get("selection", {}))
    cab_d, lin_d = tabela_definicoes(data_dir)
    cab_a, lin_a = tabela_amostra_ouro(data_dir)
    tabelas = {
        "funil": (cab_f, lin_f, "Funil de seleção dos repositórios", "llrr",
                  f"{resumo_buscas(data_dir)} {janela}"),
        "definicoes": (cab_d, lin_d, "Definições operacionais e variantes das métricas",
                       "lllp{6cm}lll", ""),
        "amostra_ouro": (cab_a, lin_a, "Protocolo da validação manual (amostra-ouro)", "lp{8cm}", ""),
    }

    os.makedirs(dir_saida, exist_ok=True)
    gerado = {}
    for nome, (cab, linhas, legenda, colunas, nota) in tabelas.items():
        md = markdown(cab, linhas) + (f"\n\n{nota}" if nota else "")
        with open(os.path.join(dir_saida, f"{nome}.md"), "w", encoding="utf-8") as f:
            f.write(f"**{legenda}**\n\n{md}\n")
        with open(os.path.join(dir_saida, f"{nome}.tex"), "w", encoding="utf-8") as f:
            f.write(latex(cab, linhas, legenda, nome, colunas) + "\n")
        gerado[nome] = md

    if relatorio and os.path.isfile(relatorio):
        injetar(relatorio, gerado)
    return gerado


def injetar(caminho, tabelas):
    """Substitui o conteúdo entre `<!-- tabela:X -->` e `<!-- /tabela:X -->`."""
    with open(caminho, encoding="utf-8") as f:
        texto = f.read()
    for nome, md in tabelas.items():
        padrao = re.compile(rf"(<!-- tabela:{nome} -->\n).*?(<!-- /tabela:{nome} -->)", re.DOTALL)
        texto = padrao.sub(lambda m: f"{m.group(1)}{md}\n{m.group(2)}", texto)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="scripts.tabelas_metodologia", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--saida", default=os.path.join(RAIZ, "docs", "tabelas"))
    parser.add_argument("--relatorio", default=os.path.join(RAIZ, "docs", "relatorio.md"))
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    gerado = gerar(cfg, args.saida, args.relatorio)
    print(f"Tabelas ({', '.join(gerado)}) gravadas em {args.saida} (.md e .tex); "
          f"relatório atualizado: {args.relatorio}")


if __name__ == "__main__":
    main()
