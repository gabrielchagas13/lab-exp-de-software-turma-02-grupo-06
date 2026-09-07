"""
RQ07 - Sistemas escritos em linguagens mais populares recebem mais
contribuicao externa, lancam mais releases e sao atualizados com mais
frequencia? Agrupa os resultados de RQ02, RQ03 e RQ04 por linguagem
primaria (RQ05), a partir do CSV gerado por fetch_repos.py.

Fonte de referencia para "linguagens mais populares": GitHub Octoverse
(https://octoverse.github.com) - mesma fonte usada na RQ05.

Uso:
    python fetch_repos_rq7.py --input data/repos_completo.csv --output data/rq07_by_language.csv
"""

import argparse
import csv
import statistics
from collections import defaultdict

# Top 10 linguagens mais populares segundo o GitHub Octoverse (ranking mais
# recente disponivel), usado como referencia para classificar cada linguagem
# do dataset como "popular" ou nao.
POPULAR_LANGUAGES = {
    "JavaScript", "Python", "Java", "TypeScript", "C#",
    "C++", "PHP", "Shell", "C", "Ruby",
}


def load_rows(input_path: str) -> list[dict]:
    with open(input_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_number(value: str):
    if value in (None, ""):
        return None
    return float(value)


def analyze(rows: list[dict]) -> list[dict]:
    by_language = defaultdict(list)
    for row in rows:
        language = row["language"] or "(sem linguagem)"
        by_language[language].append(row)

    results = []
    for language, repos in by_language.items():
        merged_prs = [to_number(r["merged_pull_requests"]) for r in repos]
        releases = [to_number(r["total_releases"]) for r in repos]
        days_since_update = [v for r in repos if (v := to_number(r["days_since_update"])) is not None]

        results.append({
            "language": language,
            "is_popular_language": language in POPULAR_LANGUAGES,
            "repo_count": len(repos),
            "median_merged_pull_requests": statistics.median(merged_prs),
            "median_total_releases": statistics.median(releases),
            "median_days_since_update": statistics.median(days_since_update) if days_since_update else None,
        })

    results.sort(key=lambda r: r["repo_count"], reverse=True)
    return results


def save_csv(rows: list[dict], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/repos_completo.csv", help="CSV gerado por fetch_repos.py")
    parser.add_argument("--output", default="data/rq07_by_language.csv", help="CSV de saida com o cruzamento por linguagem")
    args = parser.parse_args()

    rows = load_rows(args.input)
    results = analyze(rows)
    save_csv(results, args.output)

    print(f"OK: {len(results)} linguagens analisadas, salvo em {args.output}")
    popular = [r for r in results if r["is_popular_language"]]
    other = [r for r in results if not r["is_popular_language"]]
    popular_repo_count = sum(r["repo_count"] for r in popular)
    other_repo_count = sum(r["repo_count"] for r in other)
    print(f"Repositorios em linguagens populares (Octoverse): {popular_repo_count}")
    print(f"Repositorios em outras linguagens: {other_repo_count}")


if __name__ == "__main__":
    main()
