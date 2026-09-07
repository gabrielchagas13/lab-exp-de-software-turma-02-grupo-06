"""
RQ01/RQ02 - Calcula medianas/contagens e gera visualizacoes (SVG) para:
  RQ01: idade do repositorio (age_years)
  RQ02: total de pull requests aceitas (merged_pull_requests)

Dataset: data/repos_rq1_rq2_1000.csv (1000/1000 repositorios, dataset
completo usado para RQ01/RQ02 - ver nota de metodologia no relatorio sobre
o timeout de paginacao profunda em data/repos_1000.csv).

Uso:
    python scripts/analyze_rq1_rq2.py --input data/repos_rq1_rq2_1000.csv --output data/rq01_rq02_summary.csv --img-dir docs/img
"""

import argparse
import csv
import statistics


AGE_BINS = [("0-1", 0, 1), ("1-3", 1, 3), ("3-5", 3, 5), ("5-10", 5, 10), ("10-15", 10, 15), ("15+", 15, float("inf"))]
PR_BINS = [
    ("0", 0, 1e-9), ("1-50", 1e-9, 50), ("51-200", 50, 200), ("201-1000", 200, 1000),
    ("1001-5000", 1000, 5000), ("5001-20000", 5000, 20000), ("20000+", 20000, float("inf")),
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


def bin_counts(pairs: list[tuple[str, float]], bins: list[tuple[str, float, float]]) -> list[tuple[str, int]]:
    return [(label, sum(1 for _, v in pairs if lo <= v < hi)) for label, lo, hi in bins]


def summarize(values: list[float]) -> dict:
    q1, q3 = percentile(values, 25), percentile(values, 75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = [v for v in values if v < lo or v > hi]
    return {
        "n": len(values),
        "min": min(values),
        "max": max(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "p10": percentile(values, 10),
        "p25": q1,
        "p75": q3,
        "p90": percentile(values, 90),
        "p99": percentile(values, 99),
        "outliers": len(outliers),
    }


def render_bar_chart_svg(bins: list[tuple[str, int]], title: str, unit_label: str) -> str:
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
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" font-size="11" text-anchor="middle" fill="#52514e">{count}</text>'
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


def save_summary_csv(age_bins, pr_bins, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "faixa", "repositorios"])
        for label, count in age_bins:
            writer.writerow(["age_years", label, count])
        for label, count in pr_bins:
            writer.writerow(["merged_pull_requests", label, count])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/repos_rq1_rq2_1000.csv")
    parser.add_argument("--output", default="data/rq01_rq02_summary.csv")
    parser.add_argument("--img-dir", default="docs/img")
    args = parser.parse_args()

    rows = load_rows(args.input)
    ages = [(r["repo"], float(r["age_years"])) for r in rows]
    prs = [(r["repo"], float(r["merged_pull_requests"])) for r in rows]

    age_stats = summarize([v for _, v in ages])
    pr_stats = summarize([v for _, v in prs])
    age_bins = bin_counts(ages, AGE_BINS)
    pr_bins = bin_counts(prs, PR_BINS)

    save_summary_csv(age_bins, pr_bins, args.output)
    save_svg(render_bar_chart_svg(age_bins, "RQ01 - Idade dos repositorios (anos)", "Faixas de idade (anos)"), f"{args.img_dir}/rq01_age_distribution.svg")
    save_svg(render_bar_chart_svg(pr_bins, "RQ02 - Pull requests aceitas (merged)", "Faixas de PRs aceitas"), f"{args.img_dir}/rq02_prs_distribution.svg")

    print(f"OK: {len(rows)} repositorios analisados")
    print("RQ01 (age_years):", {k: round(v, 2) if isinstance(v, float) else v for k, v in age_stats.items()})
    print("RQ02 (merged_pull_requests):", {k: round(v, 2) if isinstance(v, float) else v for k, v in pr_stats.items()})
    print(f"Resumo salvo em {args.output}")
    print(f"Graficos salvos em {args.img_dir}/rq01_age_distribution.svg e {args.img_dir}/rq02_prs_distribution.svg")


if __name__ == "__main__":
    main()
