"""
RQ05/RQ06/RQ07 - Calcula medianas/contagens e gera visualizacoes (SVG) para:
  RQ05: linguagem primaria (contagem por linguagem)
  RQ06: percentual de issues fechadas (closed_issues_ratio)
  RQ07: cruzamento de RQ02/RQ03/RQ04 por linguagem (populares vs. outras, fonte Octoverse)

Dataset: data/repos_1000.csv (990/1000 repositorios - ver nota de metodologia
no relatorio sobre o timeout de paginacao profunda).

Uso:
    python scripts/analyze_rq5_rq6_rq7.py --input data/repos_1000.csv --output data/rq05_rq06_summary.csv --img-dir docs/img
"""

import argparse
import csv
import statistics
from collections import Counter

POPULAR_LANGUAGES = {
    "JavaScript", "Python", "Java", "TypeScript", "C#",
    "C++", "PHP", "Shell", "C", "Ruby",
}

RATIO_BINS = [
    ("0-50%", 0, 0.5), ("50-70%", 0.5, 0.7), ("70-90%", 0.7, 0.9),
    ("90-99%", 0.9, 0.99), ("99-100%", 0.99, 1 + 1e-9),
]


def load_rows(input_path: str) -> list[dict]:
    with open(input_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def percentile(data: list[float], p: float) -> float:
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def summarize(values: list[float]) -> dict:
    q1, q3 = percentile(values, 25), percentile(values, 75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = [v for v in values if v < lo or v > hi]
    return {
        "n": len(values), "min": min(values), "max": max(values),
        "median": statistics.median(values), "mean": statistics.mean(values),
        "p10": percentile(values, 10), "p25": q1, "p75": q3,
        "p90": percentile(values, 90), "p99": percentile(values, 99),
        "outliers": len(outliers),
    }


def bin_counts_ratio(values: list[float], bins) -> list[tuple[str, int]]:
    return [(label, sum(1 for v in values if lo <= v < hi)) for label, lo, hi in bins]


def render_bar_chart_svg(bins: list[tuple[str, float]], title: str, unit_label: str, value_fmt=str) -> str:
    width, height = 640, 300
    pad_left, pad_right, pad_top, pad_bottom = 50, 20, 30, 60
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    max_count = max(c for _, c in bins) or 1
    bar_gap = 10
    bar_w = (plot_w - bar_gap * (len(bins) - 1)) / len(bins)

    bars = []
    for i, (label, count) in enumerate(bins):
        bar_h = (count / max_count) * plot_h
        x = pad_left + i * (bar_w + bar_gap)
        y = pad_top + plot_h - bar_h
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="#2a78d6" />'
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" font-size="11" text-anchor="middle" fill="#52514e">{value_fmt(count)}</text>'
            f'<text x="{x + bar_w / 2:.1f}" y="{pad_top + plot_h + 18:.1f}" font-size="11" text-anchor="middle" fill="#898781">{label}</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" font-family="system-ui,sans-serif">'
        f'<rect width="{width}" height="{height}" fill="#fcfcfb" />'
        f'<text x="{pad_left}" y="18" font-size="13" font-weight="700" fill="#0b0b0b">{title}</text>'
        f'<line x1="{pad_left}" y1="{pad_top + plot_h}" x2="{pad_left + plot_w}" y2="{pad_top + plot_h}" stroke="#c3c2b7" stroke-width="1" />'
        + "".join(bars)
        + f'<text x="{pad_left}" y="{height - 8}" font-size="10.5" fill="#898781">{unit_label}</text>'
        f"</svg>"
    )


def save_svg(svg: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def save_summary_csv(lang_counts, ratio_bins, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "faixa", "repositorios"])
        for label, count in lang_counts:
            writer.writerow(["language", label, count])
        for label, count in ratio_bins:
            writer.writerow(["closed_issues_ratio", label, count])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/repos_1000.csv")
    parser.add_argument("--output", default="data/rq05_rq06_summary.csv")
    parser.add_argument("--img-dir", default="docs/img")
    args = parser.parse_args()

    rows = load_rows(args.input)

    # RQ05 - contagem por linguagem (top 10 + "outras")
    lang_counter = Counter(r["language"] if r["language"] else "(sem linguagem)" for r in rows)
    top_langs = lang_counter.most_common(10)
    other_count = sum(c for _, c in lang_counter.most_common()[10:])
    lang_bins = top_langs + ([("outras", other_count)] if other_count else [])

    # RQ06 - percentual de issues fechadas
    ratios = [float(r["closed_issues_ratio"]) for r in rows if r["closed_issues_ratio"] != ""]
    ratio_stats = summarize(ratios)
    ratio_bins = bin_counts_ratio(ratios, RATIO_BINS)

    save_summary_csv(lang_bins, ratio_bins, args.output)
    save_svg(
        render_bar_chart_svg(lang_bins, "RQ05 - Repositorios por linguagem primaria (top 10)", "Linguagem"),
        f"{args.img_dir}/rq05_language_distribution.svg",
    )
    save_svg(
        render_bar_chart_svg(ratio_bins, "RQ06 - Percentual de issues fechadas", "Faixas de % issues fechadas"),
        f"{args.img_dir}/rq06_closed_issues_distribution.svg",
    )

    # RQ07 - cruzamento por linguagem: populares (Octoverse) vs. outras
    popular_rows = [r for r in rows if r["language"] in POPULAR_LANGUAGES]
    other_rows = [r for r in rows if r["language"] not in POPULAR_LANGUAGES]

    def group_median(group, field):
        return statistics.median(float(r[field]) for r in group)

    pr_bins = [
        ("Populares", round(group_median(popular_rows, "merged_pull_requests"))),
        ("Outras", round(group_median(other_rows, "merged_pull_requests"))),
    ]
    release_bins = [
        ("Populares", round(group_median(popular_rows, "total_releases"))),
        ("Outras", round(group_median(other_rows, "total_releases"))),
    ]
    days_bins = [
        ("Populares", round(group_median(popular_rows, "days_since_update"))),
        ("Outras", round(group_median(other_rows, "days_since_update"))),
    ]

    save_svg(
        render_bar_chart_svg(pr_bins, "RQ07 - Mediana de PRs aceitas: linguagens populares vs. outras", "Grupo de linguagem"),
        f"{args.img_dir}/rq07_prs_by_group.svg",
    )
    save_svg(
        render_bar_chart_svg(release_bins, "RQ07 - Mediana de releases: linguagens populares vs. outras", "Grupo de linguagem"),
        f"{args.img_dir}/rq07_releases_by_group.svg",
    )
    save_svg(
        render_bar_chart_svg(days_bins, "RQ07 - Mediana de dias desde atualizacao: populares vs. outras", "Grupo de linguagem"),
        f"{args.img_dir}/rq07_days_by_group.svg",
    )

    print(f"OK: {len(rows)} repositorios analisados")
    print("RQ05 (top linguagens):", lang_bins)
    print("RQ06 (closed_issues_ratio):", {k: round(v, 4) if isinstance(v, float) else v for k, v in ratio_stats.items()})
    print("RQ07 populares vs outras - PRs:", pr_bins, "| Releases:", release_bins, "| Dias:", days_bins)
    print(f"Resumo salvo em {args.output}")
    print(f"Graficos salvos em {args.img_dir}/rq05_*.svg, rq06_*.svg, rq07_*.svg")


if __name__ == "__main__":
    main()
